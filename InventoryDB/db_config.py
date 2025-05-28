# db_config.py

import pyodbc

def get_connection():
    try:
        conn = pyodbc.connect(
            'DRIVER={SQL Server};SERVER=localhost;DATABASE=InventoryDB;UID=sa;PWD=Gaoqianya1102',
            timeout=5
        )
        return conn
    except Exception as e:
        print("数据库连接失败：", e)
        return None
