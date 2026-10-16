import numpy as np
import pandas as pd

from adx_rsi_pullback.indicators import adx, rsi


def test_rsi_reaches_100_for_monotonic_rise():
    values = pd.Series(np.arange(1.0, 41.0))
    assert rsi(values, period=14).iloc[-1] == 100.0


def test_adx_returns_bounded_directional_series():
    close = pd.Series(np.linspace(100, 150, 60))
    result = adx(close + 2, close - 2, close, period=14)
    assert list(result.columns) == ["ADX", "Plus_DI", "Minus_DI"]
    assert result["ADX"].dropna().between(0, 100).all()
    assert result["Plus_DI"].iloc[-1] > result["Minus_DI"].iloc[-1]
