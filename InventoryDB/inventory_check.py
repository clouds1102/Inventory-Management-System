# inventory_check.py

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from db_config import get_connection
from datetime import datetime
import openpyxl
from utils import check_alert

class InventoryCheckWindow(ctk.CTkToplevel):
    def __init__(self, user_id, master=None):
        super().__init__(master)
        self.title("盘点记录管理")
        self.geometry("1100x700")
        self.user_id = user_id
        ctk.set_appearance_mode("light")

        # 搜索区域
        search_frame = ctk.CTkFrame(self, corner_radius=8)
        search_frame.pack(pady=15, padx=15, fill="x")

        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="输入物料名称搜索",
            width=400,
            height=35
        )
        search_entry.pack(side="left", padx=10, fill="x", expand=True)

        ctk.CTkButton(
            search_frame,
            text="搜索",
            width=80,
            height=35,
            command=self.load_records
        ).pack(side="left", padx=10)

        # 操作按钮区域
        button_frame = ctk.CTkFrame(self, corner_radius=8)
        button_frame.pack(pady=(0, 15), padx=15, fill="x")

        ctk.CTkButton(
            button_frame,
            text="➕ 新增盘点记录",
            width=140,
            height=35,
            command=self.add_check_window
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="导出Excel",
            width=120,
            height=35,
            command=self.export_to_excel
        ).pack(side="right", padx=5)

        # 表格容器
        table_container = ctk.CTkFrame(self, corner_radius=8)
        table_container.pack(padx=15, pady=(0, 15), fill="both", expand=True)

        # 表格配置
        columns = ("物料名称", "实际数量", "系统数量", "调整人", "盘点时间")
        self.table = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # 滚动条
        vsb = ttk.Scrollbar(table_container, orient="vertical", command=self.table.yview)
        hsb = ttk.Scrollbar(table_container, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 表格样式
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
            background="#ffffff",
            foreground="black",
            rowheight=30,
            fieldbackground="#ffffff",
            font=('Microsoft YaHei', 10)
        )
        style.configure("Treeview.Heading", 
            font=('Microsoft YaHei', 11, 'bold'),
            background="#f0f0f0",
            relief="flat"
        )
        style.map("Treeview", background=[('selected', '#e6e6e6')])

        # 列配置
        column_settings = {
            "物料名称": {"width": 280, "anchor": "w"},
            "实际数量": {"width": 120, "anchor": "e"},
            "系统数量": {"width": 120, "anchor": "e"},
            "调整人": {"width": 150, "anchor": "w"},
            "盘点时间": {"width": 200, "anchor": "w"}
        }

        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, **column_settings.get(col, {}))

        # 布局
        self.table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        self.load_records()

    def load_records(self):
        keyword = self.search_var.get()
        for row in self.table.get_children():
            self.table.delete(row)

        try:
            conn = get_connection()
            cursor = conn.cursor()

            query = """
                SELECT M.material_name, C.real_quantity, C.recorded_quantity,
                       U.username, C.check_time
                FROM InventoryCheck C
                JOIN Material M ON C.material_id = M.material_id
                JOIN Users U ON C.adjusted_by_user = U.user_id
                WHERE M.material_name LIKE ?
            """ if keyword else """
                SELECT M.material_name, C.real_quantity, C.recorded_quantity,
                       U.username, C.check_time
                FROM InventoryCheck C
                JOIN Material M ON C.material_id = M.material_id
                JOIN Users U ON C.adjusted_by_user = U.user_id
            """

            params = (f"%{keyword}%",) if keyword else ()

            cursor.execute(query, params)

            for row in cursor.fetchall():
                formatted_row = list(row)
                # 格式化时间
                if isinstance(formatted_row[4], datetime):
                    formatted_row[4] = formatted_row[4].strftime("%Y-%m-%d %H:%M:%S")
                self.table.insert("", "end", values=formatted_row)

        except Exception as e:
            messagebox.showerror("错误", f"查询失败：{e}")
        finally:
            if conn:
                conn.close()

    def export_to_excel(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")],
            title="保存盘点记录"
        )

        if not file_path:
            return

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "盘点记录"

            # 写入标题
            headers = [self.table.heading(col)["text"] for col in self.table["columns"]]
            ws.append(headers)

            # 写入数据
            for item in self.table.get_children():
                row_data = self.table.item(item)["values"]
                ws.append(row_data)

            # 自动调整列宽
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.2
                ws.column_dimensions[column].width = adjusted_width

            wb.save(file_path)
            messagebox.showinfo("导出成功", f"文件已保存至：\n{file_path}")

        except Exception as e:
            messagebox.showerror("导出失败", f"错误原因：{e}")

    def add_check_window(self):
        top = ctk.CTkToplevel(self)
        top.title("新增盘点记录")
        top.geometry("400x300")

        ctk.CTkLabel(top, text="物料名称").pack(pady=5)
        material_var = ctk.StringVar()
        material_box = ctk.CTkComboBox(top, variable=material_var)
        material_box.pack(pady=5)

        ctk.CTkLabel(top, text="实际数量").pack(pady=5)
        real_entry = ctk.CTkEntry(top)
        real_entry.pack(pady=5)

        def save_check():
            name = material_var.get()
            real = real_entry.get()

            try:
                real = int(real)
                conn = get_connection()
                cursor = conn.cursor()

                # 获取物料ID
                cursor.execute("SELECT material_id FROM Material WHERE material_name=?", (name,))
                row = cursor.fetchone()
                if not row:
                    messagebox.showerror("错误", "未找到该物料")
                    return
                material_id = row[0]

                # 获取当前库存（新增事务开始）
                cursor.execute("SELECT current_quantity FROM Inventory WHERE material_id=?", (material_id,))
                row = cursor.fetchone()
                if not row:
                    messagebox.showerror("错误", "库存中无该物料")
                    return
                recorded = row[0]

                # 更新库存表（新增逻辑）
                cursor.execute("""
                    UPDATE Inventory 
                    SET current_quantity = ?, 
                        last_updated = GETDATE() 
                    WHERE material_id = ?
                """, (real, material_id))

                # 插入盘点记录
                cursor.execute(
                    "INSERT INTO InventoryCheck (material_id, real_quantity, recorded_quantity, adjusted_by_user) VALUES (?, ?, ?, ?)",
                    (material_id, real, recorded, self.user_id)
                )

                conn.commit()
            
                # 触发预警检查
                try:
                    check_alert(material_id)
                except Exception as alert_error:
                    print(f"预警检查时发生错误: {alert_error}")

                messagebox.showinfo("成功", "盘点记录已添加并更新库存")
                top.destroy()
                self.load_records()

            except ValueError:
                messagebox.showerror("错误", "请输入有效的实际数量")
            except Exception as e:
                conn.rollback()  # 新增回滚操作
                messagebox.showerror("错误", f"保存失败：{e}")
            finally:
                if conn:
                    conn.close()

        # 获取物料名称
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT material_name FROM Material")
            material_box.configure(values=[row[0] for row in cursor.fetchall()])
        except:
            pass
        finally:
            if conn:
                conn.close()

        ctk.CTkButton(top, text="保存", command=save_check).pack(pady=10)