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
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
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


# ============================================================
# 模块 1：Sense - 价格波动监测
# 【标记】[建议手敲] — 这个模块的核心思路很简单：
#   基准价 × (1 + Δ) = 新价格
# 然后按幅度打标签（平稳/小幅/大幅/剧烈）
# 这是数据分析中最基础的"变化率计算"，几乎所有时序预测都会用到。
#
# 【手敲重点】: scenarios 字典 + for 循环里的 if-elif 分级判断
# ============================================================
def simulate_price_fluctuation(shadow_df, scenario="default"):
    # 提取基准价
    retail_prices = {}
    for _, row in shadow_df.iterrows():
        key = f"{row['品牌']}_{row['硬件类型']}"
        retail_prices[key] = row['中位数价格']

    print("=" * 60)
    print("  Sense 层 - 价格波动监测")
    print("=" * 60)

    # 【手敲重点】定义模拟场景 — 这就是你自己在设计"假设实验"
    # 比如"如果内存涨了10%，整机会怎样？"
    scenarios = {
        "default": {
            "内存": 0.50,    # 内存涨价50%（从原来的0.10修改）
            "硬盘": -0.05,   # 硬盘降价5%
        },
        "chip_shortage": {
            "内存": 0.20,    # 芯片短缺，内存涨20% → 剧烈
            "硬盘": 0.15,    # 硬盘涨15% → 剧烈
        },
        "price_drop": {
            "内存": -0.08,   # 内存降价8%
            "硬盘": -0.12,   # 硬盘降价12%
        },
        "stable": {
            "内存": 0.01,    # 平稳
            "硬盘": 0.02,    # 平稳
        }
    }

    if scenario not in scenarios:
        print(f"  警告: 未找到场景 '{scenario}'，使用 default 场景")
        scenario = "default"

    fluctuations = scenarios[scenario]
    print(f"  模拟场景: {scenario}")
    print()

    # 【手敲重点】for 循环 + if-elif 分级 — 这是数据分析中常用的"打标签"操作
    fluctuation_report = []
    for hw_type , delta in fluctuations:
        delta_pct = delta * 100
        if abs(delta_pct) < 3 :
            level = '平稳'
        elif 5 > abs(delta_pct) > 3 :
            level = '起伏'
        elif abs(delta_pct) >= 10 :
            level = '剧烈'

        base_price = retail_prices.get(hw_type,0)
        new_price = base_price * (1 + delta)
        delta_amount = abs(new_price - base_price)

        print(f"  [{hw_type}] 基准价: {base_price:.2f} 元/GB")
        print(f"           新价格: {new_price:.2f} 元/GB  (Δ = {delta_pct:+.1f}%)")
        print(f"           波动等级: {level}")
        print()

        fluctuation_report.append({
            '硬件类型': hw_type,
            '基准价': base_price,
            '新价格': new_price,
            'Δ变化率': delta_pct,
            'Δ金额': delta_amount,
            '波动等级': level
        })

    return pd.DataFrame(fluctuation_report)


