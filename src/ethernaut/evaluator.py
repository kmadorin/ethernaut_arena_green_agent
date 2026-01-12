"""EthernautEvaluator - Green Agent for multi-level evaluation using A2A SDK."""

import argparse
import asyncio
import json
import re
import logging
import uvicorn
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
load_dotenv()

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Part,
    TextPart,
    DataPart,
    TaskState,
)
from a2a.utils import new_agent_text_message
from web3 import Web3
from solcx import compile_source, install_solc, get_installed_solc_versions, set_solc_version

from agentbeats.green_executor import GreenAgent, GreenExecutor
from agentbeats.models import EvalRequest, EvalResult
from agentbeats.tool_provider import ToolProvider

from ethernaut.anvil_manager import AnvilManager
from ethernaut.js_sandbox import JSSandbox
from ethernaut.metrics import MetricsTracker, MultiLevelMetricsTracker
from ethernaut.levels import get_level_config, get_all_levels

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ethernaut_evaluator")


def ensure_solc_installed(version: str = "0.8.20") -> None:
    """Ensure solc compiler is installed for attack contract compilation.

    This enables realistic compilation of attack contracts in isolation,
    similar to how players use Remix in the real Ethernaut game.

    Args:
        version: Solidity version to install (default 0.8.20)
    """
    installed = get_installed_solc_versions()

    if not any(str(v).startswith(version) for v in installed):
        logger.info(f"Installing solc {version} for attack contract compilation...")
        install_solc(version)
        logger.info(f"solc {version} installed successfully")
    else:
        logger.debug(f"solc {version} already installed")


