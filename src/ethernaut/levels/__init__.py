"""Level configuration registry for Ethernaut challenges."""

from .level_config import LevelConfig
from .level_00 import CONFIG as LEVEL_00
from .level_01 import CONFIG as LEVEL_01
from .level_02 import CONFIG as LEVEL_02
from .level_03 import CONFIG as LEVEL_03
from .level_04 import CONFIG as LEVEL_04
from .level_05 import CONFIG as LEVEL_05
from .level_06 import CONFIG as LEVEL_06
from .level_07 import CONFIG as LEVEL_07
from .level_08 import CONFIG as LEVEL_08
from .level_09 import CONFIG as LEVEL_09
from .level_10 import CONFIG as LEVEL_10
from .level_11 import CONFIG as LEVEL_11
from .level_12 import CONFIG as LEVEL_12
from .level_13 import CONFIG as LEVEL_13
from .level_14 import CONFIG as LEVEL_14
from .level_15 import CONFIG as LEVEL_15
from .level_16 import CONFIG as LEVEL_16
from .level_17 import CONFIG as LEVEL_17
from .level_18 import CONFIG as LEVEL_18
from .level_19 import CONFIG as LEVEL_19
from .level_20 import CONFIG as LEVEL_20
from .level_21 import CONFIG as LEVEL_21
from .level_22 import CONFIG as LEVEL_22
from .level_23 import CONFIG as LEVEL_23
from .level_24 import CONFIG as LEVEL_24
from .level_25 import CONFIG as LEVEL_25
from .level_26 import CONFIG as LEVEL_26
from .level_27 import CONFIG as LEVEL_27
from .level_28 import CONFIG as LEVEL_28
from .level_29 import CONFIG as LEVEL_29
from .level_30 import CONFIG as LEVEL_30
from .level_31 import CONFIG as LEVEL_31
from .level_32 import CONFIG as LEVEL_32
from .level_33 import CONFIG as LEVEL_33
from .level_34 import CONFIG as LEVEL_34
from .level_35 import CONFIG as LEVEL_35
from .level_36 import CONFIG as LEVEL_36
from .level_37 import CONFIG as LEVEL_37
from .level_38 import CONFIG as LEVEL_38
from .level_39 import CONFIG as LEVEL_39
from .level_40 import CONFIG as LEVEL_40

# Level registry mapping level IDs to configurations
LEVEL_REGISTRY: dict[int, LevelConfig] = {
    0: LEVEL_00,
    1: LEVEL_01,
    2: LEVEL_02,
    3: LEVEL_03,
    4: LEVEL_04,
    5: LEVEL_05,
    6: LEVEL_06,
    7: LEVEL_07,
    8: LEVEL_08,
    9: LEVEL_09,
    10: LEVEL_10,
    11: LEVEL_11,
    12: LEVEL_12,
    13: LEVEL_13,
    14: LEVEL_14,
    15: LEVEL_15,
    16: LEVEL_16,
    17: LEVEL_17,
    18: LEVEL_18,
    19: LEVEL_19,
    20: LEVEL_20,
    21: LEVEL_21,
    22: LEVEL_22,
    23: LEVEL_23,
    24: LEVEL_24,
    25: LEVEL_25,
    26: LEVEL_26,
    27: LEVEL_27,
    28: LEVEL_28,
    29: LEVEL_29,
    30: LEVEL_30,
    31: LEVEL_31,
    32: LEVEL_32,
    33: LEVEL_33,
    34: LEVEL_34,
    35: LEVEL_35,
    36: LEVEL_36,
    37: LEVEL_37,
    38: LEVEL_38,
    39: LEVEL_39,
    40: LEVEL_40,
}


def get_level_config(level_id: int) -> LevelConfig:
    """Get configuration for a specific level.

    Args:
        level_id: The level number (0-40)

    Returns:
        LevelConfig for the requested level

    Raises:
        ValueError: If level_id is not found in registry
    """
    if level_id not in LEVEL_REGISTRY:
        raise ValueError(
            f"Unknown level: {level_id}. Available levels: {sorted(LEVEL_REGISTRY.keys())}"
        )
    return LEVEL_REGISTRY[level_id]


def get_all_levels() -> list[int]:
    """Get list of all available level IDs.

    Returns:
        Sorted list of level IDs
    """
    return sorted(LEVEL_REGISTRY.keys())


__all__ = ["LevelConfig", "get_level_config", "get_all_levels", "LEVEL_REGISTRY"]
