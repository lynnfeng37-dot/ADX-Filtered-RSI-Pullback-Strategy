# ADX-Filtered RSI Pullback Strategy

一个可复现、可测试的期货趋势回调策略研究项目。策略使用 ADX 判断趋势强度，使用 `+DI/-DI` 判断趋势方向，再用 RSI 寻找趋势中的短期回调机会。

> 本项目仅用于量化研究与教学，不构成投资建议。历史回测不代表未来收益。

## 本次升级

- 移除难安装的 TA-Lib 依赖，使用 pandas 实现 Wilder RSI、ADX、`+DI/-DI`。
- 修正原策略只看 ADX、不辨趋势方向的问题。
- 使用状态化持仓：入场后持有到退出条件成立，而不是信号消失即在下一天清仓。
- 所有信号延迟一个交易日执行，避免前视偏差。
- 将手续费和滑点按实际仓位变动计入收益。
- 输出策略与买入持有基准、净值、回撤、指标 JSON 和图表。
- 增加命令行入口、参数校验、自动化测试和 CI。
- 保留 `adxrsi.py` 与 `clean_data2025m.py` 两个旧入口。

## 策略规则

| 场景 | 默认条件 | 动作 |
| --- | --- | --- |
| 多头入场 | ADX ≥ 20、`+DI > -DI`、RSI ≤ 40 | 下一交易日做多 |
| 多头退出 | RSI ≥ 55，或趋势/方向条件失效 | 下一交易日平仓 |
| 空头入场 | ADX ≥ 20、`-DI > +DI`、RSI ≥ 60 | 下一交易日做空 |
| 空头退出 | RSI ≤ 45，或趋势/方向条件失效 | 下一交易日平仓 |

## 安装

```bash
git clone https://github.com/lynnfeng37-dot/ADX-Filtered-RSI-Pullback-Strategy.git
cd ADX-Filtered-RSI-Pullback-Strategy
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install -e ".[dev]"
```

## 数据格式

回测输入至少需要以下四列：

```csv
Date,Adj_High,Adj_Low,Adj_Close
2025-01-02,2660,2630,2648
```

仓库不包含原始行情数据。若你有包含中文列名的逐合约 CSV，可先构造主力连续合约：

```bash
adx-rsi prepare m_ftr.CSV --output m_continuous_adj.csv
```

程序以每日持仓量最大（成交量作为平局规则）的合约作为主力合约，并用价差法对换月前历史价格做前复权。

## 运行回测

```bash
adx-rsi backtest m_continuous_adj.csv
```

常用参数：

```bash
adx-rsi backtest m_continuous_adj.csv \
  --output-dir outputs \
  --adx-threshold 25 \
  --rsi-long-entry 35 \
  --rsi-short-entry 65 \
  --commission 0.0001 \
  --slippage 1.0
```

输出包括 `outputs/backtest.csv`、`outputs/metrics.json` 和 `outputs/report.png`。原有工作流仍可用：把数据命名为 `m_continuous_adj.csv` 后运行 `python adxrsi.py`。

## 测试

```bash
pytest
ruff check .
```

## 重要回测假设

- 当前实现使用日线收盘到收盘收益；信号在当日收盘后产生，仓位从下一根日线生效。
- 滑点按“每单位仓位的固定价格点数 ÷ 当日价格”近似折算。
- 连续合约适合指标研究，但不能完整模拟真实合约换月、保证金、涨跌停、容量与逐笔成交。
- 进一步用于实盘前，应加入合约乘数、保证金、换月成本、无风险利率、样本外验证和参数稳健性分析。

## 项目结构

```text
src/adx_rsi_pullback/
  data.py        数据校验与连续合约
  indicators.py  RSI、ADX、+DI、-DI
  strategy.py    信号与持仓状态机
  backtest.py    成本、净值与绩效指标
  plotting.py    回测报告图
  cli.py         命令行入口
tests/            单元与集成测试
```

## License

[MIT](LICENSE)
