# login_window.py
import customtkinter as ctk
from tkinter import messagebox
from db_config import get_connection
from inventory_io import InventoryIOWindow
from material_manager import MaterialManager
from inventory_query_window import InventoryQueryWindow
from inventory_check import InventoryCheckWindow
from inventory_alert import InventoryAlertWindow
from monthly_report_window import MonthlyReportWindow
from user_management import UserManagementWindow
from inout_record_viewer import InOutRecordViewer

def check_credentials(username, password):
    conn = get_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
       
        cursor.execute(
            "SELECT user_id, username, permission_level FROM Users WHERE username=? AND password=?",
            (username, password) 
        )
        row = cursor.fetchone()
        return row
    except Exception as e:
        print("查询失败：", e)
        return None
    finally:
        conn.close()

class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("库存管理系统 - 登录")
        self.geometry("400x350")
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        # 登录界面组件
        self._create_login_widgets()

    def _create_login_widgets(self):
        """创建登录界面UI组件"""
        self.label = ctk.CTkLabel(self, text="请登录", font=ctk.CTkFont(size=20))
        self.label.pack(pady=20)

        self.username_entry = ctk.CTkEntry(self, placeholder_text="用户名", width=220)
        self.username_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="密码", show="*", width=220)
        self.password_entry.pack(pady=10)

        self.login_button = ctk.CTkButton(
            self, 
            text="登录", 
            command=self.login,
            width=220,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.login_button.pack(pady=20)

    def login(self):
        """处理登录逻辑"""
        username = self.username_entry.get()
        password = self.password_entry.get()

        user = check_credentials(username, password)
        if user:
            user_id, username, permission_level = user
            messagebox.showinfo("登录成功", f"欢迎 {username}")
            self.withdraw()  # 隐藏登录窗口
            self._create_main_interface(user_id, username, permission_level)
        else:
            messagebox.showerror("登录失败", "用户名或密码错误")

    def _create_main_interface(self, user_id, username, permission_level):
        """创建主界面"""
        main_window = ctk.CTkToplevel(self)
        main_window.title("库存管理系统")
        main_window.geometry("1200x800")
        main_window.minsize(1000, 600)
        main_window.configure(bg_color="#f8f9fa")

        # 顶部信息栏
        header_frame = ctk.CTkFrame(main_window, height=60, fg_color="#e9ecef")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header_frame, 
            text=f"👤 {username} | 权限等级：{permission_level}",
            font=ctk.CTkFont(size=14),
            anchor="w"
        ).pack(side="left", padx=20)

        # 主功能区域
        main_frame = ctk.CTkScrollableFrame(
            main_window, 
            fg_color="transparent",
            scrollbar_button_color="#adb5bd"
        )
        main_frame.pack(fill="both", expand=True, padx=50, pady=10)

        # 创建功能按钮
        self._create_function_buttons(main_frame, user_id, permission_level)

        main_window.protocol("WM_DELETE_WINDOW", lambda: self.on_close(main_window))

    def _create_function_buttons(self, master, user_id, permission_level):
        """创建功能按钮"""
        button_configs = [
            {
                "text": "出入库管理",
                "icon": "📦",
                "color": "#4a90e2",
                "required_level": 1,
                "command": lambda: InventoryIOWindow(master, user_id=user_id)
            },
            {
                "text": "商品管理",
                "icon": "🛒",
                "color": "#50c878",
                "required_level": 2,
                "command": lambda: MaterialManager(master)
            },
            {
                "text": "库存查询",
                "icon": "🔍",
                "color": "#4a90e2",
                "required_level": 0,
                "command": lambda: InventoryQueryWindow(master)
            },
            {
                "text": "盘点记录管理",
                "icon": "📋",
                "color": "#ff6b6b",
                "required_level": 1,
                "command": lambda: InventoryCheckWindow(user_id=user_id, master=master)
            },
            {
                "text": "库存预警",
                "icon": "⚠️",
                "color": "#ff6b6b",
                "required_level": 0,
                "command": lambda: InventoryAlertWindow(master=master)
            },
            {
                "text": "用户管理",
                "icon": "👤",
                "color": "#50c878",
                "required_level": 2,
                "command": lambda: UserManagementWindow(master=master)
            },
            {
                "text": "出入库记录查询",
                "icon": "📜",
                "color": "#4a90e2",
                "required_level": 0,
                "command": lambda: InOutRecordViewer(master=master)
            }
        ]

        # 网格布局参数
        column_count = 4
        btn_width = 220
        btn_height = 100
        btn_padx = 15
        btn_pady = 15

        row, col = 0, 0
        for config in button_configs:
            if permission_level >= config["required_level"]:
                btn_frame = ctk.CTkFrame(master, width=btn_width, height=btn_height)
                btn_frame.grid(row=row, column=col, padx=btn_padx, pady=btn_pady)
                
                ctk.CTkButton(
                    btn_frame,
                    text=f"{config['icon']}\n{config['text']}",
                    command=config["command"],
                    width=btn_width,
                    height=btn_height,
                    fg_color=config["color"],
                    hover_color=self._adjust_brightness(config["color"], 0.9),
                    font=ctk.CTkFont(size=16, weight="bold"),
                    anchor="center",
                    text_color="white",
                    corner_radius=12
                ).pack(fill="both", expand=True)
                
                # 更新网格位置
                col += 1
                if col >= column_count:
                    col = 0
                    row += 1

    @staticmethod
    def _adjust_brightness(hex_color, factor):
        """调整颜色亮度"""
        rgb = tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = [min(255, int(c * factor)) for c in rgb]
        return f"#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}"

    def on_close(self, main_window):
        """处理窗口关闭事件"""
        self.deiconify()
        main_window.destroy()

if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()