# inout_record_viewer.py

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import datetime
import pandas as pd
from db_config import get_connection

class InOutRecordViewer(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("出入库记录查询")
        self.geometry("1200x700")
        ctk.set_appearance_mode("light")
        self._create_widgets()
        self.load_all_records()

    def _create_widgets(self):
        # 主容器
        main_frame = ctk.CTkFrame(self, corner_radius=12)
        main_frame.pack(padx=15, pady=15, fill="both", expand=True)

        # 筛选面板
        filter_frame = ctk.CTkFrame(main_frame, corner_radius=8)
        filter_frame.pack(padx=10, pady=10, fill="x")

        # 日期选择
        ctk.CTkLabel(filter_frame, text="起始日期").grid(row=0, column=0, padx=5)
        self.start_date = DateEntry(
            filter_frame,
            date_pattern="yyyy-mm-dd",
            width=12,
            background="darkblue",
            foreground="white"
        )
        self.start_date.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(filter_frame, text="结束日期").grid(row=0, column=2, padx=5)
        self.end_date = DateEntry(
            filter_frame,
            date_pattern="yyyy-mm-dd",
            width=12,
            background="darkblue",
            foreground="white"
        )
        self.end_date.grid(row=0, column=3, padx=5)

        # 类型筛选
        ctk.CTkLabel(filter_frame, text="操作类型").grid(row=0, column=4, padx=5)
        self.type_filter = ctk.CTkComboBox(
            filter_frame,
            values=["全部", "入库", "出库"],
            width=100,
            dropdown_fg_color="#f0f0f0"
        )
        self.type_filter.set("全部")
        self.type_filter.grid(row=0, column=5, padx=5)

        # 物料名称筛选
        ctk.CTkLabel(filter_frame, text="物料名称").grid(row=1, column=0, padx=5)
        self.material_entry = ctk.CTkEntry(filter_frame, width=120)
        self.material_entry.grid(row=1, column=1, padx=5)

        # 用户筛选
        ctk.CTkLabel(filter_frame, text="操作用户").grid(row=1, column=2, padx=5)
        self.user_entry = ctk.CTkEntry(filter_frame, width=120)
        self.user_entry.grid(row=1, column=3, padx=5)

        # 按钮组
        btn_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        btn_frame.grid(row=1, column=4, columnspan=2, padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="🔍 筛选",
            width=80,
            command=self.filter_records
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="🔄 重置",
            width=80,
            fg_color="#666666",
            command=self.load_all_records
        ).pack(side="left", padx=5)

        # 表格区域
        table_container = ctk.CTkFrame(main_frame, corner_radius=8)
        table_container.pack(fill="both", expand=True, padx=10, pady=10)

        # 配置表格样式
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

        # 创建表格
        self.tree = ttk.Treeview(
            table_container,
            columns=("ID", "类型", "数量", "时间", "物料名称", "操作用户", "备注"),
            show="headings",
            selectmode="browse"
        )

        # 配置列
        columns = {
            "ID": {"width": 80, "anchor": "center"},
            "类型": {"width": 100, "anchor": "center"},
            "数量": {"width": 100, "anchor": "e"},
            "时间": {"width": 180, "anchor": "center"},
            "物料名称": {"width": 200, "anchor": "w"},
            "操作用户": {"width": 120, "anchor": "center"},
            "备注": {"width": 300, "anchor": "w"}
        }

        for col, settings in columns.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, **settings)

        # 滚动条
        vsb = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 布局
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # 导出按钮
        ctk.CTkButton(
            main_frame,
            text="📤 导出为 Excel",
            width=120,
            height=35,
            command=self.export_excel
        ).pack(pady=10)

    def _format_time(self, timestamp):
        """格式化时间显示"""
        if isinstance(timestamp, datetime.datetime):
            return timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return str(timestamp)

    def load_all_records(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            query = """
                SELECT r.record_id, r.type, r.quantity, r.timestamp, 
                       m.material_name, u.username, r.note
                FROM InOutRecord r
                JOIN Material m ON r.material_id = m.material_id
                JOIN Users u ON r.user_id = u.user_id
                ORDER BY r.timestamp DESC
            """
            cursor.execute(query)
            raw_records = cursor.fetchall()
            
            # 格式化时间字段
            self.records = []
            for row in raw_records:
                formatted_row = list(row)
                formatted_row[3] = self._format_time(formatted_row[3])
                self.records.append(formatted_row)
            
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("数据库错误", f"加载失败：{str(e)}")
        finally:
            if conn:
                conn.close()

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for row in self.records:
            self.tree.insert("", "end", values=row)

    def filter_records(self): 
        conn = None  # 初始化以确保 finally 块能关闭连接
        try:
            # 确保是 datetime.datetime 类型
            start = datetime.datetime.combine(self.start_date.get_date(), datetime.time.min)
            end = datetime.datetime.combine(self.end_date.get_date(), datetime.time.max)
        
            type_val = self.type_filter.get().strip()
            mat = self.material_entry.get().strip()
            usr = self.user_entry.get().strip()

            query = """
                SELECT r.record_id, r.type, r.quantity, r.timestamp, 
                       m.material_name, u.username, r.note
                FROM InOutRecord r
                JOIN Material m ON r.material_id = m.material_id
                JOIN Users u ON r.user_id = u.user_id
                WHERE r.timestamp BETWEEN ? AND ?
            """
            params = [start, end]

            if type_val and type_val != "全部":
                query += " AND r.type = ?"
                params.append(type_val)

            if mat:
                query += " AND m.material_name LIKE ?"
                params.append(f"%{mat}%")

            if usr:
                query += " AND u.username LIKE ?"
                params.append(f"%{usr}%")

            conn = get_connection()
            if not conn:
                raise Exception("数据库连接失败，请检查配置。")

            cursor = conn.cursor()
            cursor.execute(query + " ORDER BY r.timestamp DESC", params)
            raw_records = cursor.fetchall()
        
            # 格式化时间字段
            self.records = []
            for row in raw_records:
                formatted_row = list(row)
                formatted_row[3] = self._format_time(formatted_row[3])  # 格式化 timestamp
                self.records.append(formatted_row)

            self.refresh_table()

        except Exception as e:
            messagebox.showerror("筛选失败", f"错误原因：{str(e)}")

        finally:
            if conn:
                conn.close()

    def export_excel(self):
        if not self.records:
            messagebox.showwarning("无数据", "没有可导出的记录")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")],
            title="保存出入库记录"
        )
        
        if not filepath:
            return

        try:
            df = pd.DataFrame(
                self.records,
                columns=["ID", "类型", "数量", "时间", "物料名称", "操作用户", "备注"]
            )
            
            # 调整Excel列宽
            writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='出入库记录')
            
            worksheet = writer.sheets['出入库记录']
            worksheet.set_column('A:A', 8)   # ID
            worksheet.set_column('B:B', 10)  # 类型
            worksheet.set_column('C:C', 10)  # 数量
            worksheet.set_column('D:D', 20)  # 时间
            worksheet.set_column('E:E', 25)  # 物料名称
            worksheet.set_column('F:F', 15)  # 操作用户
            worksheet.set_column('G:G', 40)  # 备注
            
            writer.close()
            messagebox.showinfo("导出成功", f"文件已保存至：\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("导出失败", f"发生错误：{str(e)}")