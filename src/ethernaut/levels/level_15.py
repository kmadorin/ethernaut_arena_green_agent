"""Level 15: Naught Coin configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=15,
    name="Naught Coin",
    instance_contract="NaughtCoin",
    factory_contract="NaughtCoinFactory",
    difficulty=5,
    max_turns=30,
    eth_required=0.0,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 15: Naught Coin ===

NaughtCoin is an ERC20 token and you're already holding all of them. The catch is that you'll only be able to transfer them after a 10 year lockout period. Can you figure out how to get them out to another address so that you can transfer them freely? Complete this level by getting your token balance to 0. 

&nbsp;
Things that might help
*  The [ERC20](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20.md) Spec
*  The [OpenZeppelin](https://github.com/OpenZeppelin/zeppelin-solidity/tree/master/contracts) codebase
""",
    expected_methods=["balanceOf", "transfer", "transferFrom", "approve"]
)