def ethernaut_evaluator_agent_card(name: str, url: str) -> AgentCard:
    """Create the agent card for the multi-level Ethernaut evaluator.

    Args:
        name: Agent name
        url: Agent URL endpoint

    Returns:
        AgentCard with multi-level Ethernaut skill
    """
    skill = AgentSkill(
        id="ethernaut_multi_level",
        name="Ethernaut Multi-Level Evaluation",
        description="Evaluates agents on multiple Ethernaut challenges (levels 0-40)",
        tags=["blockchain", "ethereum", "smart-contracts", "ethernaut", "multi-level"],
        examples=[
            '{"participants": {"agent": "http://localhost:9020"}, "config": {"levels": [0, 1, 2]}}',
            '{"participants": {"agent": "http://localhost:9020"}, "config": {"levels": "all"}}',
        ],
    )
    return AgentCard(
        name=name,
        description="Multi-level Ethernaut evaluator - tests smart contract interaction skills across 41 challenges",
        url=url,
        version="2.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )


class EthernautEvaluator(GreenAgent):
    """Green Agent for multi-level Ethernaut evaluation."""

    def __init__(self):
        """Initialize EthernautEvaluator."""
        self._required_roles = ["agent"]
        self._required_config_keys = []  # Optional: levels, max_turns_per_level, timeout_per_level
        self._tool_provider = ToolProvider()
        self._anvil: AnvilManager | None = None
        self._sandbox: JSSandbox | None = None
        self._multi_metrics = MultiLevelMetricsTracker()
        self._current_instance: str | None = None
        self._current_level_contracts: dict = {}
        self._current_level_config: Any | None = None
        self._current_tracker: MetricsTracker | None = None
        self._player_account: str | None = None
        logger.info("EthernautEvaluator initialized")

    def validate_request(self, request: EvalRequest) -> tuple[bool, str]:
        """Validate that request has required roles.

        Args:
            request: Evaluation request to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        missing_roles = set(self._required_roles) - set(request.participants.keys())
        if missing_roles:
            return False, f"Missing roles: {missing_roles}"
        return True, "ok"

    def _parse_levels(self, levels_config: Any) -> list[int]:
        """Parse levels configuration into list of level IDs.

        Args:
            levels_config: Can be "all", a single int, or a list of ints

        Returns:
            List of level IDs to run

        Raises:
            ValueError: If configuration is invalid
        """
        if levels_config == "all":
            return get_all_levels()
        elif isinstance(levels_config, int):
            return [levels_config]
        elif isinstance(levels_config, list):
            return sorted(levels_config)
        else:
            raise ValueError(
                f"Invalid levels config: {levels_config}. "
                f"Must be 'all', an int, or a list of ints."
            )

    async def run_eval(self, req: EvalRequest, updater: TaskUpdater) -> None:
        """Main evaluation loop using A2A communication.

        Args:
            req: Evaluation request
            updater: Task updater for reporting progress
        """
        logger.info(f"Starting multi-level evaluation: {req}")

        agent_url = str(req.participants["agent"])
        levels_to_run = self._parse_levels(req.config.get("levels", [0]))
        max_turns_per_level = req.config.get("max_turns_per_level", 30)
        stop_on_failure = req.config.get("stop_on_failure", False)

        logger.info(f"Running levels: {levels_to_run}")

        try:
            # === ONE-TIME SETUP PHASE ===
            await updater.update_status(
                TaskState.working,
                new_agent_text_message("Setting up Ethernaut environment...")
            )

            # Ensure solc is available for attack contract compilation
            ensure_solc_installed("0.8.20")

            # Start Anvil and deploy main Ethernaut contract
            self._anvil = AnvilManager()
            anvil_info = await self._anvil.start(port=8545)
            logger.info(f"Anvil started: {anvil_info['rpc_url']}")
            logger.info(f"Ethernaut deployed at: {anvil_info['ethernaut_address']}")

            self._player_account = anvil_info["accounts"][0]
            player_private_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

            # Start JS Sandbox (will be reset between levels)
            self._sandbox = JSSandbox()
            await self._sandbox.start(
                rpc_url=anvil_info["rpc_url"],
                contracts={
                    "ethernaut_address": anvil_info["ethernaut_address"],
                    "ethernaut_abi": anvil_info["ethernaut_abi"],
                },
                player_key=player_private_key,
            )
            logger.info("JS Sandbox started")

            # Start multi-level metrics tracking
            self._multi_metrics.start()

            # === LEVEL LOOP ===
            for level_id in levels_to_run:
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(f"Starting Level {level_id}...")
                )

                try:
                    await self._run_single_level(
                        level_id=level_id,
                        agent_url=agent_url,
                        max_turns=max_turns_per_level,
                        updater=updater,
                    )
                except Exception as e:
                    logger.error(f"Level {level_id} failed with error: {e}")
                    # Note: Metrics already recorded in _run_single_level's finally block

                    if stop_on_failure:
                        logger.info("stop_on_failure=true, halting evaluation")
                        break

            # === RESULTS PHASE ===
            aggregate_metrics = self._multi_metrics.calculate_aggregate_metrics()

            # Determine winner based on overall success rate
            success_rate = aggregate_metrics["success_rate"]
            winner = "agent" if success_rate >= 0.5 else "evaluator"

            result = EvalResult(winner=winner, detail=aggregate_metrics)

            await updater.add_artifact(
                parts=[
                    Part(root=TextPart(
                        text=f"Completed {aggregate_metrics['levels_completed']}/{aggregate_metrics['levels_attempted']} levels"
                    )),
                    Part(root=DataPart(data=result.model_dump())),
                ],
                name="Multi-Level Result",
            )

            logger.info(
                f"Evaluation complete. Success rate: {success_rate:.1%} "
                f"({aggregate_metrics['levels_completed']}/{aggregate_metrics['levels_attempted']} levels)"
            )

        finally:
            # === CLEANUP ===
            logger.info("Cleaning up environment...")
            self._tool_provider.reset()

            if self._sandbox:
                try:
                    await self._sandbox.stop()
                    logger.info("JS Sandbox stopped")
                except Exception as e:
                    logger.error(f"Failed to stop sandbox: {e}")

            if self._anvil:
                try:
                    await self._anvil.stop()
                    logger.info("Anvil stopped")
                except Exception as e:
                    logger.error(f"Failed to stop Anvil: {e}")

    async def _run_single_level(
        self,
        level_id: int,
        agent_url: str,
        max_turns: int,
        updater: TaskUpdater,
    ) -> None:
        """Run evaluation for a single level.

        Args:
            level_id: The level to run
            agent_url: URL of the purple agent
            max_turns: Maximum turns for this level
            updater: Task updater for status updates
        """
        level_config = get_level_config(level_id)
        logger.info(f"=== Starting Level {level_id}: {level_config.name} ===")

        # RESET context for fresh conversation
        self._tool_provider.reset()
        tracker = MetricsTracker()
        tracker.start()

        try:
            # Store current level config for tools to access
            self._current_level_config = level_config

            # Deploy this level's factory and get instance ABI
            level_contracts = await self._anvil.deploy_level_factory(level_config)
            self._current_level_contracts = {
                **level_contracts,
                "ethernaut_address": self._anvil.ethernaut_address,
                "ethernaut_abi": self._anvil.ethernaut_abi,
            }
            logger.info(f"Level {level_id} factory deployed")

            # Register level-specific tools
            self._register_tools(level_config)

            # Run A2A loop for this level
            await self._run_a2a_loop(
                level_config=level_config,
                agent_url=agent_url,
                max_turns=max_turns,
                tracker=tracker,
                updater=updater,
            )

        except Exception as e:
            logger.error(f"Error in level {level_id}: {e}")
            raise

        finally:
            # Record metrics for this level
            self._multi_metrics.record_level_result(
                level_id=level_id,
                level_name=level_config.name,
                tracker=tracker,
                expected_methods=level_config.expected_methods,
                error_message=None if tracker.level_completed else "Level not completed",
            )

            logger.info(
                f"=== Level {level_id} complete. Success: {tracker.level_completed} ==="
            )

    def _register_tools(self, level_config) -> None:
        """Register all available tools with tool provider.

        Args:
            level_config: Configuration for the current level
        """
        self._tool_provider.register_tool(
            name="get_new_instance",
            description=f"Deploy a new instance of Level {level_config.level_id} ({level_config.name}). This creates a new instance contract and updates the global 'contract' variable in the console.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

        self._tool_provider.register_tool(
            name="exec_console",
            description="""Execute JavaScript code in the Ethernaut console.

AVAILABLE GLOBALS AND FUNCTIONS:
• player: Your wallet address (string)
• ethernaut: Main Ethernaut game contract (ethers.Contract)
• contract: Current level instance contract (ethers.Contract)
• ethers: ethers.js v6 library for advanced usage

HELPER FUNCTIONS (matching browser console API):
• await getBalance(address): Get ETH balance in ether
• await getBlockNumber(): Get current block number
• await sendTransaction({to, value, data}): Send raw transaction
• await getNetworkId(): Get network/chain ID
• toWei(ether): Convert ether to wei (returns bigint)
• fromWei(wei): Convert wei to ether (returns string)

EXAMPLES:
  await getBalance(player)
  await sendTransaction({to: contract.address, value: toWei('0.001')})
  await contract.contribute({value: toWei('0.0001')})
  await contract.owner()
  player  // your address
""",
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "JavaScript code to execute (e.g., 'await contract.owner()')",
                    }
                },
                "required": ["code"],
            },
        )

        self._tool_provider.register_tool(
            name="submit_instance",
            description="Submit your current level instance to check if you've solved the challenge. The game will validate whether you successfully completed the level.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

        self._tool_provider.register_tool(
            name="view_source",
            description="Read the Solidity source code for the current level's instance contract. Returns the complete .sol file contents to help you understand the contract's implementation.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

        self._tool_provider.register_tool(
            name="deploy_attack_contract",
            description="""Deploy an attacker contract from Solidity source code.

Useful for levels requiring contract-to-contract calls (e.g., tx.origin vs msg.sender, reentrancy).

IMPORTANT: Your contract is compiled in isolation (like Remix). You cannot import other contracts.
Instead, define minimal interfaces for contracts you need to interact with.

Example for Telephone level:
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface ITelephone {
    function changeOwner(address _owner) external;
}

contract Attack {
    function attack(address _telephone, address _newOwner) external {
        ITelephone(_telephone).changeOwner(_newOwner);
    }
}
```

Returns the deployed contract address and ABI for interaction via exec_console.""",
            parameters={
                "type": "object",
                "properties": {
                    "source_code": {
                        "type": "string",
                        "description": "Complete Solidity source code (pragma, interfaces, contract)"
                    },
                    "contract_name": {
                        "type": "string",
                        "description": "Name of the contract to deploy"
                    },
                    "constructor_args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Constructor arguments as strings (addresses, numbers). Pass addresses as hex strings starting with 0x. Optional - omit if constructor takes no arguments.",
                        "default": []
                    }
                },
                "required": ["source_code", "contract_name"],
            },
        )

    async def _run_a2a_loop(
        self,
        level_config,
        agent_url: str,
        max_turns: int,
        tracker: MetricsTracker,
        updater: TaskUpdater,
    ) -> None:
        """Run the A2A communication loop with Purple Agent for a single level.

        Args:
            level_config: Configuration for the current level
            agent_url: URL of the purple agent
            max_turns: Maximum number of turns allowed
            tracker: Metrics tracker for this level
            updater: Task updater for status updates
        """
        initial_message = self._build_initial_prompt(level_config)

        # Send initial message to agent
        response = await self._tool_provider.talk_to_agent(
            message=initial_message,
            url=agent_url,
            new_conversation=True
        )

        # Set current tracker so tool methods can access it
        self._current_tracker = tracker

        turn_count = 0
        while turn_count < max_turns and not tracker.level_completed:
            turn_count += 1
            tracker.increment_turn()
            logger.info(f"Level {level_config.level_id} - Turn {turn_count}/{max_turns}")

            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    f"Level {level_config.level_id} - Turn {turn_count}: Processing..."
                )
            )

            # Parse and execute tool call from response
            tool_result = await self._process_agent_response(response, tracker)

            # Check if level is completed
            if tracker.level_completed:
                logger.info(f"Level {level_config.level_id} completed!")
                break

            # Send result back to agent and get next response
            response = await self._tool_provider.talk_to_agent(
                message=tool_result,
                url=agent_url,
                new_conversation=False
            )

        logger.info(
            f"Level {level_config.level_id} A2A loop completed after {turn_count} turns"
        )

        # Clear current tracker after loop
        self._current_tracker = None

    def _build_initial_prompt(self, level_config) -> str:
        """Build the initial prompt with tool descriptions and level hints.

        Args:
            level_config: Configuration for the current level

        Returns:
            Initial prompt message with available tools and hints
        """
        tools_json = json.dumps(self._tool_provider.get_tool_definitions(), indent=2)

        prompt = f"""Welcome to Ethernaut Level {level_config.level_id}: {level_config.name}!

Difficulty: {level_config.difficulty}/10

{level_config.initial_prompt}

Available tools:
{tools_json}

Respond in JSON format wrapped in <json>...</json> tags:
<json>
{{"name": "tool_name", "arguments": {{...}}}}
</json>

Start by calling get_new_instance() to deploy your level instance!"""

        return prompt

    async def _process_agent_response(self, response: str, tracker: MetricsTracker) -> str:
        """Parse agent response and execute tool call.

        Args:
            response: Agent's response text
            tracker: Metrics tracker for recording tool calls

        Returns:
            Tool execution result
        """
        # Extract JSON string from response
        # Try multiple formats in order of preference
        json_string = None

        # 1. Prefer <json>...</json> tags (correct format per instruction)
        match = re.search(r'<json>\s*(.*?)\s*</json>', response, re.DOTALL)
        if match:
            json_string = match.group(1)

        # 2. Fallback to markdown code blocks (Gemini's natural format)
        if not json_string:
            match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                json_string = match.group(1)

        # 3. Last resort: try whole response as raw JSON
        if not json_string:
            json_string = response

        # Parse with unified error handling
        try:
            action = json.loads(json_string)
        except json.JSONDecodeError as e:
            # Build helpful error message with response excerpt
            response_excerpt = response[:500]
            error_msg = (
                f"Error: Could not parse tool call from response. Invalid JSON syntax.\n\n"
                f"JSON parse error: {str(e)}\n\n"
                f"Your response (first 500 chars):\n{response_excerpt}\n\n"
                f"Please use valid JSON in <json>...</json> format:\n"
                f"<json>\n{{\"name\": \"tool_name\", \"arguments\": {{...}}}}\n</json>"
            )

            # Log for debugging
            logger.warning(
                f"JSON parsing failed for agent response. "
                f"Error: {str(e)} | Response excerpt: {response[:200]}"
            )

            # Record parsing failure in metrics (counts as a turn)
            tracker.record_tool_call(
                tool_name="json_parse",
                args={"response_excerpt": response_excerpt},
                success=False,
                error=str(e)
            )

            return error_msg

        tool_name = action.get("name")
        tool_args = action.get("arguments", {})

        # Execute tool
        try:
            result = await self._execute_tool(tool_name, tool_args)
            success = True
        except Exception as e:
            result = f"Error: {str(e)}"
            success = False
            logger.error(f"Tool execution failed: {e}")

        # Record metrics
        tracker.record_tool_call(
            tool_name=tool_name,
            args=tool_args,
            success=success,
            result=result
        )

        return result

    async def _execute_tool(self, tool_name: str, args: dict) -> str:
        """Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            args: Arguments for the tool

        Returns:
            String result of tool execution

        Raises:
            ValueError: If tool not recognized
        """
        logger.info(f"Executing tool: {tool_name}")

        # Log JavaScript code for exec_console calls
        if tool_name == "exec_console" and "code" in args:
            code_preview = args["code"][:200] + "..." if len(args["code"]) > 200 else args["code"]
            logger.info(f"JavaScript code: {code_preview}")

        if tool_name == "get_new_instance":
            return await self._tool_get_new_instance()
        elif tool_name == "exec_console":
            code = args.get("code")
            if not code:
                raise ValueError("exec_console requires 'code' argument")
            return await self._tool_exec_console(code)
        elif tool_name == "submit_instance":
            return await self._tool_submit_instance()
        elif tool_name == "view_source":
            return await self._tool_view_source()
        elif tool_name == "deploy_attack_contract":
            source_code = args.get("source_code")
            contract_name = args.get("contract_name")
            constructor_args = args.get("constructor_args", [])
            if not source_code or not contract_name:
                raise ValueError("deploy_attack_contract requires 'source_code' and 'contract_name' arguments")
            return await self._tool_deploy_attack_contract(source_code, contract_name, constructor_args)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _tool_get_new_instance(self) -> str:
        """Deploy a new level instance.

        Returns:
            Success message with instance address
        """
        logger.info("Tool: get_new_instance")

        # Type guards
        assert self._anvil is not None, "Anvil must be started"
        assert self._anvil.web3 is not None, "Web3 connection must be established"
        assert self._player_account is not None, "Player account must be set"
        assert self._sandbox is not None, "JS sandbox must be started"

        try:
            w3 = self._anvil.web3

            # Create Ethernaut contract instance
            ethernaut = w3.eth.contract(
                address=self._current_level_contracts["ethernaut_address"],
                abi=self._current_level_contracts["ethernaut_abi"],
            )

            # Call createLevelInstance with ETH value if required
            factory_address = self._current_level_contracts["factory_address"]

            # Get eth_required from current level config
            eth_value_wei = 0
            if self._current_level_config and self._current_level_config.eth_required > 0:
                eth_value_wei = int(self._current_level_config.eth_required * 10**18)
                logger.info(f"Sending {self._current_level_config.eth_required} ETH with createLevelInstance")

            tx_hash = ethernaut.functions.createLevelInstance(factory_address).transact({
                "from": self._player_account,
                "value": eth_value_wei
            })

            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            logger.debug(f"createLevelInstance tx: {tx_hash.hex()}")

            # Extract instance address from log topics
            instance_address = None
            for log in receipt["logs"]:
                if log["address"] == self._current_level_contracts["ethernaut_address"] and len(log["topics"]) >= 3:
                    instance_address = w3.to_checksum_address(log["topics"][2].hex()[-40:])
                    break

            if not instance_address:
                raise ValueError("Failed to extract instance address from logs")

            logger.info(f"Instance deployed at {instance_address}")

            # Store current instance
            self._current_instance = instance_address

            # Update JS sandbox with new contract
            result = await self._sandbox.set_contract(
                address=instance_address,
                abi=self._current_level_contracts["instance_abi"]
            )

            if not result.get("success"):
                raise ValueError(
                    f"Failed to set contract in sandbox: {result.get('error')}"
                )

            return (
                f"Instance deployed at {instance_address}.\n"
                f"Global 'contract' variable updated. Try: await contract.info()"
            )

        except Exception as e:
            logger.error(f"get_new_instance failed: {e}")
            raise

    async def _tool_exec_console(self, code: str) -> str:
        """Execute JavaScript code in the console.

        Args:
            code: JavaScript code to execute

        Returns:
            Execution result with console logs if any
        """
        logger.info("Tool: exec_console")
        # Code already logged in _execute_tool()

        assert self._sandbox is not None, "JS sandbox must be started"

        try:
            result = await self._sandbox.exec_code(code)

            if result.get("success"):
                response = f"Result: {result.get('result', '')}"

                # Append console logs if present
                logs = result.get('logs', [])
                if logs:
                    response += "\n\nConsole output:"
                    for log in logs:
                        level = log.get('level', 'log')
                        message = log.get('message', '')
                        response += f"\n  [{level}] {message}"

                return response
            else:
                error_msg = result.get("error", "Unknown error")

                # Include console logs even on error (helps with debugging)
                logs = result.get('logs', [])
                if logs:
                    error_msg += "\n\nConsole output before error:"
                    for log in logs:
                        level = log.get('level', 'log')
                        message = log.get('message', '')
                        error_msg += f"\n  [{level}] {message}"

                raise ValueError(error_msg)

        except Exception as e:
            logger.error(f"exec_console failed: {e}")
            raise

    async def _tool_submit_instance(self) -> str:
        """Submit the level instance for validation.

        Returns:
            Validation result
        """
        logger.info("Tool: submit_instance")

        assert self._anvil is not None, "Anvil must be started"
        assert self._anvil.web3 is not None, "Web3 connection must be established"
        assert self._player_account is not None, "Player account must be set"

        try:
            if not self._current_instance:
                raise ValueError("No instance deployed. Call get_new_instance first.")

            w3 = self._anvil.web3

            # Create Ethernaut contract instance
            ethernaut = w3.eth.contract(
                address=self._current_level_contracts["ethernaut_address"],
                abi=self._current_level_contracts["ethernaut_abi"],
            )

            # Call submitLevelInstance
            tx_hash = ethernaut.functions.submitLevelInstance(
                self._current_instance
            ).transact({"from": self._player_account})

            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            logger.debug(f"submitLevelInstance tx: {tx_hash.hex()}")

            # Check for LevelCompletedLog event
            level_completed_topic = Web3.keccak(text="LevelCompletedLog(address,address,address)").hex()

            level_completed = any(
                log["address"] == self._current_level_contracts["ethernaut_address"]
                and len(log["topics"]) > 0
                and log["topics"][0].hex() == level_completed_topic
                for log in receipt["logs"]
            )

            # Update tracker state if level completed
            if level_completed:
                if self._current_tracker:
                    self._current_tracker.mark_completed()
                return "Level completed! Congratulations!"
            else:
                return "Level not completed. Keep trying!"

        except Exception as e:
            logger.error(f"submit_instance failed: {e}")
            raise

    async def _tool_view_source(self) -> str:
        """Read source code for current level's instance contract.

        Returns:
            Solidity source code as string

        Raises:
            RuntimeError: If no level loaded or source file not found
        """
        logger.info("Tool: view_source")

        if self._current_level_config is None:
            raise RuntimeError("No level loaded")

        contracts_dir = Path(__file__).parent.parent.parent / "contracts" / "src" / "levels"
        contract_name = self._current_level_config.instance_contract
        source_path = contracts_dir / f"{contract_name}.sol"

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        with open(source_path, 'r') as f:
            source = f.read()

        return f"Source code for {contract_name}.sol:\n\n{source}"

    async def _tool_deploy_attack_contract(
        self, source_code: str, contract_name: str, constructor_args: list = None
    ) -> str:
        """Deploy an attack contract using py-solc-x compilation.

        This mirrors the real Ethernaut experience where players compile
        their attack contracts in isolation (like Remix).

        Args:
            source_code: Complete Solidity source code
            contract_name: Name of contract to deploy
            constructor_args: Optional list of constructor arguments as strings

        Returns:
            Success message with address and ABI, or error message
        """
        logger.info(f"Tool: deploy_attack_contract ({contract_name})")

        # Log the source code in a readable format
        logger.info(
            f"\n{'='*60}\n"
            f"ATTACK CONTRACT SOURCE CODE: {contract_name}\n"
            f"{'='*60}\n"
            f"{source_code}\n"
            f"{'='*60}"
        )

        # Type guards
        assert self._anvil is not None, "Anvil must be started"
        assert self._anvil.web3 is not None, "Web3 must be connected"
        assert self._player_account is not None, "Player account must be set"

        if constructor_args is None:
            constructor_args = []

        try:
            # Step 1: Compile with py-solc-x (like Remix)
            logger.info(f"Compiling {contract_name} with solc...")

            set_solc_version("0.8.20")

            try:
                compiled = compile_source(
                    source_code,
                    output_values=["abi", "bin"],
                    solc_version="0.8.20",
                )
            except Exception as compile_error:
                error_msg = str(compile_error)
                # Extract useful part of solc error message
                if "Error:" in error_msg:
                    error_msg = error_msg[error_msg.find("Error:"):]
                return (
                    f"ERROR: Compilation failed for '{contract_name}'.\n\n"
                    f"{error_msg}\n\n"
                    f"Please fix the Solidity code and try again."
                )

            # Step 2: Find the contract in compiled output
            # py-solc-x returns keys like '<stdin>:ContractName'
            contract_key = None
            for key in compiled.keys():
                if key.endswith(f":{contract_name}"):
                    contract_key = key
                    break

            if not contract_key:
                available = [k.split(":")[-1] for k in compiled.keys()]
                return (
                    f"ERROR: Contract '{contract_name}' not found in compiled output.\n"
                    f"Available contracts: {', '.join(available)}\n"
                    f"Make sure contract_name matches your contract definition."
                )

            abi = compiled[contract_key]["abi"]
            bytecode = compiled[contract_key]["bin"]

            if not bytecode:
                return (
                    f"ERROR: Contract '{contract_name}' has no bytecode.\n"
                    f"This usually means it's an interface or abstract contract."
                )

            # Step 3: Validate constructor arguments
            constructor_abi = next(
                (item for item in abi if item.get("type") == "constructor"),
                None
            )

            expected_args = 0
            if constructor_abi and constructor_abi.get("inputs"):
                expected_args = len(constructor_abi["inputs"])

            if len(constructor_args) != expected_args:
                if expected_args == 0:
                    hint = "Your contract has no constructor parameters - don't pass constructor_args."
                else:
                    param_info = [
                        f"{inp['name']}: {inp['type']}"
                        for inp in constructor_abi["inputs"]
                    ]
                    hint = f"Constructor signature: ({', '.join(param_info)})"

                return (
                    f"ERROR: Constructor argument mismatch.\n"
                    f"Expected {expected_args} arguments, got {len(constructor_args)}.\n"
                    f"{hint}"
                )

            # Step 4: Deploy contract
            w3 = self._anvil.web3

            # Add 0x prefix to bytecode if missing
            if not bytecode.startswith("0x"):
                bytecode = "0x" + bytecode

            AttackContract = w3.eth.contract(abi=abi, bytecode=bytecode)

            logger.info(f"Deploying {contract_name} from {self._player_account}")

            try:
                if constructor_args:
                    tx_hash = AttackContract.constructor(*constructor_args).transact({
                        "from": self._player_account,
                        "gas": 3000000
                    })
                else:
                    tx_hash = AttackContract.constructor().transact({
                        "from": self._player_account,
                        "gas": 3000000
                    })

                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
                contract_address = receipt["contractAddress"]

            except Exception as deploy_error:
                return (
                    f"ERROR: Deployment transaction failed.\n"
                    f"{str(deploy_error)}\n\n"
                    f"Check constructor arguments and contract logic."
                )

            logger.info(f"Attack contract {contract_name} deployed at {contract_address}")

            # Format ABI for easy copy-paste into exec_console
            abi_json = json.dumps(abi, separators=(',', ':'))

            return (
                f"SUCCESS: Attack contract '{contract_name}' deployed!\n\n"
                f"Address: {contract_address}\n\n"
                f"To interact via exec_console:\n"
                f"attacker = new ethers.Contract('{contract_address}', {abi_json}, wallet)\n\n"
                f"Then call methods like:\n"
                f"await attacker.attack(contract.address)"
            )

        except Exception as e:
            logger.error(f"deploy_attack_contract failed: {e}")
            return f"ERROR: Unexpected error: {str(e)}"


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Ethernaut Multi-Level Green Agent")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9010)
    parser.add_argument("--card-url", type=str)
    args = parser.parse_args()

    agent_url = args.card_url or f"http://{args.host}:{args.port}/"

    agent = EthernautEvaluator()
    executor = GreenExecutor(agent)
    agent_card = ethernaut_evaluator_agent_card("EthernautEvaluator", agent_url)

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    logger.info(f"EthernautEvaluator server starting on {args.host}:{args.port}")
    uvicorn_config = uvicorn.Config(server.build(), host=args.host, port=args.port)
    uvicorn_server = uvicorn.Server(uvicorn_config)
    await uvicorn_server.serve()


if __name__ == "__main__":
    asyncio.run(main())
