import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

def import_csvs_to_postgres(folder_path, schema="laptop", db_name="postgres"):
    """
    通用导入脚本
    :param folder_path: CSV 文件夹路径
    :param schema: 要导入的模式名 (如 laptop, phone 等)
    :param db_name: 数据库名称
    """
    print(f"📁 准备读取文件夹: {folder_path} -> 模式: {schema}")
    
    db_params = {
        'host': 'localhost',
        'database': db_name,
        'user': 'postgres',
        'password': '',  
        'port': 5432
    }
    
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # 1. 创建模式
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        conn.commit()
        
        # 2. 扫描文件
        csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
        if not csv_files:
            print("⚠️ 没找到 CSV 文件")
            return
            
        for file in csv_files:
            file_path = os.path.join(folder_path, file)
            table_name = os.path.splitext(file)[0].lower()
            
            # 读取并清理列名
            df = pd.read_csv(file_path)
            df.columns = [str(c).strip().lower().replace(' ', '_').replace('-', '_') for c in df.columns]
            
            # 3. 动态建表 (核心代码行)
            cols = ', '.join([f'"{n}" {"BIGINT" if "int" in str(t) else "DOUBLE PRECISION" if "float" in str(t) else "TEXT"}' for n, t in zip(df.columns, df.dtypes)])
            cursor.execute(f'DROP TABLE IF EXISTS {schema}."{table_name}";')
            cursor.execute(f'CREATE TABLE {schema}."{table_name}" ({cols});')
            
            # 4. 批量搬运 (核心代码行)
            data = [tuple(x) for x in df.where(pd.notnull(df), None).values.tolist()]
            insert_sql = f'INSERT INTO {schema}."{table_name}" VALUES %s'
            execute_values(cursor, insert_sql, data)
            
            conn.commit()
            print(f"✅ {table_name} 导入成功")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

# --- 以后你只需要改下面这两行 ---
my_folder = r"c:\Users\Administrator\Desktop\三创赛-笔记本电脑数据-正式整理版\data\output"
import_csvs_to_postgres(my_folder, schema="laptop") # 想换个地方存？改这里的 schema 即可