"""Anvil blockchain manager for local Ethereum environment with multi-level support."""

import asyncio
import json
import subprocess
import time
from pathlib import Path

from loguru import logger
from web3 import Web3

# Import LevelConfig for type hints
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from ethernaut.levels.level_config import LevelConfig


class AnvilManager:
    """Manages Anvil subprocess and contract deployments for multiple Ethernaut levels."""

    def __init__(self):
        """Initialize AnvilManager."""
        self.process: subprocess.Popen | None = None
        self.web3: Web3 | None = None
        self.accounts: list[str] = []
        self.ethernaut_address: str | None = None
        self.ethernaut_abi: list | None = None

    async def start(self, port: int = 8545) -> dict[str, str]:
        """Start Anvil and deploy the main Ethernaut contract.

        Args:
            port: Port to run Anvil on

        Returns:
            Dictionary with rpc_url, accounts, and ethernaut_address

        Raises:
            TimeoutError: If Anvil doesn't start within timeout
            RuntimeError: If Anvil process fails to start
        """
        try:
            # Start Anvil subprocess
            self.process = subprocess.Popen(
                ["anvil", "--port", str(port), "--host", "127.0.0.1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            logger.info(f"Anvil process started with PID {self.process.pid}")

            # Wait for Anvil to be ready
            await self._wait_for_ready(port, timeout=10)

            # Connect Web3
            rpc_url = f"http://127.0.0.1:{port}"
            self.web3 = Web3(Web3.HTTPProvider(rpc_url))

            # Get accounts
            self.accounts = self.web3.eth.accounts
            logger.info(
                f"Anvil started on port {port} with {len(self.accounts)} accounts"
            )

            # Deploy main Ethernaut contract
            await self._deploy_ethernaut()

            return {
                "rpc_url": rpc_url,
                "accounts": self.accounts,
                "ethernaut_address": self.ethernaut_address,
                "ethernaut_abi": self.ethernaut_abi,
            }

        except Exception as e:
            logger.error(f"Failed to start Anvil: {e}")
            if self.process:
                self.process.terminate()
            raise

    async def _wait_for_ready(self, port: int, timeout: int = 10) -> None:
        """Wait for Anvil to be ready by polling RPC.

        Args:
            port: Port to check
            timeout: Timeout in seconds

        Raises:
            TimeoutError: If Anvil doesn't respond within timeout
        """
        start_time = time.time()
        rpc_url = f"http://127.0.0.1:{port}"

        while time.time() - start_time < timeout:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                # Try to get block number to verify RPC is working
                block_num = w3.eth.block_number
                logger.debug(f"Anvil RPC responding, block {block_num}")
                return

            except Exception as e:
                logger.debug(f"Waiting for Anvil... {e}")
                await asyncio.sleep(0.5)

        raise TimeoutError(
            f"Anvil did not respond on port {port} within {timeout} seconds"
        )

    async def _deploy_ethernaut(self) -> None:
        """Deploy the main Ethernaut contract (called once during start).

        Raises:
            FileNotFoundError: If Ethernaut artifact not found
            Exception: If deployment fails
        """
        if not self.web3:
            raise RuntimeError("Web3 not connected")

        # Define contracts directory relative to arena root
        contracts_dir = Path(__file__).parent.parent.parent / "contracts" / "out"

        # Load Ethernaut artifact
        ethernaut_artifact_path = contracts_dir / "Ethernaut.sol" / "Ethernaut.json"
        logger.debug(f"Loading Ethernaut artifact from {ethernaut_artifact_path}")

        if not ethernaut_artifact_path.exists():
            raise FileNotFoundError(
                f"Ethernaut artifact not found at {ethernaut_artifact_path}"
            )

        with open(ethernaut_artifact_path) as f:
            ethernaut_artifact = json.load(f)

        self.ethernaut_abi = ethernaut_artifact["abi"]
        ethernaut_bytecode = ethernaut_artifact["bytecode"]["object"]

        # Deploy Ethernaut
        account = self.accounts[0]
        logger.info(f"Deploying Ethernaut contract from {account}")

        Ethernaut = self.web3.eth.contract(
            abi=self.ethernaut_abi, bytecode=ethernaut_bytecode
        )

        tx_hash = Ethernaut.constructor().transact({"from": account})
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        self.ethernaut_address = receipt["contractAddress"]

        logger.info(f"Ethernaut deployed at {self.ethernaut_address}")

        # Deploy MockStatistics
        mock_stats_artifact_path = contracts_dir / "MockStatistics.sol" / "MockStatistics.json"
        logger.debug(f"Loading MockStatistics artifact from {mock_stats_artifact_path}")

        with open(mock_stats_artifact_path) as f:
            stats_artifact = json.load(f)

        stats_abi = stats_artifact["abi"]
        stats_bytecode = stats_artifact["bytecode"]["object"]

        logger.info("Deploying MockStatistics contract")
        MockStats = self.web3.eth.contract(abi=stats_abi, bytecode=stats_bytecode)
        tx_hash = MockStats.constructor().transact({"from": account})
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        stats_address = receipt["contractAddress"]
        logger.info(f"MockStatistics deployed at {stats_address}")

        # Set statistics contract in Ethernaut
        logger.info("Setting statistics contract in Ethernaut")
        ethernaut_contract = self.web3.eth.contract(
            address=self.ethernaut_address, abi=self.ethernaut_abi
        )
        tx_hash = ethernaut_contract.functions.setStatistics(stats_address).transact(
            {"from": account}
        )
        self.web3.eth.wait_for_transaction_receipt(tx_hash)
        logger.info("Statistics contract set successfully")

    async def deploy_level_factory(self, level_config: LevelConfig) -> dict:
        """Deploy a specific level's factory contract and register it with Ethernaut.

        Args:
            level_config: Configuration for the level to deploy

        Returns:
            Dictionary with factory_address, factory_abi, and instance_abi

        Raises:
            RuntimeError: If Web3 not connected or Ethernaut not deployed
            FileNotFoundError: If contract artifacts not found
            Exception: If deployment fails
        """
        if not self.web3:
            raise RuntimeError("Web3 not connected. Call start() first.")
        if not self.ethernaut_address:
            raise RuntimeError("Ethernaut not deployed. Call start() first.")

        contracts_dir = Path(__file__).parent.parent.parent / "contracts" / "out"

        try:
            # Load factory artifact
            factory_artifact_path = (
                contracts_dir
                / f"{level_config.factory_contract}.sol"
                / f"{level_config.factory_contract}.json"
            )
            logger.debug(
                f"Loading {level_config.factory_contract} artifact from {factory_artifact_path}"
            )

            if not factory_artifact_path.exists():
                raise FileNotFoundError(
                    f"Factory artifact not found at {factory_artifact_path}. "
                    f"Run 'cd contracts && forge build' to compile."
                )

            with open(factory_artifact_path) as f:
                factory_artifact = json.load(f)

            factory_abi = factory_artifact["abi"]
            factory_bytecode = factory_artifact["bytecode"]["object"]

            # Deploy factory
            account = self.accounts[0]
            logger.info(
                f"Deploying {level_config.factory_contract} for Level {level_config.level_id}"
            )

            Factory = self.web3.eth.contract(abi=factory_abi, bytecode=factory_bytecode)

            tx_hash = Factory.constructor().transact({"from": account})
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            factory_address = receipt["contractAddress"]

            logger.info(f"{level_config.factory_contract} deployed at {factory_address}")

            # Register level with Ethernaut
            logger.info(f"Registering Level {level_config.level_id} with Ethernaut")

            ethernaut = self.web3.eth.contract(
                address=self.ethernaut_address, abi=self.ethernaut_abi
            )

            tx_hash = ethernaut.functions.registerLevel(factory_address).transact(
                {"from": account}
            )
            self.web3.eth.wait_for_transaction_receipt(tx_hash)

            logger.info(f"Level {level_config.level_id} registered with Ethernaut")

            # Load instance contract ABI
            instance_artifact_path = (
                contracts_dir
                / f"{level_config.instance_contract}.sol"
                / f"{level_config.instance_contract}.json"
            )

            if not instance_artifact_path.exists():
                raise FileNotFoundError(
                    f"Instance artifact not found at {instance_artifact_path}"
                )

            with open(instance_artifact_path) as f:
                instance_artifact = json.load(f)

            instance_abi = instance_artifact["abi"]

            return {
                "factory_address": factory_address,
                "factory_abi": factory_abi,
                "instance_abi": instance_abi,
                "deployer_account": account,
            }

        except FileNotFoundError as e:
            logger.error(f"Contract artifact not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to deploy level factory: {e}")
            raise

    async def stop(self) -> None:
        """Stop Anvil process gracefully.

        Terminates the process and waits for it to exit.
        If still running after timeout, kills it forcefully.
        """
        if not self.process:
            logger.debug("Anvil process not running")
            return

        try:
            logger.info(f"Stopping Anvil process (PID {self.process.pid})")

            # Terminate gracefully
            self.process.terminate()

            # Wait for process to exit
            try:
                self.process.wait(timeout=5)
                logger.info("Anvil process terminated gracefully")
            except subprocess.TimeoutExpired:
                logger.warning("Anvil did not terminate, killing forcefully")
                self.process.kill()
                self.process.wait(timeout=2)
                logger.info("Anvil process killed")

        except Exception as e:
            logger.error(f"Error stopping Anvil: {e}")

        finally:
            self.process = None
            self.web3 = None
            self.accounts = []
            self.ethernaut_address = None
            self.ethernaut_abi = None
