"""Backward-compatible entry point for the original project script."""

from adx_rsi_pullback.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["backtest", "m_continuous_adj.csv", "--output-dir", ".", "--show"]))
