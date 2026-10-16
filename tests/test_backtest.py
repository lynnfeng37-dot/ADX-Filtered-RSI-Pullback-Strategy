import numpy as np
import pandas as pd

from adx_rsi_pullback.backtest import BacktestConfig, run_backtest
from adx_rsi_pullback.strategy import StrategyConfig, generate_positions


def price_frame(size=120):
    index = pd.date_range("2024-01-01", periods=size, freq="B")
    base = np.linspace(100, 130, size) + np.sin(np.arange(size) / 3) * 5
    return pd.DataFrame({"Adj_High": base + 2, "Adj_Low": base - 2, "Adj_Close": base}, index=index)


def test_position_is_delayed_one_bar():
    result = generate_positions(
        price_frame(),
        StrategyConfig(adx_threshold=0, rsi_long_entry=55, rsi_long_exit=70),
    )
    entries = result.index[result["Target_Position"].diff().fillna(0) != 0]
    assert len(entries) > 0
    first = result.index.get_loc(entries[0])
    assert result["Position"].iloc[first] == result["Target_Position"].iloc[first - 1]
    assert result["Position"].iloc[first + 1] == result["Target_Position"].iloc[first]


def test_costs_reduce_equity_and_metrics_are_finite():
    frame = price_frame()
    no_cost = run_backtest(frame, backtest=BacktestConfig(commission_rate=0, slippage=0))
    with_cost = run_backtest(frame, backtest=BacktestConfig(commission_rate=0.01, slippage=2))
    assert with_cost.data["Equity"].iloc[-1] <= no_cost.data["Equity"].iloc[-1]
    assert {"total_return", "sharpe", "max_drawdown", "trade_events"}.issubset(with_cost.metrics)
    assert np.isfinite(list(with_cost.metrics.values())).all()
