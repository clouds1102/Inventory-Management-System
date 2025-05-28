# material_manager.py

import customtkinter as ctk
import tkinter.messagebox as msg
import tkinter.simpledialog as simpledialog
from db_config import get_connection

class MaterialManager(ctk.CTkToplevel):
    def __init__(self, master=None):  # 添加 master 参数
        super().__init__(master)
        self.title("商品管理")
        self.geometry("800x500")

        self.search_entry = ctk.CTkEntry(self, placeholder_text="🔍 搜索功能")
        self.search_entry.pack(pady=10)
        self.search_entry.bind("<Return>", lambda e: self.load_materials())

        self.table = ctk.CTkTextbox(self, width=750, height=300)
        self.table.pack(pady=10)

        # 按钮区域
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="➕ 新增", command=self.add_material).grid(row=0, column=0, padx=10)
        ctk.CTkButton(btn_frame, text="✏️ 编辑", command=self.edit_material).grid(row=0, column=1, padx=10)
        ctk.CTkButton(btn_frame, text="❌ 删除", command=self.delete_material).grid(row=0, column=2, padx=10)
        ctk.CTkButton(btn_frame, text="🔄 刷新", command=self.load_materials).grid(row=0, column=3, padx=10)

        self.load_materials()

    def load_materials(self):
        keyword = self.search_entry.get()
        try:
            conn = get_connection()
            cursor = conn.cursor()
            if keyword:
                query = "SELECT * FROM Material WHERE material_name LIKE ?"
                cursor.execute(query, (f'%{keyword}%',))
            else:
                query = "SELECT * FROM Material"
                cursor.execute(query)
            results = cursor.fetchall()

            self.table.delete("0.0", "end")
            self.table.insert("end", f"{'ID':<5} {'名称':<15} {'供应商':<15} {'单位':<5} {'最小':<5} {'最大':<5} {'备注':<20}\n")
            self.table.insert("end", "-" * 80 + "\n")
            for row in results:
                self.table.insert("end", f"{row.material_id:<5} {row.material_name:<15} {row.supplier:<15} {row.unit:<5} {row.min_quantity:<5} {row.max_quantity:<5} {row.note or '-':<20}\n")

        except Exception as e:
            msg.showerror("数据库错误", str(e))
        finally:
            conn.close()

    def add_material(self):
        name = simpledialog.askstring("新增", "商品名称：")
        if not name:
            return
        supplier = simpledialog.askstring("新增", "供应商：")
        unit = simpledialog.askstring("新增", "单位（如个/箱）：")
        min_q = simpledialog.askinteger("新增", "最小库存：")
        max_q = simpledialog.askinteger("新增", "最大库存：")
        note = simpledialog.askstring("新增", "备注（可选）：")

        try:
            conn = get_connection()
            cursor = conn.cursor()
            query = "INSERT INTO Material (material_name, supplier, unit, min_quantity, max_quantity, note) VALUES (?, ?, ?, ?, ?, ?)"
            cursor.execute(query, (name, supplier, unit, min_q, max_q, note))
            conn.commit()
            msg.showinfo("成功", "新增成功！")
            self.load_materials()
        except Exception as e:
            msg.showerror("错误", str(e))
        finally:
            conn.close()

    def edit_material(self):
        material_id = simpledialog.askinteger("编辑", "请输入要编辑的商品 ID：")
        if not material_id:
            return
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Material WHERE material_id = ?", (material_id,))
            result = cursor.fetchone()
            if not result:
                msg.showwarning("未找到", "该商品 ID 不存在")
                return

            name = simpledialog.askstring("编辑", "商品名称：", initialvalue=result.material_name)
            supplier = simpledialog.askstring("编辑", "供应商：", initialvalue=result.supplier)
            unit = simpledialog.askstring("编辑", "单位：", initialvalue=result.unit)
            min_q = simpledialog.askinteger("编辑", "最小库存：", initialvalue=result.min_quantity)
            max_q = simpledialog.askinteger("编辑", "最大库存：", initialvalue=result.max_quantity)
            note = simpledialog.askstring("编辑", "备注：", initialvalue=result.note)

            query = "UPDATE Material SET material_name=?, supplier=?, unit=?, min_quantity=?, max_quantity=?, note=? WHERE material_id=?"
            cursor.execute(query, (name, supplier, unit, min_q, max_q, note, material_id))
            conn.commit()
            msg.showinfo("成功", "修改成功")
            self.load_materials()
        except Exception as e:
            msg.showerror("错误", str(e))
        finally:
            conn.close()

    def delete_material(self):
        material_id = simpledialog.askinteger("删除", "请输入要删除的商品 ID：")
        if not material_id:
            return
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Material WHERE material_id = ?", (material_id,))
            conn.commit()
            msg.showinfo("成功", "删除成功")
            self.load_materials()
        except Exception as e:
            msg.showerror("错误", str(e))
        finally:
            conn.close()
