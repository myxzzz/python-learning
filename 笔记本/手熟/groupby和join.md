1. 左连接 (Left Join)：建立公允参照系
业务目的： 把 104.93 元/GB 的零售价贴到 94 款电脑的每一行后面，算出它们的“硬件公允价值”。
Pandas 答案：
```
df_result = df.merge(df_a, df_b, on='硬件类型', how='left')
df_result['硬件公允价值'] =  df['内存'] * df['零售价']
```
SQL 答案：
```sql
SELECT 
    df_a.*, 
    (df_b.零售价 * df_a.内存) AS 硬件公允价值
FROM df_a
LEFT JOIN df_b ON df_a.硬件类型 = df_b.硬件类型;
```

--------------------------------------------------------------------------------
2. 内连接 (Inner Join)：锁定暴利评价区
业务目的： 只有满足“溢价倍率 > 阈值”的品牌才会被贴上“暴利”标签。
Pandas 答案：
```python
df_profitable = pd.merge(df_brands, df_thresholds, ON='品牌', how='inner')
# 只有在两个表都存在的品牌（满足阈值条件的）才会留下
```
SQL 答案：
```sql
SELECT a.品牌, a.溢价倍率
FROM df_brands a
INNER JOIN df_thresholds b ON a.品牌 = b.品牌
WHERE a.溢价倍率 > b.预警分界线;
```

--------------------------------------------------------------------------------
3. 自连接 (Self Join)：穿透配置黑盒（差值溢价法）
业务目的： 你的核心创新！让同一型号的 24G 版减去 16G 版，算出那 8G 内存到底被厂家收了多少钱。
### 进阶：万能自连接模板（应对复杂多组合）
当你有 16/24/32/64G 多种组合时，使用“大减小”过滤法：

**Pandas 模板：**
```python
# 1. 产生所有机型内的排列组合
df_all = pd.merge(df, df, on='机型', suffixes=('_高', '_低'))

# 2. 核心规矩：只留“高配减低配”的行
df_final = df_all[df_all['内存_高'] > df_all['内存_低']].copy()

# 3. 动态算差价
df_final['GB单价'] = (df_final['价格_高'] - df_final['价格_低']) / (df_final['内存_高'] - df_final['内存_低'])
```

**SQL 模板：**
```sql
SELECT 
    a.机型,
    a.内存 AS 高配, b.内存 AS 低配,
    (a.价格 - b.价格) / (a.内存 - b.内存) AS 每GB溢价
FROM 电脑表 a
JOIN 电脑表 b ON a.机型 = b.机型
WHERE a.内存 > b.内存; -- 这一行是全自动匹配的灵魂
```
