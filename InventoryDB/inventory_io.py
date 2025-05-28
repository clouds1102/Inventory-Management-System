# inventory_io.py

import customtkinter as ctk
import tkinter.messagebox as msgbox
import pyodbc
from db_config import get_connection
from utils import check_alert

class InventoryIOWindow(ctk.CTkToplevel):
    def __init__(self, master=None, user_id=None):
        super().__init__(master)
        self.user_id = user_id
        self.title("出入库管理")
        self.geometry("500x350")

        self.conn = get_connection()
        self.materials = self.fetch_materials()
        
        self.create_widgets()

    def fetch_materials(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT material_id, material_name FROM Material")
            materials = cursor.fetchall()
            return {row.material_name: row.material_id for row in materials}
        except Exception as e:
            msgbox.showerror("数据库错误", f"无法加载物料列表: {e}")
            return {}

    def create_widgets(self):
        ctk.CTkLabel(self, text="选择物料:").pack(pady=5)
        self.material_var = ctk.StringVar()
        self.material_menu = ctk.CTkOptionMenu(self, variable=self.material_var, values=list(self.materials.keys()))
        self.material_menu.pack()

        ctk.CTkLabel(self, text="数量:").pack(pady=5)
        self.quantity_entry = ctk.CTkEntry(self)
        self.quantity_entry.pack()

        ctk.CTkLabel(self, text="操作类型:").pack(pady=5)
        self.io_type_var = ctk.StringVar(value="入库")
        self.io_type_menu = ctk.CTkOptionMenu(self, variable=self.io_type_var, values=["入库", "出库"])
        self.io_type_menu.pack()

        ctk.CTkLabel(self, text="备注（可选）:").pack(pady=5)
        self.note_entry = ctk.CTkEntry(self)
        self.note_entry.pack()

        self.submit_button = ctk.CTkButton(self, text="执行操作", command=self.handle_io)
        self.submit_button.pack(pady=20)

    def handle_io(self):
        material_name = self.material_var.get()
        material_id = self.materials.get(material_name)
        quantity_str = self.quantity_entry.get()
        io_type = self.io_type_var.get()
        note = self.note_entry.get()

        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                raise ValueError("数量必须大于0")
        except ValueError:
            msgbox.showwarning("输入错误", "请输入有效的数量")
            return

        try:
            cursor = self.conn.cursor()
            # 查询当前库存
            cursor.execute("SELECT inventory_id, current_quantity FROM Inventory WHERE material_id = ?", material_id)
            result = cursor.fetchone()
            if not result:
                # 如果库存记录不存在，初始化
                if io_type == "入库":
                    cursor.execute("INSERT INTO Inventory (material_id, current_quantity) VALUES (?, ?)", material_id, quantity)
                    self.conn.commit()
                else:
                    msgbox.showerror("错误", "该物料尚无库存，无法出库")
                    return
            else:
                inventory_id, current_quantity = result
                if io_type == "入库":
                    new_quantity = current_quantity + quantity
                    cursor.execute("UPDATE Inventory SET current_quantity = ?, last_updated = GETDATE() WHERE inventory_id = ?", new_quantity, inventory_id)
                elif io_type == "出库":
                    if quantity > current_quantity:
                        msgbox.showwarning("库存不足", "库存不足，无法出库")
                        return
                    new_quantity = current_quantity - quantity
                    cursor.execute("UPDATE Inventory SET current_quantity = ?, last_updated = GETDATE() WHERE inventory_id = ?", new_quantity, inventory_id)

            # 插入出入库记录
            if self.user_id is None:
                msgbox.showerror("错误", "未检测到用户登录信息")
                return
            
            cursor.execute(
                "INSERT INTO InOutRecord (material_id, user_id, type, quantity, note) VALUES (?, ?, ?, ?, ?)",
                material_id, self.user_id, io_type, quantity, note
            )

            self.conn.commit()

            try:
                check_alert(material_id)  # 执行库存预警检查
                print(f"已执行物料{material_id}的库存预警检查")
            except Exception as alert_error:
                print(f"预警检查时发生错误: {alert_error}")
                
            msgbox.showinfo("成功", f"{io_type}成功，已更新库存")
        except Exception as e:
            msgbox.showerror("数据库错误", f"执行失败: {e}")
