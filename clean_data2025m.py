import pandas as pd
import numpy as np

def create_continuous_contract(file_path): # 定义数据处理函数
    # 1. 读取数据
    # encoding='utf-8' 或 'gbk' 根据您的CSV实际编码调整，通常国内期货数据可能是gbk
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='gbk')

    # 2. 数据清洗与预处理
    # 映射列名，方便后续操作
    column_map = {
        '商品名称': 'Product',
        '合约名称': 'Contract',
        '交易日期': 'Date',
        '开盘价': 'Open',
        '最高价': 'High',
        '最低价': 'Low',
        '收盘价': 'Close',
        '成交量': 'Volume',
        '持仓量': 'OpenInterest',
        '成交额': 'Turnover'
    }
    df = df.rename(columns=column_map)

    # 筛选必要列 数据降噪
    cols = ['Product', 'Contract', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'OpenInterest']
    df = df[cols]

    # 清洗数值列：去除千分位逗号并转为浮点数
    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'OpenInterest']
    for col in numeric_cols:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.replace(',', '')
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 日期格式化
    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')

    # 3. 识别主力合约
    # 逻辑：按日期分组，取每日持仓量（OpenInterest）最大的合约
    # 先按日期升序、持仓量降序排列
    df = df.sort_values(['Date', 'OpenInterest'], ascending=[True, False])
    
    # 提取每日主力合约序列
    df_main = df.groupby('Date').first().reset_index()

    # 4. 计算前复权（价差法 / Panama Canal Method）
    # 目的：消除换月产生的价格跳空，使价格序列平滑，适用于技术分析
    
    # 创建索引方便快速查找特定日期、特定合约的价格
    df_lookup = df.set_index(['Date', 'Contract'])

    # 识别换月日：当今日主力合约 != 昨日主力合约
    df_main['Prev_Contract'] = df_main['Contract'].shift(1)
    df_main['Rollover'] = (df_main['Contract'] != df_main['Prev_Contract']) & (df_main['Prev_Contract'].notna())

    # 初始化缺口序列
    gaps = pd.Series(0.0, index=df_main.index)
    
    # 遍历所有换月日，计算缺口
    # 缺口(Gap) = 新合约价格 - 旧合约价格 (在换月日当天)
    rollover_indices = df_main[df_main['Rollover']].index

    for idx in rollover_indices:
        date = df_main.loc[idx, 'Date']
        new_contract = df_main.loc[idx, 'Contract']
        old_contract = df_main.loc[idx, 'Prev_Contract']
        
        try:
            # 查找当天新旧合约的收盘价
            price_new = df_lookup.loc[(date, new_contract), 'Close']
            price_old = df_lookup.loc[(date, old_contract), 'Close']
            
            # 计算价差
            gap = price_new - price_old
            gaps[idx] = gap
            
            # print(f"换月: {date}, {old_contract} -> {new_contract}, 缺口: {gap}")
        except KeyError:
            print(f"Warning: {date} 缺失合约数据，无法计算缺口")

    # 计算累积复权因子 (Adjustment Factor)
    # 逻辑：前复权是将"过去"的价格进行调整，使其衔接"现在"。
    # 因此，我们需要将"未来"发生的所有缺口累加，反向应用到过去。
    
    # 1. 反转缺口序列
    reversed_gaps = gaps.iloc[::-1]
    # 2. 计算累积和
    cum_gaps_reversed = reversed_gaps.cumsum()
    # 3. 再反转回来
    cum_gaps = cum_gaps_reversed.iloc[::-1]
    
    # 4. 错位(Shift)：换月日当天的 Gap 应该应用到换月日“之前”的所有数据
    # 即：T日的 Gap，应用在 T-1, T-2... 
    adj_factors = cum_gaps.shift(-1).fillna(0)
    
    df_main['Adj_Factor'] = adj_factors

    # 5. 应用调整因子到 OHLC 价格
    ohlc_cols = ['Open', 'High', 'Low', 'Close']
    for col in ohlc_cols:
        df_main[f'Adj_{col}'] = df_main[col] + df_main['Adj_Factor']

    # 6. 输出结果
    output_cols = ['Date', 'Contract', 'Open', 'High', 'Low', 'Close', 'Volume', 'OpenInterest', 
                   'Adj_Open', 'Adj_High', 'Adj_Low', 'Adj_Close', 'Adj_Factor']
    result = df_main[output_cols]
    
    return result

# --- 执行主程序 ---
if __name__ == "__main__":
    input_file = 'm_ftr.CSV'   # 请修改您的输入文件名
    output_file = 'm_continuous_adj.csv'
    
    print("正在处理数据...")
    df_result = create_continuous_contract(input_file)
    
    # 保存结果
    df_result.to_csv(output_file, index=False)
    print(f"处理完成！文件已保存为: {output_file}")
    
    # 打印前几行查看
    print(df_result.head())