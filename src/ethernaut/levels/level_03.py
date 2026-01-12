"""Level 3: Coin Flip configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=3,
    name="Coin Flip",
    instance_contract="CoinFlip",
    factory_contract="CoinFlipFactory",
    difficulty=3,
    max_turns=40,  # More turns needed for multiple flips
    eth_required=0.0,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 3: Coin Flip ===

This is a coin flipping game where you need to build up your winning streak by guessing the outcome of a coin flip. To complete this level you'll need to use your psychic abilities to guess the correct outcome 10 times in a row.

&nbsp;
Things that might help
* Some levels require working beyond the console - deploying your own attack contracts to interact with the level's instance
""",
    expected_methods=["flip", "consecutiveWins"]
)
