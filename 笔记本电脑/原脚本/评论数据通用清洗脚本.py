import pandas as pd

def execute(dataframe1=None, dataframe2=None, dataframe3=None):
    """
    思睿智训平台专用 ETL 脚本
    作用：清洗评价数据（电脑评论或硬盘评价）
    1. 剔除重复行
    2. 过滤“此用户没有填写评价。”与“系统默认好评”
    """
    # 优先处理第一个输入的数据框
    if dataframe1 is None:
        return pd.DataFrame()

    df = dataframe1.copy()

    # 1. 基础清理：去除表头空格
    df.columns = df.columns.str.strip() # .strip()可以去除字符串前后的空格

    # 2. 核心清洗逻辑：针对“评价内容”列进行过滤
    target_col = '评价内容'

    if target_col in df.columns:
        # a. 转换为字符串并去除前后空格
        df[target_col] = df[target_col].astype(str).str.strip()

        # b. 去重（全行重复）
        df = df.drop_duplicates()

        # c. 过滤指定关键词
        exclude_list = ['此用户没有填写评价。', '此用户没有填写评价', '系统默认好评']
        
        # 使用 ~ 表示取反，保留不在列表中的行
        df = df[~df[target_col].isin(exclude_list)] # isin()可以筛选和过滤指定列表中的值
        
        # 额外处理：如果内容中包含这些词（模糊匹配），也可以过滤
        # df = df[~df[target_col].str.contains('系统默认好评', na=False)] 
        
        # 过滤空内容
        df = df[df[target_col].str.len() > 0]
        # 修复位置：增加 .str. 访问器
        df = df[df[target_col].str.lower() != 'nan']

    # 3. 结果返回
    return df
