import pandas as pd

def execute(dataframe1=None, dataframe2=None, dataframe3=None):
    
    if dataframe1 is None or dataframe1.empty:
        return pd.DataFrame([{"结果": "无数据", "值": 0}])

    df = dataframe1.copy()
    
    # 1. 鲁棒性处理：清理列名空格及特殊字符
    df.columns = df.columns.str.strip().str.replace('\n', '')

    # 2. 自动匹配关键列名
    model_col = next((c for c in df.columns if "型号" in c), "型号")
    vram_col = next((c for c in df.columns if "显存" in c), "显存")

    # 3. 核心统计：按型号和显存联立分组，计算每组的数量
    # 这一步能精准锁定那些“底盘”一模一样、仅内存硬盘不同的配置组
    df['组样本数'] = df.groupby([model_col, vram_col])[model_col].transform('count')

    # 4. 执行双重筛选逻辑
    # 筛选出 组样本数 >= 2 的行（即同一型号同显存至少有 2 台机器可对比）
    analyzable_df = df[df['组样本数'] >= 2].copy()

    # 5. 为了方便观察，按型号和显存排序
    analyzable_df = analyzable_df.sort_values(by=[model_col, vram_col, '售价'])

    # 如果没有符合条件的行，返回友好提示
    if analyzable_df.empty:
        return pd.DataFrame([{"结果": "未找到符合双重筛选条件的样本", "说明": "建议放宽条件至 > 1"}])

    return analyzable_df
