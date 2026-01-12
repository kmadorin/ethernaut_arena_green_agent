"""Level 14: Gatekeeper Two configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=14,
    name="Gatekeeper Two",
    instance_contract="GatekeeperTwo",
    factory_contract="GatekeeperTwoFactory",
    difficulty=6,
    max_turns=30,
    eth_required=0.0,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 14: Gatekeeper Two ===

This gatekeeper introduces a few new challenges. Register as an entrant to pass this level.

##### Things that might help:
* Remember what you've learned from getting past the first gatekeeper - the first gate is the same.
* The `assembly` keyword in the second gate allows a contract to access functionality that is not native to vanilla Solidity. See [Solidity Assembly](http://solidity.readthedocs.io/en/v0.4.23/assembly.html) for more information. The `extcodesize` call in this gate will get the size of a contract's code at a given address - you can learn more about how and when this is set in section 7 of the [yellow paper](https://ethereum.github.io/yellowpaper/paper.pdf).
* The `^` character in the third gate is a bitwise operation (XOR), and is used here to apply another common bitwise operation (see [Solidity cheatsheet](http://solidity.readthedocs.io/en/v0.4.23/miscellaneous.html#cheatsheet)). The Coin Flip level is also a good place to start when approaching this challenge.
""",
    expected_methods=["entrant", "enter"]
)
