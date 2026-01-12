"""Level 27: Good Samaritan configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=27,
    name="Good Samaritan",
    instance_contract="GoodSamaritan",
    factory_contract="GoodSamaritanFactory",
    difficulty=5,
    max_turns=30,
    eth_required=0.0,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 27: Good Samaritan ===

This instance represents a Good Samaritan that is wealthy and ready to donate some coins to anyone requesting it.

Would you be able to drain all the balance from his Wallet?

Things that might help:

- [Solidity Custom Errors](https://blog.soliditylang.org/2021/04/21/custom-errors/)
""",
    expected_methods=["coin", "wallet", "requestDonation"]
)
