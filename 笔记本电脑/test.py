"""
trend_predictor.py - 三创赛「算力影子」价格预测系统

【学习目标】
这个脚本是整个预测系统的"总指挥"，负责串联三个模块：
1. Sense（感知）：模拟硬件价格波动
2. Reason（推理）：用稳态公式预测整机售价
3. Act（执行）：输出预测结果CSV + 可视化图表

【数据流】
原始Excel数据 → 模拟Δ波动 → 稳态公式计算 → 规则树分类 → 心智修正 → CSV + PNG图表

【核心原理】
硬件成本占售价的36%（价值稳态点），所以：
    预测售价 = 硬件成本 / 0.36
硬件涨1元，整机会放大涨2.77元（定价杠杆比1:2.77）

【运行环境】
conda activate D:\conda-envs\data-learning
cd 本地使用的py脚本
python trend_predictor.py
"""

# ===== [可直接复制] import 库 =====
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# ============================================================
# 配置路径
# 【学习点】os.path.dirname(__file__) 获取脚本所在目录
# 这个技巧可以避免硬编码路径，脚本移到别的地方也能跑
# 【标记】[直接复制] — 这是模板代码，以后任何数据分析脚本都差不多这样写
# ============================================================
PROJECT_DIR = r"C:\Users\Administrator\Desktop\三创赛比赛"
RAW_DATA = os.path.join(PROJECT_DIR, "数据源", "原始数据", "电脑数据_已处理.xlsx")
HARDWARE_RATIO_CSV = os.path.join(PROJECT_DIR, "数据源", "输出数据", "不同类硬件占比.csv")
KMEANS_CSV = os.path.join(PROJECT_DIR, "数据源", "输出数据", "电脑k均值.csv")
SHADOW_PRICE_CSV = os.path.join(PROJECT_DIR, "数据源", "输出数据", "各品牌影子价格查.csv")
PREMIUM_CSV = os.path.join(PROJECT_DIR, "数据源", "输出数据", "品牌硬件溢价对比分析.csv")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "数据源", "输出数据", "预测系统")
# 全局基准常量
HARDWARE_RATIO = 0.36
PRICING_LEVERAGE = 2.77
BRAND_PREMIUM = 2.33

np.random.seed(15)
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


# ============================================================
# 模块 0：数据加载
# 【标记】[直接复制] — 读Excel + 读CSV 是固定套路，背下来也没用
# 但要理解 pd.to_numeric() 这一步：原始数据里"售价"列可能是字符串，
# 比如 "26999"，不转成数字就没法做数学运算。
# ============================================================
def load_data():
    raw_df = pd.read_excel(RAW_DATA)
    raw_df['售价'] = pd.to_numeric(raw_df['售价'], errors='coerce')
    hardware_ratio_df = pd.read_csv(HARDWARE_RATIO_CSV, encoding='utf-8')
    kmeans_df = pd.read_csv(KMEANS_CSV, encoding='utf-8')
    shadow_df = pd.read_csv(SHADOW_PRICE_CSV, encoding='utf-8')
    premium_df = pd.read_csv(PREMIUM_CSV, encoding='utf-8')

    print("=" * 60)
    print("  数据加载完成")
    print("=" * 60)
    print(f"  电脑原始数据: {raw_df.shape[0]} 条, {raw_df.shape[1]} 列")
    print(f"  硬件占比参考: {hardware_ratio_df.shape[0]} 个档位")
    print(f"  K-Means档位: {kmeans_df.shape[0]} 个聚类")
    print(f"  影子价格: {shadow_df.shape[0]} 条品牌×硬件记录")
    print()

    return raw_df, hardware_ratio_df, kmeans_df, shadow_df, premium_df


def clean_hardware_data(df):
    df['容量(GB)'] = pd.to_numeric(df.get('容量(GB)'), errors='coerce')

    # 兼容一下列名
    type_col = 'type' if 'type' in df.columns else '硬件类型'

    if type_col in df.columns:
        df.loc[df[type_col] == '内存','容量(GB)'] = df.loc[df[type_col] == '内存', '容量(GB)'].fillna(16)
        df.loc[df[type_col] == '硬盘','容量(GB)'] = df.loc[df[type_col] == '硬盘', '容量(GB)'].fillna(1024)
    
    # 无论是否执行了 if 里面的代码，最后都要返回 df
    return df

