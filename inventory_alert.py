# inventory_alert.py

import customtkinter as ctk
from tkinter import ttk, messagebox
from db_config import get_connection

class InventoryAlertWindow(ctk.CTkToplevel):
    def __init__(self, master=None):  # 添加 master 参数
        super().__init__(master)
        self.title("库存预警提示")
        self.geometry("800x500")

        # 表格区域
        self.table = ttk.Treeview(
            self, columns=("物料名称", "预警类型", "当前库存", "生成时间", "是否已处理"), show="headings"
        )
        for col in self.table["columns"]:
            self.table.heading(col, text=col)
        self.table.pack(padx=10, pady=10, fill="both", expand=True)

        # 操作按钮区域
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="🔄 刷新", command=self.load_alerts).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="✅ 标记为已处理", command=self.mark_as_resolved).pack(side="left", padx=10)

        self.load_alerts()

    def load_alerts(self):
        for row in self.table.get_children():
            self.table.delete(row)

        try:
            conn = get_connection()
            cursor = conn.cursor()

            query = """
                SELECT A.alert_id, M.material_name, A.alert_type, A.current_quantity,
                       A.generated_time, A.is_resolved
                FROM Alert A
                JOIN Material M ON A.material_id = M.material_id
                ORDER BY A.generated_time DESC
            """
            cursor.execute(query)

            self.alerts = []  # 用于存储 alert_id 对应行
            for row in cursor.fetchall():
                alert_id, name, alert_type, quantity, time, resolved = row
                self.alerts.append(alert_id)
                resolved_text = "是" if resolved else "否"
                self.table.insert("", "end", values=(name, alert_type, quantity, time, resolved_text))

        except Exception as e:
            messagebox.showerror("加载失败", f"数据库错误：{e}")
        finally:
            if conn:
                conn.close()

    def mark_as_resolved(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一条预警记录")
            return

        try:
            index = self.table.index(selected[0])
            alert_id = self.alerts[index]

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE Alert SET is_resolved = 1 WHERE alert_id = ?", (alert_id,))
            conn.commit()

            messagebox.showinfo("已处理", "预警已标记为处理")
            self.load_alerts()

        except Exception as e:
            messagebox.showerror("处理失败", f"数据库错误：{e}")
        finally:
            if conn:
                conn.close()