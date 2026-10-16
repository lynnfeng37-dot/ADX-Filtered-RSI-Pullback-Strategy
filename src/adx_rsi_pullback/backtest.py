"""Vectorized return accounting and performance metrics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .strategy import StrategyConfig, generate_positions


@dataclass(frozen=True)
class BacktestConfig:
    initial_capital: float = 1_000_000.0
    commission_rate: float = 0.0001
    slippage: float = 1.0
    trading_days: int = 242

    def __post_init__(self) -> None:
        if self.initial_capital <= 0:
            raise ValueError("Initial capital must be positive")
        if self.commission_rate < 0 or self.slippage < 0:
            raise ValueError("Trading costs cannot be negative")


@dataclass(frozen=True)
class BacktestResult:
    data: pd.DataFrame
    metrics: dict[str, float | int]


def _metrics(frame: pd.DataFrame, config: BacktestConfig) -> dict[str, float | int]:
    returns = frame["Strategy_Return"]
    years = max(len(frame) / config.trading_days, 1 / config.trading_days)
    total_return = float(frame["Equity"].iloc[-1] / config.initial_capital - 1)
    cagr = float((1 + total_return) ** (1 / years) - 1) if total_return > -1 else -1.0
    volatility = float(returns.std(ddof=0) * np.sqrt(config.trading_days))
    sharpe = (
        float(returns.mean() / returns.std(ddof=0) * np.sqrt(config.trading_days))
        if volatility
        else 0.0
    )
    downside = returns.clip(upper=0).std(ddof=0)
    sortino = float(returns.mean() / downside * np.sqrt(config.trading_days)) if downside else 0.0
    max_drawdown = float(frame["Drawdown"].min())
    trade_count = int((frame["Turnover"] > 0).sum())
    active = returns[frame["Position"] != 0]
    return {
        "total_return": total_return,
        "cagr": cagr,
        "annual_volatility": volatility,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_drawdown,
        "calmar": float(cagr / abs(max_drawdown)) if max_drawdown else 0.0,
        "trade_events": trade_count,
        "exposure": float((frame["Position"] != 0).mean()),
        "positive_active_days": float((active > 0).mean()) if len(active) else 0.0,
    }


def run_backtest(
    frame: pd.DataFrame,
    strategy: StrategyConfig | None = None,
    backtest: BacktestConfig | None = None,
) -> BacktestResult:
    """Run the strategy using close-to-close returns and next-bar execution."""
    strategy = strategy or StrategyConfig()
    backtest = backtest or BacktestConfig()
    result = generate_positions(frame, strategy)
    result["Market_Return"] = result["Adj_Close"].pct_change().fillna(0.0)
    result["Turnover"] = result["Position"].diff().abs().fillna(result["Position"].abs())
    result["Trading_Cost"] = result["Turnover"] * (
        backtest.commission_rate + backtest.slippage / result["Adj_Close"]
    )
    result["Strategy_Return"] = (
        result["Position"] * result["Market_Return"] - result["Trading_Cost"]
    )
    result["Equity"] = backtest.initial_capital * (1 + result["Strategy_Return"]).cumprod()
    result["Benchmark_Equity"] = backtest.initial_capital * (1 + result["Market_Return"]).cumprod()
    result["Drawdown"] = result["Equity"] / result["Equity"].cummax() - 1
    return BacktestResult(result, _metrics(result, backtest))
