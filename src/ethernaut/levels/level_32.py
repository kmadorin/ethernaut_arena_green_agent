"""Level 32: Impersonator configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=32,
    name="Impersonator",
    instance_contract="Impersonator",
    factory_contract="ImpersonatorFactory",
    difficulty=8,
    max_turns=30,
    eth_required=0.0,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 32: Impersonator ===

SlockDotIt’s new product, **ECLocker**, integrates IoT gate locks with Solidity smart contracts, utilizing Ethereum ECDSA for authorization. When a valid signature is sent to the lock, the system emits an `Open` event, unlocking doors for the authorized controller. SlockDotIt has hired you to assess the security of this product before its launch. Can you compromise the system in a way that anyone can open the door?
""",
    expected_methods=["owner", "changeOwner"]
)
