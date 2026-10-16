"""Signal generation for the ADX-filtered RSI pullback strategy."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .indicators import adx, rsi


@dataclass(frozen=True)
class StrategyConfig:
    rsi_period: int = 14
    adx_period: int = 14
    adx_threshold: float = 20.0
    rsi_long_entry: float = 40.0
    rsi_short_entry: float = 60.0
    rsi_long_exit: float = 55.0
    rsi_short_exit: float = 45.0
    allow_short: bool = True

    def __post_init__(self) -> None:
        if not 0 <= self.rsi_long_entry < self.rsi_long_exit <= 100:
            raise ValueError("Long RSI thresholds must satisfy 0 <= entry < exit <= 100")
        if not 0 <= self.rsi_short_exit < self.rsi_short_entry <= 100:
            raise ValueError("Short RSI thresholds must satisfy 0 <= exit < entry <= 100")
        if self.adx_threshold < 0:
            raise ValueError("ADX threshold cannot be negative")


def generate_positions(frame: pd.DataFrame, config: StrategyConfig) -> pd.DataFrame:
    """Calculate indicators and stateful target/next-bar positions."""
    result = frame.copy()
    result[["ADX", "Plus_DI", "Minus_DI"]] = adx(
        result["Adj_High"], result["Adj_Low"], result["Adj_Close"], config.adx_period
    )
    result["RSI"] = rsi(result["Adj_Close"], config.rsi_period)

    target: list[int] = []
    current = 0
    for row in result[["ADX", "Plus_DI", "Minus_DI", "RSI"]].itertuples(index=False):
        if pd.isna(row.ADX) or pd.isna(row.RSI):
            current = 0
        else:
            trending = row.ADX >= config.adx_threshold
            uptrend = row.Plus_DI > row.Minus_DI
            downtrend = row.Minus_DI > row.Plus_DI
            if (
                current == 1
                and (row.RSI >= config.rsi_long_exit or not trending or not uptrend)
                or current == -1
                and (row.RSI <= config.rsi_short_exit or not trending or not downtrend)
            ):
                current = 0
            if current == 0 and trending and uptrend and row.RSI <= config.rsi_long_entry:
                current = 1
            elif (
                current == 0
                and config.allow_short
                and trending
                and downtrend
                and row.RSI >= config.rsi_short_entry
            ):
                current = -1
        target.append(current)

    result["Target_Position"] = target
    result["Position"] = result["Target_Position"].shift(1).fillna(0).astype(int)
    result["Signal"] = (
        result["Target_Position"].diff().fillna(result["Target_Position"]).astype(int)
    )
    return result
