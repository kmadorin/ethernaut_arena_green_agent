"""Level configuration dataclass."""

from dataclasses import dataclass, field

# ==============================================================================
# Game tutorial adapted from original Ethernaut Level 0
# This provides the educational context that human players receive in Level 0
# and remember throughout the game. Agents receive this fresh for each level.
# ==============================================================================

GAME_TUTORIAL = """=== HOW TO PLAY ETHERNAUT ===

The player address:
You can see your player address by entering the following command via exec_console:
player

Console helpers:
You can see your current ether balance by typing via exec_console:
await getBalance(player)

These helper functions are available via exec_console:
• await getBalance(address) - Get ETH balance in ether
• await sendTransaction({to, value}) - Send a transaction
• toWei(ether) - Convert ether to wei (returns bigint)
• fromWei(wei) - Convert wei to ether (returns string)

The ethernaut contract:
Enter the following command via exec_console:
ethernaut

This is the game's main smart contract. You don't need to interact with it directly (as the Arena will do that for you) but you can if you want to. Playing around with this object now is a great way to learn how to interact with the other smart contracts of the game.

Interact with the ABI:
ethernaut is a contract object that wraps the Ethernaut.sol contract that has been deployed to the blockchain.
( this is an ethers.js Contract object.)

Among other things, the contract's ABI exposes all of Ethernaut.sol's public methods, such as owner. Type the following command via exec_console for example:
await ethernaut.owner()

Getting a level instance:
When playing a level, you don't interact directly with the ethernaut contract. Instead, you ask it to generate a level instance for you. Use the get_new_instance tool to do this (equivalent to the "Get New Instance" button in the browser version). This deploys a new contract in the blockchain.

Inspecting the contract:
Just as you did with the ethernaut contract, you can inspect this contract's ABI using the contract variable via exec_console.
The contract variable is a contract object that wraps the contract instance deployed for this level.
The contract's ABI exposes all of its public methods.
You can call methods like: await contract.methodName()
You can inspect contract properties: contract.address, contract.abi

Submitting the level:
When you know you have completed the level, use the submit_instance tool (equivalent to the "Submit Instance" button in the browser version).

Arena tools:
• view_source - Read the contract's Solidity source code (in the browser version, this is displayed on the level page)
• exec_console - Execute JavaScript to interact with contracts (equivalent to the browser console)
• get_new_instance - Deploy a new level instance
• submit_instance - Submit your completed instance

Tip: don't forget that you can always look in the contract's ABI!

"""


@dataclass
class LevelConfig:
    """Configuration for an Ethernaut level.

    Attributes:
        level_id: Numeric level identifier (0-40)
        name: Human-readable level name
        instance_contract: Name of the instance contract (e.g., "Instance")
        factory_contract: Name of the factory contract (e.g., "InstanceFactory")
        difficulty: Difficulty rating (0-8, from Ethernaut gamedata)
        max_turns: Maximum turns allowed for Purple agent
        eth_required: ETH to send when creating instance (in ETH, not wei)
        extra_tools: Additional tool names to register for this level
        initial_prompt: Level-specific hints/guidance for Purple agent
        expected_methods: Methods expected to be called (for metrics tracking)
    """

    level_id: int
    name: str
    instance_contract: str
    factory_contract: str
    difficulty: int
    max_turns: int = 30
    eth_required: float = 0.0
    extra_tools: list[str] = field(default_factory=list)
    initial_prompt: str = ""
    expected_methods: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.level_id < 0 or self.level_id > 40:
            raise ValueError(f"Invalid level_id: {self.level_id}. Must be 0-40.")
        if self.difficulty < 0 or self.difficulty > 10:
            raise ValueError(f"Invalid difficulty: {self.difficulty}. Must be 0-10.")
        if self.max_turns < 1:
            raise ValueError(f"Invalid max_turns: {self.max_turns}. Must be >= 1.")
        if self.eth_required < 0:
            raise ValueError(f"Invalid eth_required: {self.eth_required}. Must be >= 0.")
