import customtkinter as ctk
from tkinter import ttk
from tkinter import filedialog
import tkinter.messagebox as msg
from db_config import get_connection
import pandas as pd
from datetime import datetime
import xlsxwriter

class MonthlyReportWindow(ctk.CTkToplevel):
    def __init__(self, master, user_id):  # 添加 master 参数
        super().__init__(master)
        self.title("📊 月结报表生成")
        self.geometry("800x500")
        self.user_id = user_id

        # 月份选择
        self.month_var = ctk.StringVar(value=self.get_current_month_str())
        self.month_menu = ctk.CTkOptionMenu(self, values=self.get_recent_months(), variable=self.month_var)
        self.month_menu.pack(pady=10)

        # 生成按钮
        ctk.CTkButton(self, text="📤 生成报表", command=self.generate_report).pack(pady=10)

        # 表格
        self.tree = ttk.Treeview(self, columns=("Material", "Start Qty", "In Qty", "Out Qty", "End Qty"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        # 导出按钮
        ctk.CTkButton(self, text="📁 导出为 Excel", command=self.export_to_excel).pack(pady=10)

    def get_current_month_str(self):
        now = datetime.now()
        return now.strftime("%Y-%m")

    def get_recent_months(self):
        return [(datetime.now().replace(day=1) - pd.DateOffset(months=i)).strftime("%Y-%m") for i in range(6)]

    def generate_report(self):
        month_str = self.month_var.get()
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 查询当月的入库/出库
            query = f"""
            SELECT
                m.material_name,
                ISNULL(start_qty.start_qty, 0) AS start_quantity,
                ISNULL(in_qty.in_quantity, 0) AS in_quantity,
                ISNULL(out_qty.out_quantity, 0) AS out_quantity,
                ISNULL(start_qty.start_qty, 0) + ISNULL(in_qty.in_quantity, 0) - ISNULL(out_qty.out_quantity, 0) AS end_quantity
            FROM Material m
            LEFT JOIN (
                SELECT material_id, SUM(quantity) AS in_quantity
                FROM InOutRecord
                WHERE type = '入库' AND FORMAT(timestamp, 'yyyy-MM') = ?
                GROUP BY material_id
            ) in_qty ON m.material_id = in_qty.material_id
            LEFT JOIN (
                SELECT material_id, SUM(quantity) AS out_quantity
                FROM InOutRecord
                WHERE type = '出库' AND FORMAT(timestamp, 'yyyy-MM') = ?
                GROUP BY material_id
            ) out_qty ON m.material_id = out_qty.material_id
            LEFT JOIN (
                SELECT material_id, 
                       SUM(quantity * CASE WHEN type = '入库' THEN 1 ELSE -1 END) AS start_qty
                FROM InOutRecord
                WHERE timestamp < DATEFROMPARTS(YEAR(CONVERT(datetime, ?)), MONTH(CONVERT(datetime, ?)), 1)
                GROUP BY material_id
            ) start_qty ON m.material_id = start_qty.material_id
            """

            cursor.execute(query, month_str, month_str, month_str, month_str)
            results = cursor.fetchall()

            self.tree.delete(*self.tree.get_children())
            self.report_data = []

            for row in results:
                self.tree.insert("", "end", values=row)
                self.report_data.append({
                    "物料名称": row[0],
                    "期初库存": row[1],
                    "入库量": row[2],
                    "出库量": row[3],
                    "期末库存": row[4]
                })

        except Exception as e:
            msg.showerror("错误", str(e))
        finally:
            if conn:
                conn.close()

    def export_to_excel(self):
        if not hasattr(self, "report_data") or not self.report_data:
            msg.showwarning("提示", "请先生成报表")
            return

        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel 文件", "*.xlsx")])
        if path:
            try:
                df = pd.DataFrame(self.report_data)
                df.to_excel(path, index=False)
                msg.showinfo("导出成功", f"已保存到：{path}")
            except Exception as e:
                msg.showerror("导出失败", str(e))
