# SQL 与 Pandas 核心操作对照表

> 💡 **核心理念**：SQL 是声明式的（告诉数据库我要什么），Pandas 是命令式的（一步步写怎么做）。但它们处理表格数据的底层逻辑是完全相通的！

---

## 1. 基础查询与筛选 (SELECT & WHERE)

> 💡 **Pandas 的 `query()` 方法**：如果你非常习惯 SQL 的 `WHERE` 语法，Pandas 提供了一个 `query()` 方法，允许你直接用类似 SQL 的字符串来筛选数据，代码更短更易读！

| 操作目标 | SQL 语法 | Pandas 语法 (传统) | Pandas 语法 (`query` 推荐) |
| :--- | :--- | :--- | :--- |
| **条件筛选** | `WHERE col > 10` | `df[df['col'] > 10]` | `df.query("col > 10")` |
| **多条件筛选** | `WHERE col1 > 10 AND col2 = 'A'` | `df[(df['col1'] > 10) & (df['col2'] == 'A')]` | `df.query("col1 > 10 and col2 == 'A'")` |
| **IN 匹配** | `WHERE col IN ('A', 'B')` | `df[df['col'].isin(['A', 'B'])]` | `df.query("col in ['A', 'B']")` |
| **引用外部变量** | `WHERE col > @var` | `df[df['col'] > var]` | `df.query("col > @var")` |

---

## 2. 排序与限制 (ORDER BY & LIMIT)

| 操作目标 | SQL 语法 | Pandas 语法 |
| :--- | :--- | :--- |
| **升序排列** | `ORDER BY col ASC` | `df.sort_values('col')` |
| **降序排列** | `ORDER BY col DESC` | `df.sort_values('col', ascending=False)` |
| **多列排序** | `ORDER BY col1 ASC, col2 DESC` | `df.sort_values(['col1', 'col2'], ascending=[True, False])` |
| **限制行数** | `LIMIT 5` | `df.head(5)` |

---

## 3. 分组与聚合 (GROUP BY)

| 操作目标 | SQL 语法 | Pandas 语法 |
| :--- | :--- | :--- |
| **单列分组求和** | `SELECT col1, SUM(col2) FROM table GROUP BY col1` | `df.groupby('col1')['col2'].sum().reset_index()` |
| **多列分组计数** | `SELECT col1, col2, COUNT(*) FROM table GROUP BY col1, col2` | `df.groupby(['col1', 'col2']).size().reset_index(name='count')` |
| **多种聚合** | `SELECT col1, MAX(col2), MIN(col2) FROM table GROUP BY col1` | `df.groupby('col1').agg({'col2': ['max', 'min']}).reset_index()` |
| **分组后筛选** | `HAVING SUM(col2) > 100` | `grouped = df.groupby('col1').sum(); grouped[grouped['col2'] > 100]` |

---

## 4. 表连接 (JOIN)

| 操作目标 | SQL 语法 | Pandas 语法 |
| :--- | :--- | :--- |
| **内连接** | `SELECT * FROM t1 INNER JOIN t2 ON t1.id = t2.id` | `pd.merge(t1, t2, on='id', how='inner')` |
| **左连接** | `SELECT * FROM t1 LEFT JOIN t2 ON t1.id = t2.id` | `pd.merge(t1, t2, on='id', how='left')` |
| **全外连接** | `SELECT * FROM t1 FULL OUTER JOIN t2 ON t1.id = t2.id` | `pd.merge(t1, t2, on='id', how='outer')` |
| **上下拼接** | `SELECT * FROM t1 UNION ALL SELECT * FROM t2` | `pd.concat([t1, t2], ignore_index=True)` |

---

## 5. 进阶：窗口函数 (Window Functions) ⭐

> 窗口函数的核心是：**不改变原表的行数，但在每一行后面追加一个基于“分组(PARTITION)”和“排序(ORDER)”计算出来的值。**
> 在 Pandas 中，窗口函数通常通过 `groupby().transform()` 或 `groupby().rank()` 来实现。

| 操作目标 | SQL 语法 | Pandas 语法 |
| :--- | :--- | :--- |
| **分组求和(不聚合)** | `SUM(price) OVER (PARTITION BY brand)` | `df['品牌总价'] = df.groupby('brand')['price'].transform('sum')` |
| **分组求均值** | `AVG(price) OVER (PARTITION BY brand)` | `df['品牌均价'] = df.groupby('brand')['price'].transform('mean')` |
| **分组排名(1,2,3)** | `ROW_NUMBER() OVER (PARTITION BY brand ORDER BY price DESC)` | `df['排名'] = df.groupby('brand')['price'].rank(method='first', ascending=False)` |
| **分组排名(并列)** | `RANK() OVER (PARTITION BY brand ORDER BY price DESC)` | `df['排名'] = df.groupby('brand')['price'].rank(method='min', ascending=False)` |
| **计算占比** | `price / SUM(price) OVER (PARTITION BY brand)` | `df['占比'] = df['price'] / df.groupby('brand')['price'].transform('sum')` |

### 💡 窗口函数 Pandas 实例解析：
假设你想计算每个品牌里，各个电脑的价格占该品牌总销售额的比例：

**SQL 写法：**
```sql
SELECT 
    商品名, 
    品牌, 
    价格,
    价格 / SUM(价格) OVER (PARTITION BY 品牌) AS 品牌内价格占比
FROM table;
```

**Pandas 写法：**
```python
# transform('sum') 会计算出每个品牌的总价，并且把这个总价"广播"回每一行，保持行数不变
df['品牌总价'] = df.groupby('品牌')['价格'].transform('sum')

# 然后直接相除
df['品牌内价格占比'] = df['价格'] / df['品牌总价']
```

---

## 6. 数据更新与条件赋值 (UPDATE & CASE WHEN)

| 操作目标 | SQL 语法 | Pandas 语法 |
| :--- | :--- | :--- |
| **更新整列** | `UPDATE table SET col = 0` | `df['col'] = 0` |
| **条件更新** | `UPDATE table SET col = 1 WHERE col2 > 10` | `df.loc[df['col2'] > 10, 'col'] = 1` |
| **多条件分支** | `CASE WHEN col>10 THEN 'A' ELSE 'B' END` | `np.where(df['col']>10, 'A', 'B')` |