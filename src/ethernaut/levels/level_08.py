"""Level 8: Vault configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=8,
    name="Vault",
    instance_contract="Vault",
    factory_contract="VaultFactory",
    difficulty=3,
    max_turns=30,
    eth_required=0.0,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 8: Vault ===

Unlock the vault to pass the level!
""",
    expected_methods=["locked", "unlock"]
)
