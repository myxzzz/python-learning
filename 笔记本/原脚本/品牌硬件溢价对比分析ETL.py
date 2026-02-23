import pandas as pd
import numpy as np

def execute(dataframe1=None, dataframe2=None, dataframe3=None):
    """
    品牌硬件溢价对比 ETL：
    将笔记本电脑的“影子价格”与零售市场的“每GB单价”进行交叉比对，
    计算出各品牌在内存和硬盘上的“溢价倍率”。
    """
    # 1. 提取与复制（响应用户要求的 df.copy()）
    # 假设：df1 为内存条行情, df2 为硬盘行情, df3 为电脑影子价格结果
    if dataframe1 is None or dataframe2 is None or dataframe3 is None:
        return pd.DataFrame([{"结果": "需要三个数据源：内存行情、硬盘行情、影子价格"}])
        
    mkt_ram = dataframe1.copy()
    mkt_ssd = dataframe2.copy()
    laptop_shadow = dataframe3.copy()

    # 2. 清洗与类型转换（响应用户要求的 astype()）
    try:
        # 统一转为浮点数
        mkt_ram['每GB单价'] = mkt_ram['每GB单价'].astype(float)
        mkt_ssd['每GB单价'] = mkt_ssd['每GB单价'].astype(float)
        laptop_shadow['平均影子价格'] = laptop_shadow['平均影子价格'].astype(float)
    except Exception as e:
        return pd.DataFrame([{"结果": f"清洗失败: {str(e)}"}])

    # 3. 计算市场基准值（Baseline）
    # 我们取市场的平均值作为参考锚点
    ram_baseline = mkt_ram['每GB单价'].mean()
    ssd_baseline = mkt_ssd['每GB单价'].mean()

    # 4. 对比分析逻辑
    # 我们遍历电脑影子价格表，根据【硬件类型】匹配对应的市场基准
    analysis_results = []
    
    for _, row in laptop_shadow.iterrows(): # iterrows()可以遍历DataFrame的每一行, _是省略索引列
        brand = row['品牌']
        h_type = row['硬件类型']
        shadow_p = row['平均影子价格']
        
        if h_type == '内存':
            baseline = ram_baseline
            protocol = "DDR5平均"
        elif h_type == '硬盘':
            baseline = ssd_baseline
            protocol = "NVMe平均"
        else:
            continue # 基础价等类型暂不参与硬件倍率对比
            
        # 计算溢价倍率：影子价格 / 市场价格
        premium_rate = shadow_p / baseline
        
        # 计算“消费者潜在经济流失” (Estimated Value Loss)
        # 假设常见的升级步进：内存 16G，硬盘 512G
        if h_type == '内存':
            loss_per_upgrade = (shadow_p - baseline) * 16
        else:
            loss_per_upgrade = (shadow_p - baseline) * 512
            
        analysis_results.append({
            '品牌': brand,
            '硬件项目': h_type,
            '厂商升级单价_每GB': round(shadow_p, 2),
            '零售市场单价_每GB': round(baseline, 2),
            '溢价倍率': round(premium_rate, 2),
            '单次升级多花钱_估算': round(max(0, loss_per_upgrade), 2),
            '评价': '良心' if premium_rate < 1.1 else ('暴利' if premium_rate > 2.0 else '常规')
        })

    # 5. 生成结果报告
    result_df = pd.DataFrame(analysis_results)
    
    # 按多花钱的程度排序
    return result_df.sort_values(by='单次升级多花钱_估算', ascending=False)


