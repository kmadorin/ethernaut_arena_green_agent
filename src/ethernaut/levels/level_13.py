"""Level 13: Gatekeeper One configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=13,
    name="Gatekeeper One",
    instance_contract="GatekeeperOne",
    factory_contract="GatekeeperOneFactory",
    difficulty=8,
    max_turns=30,
    eth_required=0.0,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 13: Gatekeeper One ===

Make it past the gatekeeper and register as an entrant to pass this level.

##### Things that might help:
* Remember what you've learned from the Telephone and Token levels.
* You can learn more about the special function `gasleft()`, in Solidity's documentation (see [Units and Global Variables](https://docs.soliditylang.org/en/v0.8.3/units-and-global-variables.html) and [External Function Calls](https://docs.soliditylang.org/en/v0.8.3/control-structures.html#external-function-calls)).
""",
    expected_methods=["entrant", "enter"]
)
