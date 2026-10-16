"""Dependency-light implementations of the indicators used by the strategy."""

from __future__ import annotations

import pandas as pd


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Return Wilder's Relative Strength Index."""
    if period < 2:
        raise ValueError("RSI period must be at least 2")
    delta = close.astype(float).diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    alpha = 1 / period
    avg_gain = gain.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    relative_strength = avg_gain / avg_loss
    result = 100 - 100 / (1 + relative_strength)
    result = result.mask((avg_gain == 0) & (avg_loss == 0), 50.0)
    return result.mask((avg_loss == 0) & (avg_gain > 0), 100.0)


def adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.DataFrame:
    """Return ADX, +DI and -DI using Wilder smoothing."""
    if period < 2:
        raise ValueError("ADX period must be at least 2")

    high = high.astype(float)
    low = low.astype(float)
    close = close.astype(float)
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

    true_range = pd.concat(
        [(high - low), (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1
    ).max(axis=1)
    alpha = 1 / period
    atr = true_range.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    plus_di = 100 * plus_dm.ewm(alpha=alpha, adjust=False, min_periods=period).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=alpha, adjust=False, min_periods=period).mean() / atr
    denominator = (plus_di + minus_di).replace(0, float("nan"))
    dx = 100 * (plus_di - minus_di).abs() / denominator
    adx_value = dx.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    return pd.DataFrame({"ADX": adx_value, "Plus_DI": plus_di, "Minus_DI": minus_di})
