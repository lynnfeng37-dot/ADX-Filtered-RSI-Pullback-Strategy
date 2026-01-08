import pandas as pd
import numpy as np
import talib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 设置图表风格，使其看起来更专业
plt.style.use('ggplot')
# 解决中文显示问题 (如果您的环境支持)
plt.rcParams['axes.unicode_minus'] = False
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial'] 
except:
    pass

# ==========================================
# 1. 数据读取与清洗
# ==========================================
print("正在读取数据...")
try:
    df = pd.read_csv('m_continuous_adj.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
except FileNotFoundError:
    print("错误: 未找到文件，请检查文件名。")
    df = pd.DataFrame()

# 去除无效数据
df.dropna(subset=['Adj_Close', 'Adj_High', 'Adj_Low'], inplace=True)

# ==========================================
# 2. 指标计算 (ADX + RSI)
# ==========================================
high = df['Adj_High'].values
low = df['Adj_Low'].values
close = df['Adj_Close'].values

# 参数设置
rsi_period = 14
adx_period = 14

# 计算指标
df['ADX'] = talib.ADX(high, low, close, timeperiod=adx_period)
df['RSI'] = talib.RSI(close, timeperiod=rsi_period)

# ==========================================
# 3. 交易信号生成 (宽松参数)
# ==========================================
# 策略参数
adx_threshold = 20      # 趋势强度阈值
rsi_buy = 40            # 超卖买入阈值
rsi_sell = 60           # 超买卖出阈值

df['Signal'] = 0

# 多头信号: 趋势存在(ADX>20) 且 短期超卖(RSI<40)
long_cond = (df['ADX'] > adx_threshold) & (df['RSI'] < rsi_buy)
df.loc[long_cond, 'Signal'] = 1

# 空头信号: 趋势存在(ADX>20) 且 短期超买(RSI>60)
short_cond = (df['ADX'] > adx_threshold) & (df['RSI'] > rsi_sell)
df.loc[short_cond, 'Signal'] = -1

# 持仓逻辑: 信号触发次日持有
df['Position'] = df['Signal'].shift(1).fillna(0)

# ==========================================
# 4. 回测核心: 收益、成本与风险
# ==========================================
# 资金设置
initial_capital = 1000000 # 假设100万初始资金
commission_rate = 0.0001  # 万一手续费
slippage = 1.0            # 1元滑点

# 1. 计算标的涨跌幅
df['Pct_Change'] = df['Adj_Close'].pct_change().fillna(0)

# 2. 计算换手率 (用于算成本)
# abs(diff) 表示仓位变动绝对值: 0->1(开仓)为1, 1->-1(反手)为2
df['Turnover'] = df['Position'].diff().abs().fillna(0)

# 3. 计算交易成本 (转为百分比)
# 成本 = 换手量 * (费率 + 滑点/股价)
cost_pct = df['Turnover'] * (commission_rate + slippage / df['Adj_Close'])

# 4. 计算策略净收益
df['Strategy_Ret'] = df['Position'] * df['Pct_Change'] - cost_pct

# 5. 计算净值曲线 (Equity Curve)
df['Equity_Curve'] = (1 + df['Strategy_Ret']).cumprod() * initial_capital

# ==========================================
# 5. 高级风险指标计算
# ==========================================
# 1. 最大回撤 (Max Drawdown)
# 累计最大净值
df['Peak'] = df['Equity_Curve'].cummax()
# 当前回撤幅度
df['Drawdown'] = (df['Equity_Curve'] - df['Peak']) / df['Peak']
# 最大回撤
max_drawdown = df['Drawdown'].min()

# 2. 策略总收益
total_return = (df['Equity_Curve'].iloc[-1] / initial_capital) - 1

# 3. 年化夏普比率 (假设无风险利率为0, 一年242个交易日)
daily_volatility = df['Strategy_Ret'].std()
annualized_sharpe = (df['Strategy_Ret'].mean() / daily_volatility) * np.sqrt(242) if daily_volatility > 0 else 0

# 输出统计
print("="*40)
print("策略回测绩效报告")
print("="*40)
print(f"交易区间: {df.index[0].date()} 至 {df.index[-1].date()}")
print(f"总收益率: {total_return:.2%}")
print(f"最大回撤: {max_drawdown:.2%}")
print(f"夏普比率: {annualized_sharpe:.2f}")
print(f"交易次数: {df['Turnover'].sum() / 2:.1f} 次 (估算)")
print("="*40)

# ==========================================
# 6. 数据保存
# ==========================================
output_file = 'backtest_result_full.csv'
save_cols = ['Adj_Close', 'ADX', 'RSI', 'Signal', 'Position', 'Strategy_Ret', 'Equity_Curve', 'Drawdown']
df[save_cols].to_csv(output_file)
print(f"详细数据已保存至: {output_file}")

# ==========================================
# 7. 专业绘图 (Pro Visualization)
# ==========================================
# 创建画布: 3个子图 (净值、价格+信号、回撤)
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 12), sharex=True, gridspec_kw={'height_ratios': [2, 2, 1]})

# --- 子图1: 账户净值曲线 ---
ax1.plot(df.index, df['Equity_Curve'], label='策略净值', color='#d62728', linewidth=2)
ax1.set_title(f'策略净值曲线 (收益: {total_return:.1%} | 回撤: {max_drawdown:.1%})', fontsize=12, fontweight='bold')
ax1.set_ylabel('账户资产')
ax1.legend(loc='upper left')
ax1.grid(True, linestyle='--', alpha=0.5)

# 填充收益/亏损区域颜色
ax1.fill_between(df.index, initial_capital, df['Equity_Curve'], where=(df['Equity_Curve']>=initial_capital), color='red', alpha=0.1)
ax1.fill_between(df.index, initial_capital, df['Equity_Curve'], where=(df['Equity_Curve']<initial_capital), color='green', alpha=0.1)

# --- 子图2: 标的价格与买卖点 ---
ax2.plot(df.index, df['Adj_Close'], label='标的价格 (前复权)', color='black', alpha=0.6, linewidth=1)

# 提取买卖点
# Buy: Position 0->1 or -1->1 (这里简化处理，只标记 Position=1 的时刻)
# 为了图表清晰，我们只标记开仓点
buy_signals = df[(df['Position'] == 1) & (df['Position'].shift(1) != 1)]
sell_signals = df[(df['Position'] == -1) & (df['Position'].shift(1) != -1)]

ax2.scatter(buy_signals.index, buy_signals['Adj_Close'], marker='^', color='red', s=80, label='多头开仓', zorder=5)
ax2.scatter(sell_signals.index, sell_signals['Adj_Close'], marker='v', color='green', s=80, label='空头开仓', zorder=5)

ax2.set_ylabel('价格')
ax2.legend(loc='upper left')
ax2.grid(True, linestyle='--', alpha=0.5)

# --- 子图3: 水下回撤图 (Underwater Plot) ---
ax3.fill_between(df.index, df['Drawdown'], 0, color='gray', alpha=0.4, label='回撤幅度')
ax3.plot(df.index, df['Drawdown'], color='black', linewidth=0.5)
ax3.set_ylabel('回撤幅度')
ax3.set_xlabel('日期')
# 格式化Y轴为百分比
import matplotlib.ticker as mtick
ax3.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax3.legend(loc='lower right')
ax3.grid(True, linestyle='--', alpha=0.5)

# 调整布局
plt.tight_layout()

# 保存图片
plt.savefig('strategy_performance_report.png', dpi=300)
print("图表已保存为: strategy_performance_report.png")
plt.show()