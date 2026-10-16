import pandas as pd
import pytest

from adx_rsi_pullback.data import create_continuous_contract, load_adjusted_data


def test_load_adjusted_data_sorts_and_deduplicates(tmp_path):
    path = tmp_path / "prices.csv"
    pd.DataFrame(
        {
            "Date": ["2025-01-02", "2025-01-01", "2025-01-02"],
            "Adj_High": [12, 11, 13],
            "Adj_Low": [10, 9, 10],
            "Adj_Close": [11, 10, 12],
        }
    ).to_csv(path, index=False)
    result = load_adjusted_data(path)
    assert result.index.is_monotonic_increasing
    assert len(result) == 2
    assert result.loc["2025-01-02", "Adj_Close"] == 12


def test_load_adjusted_data_rejects_missing_columns(tmp_path):
    path = tmp_path / "prices.csv"
    pd.DataFrame({"Date": ["2025-01-01"], "Adj_Close": [10]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="Missing required columns"):
        load_adjusted_data(path)


def test_continuous_contract_applies_roll_gap_only_to_history(tmp_path):
    path = tmp_path / "raw.csv"
    rows = [
        ["豆粕", "A", 20250101, 99, 102, 98, 100, 10, 100],
        ["豆粕", "B", 20250101, 109, 112, 108, 110, 20, 50],
        ["豆粕", "A", 20250102, 100, 103, 99, 101, 10, 80],
        ["豆粕", "B", 20250102, 110, 113, 109, 111, 20, 120],
    ]
    columns = [
        "商品名称",
        "合约名称",
        "交易日期",
        "开盘价",
        "最高价",
        "最低价",
        "收盘价",
        "成交量",
        "持仓量",
    ]
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False)
    result = create_continuous_contract(path)
    assert result["Contract"].tolist() == ["A", "B"]
    assert result["Adj_Close"].tolist() == [110.0, 111.0]
    assert result["Adj_Factor"].tolist() == [10.0, 0.0]
