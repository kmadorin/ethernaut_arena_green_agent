"""Level 17: Recovery configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=17,
    name="Recovery",
    instance_contract="Recovery",
    factory_contract="RecoveryFactory",
    difficulty=6,
    max_turns=30,
    eth_required=0.001,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 17: Recovery ===

A contract creator has built a very simple token factory contract. Anyone can create new tokens with ease. After deploying the first token contract, the creator sent `0.001` ether to obtain more tokens. They have since lost the contract address. 

This level will be completed if you can recover (or remove) the `0.001` ether from the lost contract address.
""",
    expected_methods=[]  # Recovery has no useful methods, need to find SimpleToken
)
