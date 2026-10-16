"""Market-data loading and continuous-contract construction."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PRICE_COLUMNS = ("Adj_Open", "Adj_High", "Adj_Low", "Adj_Close")


def load_adjusted_data(path: str | Path) -> pd.DataFrame:
    """Load, validate and chronologically index adjusted OHLC data."""
    frame = pd.read_csv(path)
    required = {"Date", "Adj_High", "Adj_Low", "Adj_Close"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    frame["Date"] = pd.to_datetime(frame["Date"], errors="raise")
    frame = frame.sort_values("Date").drop_duplicates("Date", keep="last").set_index("Date")
    for column in required - {"Date"}:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["Adj_High", "Adj_Low", "Adj_Close"])
    if frame.empty:
        raise ValueError("No valid price rows remain after cleaning")
    if (frame["Adj_High"] < frame["Adj_Low"]).any():
        raise ValueError("Adj_High must be greater than or equal to Adj_Low")
    return frame


def create_continuous_contract(file_path: str | Path) -> pd.DataFrame:
    """Build an open-interest-selected, backward-adjusted continuous contract."""
    try:
        frame = pd.read_csv(file_path, encoding="utf-8")
    except UnicodeDecodeError:
        frame = pd.read_csv(file_path, encoding="gbk")

    column_map = {
        "商品名称": "Product",
        "合约名称": "Contract",
        "交易日期": "Date",
        "开盘价": "Open",
        "最高价": "High",
        "最低价": "Low",
        "收盘价": "Close",
        "成交量": "Volume",
        "持仓量": "OpenInterest",
    }
    frame = frame.rename(columns=column_map)
    columns = [
        "Product",
        "Contract",
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "OpenInterest",
    ]
    missing = set(columns).difference(frame.columns)
    if missing:
        raise ValueError(f"Missing source columns: {', '.join(sorted(missing))}")
    frame = frame[columns].copy()
    for column in ["Open", "High", "Low", "Close", "Volume", "OpenInterest"]:
        frame[column] = pd.to_numeric(
            frame[column].astype(str).str.replace(",", "", regex=False), errors="coerce"
        )
    frame["Date"] = pd.to_datetime(frame["Date"].astype(str), format="%Y%m%d", errors="raise")
    frame = frame.dropna(subset=["Contract", "Open", "High", "Low", "Close", "OpenInterest"])
    frame = frame.sort_values(["Date", "OpenInterest", "Volume"], ascending=[True, False, False])
    main = frame.drop_duplicates("Date", keep="first").copy().reset_index(drop=True)
    if main.empty:
        raise ValueError("No valid rows remain after cleaning")

    lookup = frame.drop_duplicates(["Date", "Contract"]).set_index(["Date", "Contract"])["Close"]
    main["Prev_Contract"] = main["Contract"].shift()
    main["Rollover"] = main["Contract"].ne(main["Prev_Contract"]) & main["Prev_Contract"].notna()
    gaps = pd.Series(0.0, index=main.index)
    for index, row in main.loc[main["Rollover"]].iterrows():
        new_key = (row["Date"], row["Contract"])
        old_key = (row["Date"], row["Prev_Contract"])
        if new_key in lookup.index and old_key in lookup.index:
            gaps.loc[index] = float(lookup.loc[new_key] - lookup.loc[old_key])

    # Each rollover gap adjusts only observations strictly before that rollover date.
    main["Adj_Factor"] = gaps.iloc[::-1].cumsum().iloc[::-1] - gaps
    for column in ["Open", "High", "Low", "Close"]:
        main[f"Adj_{column}"] = main[column] + main["Adj_Factor"]
    output_columns = [
        "Date",
        "Contract",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "OpenInterest",
        "Adj_Open",
        "Adj_High",
        "Adj_Low",
        "Adj_Close",
        "Adj_Factor",
        "Rollover",
    ]
    return main[output_columns]