# ============================================================
# 模块 2：Reason - 价格预测引擎（**整份脚本的核心，必须手敲**）
# 【标记】[必须手敲] — 这是你最需要理解的部分
# 三个步骤，每步对应一个数据分析概念：
#
#   Step 2.2 规则树      → 分类算法基础（if-elif 版决策树）
#   Step 2.1 稳态公式    → 线性回归思想（找到稳定比例关系）
#   Step 2.3 心智修正    → 行为经济学（用消费者数据修正数学预测）
#
# 这三个步骤的顺序不能乱：先分类 → 再算基础价 → 最后修正
# ============================================================
def predict_prices(raw_df, fluctuation_df, kmeans_df, hardware_ratio_df):
    print("=" * 60)
    print("  Reason 层 - 价格预测引擎")
    print("=" * 60)
    print()

    # ========================================================
    # 【必须手敲】Step 2.2: 规则树分类
    # 【学习点】决策树分类：先用你"认为的规则"分类
    # def classify_machine 这个函数是整份脚本最重要的代码之一
    # 它回答了一个核心问题："这台电脑属于什么档次？"
    #
    # 思考题：为什么要自己写规则树，而不是直接用 sklearn？
    # 答案：因为规则树是你"假设的分类逻辑"，后面用 sklearn 训练
    # 出来的决策树是"数据实际的分类逻辑"。两者对比能发现你
    # 没想到的模式——这是答辩时的亮点。
    # ========================================================
    def classify_machine(row):
        memory = row['内存(G)']
        storage = row['储存(G)']
        price = row['售价']
        has_gpu = row['独立显卡'] != '无'

        # 【复原】把 128G 改回 48G
        if memory >= 48 and has_gpu:
            return 1  # 移动工作站级
        elif memory >= 32 and price > 15000:
            return 2  # 发烧创作级
        elif memory >= 16 and price > 8000:
            return 3  # 性能进阶级
        else:
            return 0  # 高端入门级

    # 【必须手敲】apply + axis=1 是 pandas 中逐行操作的常用方法
    # 意思是"对每一行执行 classify_machine 函数"
    raw_df = raw_df.copy()
    raw_df['预测档位'] = raw_df.apply(classify_machine, axis=1)

    cluster_names = {
        0: '高端入门级',
        1: '移动工作站级',
        2: '发烧创作级',
        3: '性能进阶级'
    }
    raw_df['档位名称'] = raw_df['预测档位'].map(cluster_names)

    # ========================================================
    # 【必须手敲】Step 2.1: 稳态公式计算
    # 【学习点】线性回归思想
    #
    # 核心公式：预测售价 = 原售价 + 硬件成本变化 / 0.36
    #
    # 举个例子：
    #   一台电脑内存32GB，硬盘1024GB
    #   内存每GB涨10元 → 内存成本涨 32 × 10 = 320元
    #   硬盘每GB涨0元 → 硬盘成本涨 0元
    #   硬件成本总变化 = 320元
    #   售价变化 = 320 / 0.36 = 889元
    #
    # 为什么硬件涨320元，售价会涨889元？
    # 因为硬件成本只占售价的36%，所以硬件涨的钱会被"杠杆放大"
    # 这就是"定价杠杆比 1:2.77"的来源（1/0.36 ≈ 2.77）
    # ========================================================
    memory_delta = fluctuation_df[fluctuation_df['硬件类型'] == '内存']['Δ金额'].values
    storage_delta = fluctuation_df[fluctuation_df['硬件类型'] == '硬盘']['Δ金额'].values

    mem_delta_val = memory_delta[0] if len(memory_delta) > 0 else 0
    stor_delta_val = storage_delta[0] if len(storage_delta) > 0 else 0

    # 每台机器的硬件成本变化 = 内存GB × 每GB变化 + 硬盘GB × 每GB变化
    raw_df['硬件成本变化'] = raw_df['内存(G)'] * mem_delta_val + raw_df['储存(G)'] * stor_delta_val

    # 稳态公式
    raw_df['预测售价_基础'] = raw_df['售价'] + raw_df['硬件成本变化'] / HARDWARE_RATIO

    # ========================================================
    # 【必须手敲】Step 2.3: 心智偏置修正
    # 【学习点】行为经济学在数据分析中的应用
    #
    # 纯数学预测是不够的——不同档次的消费者对价格敏感度不同。
    # 入门档用户对性价比敏感（23.8%关注度），厂商不敢随便涨价 → ×0.85
    # 顶级档用户关注"质感"等情绪价值（2.6%关注度），厂商可以大胆溢价
    #
    # 这个修正系数是项目的一大亮点，答辩时可以说：
    # "我们的预测不是纯数学，还融入了消费者行为学的考量"
    # ========================================================
    correction_map = {
        0: 0.85,   # 入门级：提价阻力大
        1: 1.00,   # 工作站级：强溢价能力（后面单独叠加品牌溢价）
        2: 1.00,   # 发烧级：正常传导
        3: 0.95,   # 进阶级：轻微阻力
    }
    raw_df['修正系数'] = raw_df['预测档位'].map(correction_map)

    raw_df['预测售价_修正'] = raw_df['预测售价_基础'] * raw_df['修正系数']

    # 【理解】移动工作站级（Cluster 1）额外叠加品牌溢价杠杆
    # 2.33倍溢价只对"涨价部分"生效，不是整机价格 × 2.33
    mask_workstation = raw_df['预测档位'] == 1
    premium_amount = (raw_df.loc[mask_workstation, '预测售价_基础'] - raw_df.loc[mask_workstation, '售价'])
    raw_df.loc[mask_workstation, '预测售价_修正'] = (
        raw_df.loc[mask_workstation, '售价'] + premium_amount * BRAND_PREMIUM
    )

    # 计算涨幅
    raw_df['涨幅'] = raw_df['预测售价_修正'] - raw_df['售价']
    raw_df['涨幅百分比'] = (raw_df['涨幅'] / raw_df['售价'] * 100).round(2)

    # 置信度（基于波动等级）
    max_level = fluctuation_df['波动等级'].map(
        {'平稳': 1, '小幅': 2, '大幅': 3, '剧烈': 4}
    ).max()
    confidence_map = {1: '高', 2: '中', 3: '中低', 4: '低'}
    raw_df['置信度'] = confidence_map.get(max_level, '中')

    # 打印摘要
    print("  预测结果摘要（按档位分组）:")
    print("  " + "-" * 50)
    for cluster_id in sorted(raw_df['预测档位'].unique()):
        subset = raw_df[raw_df['预测档位'] == cluster_id]
        name = cluster_names[cluster_id]
        avg_orig = subset['售价'].mean()
        avg_pred = subset['预测售价_修正'].mean()
        avg_change = (avg_pred - avg_orig) / avg_orig * 100
        corr = correction_map[cluster_id]
        print(f"  {name} (Cluster {cluster_id}):")
        print(f"    机型数: {len(subset)}")
        print(f"    平均原价: {avg_orig:.0f} → 预测价: {avg_pred:.0f}  (涨 {avg_change:+.1f}%)")
        print(f"    修正系数: {corr}")
    print()

    return raw_df


