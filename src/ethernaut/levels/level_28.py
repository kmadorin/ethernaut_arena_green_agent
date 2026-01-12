"""Level 28: Gatekeeper Three configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=28,
    name="Gatekeeper Three",
    instance_contract="GatekeeperThree",
    factory_contract="GatekeeperThreeFactory",
    difficulty=6,
    max_turns=30,
    eth_required=0.0,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 28: Gatekeeper Three ===

Cope with gates and become an entrant.

##### Things that might help:
* Recall return values of low-level functions.
* Be attentive with semantic.
* Refresh how storage works in Ethereum.
""",
    expected_methods=["entrant", "owner", "allowEntrance", "trick", "enter", "construct0r", "getAllowance"]
)
