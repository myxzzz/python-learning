import pandas as pd

def execute(dataframe1=None, dataframe2=None, dataframe3=None):
    """
    思睿智训平台专用 ETL 脚本
    任务：添加 is_AI_Hardware (AI硬件标记) 列
    逻辑：只要'型号'或'标题特征词'中包含 AI, Ultra, M5, 锐龙 AI, 元启, 鸿蒙，则标记为 1
    """
    if dataframe1 is None:
        return pd.DataFrame()

    df = dataframe1.copy()

    # 1. 鲁棒性处理：清理表头空格
    df.columns = df.columns.str.strip()

    # 2. 定义 AI 硬件关键词
    ai_keywords = ["AI", "Ultra", "M5", "锐龙 AI", "元启", "鸿蒙"]

    def check_ai_hardware(row):
        # 将需要检查的列合并，统一寻找关键词
        check_text = ""
        if '型号' in row:
            check_text += str(row['型号'])
        if '标题特征词' in row:
            check_text += str(row['标题特征词'])
        
        check_text = check_text.upper()  #.upper()只会影响字母部分，中文不受影响
        
        for kw in ai_keywords:
            if kw.upper() in check_text:
                return 1
        return 0

    # 3. 计算并生成新列
    df['is_AI_Hardware'] = df.apply(check_ai_hardware, axis=1)

    # 4. 调整列顺序，将新列放在第一列
    cols = ['is_AI_Hardware'] + [c for c in df.columns if c != 'is_AI_Hardware']
    df = df[cols]

    return df
