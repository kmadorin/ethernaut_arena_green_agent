"""Level 18: MagicNumber configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=18,
    name="MagicNumber",
    instance_contract="MagicNum",
    factory_contract="MagicNumFactory",
    difficulty=6,
    max_turns=30,
    eth_required=0.0,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 18: MagicNumber ===

To solve this level, you only need to provide the Ethernaut with a `Solver`, a contract that responds to `whatIsTheMeaningOfLife()` with the right 32 byte number.

Easy right?
Well... there's a catch.

The solver's code needs to be really tiny. Really reaaaaaallly tiny. Like freakin' really really itty-bitty tiny: 10 bytes at most.

Hint: Perhaps its time to leave the comfort of the Solidity compiler momentarily, and build this one by hand O_o.
That's right: Raw EVM bytecode.

Good luck!
""",
    expected_methods=["solver", "setSolver"]
)
