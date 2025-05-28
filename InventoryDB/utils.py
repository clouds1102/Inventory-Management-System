# utils.py
import pyodbc
from db_config import get_connection

def check_alert(material_id):
    # 在check_alert函数中添加日志
    print(f"正在检查物料{material_id}的库存预警...")
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 获取当前库存、最大最小
        cursor.execute("""
            SELECT I.current_quantity, M.max_quantity, M.min_quantity
            FROM Inventory I
            JOIN Material M ON I.material_id = M.material_id
            WHERE I.material_id = ?
        """, (material_id,))
        row = cursor.fetchone()
        if not row:
            return  # 没查到就跳过

        current_quantity, max_q, min_q = row

        # 先将未处理的预警设为已处理
        cursor.execute("""
            UPDATE Alert
            SET is_resolved = 1
            WHERE material_id = ? AND is_resolved = 0
        """, (material_id,))

        # 判断是否需要生成新的预警
        if current_quantity < min_q:
            alert_type = '库存过低'
        elif current_quantity > max_q:
            alert_type = '库存过高'
        else:
            conn.commit()
            return  # 在合理范围内，无需新增预警

        # 插入新预警
        cursor.execute("""
            INSERT INTO Alert (material_id, alert_type, current_quantity)
            VALUES (?, ?, ?)
        """, (material_id, alert_type, current_quantity))
        conn.commit()

    except Exception as e:
        print("预警检查失败：", e)
    finally:
        if conn:
            conn.close()
