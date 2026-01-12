"""Level 31: Stake configuration."""

from .level_config import LevelConfig, GAME_TUTORIAL

CONFIG = LevelConfig(
    level_id=31,
    name="Stake",
    instance_contract="Stake",
    factory_contract="StakeFactory",
    difficulty=6,
    max_turns=30,
    eth_required=0.0,
    extra_tools=[],
    initial_prompt=GAME_TUTORIAL + """=== LEVEL 31: Stake ===

Stake is safe for staking native ETH and ERC20 WETH, considering the same 1:1 value of the tokens. Can you drain the contract?

To complete this level, the contract state must meet the following conditions:

- The `Stake` contract's ETH balance has to be greater than 0.
- `totalStaked` must be greater than the `Stake` contract's ETH balance.
- You must be a staker.
- Your staked balance must be 0.

Things that might be useful:

- [ERC-20](https://github.com/ethereum/ercs/blob/master/ERCS/erc-20.md) specification.
- [OpenZeppelin contracts](https://github.com/OpenZeppelin/openzeppelin-contracts)
""",
    expected_methods=["totalStaked", "UserStake", "StakeWETH", "Unstake"]
)
