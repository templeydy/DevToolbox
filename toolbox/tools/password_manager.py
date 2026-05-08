"""
账号密码管理工具
使用邮箱作为账户，通过邮件验证码登录
支持加密存储账号密码、分组管理、搜索、复制
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import hashlib
import base64
import secrets
import threading
from datetime import datetime
from toolbox.settings import (
    get_smtp_config, get_smtp_account, generate_verification_code,
    send_verification_email, encrypt_data, decrypt_data
)


VAULT_DIR = os.path.join(os.path.expanduser("~"), ".devtoolbox_vault")


class PasswordManagerPanel:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.master_password = None
        self.current_email = None
        self.entries = []
        self.unlocked = False
        self._pending_code = None
        self._pending_email = None
        self._ensure_vault_dir()
        self._build_ui()

    def _ensure_vault_dir(self):
        os.makedirs(VAULT_DIR, exist_ok=True)

    def _user_file(self, email):
        """每个用户一个文件"""
        safe_name = email.replace("@", "_at_").replace(".", "_")
        return os.path.join(VAULT_DIR, f"user_{safe_name}.json")

    def _user_exists(self, email):
        return os.path.exists(self._user_file(email))

    def _load_user_data(self, email):
        path = self._user_file(email)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def _save_user_data(self, email, data):
        with open(self._user_file(email), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_entries(self):
        """加载并解密用户的密码条目"""
        user_data = self._load_user_data(self.current_email)
        if not user_data or "vault" not in user_data:
            self.entries = []
            return
        try:
            plaintext = decrypt_data(user_data["vault"], self.master_password)
            self.entries = json.loads(plaintext)
        except Exception:
            self.entries = []
            messagebox.showerror("解密失败", "密码错误或数据损坏")

    def _save_entries(self):
        """加密并保存密码条目"""
        user_data = self._load_user_data(self.current_email) or {}
        plaintext = json.dumps(self.entries, ensure_ascii=False)
        user_data["vault"] = encrypt_data(plaintext, self.master_password)
        self._save_user_data(self.current_email, user_data)

    def _build_ui(self):
        # === 登录界面 ===
        self.login_frame = ttk.Frame(self.frame)
        self.login_frame.pack(fill=tk.BOTH, expand=True)

        login_inner = ttk.Frame(self.login_frame)
        login_inner.place(relx=0.5, rely=0.35, anchor=tk.CENTER)

        ttk.Label(login_inner, text="🔒 账号密码管理器", font=("", 16, "bold")).pack(pady=(0, 20))

        # 邮箱输入
        email_frame = ttk.Frame(login_inner)
        email_frame.pack(fill=tk.X, pady=5)
        ttk.Label(email_frame, text="邮箱:", width=8).pack(side=tk.LEFT)
        self.login_email_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.login_email_var, width=30).pack(side=tk.LEFT, padx=5)

        # 密码输入（已有密码的用户）
        self.pw_login_frame = ttk.Frame(login_inner)
        self.pw_login_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.pw_login_frame, text="密码:", width=8).pack(side=tk.LEFT)
        self.login_pw_var = tk.StringVar()
        pw_entry = ttk.Entry(self.pw_login_frame, textvariable=self.login_pw_var, show="*", width=30)
        pw_entry.pack(side=tk.LEFT, padx=5)
        pw_entry.bind("<Return>", lambda e: self._do_password_login())

        # 验证码输入（验证码登录时显示）
        self.code_frame = ttk.Frame(login_inner)
        ttk.Label(self.code_frame, text="验证码:", width=8).pack(side=tk.LEFT)
        self.login_code_var = tk.StringVar()
        code_entry = ttk.Entry(self.code_frame, textvariable=self.login_code_var, width=15)
        code_entry.pack(side=tk.LEFT, padx=5)
        code_entry.bind("<Return>", lambda e: self._verify_code())
        ttk.Button(self.code_frame, text="验证", command=self._verify_code).pack(side=tk.LEFT, padx=3)

        # 按钮区
        btn_frame = ttk.Frame(login_inner)
        btn_frame.pack(fill=tk.X, pady=10)
        self.login_btn = ttk.Button(btn_frame, text="登录", command=self._do_password_login)
        self.login_btn.pack(side=tk.LEFT, padx=5)
        self.send_code_btn = ttk.Button(btn_frame, text="发送验证码登录", command=self._send_verification_code)
        self.send_code_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="忘记密码", command=self._forgot_password).pack(side=tk.LEFT, padx=5)

        self.login_status_var = tk.StringVar()
        ttk.Label(login_inner, textvariable=self.login_status_var, foreground="blue").pack(pady=5)

        # SMTP 提示
        ttk.Label(login_inner, text="首次使用请先在左侧「⚙ 全局设置」中配置 SMTP",
                  foreground="gray").pack(pady=(10, 0))

        # === 主界面（解锁后显示）===
        self.main_frame = ttk.Frame(self.frame)
        self._build_main_ui()

    def _build_main_ui(self):
        # 顶部工具栏
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="新增", command=self._add_entry).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="编辑", command=self._edit_entry).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="删除", command=self._delete_entry).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="复制密码", command=self._copy_password).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="复制用户名", command=self._copy_username).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Button(toolbar, text="修改密码", command=self._change_password).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="🔒 锁定", command=self._lock).pack(side=tk.RIGHT)

        # 当前用户
        self.user_label_var = tk.StringVar()
        ttk.Label(toolbar, textvariable=self.user_label_var, foreground="green").pack(side=tk.RIGHT, padx=10)

        # 搜索
        search_frame = ttk.Frame(self.main_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side=tk.LEFT, padx=5)

        ttk.Label(search_frame, text="分组:").pack(side=tk.LEFT, padx=(15, 0))
        self.group_filter_var = tk.StringVar(value="全部")
        self.group_combo = ttk.Combobox(search_frame, textvariable=self.group_filter_var,
                                         state="readonly", width=15)
        self.group_combo.pack(side=tk.LEFT, padx=5)
        self.group_combo.bind("<<ComboboxSelected>>", self._on_search)

        # 列表
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        columns = ("group", "title", "username", "url", "updated")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("group", text="分组")
        self.tree.heading("title", text="标题")
        self.tree.heading("username", text="用户名")
        self.tree.heading("url", text="网址/备注")
        self.tree.heading("updated", text="更新时间")
        self.tree.column("group", width=80)
        self.tree.column("title", width=150)
        self.tree.column("username", width=150)
        self.tree.column("url", width=200)
        self.tree.column("updated", width=130)

        vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Double-1>", lambda e: self._edit_entry())

    # ---------- 登录流程 ----------

    def _send_verification_code(self):
        """发送验证码（使用全局 SMTP 配置）"""
        email = self.login_email_var.get().strip()
        if not email or "@" not in email:
            messagebox.showwarning("提示", "请输入有效的邮箱地址")
            return

        if not get_smtp_account():
            messagebox.showwarning("提示", "请先在左侧「⚙ 全局设置」中配置 SMTP")
            return

        self.send_code_btn.config(state=tk.DISABLED)
        self.login_status_var.set("正在发送验证码...")
        threading.Thread(target=self._do_send_code, args=(email,), daemon=True).start()

    def _do_send_code(self, email):
        try:
            code = generate_verification_code()
            send_verification_email(email, code)
            self._pending_code = code
            self._pending_email = email

            def on_success():
                self.login_status_var.set(f"验证码已发送到 {email}")
                self.code_frame.pack(fill=tk.X, pady=5, after=self.pw_login_frame)
                self.send_code_btn.config(state=tk.NORMAL)

            self.frame.after(0, on_success)
        except Exception as e:
            self.frame.after(0, lambda: self.login_status_var.set(f"发送失败: {str(e)[:60]}"))
            self.frame.after(0, lambda: messagebox.showerror("发送失败", str(e)))
            self.frame.after(0, lambda: self.send_code_btn.config(state=tk.NORMAL))

    def _verify_code(self):
        """验证验证码"""
        code = self.login_code_var.get().strip()
        if not code:
            messagebox.showwarning("提示", "请输入验证码")
            return

        if code != self._pending_code:
            messagebox.showerror("错误", "验证码错误")
            return

        email = self._pending_email
        self._pending_code = None

        if self._user_exists(email):
            # 老用户验证码登录 - 使用邮箱作为临时密码解密
            # 验证码登录时用存储的 key 解密
            user_data = self._load_user_data(email)
            self.current_email = email
            self.master_password = user_data.get("_master_key", email)
            self._load_entries()
            self._unlock_ui()
        else:
            # 新用户 - 创建账户
            self.current_email = email
            self.master_password = email  # 默认用邮箱作为初始密钥
            user_data = {
                "_master_key": email,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self._save_user_data(email, user_data)
            self.entries = []
            self._save_entries()
            self._unlock_ui()
            messagebox.showinfo("欢迎", "新账户创建成功！建议在登录后设置密码（点击 修改密码 按钮）。")

    def _do_password_login(self):
        """密码登录"""
        email = self.login_email_var.get().strip()
        password = self.login_pw_var.get().strip()

        if not email or "@" not in email:
            messagebox.showwarning("提示", "请输入有效的邮箱地址")
            return
        if not password:
            messagebox.showwarning("提示", "请输入密码")
            return

        if not self._user_exists(email):
            # 用户不存在，按新用户处理，发验证码
            messagebox.showinfo("提示", "该邮箱尚未注册，将发送验证码进行注册")
            self._send_verification_code()
            return

        user_data = self._load_user_data(email)
        stored_key = user_data.get("_master_key", email)

        # 验证密码
        if user_data.get("_password_hash"):
            salt = base64.b64decode(user_data["_password_salt"])
            computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
            if base64.b64encode(computed).decode() != user_data["_password_hash"]:
                messagebox.showerror("错误", "密码错误")
                return
            self.master_password = password
        else:
            # 没设置过密码，用默认 key
            self.master_password = stored_key

        self.current_email = email
        self._load_entries()
        self._unlock_ui()

    def _forgot_password(self):
        """忘记密码 - 发送验证码"""
        email = self.login_email_var.get().strip()
        if not email or "@" not in email:
            messagebox.showwarning("提示", "请先输入邮箱地址")
            return
        self.login_status_var.set("正在发送重置验证码...")
        self._send_verification_code()

    def _unlock_ui(self):
        """切换到主界面"""
        self.unlocked = True
        self.user_label_var.set(f"当前用户: {self.current_email}")
        self.login_frame.pack_forget()
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self._refresh_list()
        self._refresh_groups()
        # 清理登录状态
        self.login_pw_var.set("")
        self.login_code_var.set("")
        self.login_status_var.set("")
        self.code_frame.pack_forget()

    def _lock(self):
        """锁定"""
        self.master_password = None
        self.current_email = None
        self.unlocked = False
        self.entries = []
        self.main_frame.pack_forget()
        self.login_frame.pack(fill=tk.BOTH, expand=True)

    # ---------- 修改密码 ----------

    def _change_password(self):
        """修改密码"""
        win = tk.Toplevel(self.frame.winfo_toplevel())
        win.title("修改密码")
        win.geometry("350x200")
        win.transient(self.frame.winfo_toplevel())
        win.grab_set()

        f = ttk.Frame(win, padding=15)
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(f, text="设置新密码", font=("", 11, "bold")).pack(pady=(0, 10))

        pw1_frame = ttk.Frame(f)
        pw1_frame.pack(fill=tk.X, pady=5)
        ttk.Label(pw1_frame, text="新密码:", width=10).pack(side=tk.LEFT)
        pw1_var = tk.StringVar()
        ttk.Entry(pw1_frame, textvariable=pw1_var, show="*", width=25).pack(side=tk.LEFT)

        pw2_frame = ttk.Frame(f)
        pw2_frame.pack(fill=tk.X, pady=5)
        ttk.Label(pw2_frame, text="确认密码:", width=10).pack(side=tk.LEFT)
        pw2_var = tk.StringVar()
        ttk.Entry(pw2_frame, textvariable=pw2_var, show="*", width=25).pack(side=tk.LEFT)

        def do_change():
            pw1 = pw1_var.get()
            pw2 = pw2_var.get()
            if not pw1:
                messagebox.showwarning("提示", "密码不能为空", parent=win)
                return
            if pw1 != pw2:
                messagebox.showerror("错误", "两次输入不一致", parent=win)
                return

            # 用新密码重新加密数据
            old_password = self.master_password
            self.master_password = pw1

            # 保存密码哈希
            user_data = self._load_user_data(self.current_email) or {}
            salt = secrets.token_bytes(16)
            pw_hash = hashlib.pbkdf2_hmac("sha256", pw1.encode("utf-8"), salt, 100000)
            user_data["_password_hash"] = base64.b64encode(pw_hash).decode()
            user_data["_password_salt"] = base64.b64encode(salt).decode()
            user_data["_master_key"] = pw1
            self._save_user_data(self.current_email, user_data)

            # 重新加密条目
            self._save_entries()

            messagebox.showinfo("成功", "密码修改成功", parent=win)
            win.destroy()

        ttk.Button(f, text="确认修改", command=do_change).pack(pady=10)

    # ---------- 列表操作 ----------

    def _refresh_groups(self):
        groups = sorted(set(e.get("group", "默认") for e in self.entries))
        self.group_combo["values"] = ["全部"] + groups

    def _refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        filter_text = self.search_var.get().lower()
        group_filter = self.group_filter_var.get()

        for entry in self.entries:
            group = entry.get("group", "默认")
            if group_filter != "全部" and group != group_filter:
                continue
            if filter_text:
                searchable = f"{entry.get('title', '')} {entry.get('username', '')} {entry.get('url', '')} {entry.get('notes', '')}".lower()
                if filter_text not in searchable:
                    continue
            self.tree.insert("", tk.END, iid=entry["id"], values=(
                group,
                entry.get("title", ""),
                entry.get("username", ""),
                entry.get("url", "")[:40],
                entry.get("updated", ""),
            ))

    def _on_search(self, *args):
        self._refresh_list()

    def _get_selected_entry(self):
        sel = self.tree.selection()
        if not sel:
            return None
        entry_id = sel[0]
        for e in self.entries:
            if e["id"] == entry_id:
                return e
        return None

    # ---------- 增删改 ----------

    def _add_entry(self):
        self._open_entry_dialog(None)

    def _edit_entry(self):
        entry = self._get_selected_entry()
        if not entry:
            messagebox.showwarning("提示", "请先选择一条记录")
            return
        self._open_entry_dialog(entry)

    def _delete_entry(self):
        entry = self._get_selected_entry()
        if not entry:
            messagebox.showwarning("提示", "请先选择一条记录")
            return
        if not messagebox.askyesno("确认", f"确定删除「{entry.get('title', '')}」？"):
            return
        self.entries = [e for e in self.entries if e["id"] != entry["id"]]
        self._save_entries()
        self._refresh_list()
        self._refresh_groups()

    def _open_entry_dialog(self, entry):
        is_new = entry is None
        dialog = tk.Toplevel(self.frame.winfo_toplevel())
        dialog.title("新增账号" if is_new else "编辑账号")
        dialog.geometry("450x380")
        dialog.transient(self.frame.winfo_toplevel())
        dialog.grab_set()

        fields_frame = ttk.Frame(dialog, padding=15)
        fields_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(fields_frame, text="分组:").grid(row=0, column=0, sticky=tk.W, pady=5)
        group_var = tk.StringVar(value=entry.get("group", "默认") if entry else "默认")
        groups = sorted(set(e.get("group", "默认") for e in self.entries)) or ["默认"]
        ttk.Combobox(fields_frame, textvariable=group_var, values=groups, width=30).grid(
            row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(fields_frame, text="标题:").grid(row=1, column=0, sticky=tk.W, pady=5)
        title_var = tk.StringVar(value=entry.get("title", "") if entry else "")
        ttk.Entry(fields_frame, textvariable=title_var, width=32).grid(
            row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(fields_frame, text="用户名:").grid(row=2, column=0, sticky=tk.W, pady=5)
        username_var = tk.StringVar(value=entry.get("username", "") if entry else "")
        ttk.Entry(fields_frame, textvariable=username_var, width=32).grid(
            row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(fields_frame, text="密码:").grid(row=3, column=0, sticky=tk.W, pady=5)
        pw_frame = ttk.Frame(fields_frame)
        pw_frame.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        password_var = tk.StringVar(value=entry.get("password", "") if entry else "")
        pw_entry = ttk.Entry(pw_frame, textvariable=password_var, show="*", width=24)
        pw_entry.pack(side=tk.LEFT)

        def toggle_pw():
            if pw_entry.cget("show") == "*":
                pw_entry.config(show="")
                toggle_btn.config(text="隐藏")
            else:
                pw_entry.config(show="*")
                toggle_btn.config(text="显示")

        toggle_btn = ttk.Button(pw_frame, text="显示", command=toggle_pw, width=5)
        toggle_btn.pack(side=tk.LEFT, padx=3)

        def gen_pw():
            chars = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%&*"
            password_var.set("".join(secrets.choice(chars) for _ in range(16)))

        ttk.Button(pw_frame, text="生成", command=gen_pw, width=5).pack(side=tk.LEFT)

        ttk.Label(fields_frame, text="网址:").grid(row=4, column=0, sticky=tk.W, pady=5)
        url_var = tk.StringVar(value=entry.get("url", "") if entry else "")
        ttk.Entry(fields_frame, textvariable=url_var, width=32).grid(
            row=4, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(fields_frame, text="备注:").grid(row=5, column=0, sticky=tk.NW, pady=5)
        notes_text = tk.Text(fields_frame, width=32, height=4, font=("", 10))
        notes_text.grid(row=5, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        if entry and entry.get("notes"):
            notes_text.insert("1.0", entry["notes"])

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=15, pady=10)

        def save():
            title = title_var.get().strip()
            if not title:
                messagebox.showwarning("提示", "标题不能为空", parent=dialog)
                return
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if is_new:
                new_entry = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                    "group": group_var.get().strip() or "默认",
                    "title": title,
                    "username": username_var.get().strip(),
                    "password": password_var.get(),
                    "url": url_var.get().strip(),
                    "notes": notes_text.get("1.0", tk.END).strip(),
                    "created": now,
                    "updated": now,
                }
                self.entries.insert(0, new_entry)
            else:
                entry["group"] = group_var.get().strip() or "默认"
                entry["title"] = title
                entry["username"] = username_var.get().strip()
                entry["password"] = password_var.get()
                entry["url"] = url_var.get().strip()
                entry["notes"] = notes_text.get("1.0", tk.END).strip()
                entry["updated"] = now
            self._save_entries()
            self._refresh_list()
            self._refresh_groups()
            dialog.destroy()

        ttk.Button(btn_frame, text="保存", command=save).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)

    # ---------- 复制 ----------

    def _copy_password(self):
        entry = self._get_selected_entry()
        if not entry:
            messagebox.showwarning("提示", "请先选择一条记录")
            return
        self.frame.clipboard_clear()
        self.frame.clipboard_append(entry.get("password", ""))
        messagebox.showinfo("已复制", "密码已复制到剪贴板")

    def _copy_username(self):
        entry = self._get_selected_entry()
        if not entry:
            messagebox.showwarning("提示", "请先选择一条记录")
            return
        self.frame.clipboard_clear()
        self.frame.clipboard_append(entry.get("username", ""))
        messagebox.showinfo("已复制", "用户名已复制到剪贴板")


def create_password_manager(parent):
    """工厂函数，供主界面注册调用"""
    panel = PasswordManagerPanel(parent)
    return panel.frame
