import pandas as pd
from snownlp import SnowNLP

def execute(dataframe1=None, dataframe2=None, dataframe3=None):
    df = dataframe1
    
    def get_real_sentiment(row):
        content = str(row.get('评价内容', ''))
        star_str = str(row.get('星级', row.get('评价星级', '5星')))  # .get() 温柔的查询，这里是如果找不到‘星级’就去找'评价星级'，都找不到就默认'5星'
        
        # 1. 基础分：将星级转为 0-1 之间的数字
        star_map = {'5星': 1.0, '4星': 0.8, '3星': 0.6, '2星': 0.4, '1星': 0.2}
        star_score = star_map.get(star_str, 0.5)
        
        # 2. 文本分：计算文字真实情感（如果内容太短则参考星级）
        if len(content) > 5:
            try:
                text_score = SnowNLP(content).sentiments
                # 融合逻辑：六成看内容，四成看星级
                return (text_score * 0.6) + (star_score * 0.4)
            except:
                return star_score
        return star_score

    df['情感得分'] = df.apply(get_real_sentiment, axis=1)
    return df