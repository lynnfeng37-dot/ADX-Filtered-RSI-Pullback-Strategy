"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .backtest import BacktestConfig, run_backtest
from .data import create_continuous_contract, load_adjusted_data
from .plotting import save_report
from .strategy import StrategyConfig


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ADX-filtered RSI pullback research CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    clean = subparsers.add_parser(
        "prepare", help="Build a continuous contract from raw Chinese CSV data"
    )
    clean.add_argument("input", type=Path)
    clean.add_argument("--output", type=Path, default=Path("m_continuous_adj.csv"))

    run = subparsers.add_parser("backtest", help="Run a backtest from adjusted OHLC data")
    run.add_argument("input", type=Path)
    run.add_argument("--output-dir", type=Path, default=Path("outputs"))
    run.add_argument("--adx-threshold", type=float, default=20.0)
    run.add_argument("--rsi-long-entry", type=float, default=40.0)
    run.add_argument("--rsi-short-entry", type=float, default=60.0)
    run.add_argument("--commission", type=float, default=0.0001)
    run.add_argument("--slippage", type=float, default=1.0)
    run.add_argument("--long-only", action="store_true")
    run.add_argument("--show", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "prepare":
        result = create_continuous_contract(args.input)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(args.output, index=False)
        print(f"Prepared {len(result)} rows -> {args.output}")
        return 0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    strategy = StrategyConfig(
        adx_threshold=args.adx_threshold,
        rsi_long_entry=args.rsi_long_entry,
        rsi_short_entry=args.rsi_short_entry,
        allow_short=not args.long_only,
    )
    result = run_backtest(
        load_adjusted_data(args.input),
        strategy,
        BacktestConfig(commission_rate=args.commission, slippage=args.slippage),
    )
    result.data.to_csv(args.output_dir / "backtest.csv")
    save_report(result.data, args.output_dir / "report.png", show=args.show)
    (args.output_dir / "metrics.json").write_text(
        json.dumps(result.metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result.metrics, ensure_ascii=False, indent=2))
    return 0
