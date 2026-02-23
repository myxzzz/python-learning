import pandas as pd
import numpy as np

def execute(dataframe1=None, dataframe2=None, dataframe3=None):
    """
    高阶 ETL 脚本：多维边际定价模型（Shadow Pricing Model）。
    通过对同一型号不同配置进行最小二乘法回归，同时剥离内存和硬盘的单位溢价。
    即使配置同时变动，也能计算出各自的贡献值。
    """
    if dataframe1 is None or dataframe1.empty:
        return pd.DataFrame([{"结果": "无数据"}])

    df = dataframe1.copy()
    df.columns = df.columns.str.strip().str.replace('\n', '')
    
    # 1. 规范化列名
    price_col = '售价'
    ram_col = next((c for c in df.columns if "内存" in c), '内存（G）')
    ssd_col = next((c for c in df.columns if "储存" in c or "存储" in c), '储存（G）')
    brand_col = '品牌'
    model_col = '型号'
    vram_col = '显存'

    # 2. 清洗数值
    for col in [price_col, ram_col, ssd_col]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=[price_col, ram_col, ssd_col])

    group_results = []

    # 3. 按【品牌+型号+显存】分组，保证“底盘核心硬件”一致
    grouped = df.groupby([brand_col, model_col, vram_col]) # 把大表按品牌型号显存拆成小表，确保同一组内的机器底盘和核心显卡配置完全一致，只有内存和硬盘配置不同

    for (brand, model, vram), group in grouped: # 进入每个小表，进行回归分析
        # 必须有至少3个不同配置才能解出两个变量（内存和硬盘）
        if len(group) < 3:
            # 如果只有2个样组，回退到单一变量对冲逻辑
            if len(group) == 2:
                rows = group.iloc # .iloc重置小表的行索引，方便后续按位置访问
                dp = abs(rows[0][price_col] - rows[1][price_col]) # abs()取绝对值，计算两台机器售价的差价
                dr = abs(rows[0][ram_col] - rows[1][ram_col])
                ds = abs(rows[0][ssd_col] - rows[1][ssd_col])
                if dr > 0 and ds == 0:
                    group_results.append({'品牌': brand, '型号': model, '硬件类型': '内存', '影子单价': dp/dr})
                elif ds > 0 and dr == 0:
                    group_results.append({'品牌': brand, '型号': model, '硬件类型': '硬盘', '影子单价': dp/ds})
            continue
        
        try:
            # 执行多维回归分析：售价 ~ 内存 + 硬盘 + 常数项
            # Y = AX -> [售价] = [内存, 硬盘, 1] * [内存系数, 硬盘系数, 基础价]
            Y = group[price_col].values # 目标变量：售价
            X = group[[ram_col, ssd_col]].values # 自变量矩阵：内存和硬盘配置
            X = np.hstack([X, np.ones((len(X), 1))]) # 添加常数项，代表固定硬件价值
            
            # 使用最小二乘法求解
            coeffs, residuals, rank, s = np.linalg.lstsq(X, Y, rcond=None) # coeffs是最后的结果，包含内存系数、硬盘系数和基础价
            ram_shadow = coeffs[0]
            ssd_shadow = coeffs[1]

            # 过滤掉不合理的负数结果
            if ram_shadow > 0:
                group_results.append({'品牌': brand, '型号': model, '硬件类型': '内存', '影子单价': ram_shadow})
            if ssd_shadow > 0:
                group_results.append({'品牌': brand, '型号': model, '硬件类型': '硬盘', '影子单价': ssd_shadow})
        except:
            continue

    # 4. 生成品牌级汇总报告
    if not group_results:
        return pd.DataFrame([{"结果": "样本量不足以执行回归分析"}])

    final_df = pd.DataFrame(group_results)
    
    # 汇总计算
    report = final_df.groupby(['品牌', '硬件类型']).agg({
        '影子单价': ['mean', 'median', 'std', 'count']
    }).reset_index()
    
    report.columns = ['品牌', '硬件类型', '平均影子价格', '中位数价格', '价格波动_标准差', '样本型号数']
    
    # 5. 填补缺失值
    report['价格波动_标准差'] = report['价格波动_标准差'].fillna(0)
    
    return report.round(2)


