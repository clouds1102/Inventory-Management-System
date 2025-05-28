# inventory_query_window.py

import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from db_config import get_connection
from datetime import datetime
import openpyxl

class InventoryQueryWindow(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("库存查询")
        self.geometry("1000x600")
        ctk.set_appearance_mode("light")

        # 搜索栏
        search_frame = ctk.CTkFrame(self, corner_radius=8)
        search_frame.pack(pady=15, padx=15, fill="x")

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="输入物料名称或供应商进行搜索",
            width=400,
            height=35
        )
        self.search_entry.pack(side="left", padx=10, fill="x", expand=True)
        self.search_entry.bind("<Return>", lambda e: self.load_inventory())

        ctk.CTkButton(
            search_frame,
            text="搜索",
            width=80,
            height=35,
            command=self.load_inventory
        ).pack(side="left", padx=10)

        # 导出按钮（新增）
        export_frame = ctk.CTkFrame(self, corner_radius=8)
        export_frame.pack(pady=(0, 15), padx=15, fill="x")
        ctk.CTkButton(
            export_frame,
            text="导出为Excel",
            width=120,
            height=35,
            command=self.export_to_excel
        ).pack(side="right", padx=5)

        # 表格容器
        table_container = ctk.CTkFrame(self, corner_radius=8)
        table_container.pack(padx=15, pady=(0, 15), fill="both", expand=True)

        # 表格和滚动条
        self.table = ttk.Treeview(
            table_container,
            columns=("名称", "供应商", "单位", "库存数量", "更新时间"),
            show="headings",
            selectmode="browse"
        )

        vsb = ttk.Scrollbar(table_container, orient="vertical", command=self.table.yview)
        hsb = ttk.Scrollbar(table_container, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 配置表格样式（保持原优化样式）
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
            background="#ffffff",
            foreground="black",
            rowheight=28,
            fieldbackground="#ffffff",
            font=('Microsoft YaHei', 10)
        )
        style.configure("Treeview.Heading", 
            font=('Microsoft YaHei', 11, 'bold'),
            background="#f0f0f0",
            relief="flat"
        )
        style.map("Treeview", background=[('selected', '#e6e6e6')])

        # 配置列
        columns = {
            "名称": {"width": 280, "anchor": "w"},
            "供应商": {"width": 220, "anchor": "w"},
            "单位": {"width": 80, "anchor": "center"},
            "库存数量": {"width": 120, "anchor": "e"},
            "更新时间": {"width": 200, "anchor": "w"}
        }

        for col, settings in columns.items():
            self.table.heading(col, text=col)
            self.table.column(col, **settings)

        # 布局组件
        self.table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        self.load_inventory()

    def load_inventory(self):
        # （保持原优化逻辑）
        keyword = self.search_entry.get()
        for row in self.table.get_children():
            self.table.delete(row)

        try:
            conn = get_connection()
            cursor = conn.cursor()

            query = """
                SELECT M.material_name, M.supplier, M.unit, 
                       I.current_quantity, I.last_updated
                FROM Inventory I
                JOIN Material M ON I.material_id = M.material_id
            """
            params = ()
            
            if keyword:
                query += " WHERE M.material_name LIKE ? OR M.supplier LIKE ?"
                params = (f'%{keyword}%', f'%{keyword}%')

            cursor.execute(query, params)

            for row in cursor.fetchall():
                formatted_row = list(row)
                if isinstance(formatted_row[4], datetime):
                    formatted_row[4] = formatted_row[4].strftime("%Y-%m-%d %H:%M:%S")
                formatted_row[3] = f"{formatted_row[3]:.2f}"
                self.table.insert("", "end", values=formatted_row)

        except Exception as e:
            messagebox.showerror("加载失败", f"数据库错误：{e}")  # 改用messagebox
        finally:
            if conn:
                conn.close()

    def export_to_excel(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")],
            title="保存为 Excel 文件"
        )

        if not file_path:
            return

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "库存查询"

            # 写入标题（与表格列名对应）
            headers = [self.table.heading(col)["text"] for col in self.table["columns"]]
            ws.append(headers)

            # 写入数据（保持格式化后的数据）
            for item in self.table.get_children():
                row_data = self.table.item(item)["values"]
                ws.append(row_data)

            # 自动调整列宽
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.2
                ws.column_dimensions[column].width = adjusted_width

            wb.save(file_path)
            messagebox.showinfo("导出成功", f"数据已保存到：\n{file_path}")

        except Exception as e:
            messagebox.showerror("导出失败", f"发生错误：{e}")