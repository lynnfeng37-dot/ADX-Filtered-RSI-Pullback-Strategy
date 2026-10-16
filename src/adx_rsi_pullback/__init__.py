"""ADX-filtered RSI pullback research toolkit."""

from .backtest import BacktestConfig, BacktestResult, run_backtest
from .strategy import StrategyConfig

__all__ = ["BacktestConfig", "BacktestResult", "StrategyConfig", "run_backtest"]
__version__ = "1.0.0"
