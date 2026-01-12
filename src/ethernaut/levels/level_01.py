"""Level 1: Fallback configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=1,
    name="Fallback",
    instance_contract="Fallback",
    factory_contract="FallbackFactory",
    difficulty=1,
    max_turns=30,
    eth_required=0.0,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 1: Fallback ===

Look carefully at the contract's code below.

You will beat this level if
1) you claim ownership of the contract
2) you reduce its balance to 0

&nbsp;
Things that might help
* How to send ether when interacting with an ABI
* How to send ether outside of the ABI
* Converting to and from wei/ether units (see `help()` command)
* Fallback methods
""",
    expected_methods=["contribute", "getContribution", "owner", "withdraw"]
)
