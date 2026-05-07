# 提取修正价格与原价的差值，看看它们之间的关系，将结果在test.py中打印出来，分析一下差值的分布情况。
import pandas as pd

def _step_calculate_diff(df):
    """步骤 A：计算价格差"""
    price_col = '售价'
    fix_price_col = '修正价格'
    # 计算：修正后价格 - 原价
    df['价格差'] = (df[fix_price_col] - df[price_col]).round(2)
    return df

def _step_show_distribution(df):
    """步骤 B：展示整体分布"""
    print("\n" + "="*30)
    print("      价格差值分布统计")
    print("="*30)
    print()
    # 之前是 return，现在加上 print 确保控制台能看到结果
    desc = df['价格差'].describe()
    print(desc)
    return desc

def _step_show_piture(df):
    """步骤 C：展示分布图"""
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10,6))
    plt.hist(df['价格差'], bins=30, edgecolor='k', alpha=0.7)
    plt.title('价格差分布图')
    plt.xlabel('价格差 (修正价格 - 原价)')
    plt.ylabel('频数')
    plt.grid(axis='y', alpha=0.75)
    plt.show()

def analyze_price_diff():
    # 1. 加载数据
    path = r'C:\Users\Administrator\Desktop\data_learn\python-learning\笔记本电脑\生成文件\predicted_data.csv'
    df = pd.read_csv(path)

    # 2. 执行计算
    df = _step_calculate_diff(df)
    
    # 3. 展示分布
    _step_show_distribution(df.copy())
    _step_show_piture(df.copy())

if __name__ == "__main__":
    analyze_price_diff()

