import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 设置中文字体与全局样式
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

DATA_PATH = r"c:\Users\Administrator\Desktop\25三创赛资料\笔记本电脑数据\分析结果"
INPUT_FILE = os.path.join(DATA_PATH, "品牌硬件溢价对比分析.csv")
OUTPUT_DIR = os.path.join(DATA_PATH, "可视化图片")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "品牌硬件溢价矩阵分析图.png")

def generate_premium_analysis_chart():
    # 1. 加载数据
    try:
        df = pd.read_csv(INPUT_FILE, encoding='gbk')
    except:
        df = pd.read_csv(INPUT_FILE, encoding='utf-8')

    # 排序：按溢价倍率从高到低
    df = df.sort_values('溢价倍率', ascending=False)

    # 2. 绘图设置
    plt.figure(figsize=(26, 16), dpi=150, facecolor='#F8F9F9')
    ax = plt.gca()
    
    # 使用散点图/气泡图展示矩阵关系，或者高级条形图
    # 这里我们采用“组合坐标轴条形图”来展示 厂商价格 vs 市场价格
    
    # 创建 品牌+硬件 的组合标签
    df['组合项目'] = df['品牌'] + "\n(" + df['硬件项目'] + ")"
    
    # 绘制溢价倍率条形图
    # 颜色根据“评价”来定
    color_map = {'暴利': '#E74C3C', '常规': '#F1C40F', '良心': '#2ECC71'}
    
    # 显式传递固定的颜色列表给 palette，避免 hue 映射导致的所有变色问题
    # 同时将评价列映射到具体的颜色
    df['颜色'] = df['评价'].map(color_map)
    
    bars = sns.barplot(data=df, x='组合项目', y='溢价倍率', hue='评价', palette=color_map, dodge=False)
    
    # 添加1.0倍参考线（即平价线）
    plt.axhline(y=1.0, color='#34495E', linestyle='--', linewidth=3, alpha=0.6, label='市场基准价线(1.0x)')

    # 3. 数据标注 (再次加大字号)
    for i, bar in enumerate(ax.patches):
        height = bar.get_height()
        if height > 0:
            # 标注倍率 - 提升至 32pt
            ax.annotate(f'{height:.2f}x', 
                        (bar.get_x() + bar.get_width() / 2., height),
                        ha='center', va='bottom', fontsize=32, fontweight='bold',
                        xytext=(0, 10), textcoords='offset points', color='#1A2521')
            
            # 标注 实际价格对比 - 提升至 24pt
            # 获取当前 bar 对应的原始数据索引
            # 注意：ax.patches 的顺序可能与 df 顺序一致，但为了稳妥，我们通过 i 获取
            brand_price = df.iloc[i]['厂商升级单价_每GB']
            market_price = df.iloc[i]['零售市场单价_每GB']
            price_text = f"厂商:￥{brand_price:.1f}\n市场:￥{market_price:.1f}"
            
            # 文字垂直位置自适应
            txt_y = height / 2 if height > 1.2 else height + 0.4
            txt_color = 'white' if height > 1.2 else '#2C3E50'
            
            ax.text(bar.get_x() + bar.get_width() / 2., txt_y, price_text, 
                    ha='center', va='center', fontsize=24, color=txt_color, fontweight='bold',
                    bbox=dict(facecolor='none', edgecolor='none', alpha=0.5))

    # 4. 视觉修饰 (字号提升)
    plt.title('2025年笔记本品牌硬件溢价深度透视 (高清特大字版)', fontsize=56, pad=70, fontweight='bold', color='#1A2521')
    plt.xlabel('品牌及硬件项目', fontsize=38, labelpad=25, fontweight='bold')
    plt.ylabel('溢价倍率 (与市场价相比)', fontsize=38, labelpad=25, fontweight='bold')
    
    # 增加刻度字号
    plt.xticks(fontsize=28, fontweight='bold')
    plt.yticks(fontsize=30)
    
    # 图例加大
    plt.legend(title='价值评价分级', title_fontsize=34, fontsize=30, loc='upper right', frameon=True, shadow=True)

    # 关键逻辑批注加大
    plt.text(0.98, 0.45, "🚩 警惕：\n倍率 > 2.0x 属于超高溢价区域\n多出现在特定品牌存储升级中", 
             transform=ax.transAxes, fontsize=32, color='#C0392B', fontweight='bold',
             ha='right', bbox=dict(facecolor='#FDEDEC', edgecolor='#E74C3C', boxstyle='round,pad=1.2'))

    sns.despine()
    plt.tight_layout()

    # 确保保存目录存在
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches='tight')
    print(f"品牌溢价矩阵分析图已生成: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_premium_analysis_chart()
    print("Done")
