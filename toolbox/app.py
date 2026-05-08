"""
工具集主界面 - 侧边栏导航 + 右侧工具面板
美化版：自定义配色、圆角风格、hover 效果
"""

import tkinter as tk
from tkinter import ttk, messagebox
from toolbox.settings import get_smtp_config, save_smtp_config


# 配色方案
COLORS = {
    "bg": "#1e2a3a",           # 深蓝背景
    "nav_bg": "#253545",       # 导航栏背景
    "nav_hover": "#2d4a5e",    # 导航项 hover
    "nav_active": "#3a7bd5",   # 导航项选中
    "content_bg": "#f5f7fa",   # 内容区背景
    "text": "#e8edf3",         # 浅色文字
    "text_dark": "#2c3e50",    # 深色文字
    "accent": "#3a7bd5",       # 强调色
    "accent_hover": "#4a8be5", # 强调色 hover
    "border": "#34495e",       # 边框色
    "card_bg": "#ffffff",      # 卡片背景
}


class ToolboxApp:
    def __init__(self, root):
        self.root = root
        self.root.title("开发工具集")
        self.root.geometry("1100x750")
        self.root.minsize(950, 650)
        self.root.configure(bg=COLORS["bg"])

        self.tools = {}
        self.current_tool = None
        self.nav_buttons = []

        self._setup_styles()
        self._build_ui()
        self._register_tools()
        self._load_appearance()

        # 默认选中第一个
        if self.nav_buttons:
            self._select_tool(0)

    def _setup_styles(self):
        """配置 ttk 主题样式"""
        style = ttk.Style()
        style.theme_use("clam")

        # 全局字体
        style.configure(".", font=("Microsoft YaHei UI", 10))

        # Frame 样式
        style.configure("Nav.TFrame", background=COLORS["nav_bg"])
        style.configure("Content.TFrame", background=COLORS["content_bg"])
        style.configure("Card.TFrame", background=COLORS["card_bg"])

        # Label 样式
        style.configure("NavTitle.TLabel",
                        background=COLORS["nav_bg"],
                        foreground=COLORS["text"],
                        font=("Microsoft YaHei UI", 14, "bold"))
        style.configure("NavSub.TLabel",
                        background=COLORS["nav_bg"],
                        foreground="#8899aa",
                        font=("Microsoft YaHei UI", 9))

        # Button 样式
        style.configure("Accent.TButton",
                        font=("Microsoft YaHei UI", 10),
                        padding=(12, 6))
        style.map("Accent.TButton",
                  background=[("active", COLORS["accent_hover"]),
                              ("!active", COLORS["accent"])],
                  foreground=[("active", "white"), ("!active", "white")])

        # Notebook 样式
        style.configure("TNotebook", background=COLORS["content_bg"])
        style.configure("TNotebook.Tab", padding=(12, 6),
                        font=("Microsoft YaHei UI", 10))

        # LabelFrame
        style.configure("TLabelframe", background=COLORS["card_bg"])
        style.configure("TLabelframe.Label",
                        font=("Microsoft YaHei UI", 10, "bold"),
                        foreground=COLORS["text_dark"])

    def _build_ui(self):
        # --- 左侧导航栏 ---
        self.nav_frame = tk.Frame(self.root, bg=COLORS["nav_bg"], width=200)
        self.nav_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.nav_frame.pack_propagate(False)

        # Logo/标题区
        title_frame = tk.Frame(self.nav_frame, bg=COLORS["nav_bg"])
        title_frame.pack(fill=tk.X, padx=15, pady=(20, 5))

        tk.Label(title_frame, text="📘 开发工具集",
                 font=("Microsoft YaHei UI", 13, "bold"),
                 bg=COLORS["nav_bg"], fg=COLORS["text"]).pack(anchor=tk.W)
        tk.Label(title_frame, text="DevToolbox v1.0",
                 font=("Microsoft YaHei UI", 9),
                 bg=COLORS["nav_bg"], fg="#6b8299").pack(anchor=tk.W, pady=(2, 0))

        # 分隔线
        sep = tk.Frame(self.nav_frame, bg=COLORS["border"], height=1)
        sep.pack(fill=tk.X, padx=15, pady=(15, 10))

        # 导航按钮容器
        self.nav_list_frame = tk.Frame(self.nav_frame, bg=COLORS["nav_bg"])
        self.nav_list_frame.pack(fill=tk.BOTH, expand=True, padx=8)

        # 底部设置按钮
        bottom_frame = tk.Frame(self.nav_frame, bg=COLORS["nav_bg"])
        bottom_frame.pack(fill=tk.X, padx=8, pady=(5, 15))

        sep2 = tk.Frame(bottom_frame, bg=COLORS["border"], height=1)
        sep2.pack(fill=tk.X, padx=7, pady=(0, 10))

        self._create_nav_button(bottom_frame, "⚙  全局设置", self._open_global_settings, is_settings=True)

        # --- 右侧内容区 ---
        self.content_frame = tk.Frame(self.root, bg=COLORS["content_bg"])
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 内容区顶部标题栏
        self.header_frame = tk.Frame(self.content_frame, bg=COLORS["card_bg"], height=50)
        self.header_frame.pack(fill=tk.X, padx=0, pady=0)
        self.header_frame.pack_propagate(False)

        self.header_label = tk.Label(self.header_frame, text="",
                                      font=("Microsoft YaHei UI", 13, "bold"),
                                      bg=COLORS["card_bg"], fg=COLORS["text_dark"])
        self.header_label.pack(side=tk.LEFT, padx=20, pady=12)

        # 内容区主体
        self.tool_frame = ttk.Frame(self.content_frame, style="Content.TFrame")
        self.tool_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _create_nav_button(self, parent, text, command=None, is_settings=False):
        """创建导航按钮"""
        btn = tk.Frame(parent, bg=COLORS["nav_bg"], cursor="hand2")
        btn.pack(fill=tk.X, pady=2)

        label = tk.Label(btn, text=text,
                         font=("Microsoft YaHei UI", 11),
                         bg=COLORS["nav_bg"], fg=COLORS["text"],
                         anchor=tk.W, padx=15, pady=10)
        label.pack(fill=tk.X)

        # Hover 效果
        def on_enter(e):
            if btn != getattr(self, '_active_btn', None):
                btn.configure(bg=COLORS["nav_hover"])
                label.configure(bg=COLORS["nav_hover"])

        def on_leave(e):
            if btn != getattr(self, '_active_btn', None):
                btn.configure(bg=COLORS["nav_bg"])
                label.configure(bg=COLORS["nav_bg"])

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        label.bind("<Enter>", on_enter)
        label.bind("<Leave>", on_leave)

        if is_settings:
            btn.bind("<Button-1>", lambda e: command())
            label.bind("<Button-1>", lambda e: command())
        else:
            idx = len(self.nav_buttons)
            btn.bind("<Button-1>", lambda e, i=idx: self._select_tool(i))
            label.bind("<Button-1>", lambda e, i=idx: self._select_tool(i))
            self.nav_buttons.append((btn, label))

    def _select_tool(self, index):
        """选中工具"""
        # 重置所有按钮样式
        for btn, label in self.nav_buttons:
            btn.configure(bg=COLORS["nav_bg"])
            label.configure(bg=COLORS["nav_bg"], fg=COLORS["text"])

        # 高亮选中
        btn, label = self.nav_buttons[index]
        btn.configure(bg=COLORS["nav_active"])
        label.configure(bg=COLORS["nav_active"], fg="white")
        self._active_btn = btn

        # 切换工具
        name = list(self.tools.keys())[index]
        if name == self.current_tool:
            return

        # 隐藏当前
        if self.current_tool and self.tools[self.current_tool]["frame"]:
            self.tools[self.current_tool]["frame"].pack_forget()

        # 创建或显示
        tool = self.tools[name]
        if tool["frame"] is None:
            tool["frame"] = tool["create"](self.tool_frame)
        tool["frame"].pack(fill=tk.BOTH, expand=True)
        self.current_tool = name

        # 更新标题
        self.header_label.config(text=name)

    def register(self, name, create_func):
        """注册一个工具"""
        icons = {
            "SQL 数据导出": "📊",
            "Doris 数据导入": "📥",
            "AI 笔记": "📝",
            "账号密码管理": "🔐",
        }
        icon = icons.get(name, "🔧")
        self.tools[name] = {"create": create_func, "frame": None}
        self._create_nav_button(self.nav_list_frame, f"{icon}  {name}")

    def _on_tool_select(self, _event):
        pass  # 保留兼容

    def _register_tools(self):
        from toolbox.tools.sql_exporter import create_sql_exporter
        from toolbox.tools.doris_loader import create_doris_loader
        from toolbox.tools.note_editor import create_note_editor
        from toolbox.tools.password_manager import create_password_manager
        self.register("SQL 数据导出", create_sql_exporter)
        self.register("Doris 数据导入", create_doris_loader)
        self.register("AI 笔记", create_note_editor)
        self.register("账号密码管理", create_password_manager)

    def _apply_appearance(self, cfg):
        """应用外观设置"""
        import tkinter.font as tkfont
        font_family = cfg.get("font_family", "Microsoft YaHei UI")
        font_size = cfg.get("font_size", 10)

        style = ttk.Style()
        style.configure(".", font=(font_family, font_size))
        style.configure("NavTitle.TLabel", font=(font_family, 14, "bold"))
        style.configure("NavSub.TLabel", font=(font_family, 9))
        style.configure("TLabelframe.Label", font=(font_family, font_size, "bold"))
        style.configure("TNotebook.Tab", font=(font_family, font_size))

    def _load_appearance(self):
        """启动时加载外观设置"""
        from toolbox.settings import load_settings
        settings = load_settings()
        cfg = settings.get("appearance", {})
        if cfg:
            self._apply_appearance(cfg)

    def _open_global_settings(self):
        """打开全局设置窗口"""
        win = tk.Toplevel(self.root)
        win.title("全局设置")
        win.geometry("580x620")
        win.transient(self.root)
        win.grab_set()
        win.configure(bg=COLORS["content_bg"])

        notebook = ttk.Notebook(win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

        # --- SMTP 设置页 ---
        smtp_frame = ttk.Frame(notebook, padding=20)
        notebook.add(smtp_frame, text="  SMTP 邮件  ")

        smtp = get_smtp_config()

        ttk.Label(smtp_frame, text="SMTP 配置（用于发送验证码，绑定数据加密）",
                  font=("Microsoft YaHei UI", 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        ttk.Label(smtp_frame, text="SMTP 主机:").grid(row=1, column=0, sticky=tk.W, pady=5)
        host_var = tk.StringVar(value=smtp.get("host", "smtp.qq.com"))
        ttk.Entry(smtp_frame, textvariable=host_var, width=30).grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(smtp_frame, text="端口:").grid(row=2, column=0, sticky=tk.W, pady=5)
        port_var = tk.StringVar(value=smtp.get("port", "465"))
        ttk.Entry(smtp_frame, textvariable=port_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(smtp_frame, text="发件邮箱:").grid(row=3, column=0, sticky=tk.W, pady=5)
        user_var = tk.StringVar(value=smtp.get("user", ""))
        ttk.Entry(smtp_frame, textvariable=user_var, width=30).grid(row=3, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(smtp_frame, text="密码/授权码:").grid(row=4, column=0, sticky=tk.W, pady=5)
        pass_var = tk.StringVar(value=smtp.get("password", ""))
        ttk.Entry(smtp_frame, textvariable=pass_var, show="*", width=30).grid(row=4, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ssl_var = tk.BooleanVar(value=smtp.get("use_ssl", True))
        ttk.Checkbutton(smtp_frame, text="使用 SSL", variable=ssl_var).grid(row=5, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(smtp_frame, text="⚠ 修改发件邮箱后，之前用旧邮箱加密的笔记将无法解密",
                  foreground="red", wraplength=420).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(15, 0))

        # --- 云同步设置页 ---
        sync_outer = ttk.Frame(notebook)
        notebook.add(sync_outer, text="  云同步  ")

        # 添加滚动支持
        sync_canvas = tk.Canvas(sync_outer, highlightthickness=0)
        sync_scrollbar = ttk.Scrollbar(sync_outer, orient=tk.VERTICAL, command=sync_canvas.yview)
        sync_frame = ttk.Frame(sync_canvas, padding=20)

        sync_frame.bind("<Configure>", lambda e: sync_canvas.configure(scrollregion=sync_canvas.bbox("all")))
        sync_canvas.create_window((0, 0), window=sync_frame, anchor="nw", width=520)
        sync_canvas.configure(yscrollcommand=sync_scrollbar.set)

        sync_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sync_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        from toolbox.cloud_sync import get_sync_manager
        sync_mgr = get_sync_manager()
        sync_cfg = sync_mgr.get_config()

        ttk.Label(sync_frame, text="云同步配置（未配置则仅使用本地存储）",
                  font=("Microsoft YaHei UI", 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        sync_enabled_var = tk.BooleanVar(value=sync_cfg.get("enabled", False))
        ttk.Checkbutton(sync_frame, text="启用云同步", variable=sync_enabled_var).grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=5)

        ttk.Label(sync_frame, text="存储类型:").grid(row=2, column=0, sticky=tk.W, pady=5)
        provider_var = tk.StringVar(value=sync_cfg.get("provider", "webdav"))
        provider_combo = ttk.Combobox(sync_frame, textvariable=provider_var,
                                       values=["webdav", "s3"], state="readonly", width=15)
        provider_combo.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # WebDAV 配置
        webdav_frame = ttk.LabelFrame(sync_frame, text="WebDAV 配置", padding=8)
        webdav_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=5)

        ttk.Label(webdav_frame, text="URL:").grid(row=0, column=0, sticky=tk.W, pady=3)
        wdav_url_var = tk.StringVar(value=sync_cfg.get("webdav_url", ""))
        ttk.Entry(webdav_frame, textvariable=wdav_url_var, width=38).grid(row=0, column=1, sticky=tk.W, pady=3, padx=(8, 0))

        ttk.Label(webdav_frame, text="用户名:").grid(row=1, column=0, sticky=tk.W, pady=3)
        wdav_user_var = tk.StringVar(value=sync_cfg.get("webdav_user", ""))
        ttk.Entry(webdav_frame, textvariable=wdav_user_var, width=25).grid(row=1, column=1, sticky=tk.W, pady=3, padx=(8, 0))

        ttk.Label(webdav_frame, text="密码:").grid(row=2, column=0, sticky=tk.W, pady=3)
        wdav_pass_var = tk.StringVar(value=sync_cfg.get("webdav_password", ""))
        ttk.Entry(webdav_frame, textvariable=wdav_pass_var, show="*", width=25).grid(row=2, column=1, sticky=tk.W, pady=3, padx=(8, 0))

        # S3 配置
        s3_frame = ttk.LabelFrame(sync_frame, text="S3 兼容存储配置（OSS/COS/MinIO）", padding=8)
        s3_frame.grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=5)

        ttk.Label(s3_frame, text="Endpoint:").grid(row=0, column=0, sticky=tk.W, pady=3)
        s3_endpoint_var = tk.StringVar(value=sync_cfg.get("s3_endpoint", ""))
        ttk.Entry(s3_frame, textvariable=s3_endpoint_var, width=35).grid(row=0, column=1, sticky=tk.W, pady=3, padx=(8, 0))

        ttk.Label(s3_frame, text="Bucket:").grid(row=1, column=0, sticky=tk.W, pady=3)
        s3_bucket_var = tk.StringVar(value=sync_cfg.get("s3_bucket", ""))
        ttk.Entry(s3_frame, textvariable=s3_bucket_var, width=20).grid(row=1, column=1, sticky=tk.W, pady=3, padx=(8, 0))

        ttk.Label(s3_frame, text="Access Key:").grid(row=2, column=0, sticky=tk.W, pady=3)
        s3_ak_var = tk.StringVar(value=sync_cfg.get("s3_access_key", ""))
        ttk.Entry(s3_frame, textvariable=s3_ak_var, width=25).grid(row=2, column=1, sticky=tk.W, pady=3, padx=(8, 0))

        ttk.Label(s3_frame, text="Secret Key:").grid(row=3, column=0, sticky=tk.W, pady=3)
        s3_sk_var = tk.StringVar(value=sync_cfg.get("s3_secret_key", ""))
        ttk.Entry(s3_frame, textvariable=s3_sk_var, show="*", width=25).grid(row=3, column=1, sticky=tk.W, pady=3, padx=(8, 0))

        queue_count = sync_mgr.get_queue_count()
        status_text = f"待同步: {queue_count} 项" if queue_count > 0 else "同步队列为空"
        ttk.Label(sync_frame, text=status_text, foreground="gray").grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))

        # --- 保存按钮 ---
        # --- 外观设置页 ---
        appearance_frame = ttk.Frame(notebook, padding=20)
        notebook.add(appearance_frame, text="  外观  ")

        from toolbox.settings import load_settings
        app_settings = load_settings()
        theme_cfg = app_settings.get("appearance", {})

        ttk.Label(appearance_frame, text="主题与字体设置",
                  font=("Microsoft YaHei UI", 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        ttk.Label(appearance_frame, text="主题风格:").grid(row=1, column=0, sticky=tk.W, pady=5)
        theme_var = tk.StringVar(value=theme_cfg.get("theme", "深色"))
        ttk.Combobox(appearance_frame, textvariable=theme_var,
                     values=["深色", "浅色"], state="readonly", width=12).grid(
            row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(appearance_frame, text="界面字体:").grid(row=2, column=0, sticky=tk.W, pady=5)
        font_family_var = tk.StringVar(value=theme_cfg.get("font_family", "Microsoft YaHei UI"))
        import tkinter.font as tkfont
        available_fonts = sorted(set(tkfont.families()))
        font_combo = ttk.Combobox(appearance_frame, textvariable=font_family_var,
                                   values=available_fonts, width=25)
        font_combo.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(appearance_frame, text="字体大小:").grid(row=3, column=0, sticky=tk.W, pady=5)
        font_size_var = tk.StringVar(value=str(theme_cfg.get("font_size", 10)))
        ttk.Combobox(appearance_frame, textvariable=font_size_var,
                     values=["9", "10", "11", "12", "13", "14", "16", "18"],
                     width=8).grid(row=3, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(appearance_frame, text="编辑器字体:").grid(row=4, column=0, sticky=tk.W, pady=5)
        editor_font_var = tk.StringVar(value=theme_cfg.get("editor_font", "Consolas"))
        ttk.Combobox(appearance_frame, textvariable=editor_font_var,
                     values=["Consolas", "Courier New", "Source Code Pro", "JetBrains Mono",
                             "Cascadia Code", "Microsoft YaHei UI", "SimSun"],
                     width=20).grid(row=4, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(appearance_frame, text="编辑器字号:").grid(row=5, column=0, sticky=tk.W, pady=5)
        editor_size_var = tk.StringVar(value=str(theme_cfg.get("editor_font_size", 11)))
        ttk.Combobox(appearance_frame, textvariable=editor_size_var,
                     values=["10", "11", "12", "13", "14", "16", "18", "20"],
                     width=8).grid(row=5, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(appearance_frame, text="⚠ 主题切换需要重启应用生效",
                  foreground="orange").grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(15, 0))

        def save():
            # 保存 SMTP
            smtp_config = {
                "host": host_var.get().strip(),
                "port": port_var.get().strip(),
                "user": user_var.get().strip(),
                "password": pass_var.get().strip(),
                "use_ssl": ssl_var.get(),
            }
            if smtp_config["host"] and smtp_config["user"] and smtp_config["password"]:
                save_smtp_config(smtp_config)

            # 保存云同步
            sync_config = {
                "enabled": sync_enabled_var.get(),
                "provider": provider_var.get(),
                "webdav_url": wdav_url_var.get().strip(),
                "webdav_user": wdav_user_var.get().strip(),
                "webdav_password": wdav_pass_var.get().strip(),
                "s3_endpoint": s3_endpoint_var.get().strip(),
                "s3_bucket": s3_bucket_var.get().strip(),
                "s3_access_key": s3_ak_var.get().strip(),
                "s3_secret_key": s3_sk_var.get().strip(),
            }
            sync_mgr.configure(sync_config)

            # 保存外观设置
            from toolbox.settings import load_settings, save_settings
            all_settings = load_settings()
            all_settings["appearance"] = {
                "theme": theme_var.get(),
                "font_family": font_family_var.get(),
                "font_size": int(font_size_var.get() or "10"),
                "editor_font": editor_font_var.get(),
                "editor_font_size": int(editor_size_var.get() or "11"),
            }
            save_settings(all_settings)

            # 立即应用字体（不需要重启）
            self._apply_appearance(all_settings["appearance"])

            messagebox.showinfo("成功", "设置已保存", parent=win)
            win.destroy()

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 12))
        ttk.Button(btn_frame, text="保存", command=save, style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=win.destroy).pack(side=tk.LEFT)


def main():
    root = tk.Tk()
    # 设置窗口图标
    import os, sys
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.dirname(base_path)
    icon_path = os.path.join(base_path, "app_icon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    ToolboxApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