# ============================================================
# 模块 3：Act - 商业决策输出
# 【标记】[先复制，后面再手敲] — matplotlib 画图是纯体力活
# 记住几个核心函数就行：
#   plt.subplots() → 创建画布
#   axes.bar()     → 柱状图
#   axes.scatter() → 散点图
#   plt.savefig()  → 保存图片
# 等你想自己画图时再手敲，现在先复制跑通就行。
# ============================================================
def generate_outputs(df, fluctuation_df, scenario_name):
    print("=" * 60)
    print("  Act 层 - 生成输出")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # CSV 输出
    output_cols = ['型号', '品牌', '售价', '预测售价_修正', '涨幅', '涨幅百分比',
                   '预测档位', '档位名称', '硬件成本变化', '修正系数', '置信度']
    result_csv = os.path.join(OUTPUT_DIR, "价格预测结果.csv")
    df[output_cols].to_csv(result_csv, index=False, encoding='utf-8-sig')
    print(f"  CSV已保存: {result_csv}")

    # 可视化（先复制）
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    cluster_names_map = {0: '高端入门级', 1: '移动工作站级',
                         2: '发烧创作级', 3: '性能进阶级'}
    cluster_colors = {0: '#4CAF50', 1: '#FF5722', 2: '#2196F3', 3: '#FFC107'}

    cluster_avg = df.groupby('预测档位').agg(
        原均价=('售价', 'mean'),
        预测均价=('预测售价_修正', 'mean')
    ).reset_index()

    x = np.arange(len(cluster_avg))
    width = 0.35

    bars1 = axes[0].bar(x - width/2, cluster_avg['原均价'], width,
                        label='原均价', color='#90CAF9', edgecolor='white')
    bars2 = axes[0].bar(x + width/2, cluster_avg['预测均价'], width,
                        label='预测均价', color=[cluster_colors[c] for c in cluster_avg['预测档位']],
                        edgecolor='white')

    axes[0].set_xticks(x)
    axes[0].set_xticklabels([cluster_names_map[c] for c in cluster_avg['预测档位']],
                            fontsize=9, rotation=15)
    axes[0].set_ylabel('价格 (元)')
    axes[0].set_title(f'各档位价格对比（场景: {scenario_name}）')
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)

    for bar in bars1:
        axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200,
                     f'{bar.get_height():.0f}', ha='center', va='bottom', fontsize=8)
    for bar in bars2:
        axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200,
                     f'{bar.get_height():.0f}', ha='center', va='bottom', fontsize=8)

    for cluster_id in sorted(df['预测档位'].unique()):
        subset = df[df['预测档位'] == cluster_id]
        axes[1].scatter(
            [cluster_names_map[cluster_id]] * len(subset),
            subset['涨幅百分比'],
            c=cluster_colors[cluster_id], label=cluster_names_map[cluster_id],
            alpha=0.7, s=60, edgecolors='white', linewidth=0.5
        )

    axes[1].axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.5)
    axes[1].set_ylabel('涨幅 (%)')
    axes[1].set_title('各机型涨幅分布')
    axes[1].legend(fontsize=8)
    axes[1].tick_params(axis='x', rotation=15)
    axes[1].grid(axis='y', alpha=0.3)

    plt.tight_layout()
    chart_path = os.path.join(OUTPUT_DIR, f"价格预测对比_{scenario_name}.png")
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  图表已保存: {chart_path}")

    # 溢价收割预警
    df['收割预警'] = df['涨幅百分比'].apply(
        lambda x: '⚠️ 收割预警' if x > 5 else ('✅ 正常' if x > 0 else '📉 降价')
    )
    warning_df = df[df['涨幅百分比'] > 5][['型号', '品牌', '售价', '预测售价_修正',
                                           '涨幅百分比', '档位名称', '收割预警']]
    warning_csv = os.path.join(OUTPUT_DIR, "溢价收割预警.csv")
    if len(warning_df) > 0:
        warning_df.to_csv(warning_csv, index=False, encoding='utf-8-sig')
        print(f"  预警表已保存: {warning_csv} (共 {len(warning_df)} 条)")
    else:
        print("  本场景无收割预警SKU")

    print()
    return result_csv, chart_path


# ============================================================
# 主流程
# 【标记】[建议手敲] — 这个 main() 函数展示了一个完整的
# 数据分析流水线是怎么串联起来的：
#   加载数据 → Sense → Reason → Act
# 这种"函数链式调用"的模式是数据分析项目的标准写法。
# ============================================================
def main(scenario="default"):
    print()
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║       「算力影子」Trend-Predictor 预测系统          ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print()

    raw_df, hardware_ratio_df, kmeans_df, shadow_df, premium_df = load_data()
    fluctuation_df = simulate_price_fluctuation(shadow_df, scenario=scenario)
    
    result_df = predict_prices(raw_df, fluctuation_df, kmeans_df, hardware_ratio_df)
    csv_path, chart_path = generate_outputs(result_df, fluctuation_df, scenario)

    print("=" * 60)
    print("  预测完成！")
    print("=" * 60)
    print()

    return result_df


if __name__ == "__main__":
    main("default")
