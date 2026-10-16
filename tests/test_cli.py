import json

import numpy as np
import pandas as pd

from adx_rsi_pullback.cli import main


def test_backtest_cli_writes_all_artifacts(tmp_path):
    size = 80
    base = np.linspace(100, 125, size) + np.sin(np.arange(size) / 3) * 4
    input_path = tmp_path / "prices.csv"
    output_dir = tmp_path / "result"
    pd.DataFrame(
        {
            "Date": pd.date_range("2025-01-01", periods=size, freq="B"),
            "Adj_High": base + 2,
            "Adj_Low": base - 2,
            "Adj_Close": base,
        }
    ).to_csv(input_path, index=False)

    exit_code = main(["backtest", str(input_path), "--output-dir", str(output_dir)])

    assert exit_code == 0
    assert (output_dir / "backtest.csv").is_file()
    assert (output_dir / "report.png").stat().st_size > 0
    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    assert "max_drawdown" in metrics
