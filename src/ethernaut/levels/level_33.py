"""Level 33: Magic Animal Carousel configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=33,
    name="Magic Animal Carousel",
    instance_contract="MagicAnimalCarousel",
    factory_contract="MagicAnimalCarouselFactory",
    difficulty=6,
    max_turns=30,
    eth_required=0.0,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 33: Magic Animal Carousel ===

Welcome to the Bet House.

You start with 5 Pool Deposit Tokens (PDT).

Could you master the art of strategic gambling and become a bettor?
""",
    expected_methods=["carouselAnimals", "carousel", "claimMagic"]
)
