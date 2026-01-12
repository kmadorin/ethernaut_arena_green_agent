"""Level 21: Shop configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=21,
    name="Shop",
    instance_contract="Shop",
    factory_contract="ShopFactory",
    difficulty=4,
    max_turns=30,
    eth_required=0.0,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 21: Shop ===

Сan you get the item from the shop for less than the price asked?

##### Things that might help:
* `Shop` expects to be used from a `Buyer`
* Understanding restrictions of view functions
""",
    expected_methods=["isSold", "price", "buy"]
)
