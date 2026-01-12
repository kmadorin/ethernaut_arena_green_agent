"""Level 7: Force configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=7,
    name="Force",
    instance_contract="Force",
    factory_contract="ForceFactory",
    difficulty=5,
    max_turns=30,
    eth_required=0.0,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 7: Force ===

Some contracts will simply not take your money `¯\_(ツ)_/¯`

The goal of this level is to make the balance of the contract greater than zero.

&nbsp;
Things that might help:
* Fallback methods
* Sometimes the best way to attack a contract is with another contract.
* Some levels require deploying your own contracts to attack the level's instance
""",
    expected_methods=[]  # Contract has no public methods
)
