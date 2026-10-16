"""Backtest report plotting."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd


def save_report(frame: pd.DataFrame, output: str | Path, show: bool = False) -> Path:
    """Save an equity, signal and drawdown report."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.style.use("ggplot")
    figure, (equity_ax, price_ax, drawdown_ax) = plt.subplots(
        3, 1, figsize=(15, 11), sharex=True, gridspec_kw={"height_ratios": [2, 2, 1]}
    )
    equity_ax.plot(frame.index, frame["Equity"], label="Strategy", linewidth=2)
    equity_ax.plot(frame.index, frame["Benchmark_Equity"], label="Buy & hold", alpha=0.7)
    equity_ax.set_ylabel("Equity")
    equity_ax.legend()

    price_ax.plot(
        frame.index, frame["Adj_Close"], color="black", alpha=0.65, label="Adjusted close"
    )
    changes = frame["Position"].diff().fillna(frame["Position"])
    longs = frame[changes > 0]
    shorts = frame[changes < 0]
    price_ax.scatter(longs.index, longs["Adj_Close"], marker="^", color="#d62728", label="Buy")
    price_ax.scatter(shorts.index, shorts["Adj_Close"], marker="v", color="#2ca02c", label="Sell")
    price_ax.set_ylabel("Price")
    price_ax.legend()

    drawdown_ax.fill_between(frame.index, frame["Drawdown"], 0, color="gray", alpha=0.45)
    drawdown_ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    drawdown_ax.set_ylabel("Drawdown")
    drawdown_ax.set_xlabel("Date")
    figure.tight_layout()
    figure.savefig(output, dpi=180, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(figure)
    return output
