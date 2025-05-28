# user_management.py

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pyodbc
from db_config import get_connection

class UserManagementWindow(ctk.CTkToplevel):
    def __init__(self, master=None):  # 添加 master 参数
        super().__init__(master)
        self.title("用户管理")
        self.geometry("700x500")
        self.user_data = []
        self.create_widgets()
        self.load_users()

    def create_widgets(self):
        # 搜索区域
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(pady=10, fill="x")
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="输入用户名搜索")
        self.search_entry.pack(side="left", padx=10, expand=True, fill="x")
        ctk.CTkButton(search_frame, text="🔍 搜索", command=self.search_user).pack(side="left", padx=5)
        ctk.CTkButton(search_frame, text="🔄 显示全部", command=self.load_users).pack(side="left", padx=5)

        # 操作按钮区域
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=5)
        ctk.CTkButton(btn_frame, text="➕ 添加用户", command=self.add_user).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="✏️ 修改用户", command=self.edit_user).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="❌ 删除用户", command=self.delete_user).pack(side="left", padx=10)

        # 表格显示区域
        tree_frame = ctk.CTkFrame(self)
        tree_frame.pack(pady=10, fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=("ID", "用户名", "角色", "权限等级"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("用户名", text="用户名")
        self.tree.heading("角色", text="角色")
        self.tree.heading("权限等级", text="权限等级")

        self.tree.column("ID", width=50)
        self.tree.column("用户名", width=150)
        self.tree.column("角色", width=100)
        self.tree.column("权限等级", width=100)

        self.tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def load_users(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, role, permission_level FROM Users")
            self.user_data = cursor.fetchall()
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("错误", str(e))
        finally:
            conn.close()

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.user_data:
            self.tree.insert("", "end", values=(row[0], row[1], row[2], row[3]))

    def search_user(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showinfo("提示", "请输入用户名关键词")
            return
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, role, permission_level FROM Users WHERE username LIKE ?", ('%' + keyword + '%',))
            self.user_data = cursor.fetchall()
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("错误", str(e))
        finally:
            conn.close()

    def add_user(self):
        username = simpledialog.askstring("用户名", "请输入用户名：", parent=self)
        if not username:
            return
        password = simpledialog.askstring("密码", "请输入密码：", parent=self, show="*")
        if not password:
            return
        role = simpledialog.askstring("角色", "请输入角色（如管理员）：", parent=self)
        if not role:
            return
        try:
            permission = int(simpledialog.askstring("权限等级", "请输入权限等级（整数）：", parent=self))
        except:
            messagebox.showwarning("输入错误", "权限等级必须是整数")
            return
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Users (username, password, role, permission_level) VALUES (?, ?, ?, ?)", (username, password, role, permission))
            conn.commit()
            messagebox.showinfo("成功", "添加用户成功")
            self.load_users()
        except Exception as e:
            messagebox.showerror("错误", str(e))
        finally:
            conn.close()

    def edit_user(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个用户")
            return
        item = self.tree.item(selected[0])
        user_id, old_username, old_role, old_perm = item["values"]

        new_password = simpledialog.askstring("修改密码", f"输入新密码（留空不修改）：", parent=self, show="*")
        new_role = simpledialog.askstring("修改角色", f"当前：{old_role}，修改为：", parent=self)
        if not new_role:
            new_role = old_role
        try:
            new_perm = simpledialog.askinteger("修改权限等级", f"当前：{old_perm}，修改为：", parent=self)
            if new_perm is None:
                new_perm = old_perm
        except:
            messagebox.showwarning("错误", "权限等级无效")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()
            if new_password:
                cursor.execute("UPDATE Users SET password=?, role=?, permission_level=? WHERE user_id=?", (new_password, new_role, new_perm, user_id))
            else:
                cursor.execute("UPDATE Users SET role=?, permission_level=? WHERE user_id=?", (new_role, new_perm, user_id))
            conn.commit()
            messagebox.showinfo("成功", "修改成功")
            self.load_users()
        except Exception as e:
            messagebox.showerror("错误", str(e))
        finally:
            conn.close()

    def delete_user(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个用户")
            return
        item = self.tree.item(selected[0])
        user_id = item["values"][0]
        if messagebox.askyesno("确认", "确定要删除该用户？"):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Users WHERE user_id=?", (user_id,))
                conn.commit()
                messagebox.showinfo("成功", "删除成功")
                self.load_users()
            except Exception as e:
                messagebox.showerror("错误", str(e))
            finally:
                conn.close()
