"""Level 2: Fallout configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=2,
    name="Fallout",
    instance_contract="Fallout",
    factory_contract="FalloutFactory",
    difficulty=2,
    max_turns=30,
    eth_required=0.0,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 2: Fallout ===

Claim ownership of the contract below to complete this level.

&nbsp;
Things that might help
* Look very carefully at the contract's code
""",
    expected_methods=["owner", "Fal1out"]  # Note the typo is intentional
)
