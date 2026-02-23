import pandas as pd
import jieba
from collections import Counter
import re

def execute(dataframe1=None, dataframe2=None, dataframe3=None):
    if dataframe1 is None or dataframe1.empty:
        return pd.DataFrame([{"分析项": "无数据", "指标": 0}])

    df = dataframe1.copy()

    # 1. 过滤好评：仅保留情感得分 > 0.5 的评论
    # 确保分析的是正面反馈中的关键词，使结论更具说服力
    sentiment_col = next((c for c in df.columns if "情感得分" in str(c)), "")
    if sentiment_col:
        df[sentiment_col] = pd.to_numeric(df[sentiment_col], errors='coerce')
        df = df[df[sentiment_col] > 0.5]
    
    if df.empty:
        return pd.DataFrame([{"分析项": "过滤后无符合条件的数据", "原始频次": 0}])

    # 2. 定义三级分类词库
    # 第一级：战略创新词 (AI 核心)
    ai_keywords = ["AI PC", "Ultra 9", "Ultra 7", "NPU", "DEEPSEEK", "本地部署", "智慧交互", "AI元启"]
    # 第二级：产品特色词 (差异化卖点)
    feature_keywords = ["西装暴徒", "性能猛兽", "机皇", "生产力工具", "4K", "OLED", "18寸"]
    # 第三级：基础体验词 (大众关注点)
    base_keywords = ["性能", "流畅", "游戏", "轻薄", "散热", "屏幕", "质感", "颜值"]

    for w in ai_keywords + feature_keywords + base_keywords:
        jieba.add_word(w)

    # 2. 停用词过滤 (只过滤无意义虚词，保留中性好词)
    stops = {"的", "了", "我", "在", "是", "这个", "不错", "可以", "满意", "笔记本", "电脑", "产品", "收到", "京东"}
    
    text_col = next((c for c in df.columns if "内容" in str(c) or "评论" in str(c)), "")
    all_text = "".join(df[text_col].astype(str).tolist()).upper()

    # 3. 统计原始词频
    words = jieba.lcut(all_text)
    raw_counts = Counter([w for w in words if len(w) > 1 and w not in stops])

    # 4. 计算两个维度的指标
    analysis_results = []
    
    # 我们遍历所有的词，或者至少是我们关心的词
    all_target_words = ai_keywords + feature_keywords + base_keywords
    
    for word in all_target_words:
        count = raw_counts.get(word.upper(), 0)
        if count == 0:
            count = all_text.count(word.upper()) # 兜底统计
            
        # 设置战略权重 (合理加权：AI=8倍, 特色=2倍, 基础=1倍)
        weight = 1
        category = "基础体验"
        if word in ai_keywords:
            weight = 8
            category = "战略创新(AI)"
        elif word in feature_keywords:
            weight = 2
            category = "产品特色"
            
        if count > 0:
            analysis_results.append({
                "分词": word,
                "分类": category,
                "原始频次": count,
                "传播权重得分": count * weight # 词云用这个数
            })

    # 5. 返回结果
    result_df = pd.DataFrame(analysis_results).sort_values(by="传播权重得分", ascending=False)
    
    return result_df