def practice_labeling(df):
    print('打标练习...')

    # 这里的关键：shadow_df 里没有“售价”和“内存(G)”，只有“中位数价格”和“容量(GB)”
    # 我们根据表里有的列名来决定用哪个
    target_price = '售价' if '售价' in df.columns else '中位数价格'
    target_mem = '内存(G)' if '内存(G)' in df.columns else '容量(GB)'

    df['价格定位'] = np.where(df[target_price] >= 15000, '高端', '常规')

    df['档位档次'] = '入门级'
    df.loc[(df[target_price] >= 8000) & (df[target_mem] >= 16), '档位档次'] = '中端'
    df.loc[(df[target_price] >= 15000) & (df[target_mem] >= 32), '档位档次'] = '高端'

    def complex_logic(row):
        if row['品牌'] in ['苹果','华为']:
            return '品牌溢价款'
        elif row[target_price] >= 8000 and row[target_mem] >= 32:
            return '正常'
        else:
            return '其他'
        
    df['市场标签'] = df.apply(complex_logic, axis=1)

    print('打标完成！')
    return df

def pratice_predict(df, mem_delta=10, stor_delta=0.05):
    print("预测练习...")

    t_price = '售价' if '售价' in df.columns else '价格'
    t_mem = '内存(G)' if '内存(G)' in df.columns else '容量(GB)'
    t_stor = '储存(G)' if '储存(G)' in df.columns else '容量(GB)'

    # --- 第一步：算物理基础（物理层） ---
    # 目标：算出因为硬件涨价，电脑“理应”涨多少
    # 代码提示：成本变化 = 硬件量 * 涨幅； 预测价 = 原价 + 成本/比例
    df['成本变化'] = df[t_mem] * mem_delta + df[t_stor] * stor_delta
    df['预测价'] = df[t_price] + (df['成本变化'] / 0.36)

    # --- 第二步：按档位修正（心理层） ---
    # 目标：入门级涨不动，高端随便涨。把文字档位变成对应的数字系数。
    # 代码提示：建立字典 -> map 映射 -> 乘法修正
    c_map = {'入门级': 0.85, '中端': 0.95, '高端': 1.00}
    df['修正系数'] = df['档位档次'].map(c_map) 
    df['修正价格'] = df['预测价'] * df['修正系数']

    # --- 第三步：品牌收割（溢价层） ---
    # 目标：只针对"品牌溢价款"，把它的涨幅再放大
    # 代码提示：定义 mask -> 计算差值 -> loc 精准赋值
    brand_mask = df['市场标签'] == '品牌溢价款'
    price_diff = df['修正价格'] - df[t_price]
    # 精准手术：原价 + (涨幅 * 2.33)
    df.loc[brand_mask, '修正价格'] = df[t_price] + (price_diff * 2.33)
    

    print("映射与加权完成！")
    return df

def pratice_extracting_values(shadow_df):
    """
    实验区：尝试不同的单值提取方法
    目标：提取特定品牌的硬件参数
    """
    print("\n" + "="*20 + " 提取值实验区 " + "="*20)

    val = shadow_df.loc[shadow_df['硬盘类型'] == '内存', '平均影子价格'].iloc[0]
    
    return  val
       



if __name__ == "__main__":
    from 跨表提数练习 import analyze_price_diff
    
    raw_df, hardware_ratio_df, kmeans_df, shadow_df, premium_df = load_data()
    # 之前报错的原因：shadow_df（零件价格表）里没有“售价”列
    cleaned_df = clean_hardware_data(raw_df)
    labeled_df = practice_labeling(cleaned_df)
    predicted_df = pratice_predict(labeled_df.copy())
    
    # 打印结果时，我们也用通用的列名
    price_col = '售价' if '售价' in labeled_df.columns else '中位数价格'
    mem_col = '内存(G)' if '内存(G)' in labeled_df.columns else '容量(GB)'
    #labeled_df.to_csv(r"C:\Users\Administrator\Desktop\data_learn\python-learning\笔记本电脑\生成文件\labeled_data.csv", index=False, encoding='utf-8-sig')
    #predicted_df.to_csv(r"C:\Users\Administrator\Desktop\data_learn\python-learning\笔记本电脑\生成文件\predicted_data.csv", index=False, encoding='utf-8-sig')

    # 调用跨表提数练习中的分析函数
    analyze_price_diff()
        
            
