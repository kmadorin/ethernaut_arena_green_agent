"""Level 19: Alien Codex configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=19,
    name="Alien Codex",
    instance_contract="AlienCodex",
    factory_contract="AlienCodexFactory",
    difficulty=7,
    max_turns=30,
    eth_required=0.0,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 19: Alien Codex ===

You've uncovered an Alien contract. Claim ownership to complete the level.

&nbsp;
Things that might help
* Understanding how array storage works
* Understanding [ABI specifications](https://solidity.readthedocs.io/en/v0.4.21/abi-spec.html)
* Using a very `underhanded` approach
""",
    expected_methods=["owner", "contact", "makeContact", "record", "retract", "revise"]
)
