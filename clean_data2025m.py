"""Backward-compatible continuous-contract preparation script."""

from adx_rsi_pullback.data import create_continuous_contract

if __name__ == "__main__":
    result = create_continuous_contract("m_ftr.CSV")
    result.to_csv("m_continuous_adj.csv", index=False)
    print(f"Prepared {len(result)} rows -> m_continuous_adj.csv")
