"""
AI 笔记工具
支持笔记的创建、编辑、删除、搜索
支持模板管理，AI 可根据模板生成笔记内容
集成 AI Agent 辅助编辑（润色、总结、续写、翻译、按模板写作等）
笔记数据使用全局 SMTP 账号绑定加密，更换账号后无法访问旧笔记
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import json
import os
import threading
import urllib.request
from datetime import datetime
from toolbox.settings import get_smtp_account, encrypt_data, decrypt_data


NOTES_DIR = os.path.join(os.path.expanduser("~"), ".devtoolbox_notes")


class NoteEditorPanel:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.notes = []         # [{id, title, content, created, updated}]
        self.templates = []     # [{id, name, content}]
        self.current_note = None
        self._ensure_notes_dir()
        self._load_notes()
        self._load_templates()
        self._load_ai_config()
        self._build_ui()

    def _ensure_notes_dir(self):
        os.makedirs(NOTES_DIR, exist_ok=True)

    def _notes_file(self):
        return os.path.join(NOTES_DIR, "notes_encrypted.json")

    def _templates_file(self):
        return os.path.join(NOTES_DIR, "templates.json")

    def _ai_config_file(self):
        return os.path.join(NOTES_DIR, "ai_config.json")

    def _load_ai_config(self):
        """加载保存的 AI 配置"""
        path = self._ai_config_file()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._ai_config = json.load(f)
            except Exception:
                self._ai_config = {}
        else:
            self._ai_config = {}

    def _save_ai_config(self):
        """保存 AI 配置"""
        config = {
            "api_url": self.api_url_var.get().strip(),
            "api_key": self.api_key_var.get().strip(),
            "model": self.model_var.get().strip(),
        }
        with open(self._ai_config_file(), "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def _load_notes(self):
        """加载并解密笔记（使用 SMTP 账号）"""
        account = get_smtp_account()
        path = self._notes_file()
        if not os.path.exists(path):
            self.notes = []
            return
        if not account:
            self.notes = []
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                enc_data = json.load(f)
            plaintext = decrypt_data(enc_data, account)
            self.notes = json.loads(plaintext)
        except PermissionError as e:
            self.notes = []
            # 延迟显示错误（UI 还没构建完）
            self._load_error = str(e)
        except Exception:
            self.notes = []

    def _save_notes(self):
        """加密并保存笔记（使用 SMTP 账号）"""
        account = get_smtp_account()
        if not account:
            messagebox.showwarning("提示", "请先在全局设置中配置 SMTP 发件邮箱，笔记需要绑定账号加密存储")
            return
        plaintext = json.dumps(self.notes, ensure_ascii=False)
        enc_data = encrypt_data(plaintext, account)
        with open(self._notes_file(), "w", encoding="utf-8") as f:
            json.dump(enc_data, f, ensure_ascii=False, indent=2)

    def _load_templates(self):
        path = self._templates_file()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.templates = json.load(f)
            except Exception:
                self.templates = []
        else:
            # 预置一些默认模板
            self.templates = [
                {
                    "id": "tpl_meeting",
                    "name": "会议纪要",
                    "content": "# 会议纪要\n\n## 会议信息\n- 日期：\n- 参会人：\n- 主题：\n\n## 议题与讨论\n1. \n\n## 决议事项\n- \n\n## 待办跟进\n| 事项 | 负责人 | 截止日期 |\n|------|--------|----------|\n|      |        |          |"
                },
                {
                    "id": "tpl_daily",
                    "name": "日报",
                    "content": "# 工作日报\n\n## 日期：\n\n## 今日完成\n- \n\n## 遇到的问题\n- \n\n## 明日计划\n- "
                },
                {
                    "id": "tpl_tech",
                    "name": "技术方案",
                    "content": "# 技术方案\n\n## 背景\n\n## 目标\n\n## 方案设计\n### 整体架构\n\n### 核心流程\n\n### 数据模型\n\n## 风险与应对\n\n## 排期"
                },
                {
                    "id": "tpl_bug",
                    "name": "Bug 记录",
                    "content": "# Bug 记录\n\n## 问题描述\n\n## 复现步骤\n1. \n\n## 期望行为\n\n## 实际行为\n\n## 环境信息\n- 系统：\n- 版本：\n\n## 原因分析\n\n## 修复方案"
                },
            ]
            self._save_templates()

    def _save_templates(self):
        with open(self._templates_file(), "w", encoding="utf-8") as f:
            json.dump(self.templates, f, ensure_ascii=False, indent=2)

    def _build_ui(self):
        # 主布局：左侧笔记列表 + 右侧编辑区
        paned = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- 左侧：笔记列表 ---
        left_frame = ttk.Frame(paned, width=220)
        paned.add(left_frame, weight=1)

        list_toolbar = ttk.Frame(left_frame)
        list_toolbar.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(list_toolbar, text="新建", command=self._new_note, width=6).pack(side=tk.LEFT, padx=(0, 3))
        ttk.Button(list_toolbar, text="删除", command=self._delete_note, width=6).pack(side=tk.LEFT, padx=(0, 3))
        ttk.Button(list_toolbar, text="模板", command=self._open_template_manager, width=6).pack(side=tk.LEFT, padx=(0, 3))

        # 搜索
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        ttk.Entry(search_frame, textvariable=self.search_var, width=20).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 笔记列表
        self.note_listbox = tk.Listbox(left_frame, font=("", 10), activestyle="none",
                                        selectbackground="#4a90d9", selectforeground="white")
        self.note_listbox.pack(fill=tk.BOTH, expand=True)
        self.note_listbox.bind("<<ListboxSelect>>", self._on_note_select)

        # --- 右侧：编辑区 ---
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=4)

        # 标题
        title_frame = ttk.Frame(right_frame)
        title_frame.pack(fill=tk.X, pady=(0, 3))
        ttk.Label(title_frame, text="标题:").pack(side=tk.LEFT)
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(title_frame, textvariable=self.title_var, font=("", 12))
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(title_frame, text="保存", command=self._save_current_note).pack(side=tk.RIGHT)

        # 内容编辑器（使用 PanedWindow 让编辑器和 AI 区域可调节高度）
        edit_paned = ttk.PanedWindow(right_frame, orient=tk.VERTICAL)
        edit_paned.pack(fill=tk.BOTH, expand=True, pady=(0, 3))

        # 编辑器面板
        editor_frame = ttk.Frame(edit_paned)
        edit_paned.add(editor_frame, weight=3)

        self.content_text = scrolledtext.ScrolledText(editor_frame, font=("Consolas", 11),
                                                       wrap=tk.WORD, undo=True)
        self.content_text.pack(fill=tk.BOTH, expand=True)

        # AI Agent 面板
        ai_outer = ttk.Frame(edit_paned)
        edit_paned.add(ai_outer, weight=1)

        # 时间信息
        self.time_label = ttk.Label(ai_outer, text="", foreground="gray")
        self.time_label.pack(anchor=tk.W)

        # --- AI Agent 区域 ---
        ai_frame = ttk.LabelFrame(ai_outer, text="AI Agent", padding=5)
        ai_frame.pack(fill=tk.BOTH, expand=True, pady=(3, 0))

        # AI 配置行
        ai_config_row = ttk.Frame(ai_frame)
        ai_config_row.pack(fill=tk.X, pady=(0, 3))

        ttk.Label(ai_config_row, text="API:").pack(side=tk.LEFT)
        self.api_url_var = tk.StringVar(value=self._ai_config.get("api_url", "https://api.openai.com/v1/chat/completions"))
        ttk.Entry(ai_config_row, textvariable=self.api_url_var, width=30).pack(side=tk.LEFT, padx=(3, 8))

        ttk.Label(ai_config_row, text="API Key:").pack(side=tk.LEFT)
        self.api_key_var = tk.StringVar(value=self._ai_config.get("api_key", ""))
        ttk.Entry(ai_config_row, textvariable=self.api_key_var, show="*", width=20).pack(side=tk.LEFT, padx=(3, 10))

        ttk.Label(ai_config_row, text="模型:").pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value=self._ai_config.get("model", "gpt-4o-mini"))
        ttk.Entry(ai_config_row, textvariable=self.model_var, width=15).pack(side=tk.LEFT, padx=(3, 5))

        ttk.Button(ai_config_row, text="保存配置", command=self._save_ai_config).pack(side=tk.LEFT, padx=(5, 0))

        # AI 操作行
        ai_action_row = ttk.Frame(ai_frame)
        ai_action_row.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(ai_action_row, text="操作:").pack(side=tk.LEFT)
        self.ai_action_var = tk.StringVar(value="润色")
        actions = ["润色", "总结", "续写", "翻译为英文", "翻译为中文", "修正语法", "扩展内容",
                   "按模板写作", "按模板优化", "自定义指令"]
        self.ai_action_combo = ttk.Combobox(ai_action_row, textvariable=self.ai_action_var, values=actions,
                     state="readonly", width=12)
        self.ai_action_combo.pack(side=tk.LEFT, padx=(3, 10))
        self.ai_action_combo.bind("<<ComboboxSelected>>", self._on_ai_action_change)

        # 模板选择（默认隐藏）
        self.tpl_select_frame = ttk.Frame(ai_action_row)
        ttk.Label(self.tpl_select_frame, text="模板:").pack(side=tk.LEFT)
        self.tpl_select_var = tk.StringVar()
        self.tpl_select_combo = ttk.Combobox(self.tpl_select_frame, textvariable=self.tpl_select_var,
                                              state="readonly", width=12)
        self.tpl_select_combo.pack(side=tk.LEFT, padx=(3, 10))
        self._refresh_template_combo()

        # 作用范围
        self.scope_var = tk.StringVar(value="全文")
        self.scope_frame = ttk.Frame(ai_action_row)
        self.scope_frame.pack(side=tk.LEFT)
        ttk.Radiobutton(self.scope_frame, text="全文", variable=self.scope_var, value="全文").pack(side=tk.LEFT, padx=(5, 3))
        ttk.Radiobutton(self.scope_frame, text="选中文本", variable=self.scope_var, value="选中文本").pack(side=tk.LEFT, padx=(0, 10))

        self.ai_btn = ttk.Button(ai_action_row, text="执行 AI 编辑", command=self._run_ai_edit)
        self.ai_btn.pack(side=tk.LEFT, padx=(5, 0))

        # 提示词输入区（多行）
        prompt_frame = ttk.Frame(ai_frame)
        prompt_frame.pack(fill=tk.X, pady=(0, 3))
        ttk.Label(prompt_frame, text="提示词:").pack(side=tk.LEFT, anchor=tk.N)
        self.prompt_text = tk.Text(prompt_frame, height=2, font=("", 10), wrap=tk.WORD)
        self.prompt_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.prompt_text.insert("1.0", "")

        self.ai_status_var = tk.StringVar(value="")
        ttk.Label(ai_frame, textvariable=self.ai_status_var, foreground="blue").pack(anchor=tk.W)

        # 刷新列表
        self._refresh_list()

        # 显示加载错误
        if hasattr(self, "_load_error"):
            self.frame.after(500, lambda: messagebox.showwarning(
                "笔记加载失败", self._load_error + "\n\n请确认全局设置中的 SMTP 发件邮箱与加密时一致。"))
            del self._load_error

    def _on_ai_action_change(self, _event=None):
        """切换 AI 操作时，显示/隐藏模板选择"""
        action = self.ai_action_var.get()

        # 先全部隐藏，再按需显示
        self.tpl_select_frame.pack_forget()
        self.scope_frame.pack_forget()
        self.ai_btn.pack_forget()

        if action in ("按模板写作", "按模板优化"):
            self.tpl_select_frame.pack(side=tk.LEFT, padx=(0, 10))
            self.ai_btn.pack(side=tk.LEFT, padx=(5, 0))
        else:
            self.scope_frame.pack(side=tk.LEFT)
            self.ai_btn.pack(side=tk.LEFT, padx=(5, 0))

    def _refresh_template_combo(self):
        names = [t["name"] for t in self.templates]
        self.tpl_select_combo["values"] = names
        if names:
            self.tpl_select_combo.set(names[0])

    # ---------- 模板管理 ----------

    def _open_template_manager(self):
        """打开模板管理窗口"""
        win = tk.Toplevel(self.frame.winfo_toplevel())
        win.title("模板管理")
        win.geometry("700x500")
        win.transient(self.frame.winfo_toplevel())

        # 左侧模板列表
        left = ttk.Frame(win, width=180)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left.pack_propagate(False)

        tpl_toolbar = ttk.Frame(left)
        tpl_toolbar.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(tpl_toolbar, text="新增", command=lambda: add_tpl()).pack(side=tk.LEFT, padx=(0, 3))
        ttk.Button(tpl_toolbar, text="删除", command=lambda: del_tpl()).pack(side=tk.LEFT)

        tpl_listbox = tk.Listbox(left, font=("", 10), activestyle="none",
                                  selectbackground="#4a90d9", selectforeground="white")
        tpl_listbox.pack(fill=tk.BOTH, expand=True)

        # 右侧编辑区
        right = ttk.Frame(win)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        name_frame = ttk.Frame(right)
        name_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(name_frame, text="模板名称:").pack(side=tk.LEFT)
        tpl_name_var = tk.StringVar()
        tpl_name_entry = ttk.Entry(name_frame, textvariable=tpl_name_var, width=25)
        tpl_name_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(name_frame, text="保存模板", command=lambda: save_tpl()).pack(side=tk.RIGHT)

        ttk.Label(right, text="模板内容（支持占位符如 {主题}、{日期} 等）:").pack(anchor=tk.W)
        tpl_content = scrolledtext.ScrolledText(right, font=("Consolas", 11), wrap=tk.WORD, height=18)
        tpl_content.pack(fill=tk.BOTH, expand=True, pady=(3, 0))

        def refresh_tpl_list():
            tpl_listbox.delete(0, tk.END)
            for t in self.templates:
                tpl_listbox.insert(tk.END, t["name"])

        def on_tpl_select(_event=None):
            sel = tpl_listbox.curselection()
            if not sel:
                return
            tpl = self.templates[sel[0]]
            tpl_name_var.set(tpl["name"])
            tpl_content.delete("1.0", tk.END)
            tpl_content.insert("1.0", tpl["content"])

        def add_tpl():
            new_tpl = {
                "id": f"tpl_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                "name": "新模板",
                "content": "# 标题\n\n## 内容\n\n",
            }
            self.templates.append(new_tpl)
            self._save_templates()
            refresh_tpl_list()
            # 选中新增的最后一项
            last_index = len(self.templates) - 1
            tpl_listbox.selection_clear(0, tk.END)
            tpl_listbox.selection_set(last_index)
            tpl_listbox.see(last_index)
            # 手动加载到编辑区
            tpl_name_var.set(new_tpl["name"])
            tpl_content.delete("1.0", tk.END)
            tpl_content.insert("1.0", new_tpl["content"])
            # 聚焦到名称输入框并全选，方便直接修改
            tpl_name_entry.focus_set()
            tpl_name_entry.select_range(0, tk.END)

        def del_tpl():
            sel = tpl_listbox.curselection()
            if not sel:
                return
            if not messagebox.askyesno("确认", f"确定删除模板「{self.templates[sel[0]]['name']}」？", parent=win):
                return
            self.templates.pop(sel[0])
            self._save_templates()
            refresh_tpl_list()
            tpl_name_var.set("")
            tpl_content.delete("1.0", tk.END)
            self._refresh_template_combo()

        def save_tpl():
            sel = tpl_listbox.curselection()
            if not sel:
                messagebox.showwarning("提示", "请先选择一个模板", parent=win)
                return
            idx = sel[0]
            tpl = self.templates[idx]
            tpl["name"] = tpl_name_var.get().strip() or "未命名模板"
            tpl["content"] = tpl_content.get("1.0", tk.END).rstrip("\n")
            self._save_templates()
            refresh_tpl_list()
            # 保存后重新选中
            tpl_listbox.selection_clear(0, tk.END)
            tpl_listbox.selection_set(idx)
            tpl_listbox.see(idx)
            self._refresh_template_combo()
            messagebox.showinfo("成功", "模板已保存", parent=win)

        tpl_listbox.bind("<<ListboxSelect>>", on_tpl_select)
        refresh_tpl_list()
        if self.templates:
            tpl_listbox.selection_set(0)
            on_tpl_select()

    # ---------- 笔记列表操作 ----------

    def _refresh_list(self, filter_text=""):
        self.note_listbox.delete(0, tk.END)
        for note in self.notes:
            if filter_text and filter_text.lower() not in note["title"].lower() \
                    and filter_text.lower() not in note.get("content", "").lower():
                continue
            display = note["title"] or "(无标题)"
            self.note_listbox.insert(tk.END, display)

    def _on_search(self, *args):
        self._refresh_list(self.search_var.get())

    def _on_note_select(self, _event=None):
        sel = self.note_listbox.curselection()
        if not sel:
            return
        self._auto_save()
        filter_text = self.search_var.get()
        filtered = [n for n in self.notes
                    if not filter_text or filter_text.lower() in n["title"].lower()
                    or filter_text.lower() in n.get("content", "").lower()]
        if sel[0] < len(filtered):
            self.current_note = filtered[sel[0]]
            self._display_note()

    def _display_note(self):
        if not self.current_note:
            return
        self.title_var.set(self.current_note.get("title", ""))
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", self.current_note.get("content", ""))
        created = self.current_note.get("created", "")
        updated = self.current_note.get("updated", "")
        self.time_label.config(text=f"创建: {created}  |  更新: {updated}")

    def _new_note(self):
        self._auto_save()
        note = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "title": "新笔记",
            "content": "",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.notes.insert(0, note)
        self.current_note = note
        self._save_notes()
        self._refresh_list(self.search_var.get())
        self.note_listbox.selection_set(0)
        self._display_note()
        self.title_entry.focus_set()
        self.title_entry.select_range(0, tk.END)

    def _delete_note(self):
        if not self.current_note:
            messagebox.showwarning("提示", "请先选择一个笔记")
            return
        if not messagebox.askyesno("确认", f"确定删除笔记「{self.current_note['title']}」？"):
            return
        self.notes = [n for n in self.notes if n["id"] != self.current_note["id"]]
        self.current_note = None
        self._save_notes()
        self._refresh_list(self.search_var.get())
        self.title_var.set("")
        self.content_text.delete("1.0", tk.END)
        self.time_label.config(text="")

    def _save_current_note(self):
        if not self.current_note:
            messagebox.showwarning("提示", "没有打开的笔记")
            return
        self.current_note["title"] = self.title_var.get().strip() or "无标题"
        self.current_note["content"] = self.content_text.get("1.0", tk.END).rstrip("\n")
        self.current_note["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_notes()
        self._refresh_list(self.search_var.get())
        self.time_label.config(
            text=f"创建: {self.current_note['created']}  |  更新: {self.current_note['updated']}")
        self.ai_status_var.set("已保存")

    def _auto_save(self):
        if self.current_note:
            title = self.title_var.get().strip()
            content = self.content_text.get("1.0", tk.END).rstrip("\n")
            if title != self.current_note.get("title") or content != self.current_note.get("content"):
                self.current_note["title"] = title or "无标题"
                self.current_note["content"] = content
                self.current_note["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._save_notes()

    # ---------- AI Agent 编辑 ----------

    def _run_ai_edit(self):
        if not self.current_note:
            messagebox.showwarning("提示", "请先打开一个笔记")
            return

        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("提示", "请填写 API Key")
            return

        action = self.ai_action_var.get()
        user_prompt = self.prompt_text.get("1.0", tk.END).strip()

        # 按模板写作模式
        if action == "按模板写作":
            tpl_name = self.tpl_select_var.get()
            tpl = next((t for t in self.templates if t["name"] == tpl_name), None)
            if not tpl:
                messagebox.showwarning("提示", "请选择一个模板")
                return
            if not user_prompt:
                messagebox.showwarning("提示", "请在提示词区域输入主题/要求")
                return
            prompt = self._build_template_prompt(tpl, user_prompt)
            self.ai_btn.config(state=tk.DISABLED)
            self.ai_status_var.set("AI 根据模板生成中...")
            threading.Thread(target=self._call_ai, args=(prompt, "", "全文"), daemon=True).start()
            return

        # 按模板优化模式（用模板格式优化现有内容）
        if action == "按模板优化":
            tpl_name = self.tpl_select_var.get()
            tpl = next((t for t in self.templates if t["name"] == tpl_name), None)
            if not tpl:
                messagebox.showwarning("提示", "请选择一个模板")
                return
            text = self.content_text.get("1.0", tk.END).rstrip("\n")
            if not text.strip():
                messagebox.showwarning("提示", "笔记内容为空，无法优化")
                return
            prompt = self._build_template_optimize_prompt(tpl, text, user_prompt)
            self.ai_btn.config(state=tk.DISABLED)
            self.ai_status_var.set("AI 按模板优化中...")
            threading.Thread(target=self._call_ai, args=(prompt, text, "全文"), daemon=True).start()
            return

        # 其他操作
        scope = self.scope_var.get()
        if scope == "选中文本":
            try:
                text = self.content_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                messagebox.showwarning("提示", "请先选中要处理的文本")
                return
        else:
            text = self.content_text.get("1.0", tk.END).rstrip("\n")

        if not text.strip():
            messagebox.showwarning("提示", "没有可处理的文本内容")
            return

        prompt = self._build_prompt(action, text, user_prompt)
        self.ai_btn.config(state=tk.DISABLED)
        self.ai_status_var.set("AI 处理中...")
        threading.Thread(target=self._call_ai, args=(prompt, text, scope), daemon=True).start()

    def _build_template_prompt(self, tpl, topic):
        """构建按模板写作的 prompt"""
        return (
            f"请根据以下模板格式，围绕给定的主题/要求来撰写一篇完整的笔记内容。\n"
            f"严格按照模板的结构和格式来写，填充每个部分的具体内容。\n"
            f"直接返回填写好的笔记内容，不要添加额外解释。\n\n"
            f"【模板】\n{tpl['content']}\n\n"
            f"【主题/要求】\n{topic}"
        )

    def _build_template_optimize_prompt(self, tpl, text, extra_prompt=""):
        """构建按模板优化润色的 prompt"""
        base = (
            f"请按以下模板格式重新组织下面的原文，保留核心信息，使内容结构化。直接返回结果。\n\n"
            f"【模板】\n{tpl['content']}\n\n"
            f"【原文】\n{text}"
        )
        if extra_prompt:
            base += f"\n\n【要求】{extra_prompt}"
        return base

    def _build_prompt(self, action, text, user_prompt=""):
        prompts = {
            "润色": f"请润色以下文本，使其更加流畅、专业，保持原意不变。只返回润色后的文本，不要添加解释：\n\n{text}",
            "总结": f"请用简洁的语言总结以下内容的要点，使用条目列表格式：\n\n{text}",
            "续写": f"请根据以下内容的上下文和风格，自然地续写下去（约200字）：\n\n{text}",
            "翻译为英文": f"请将以下文本翻译为英文，保持原文格式。只返回翻译结果：\n\n{text}",
            "翻译为中文": f"请将以下文本翻译为中文，保持原文格式。只返回翻译结果：\n\n{text}",
            "修正语法": f"请修正以下文本中的语法错误和拼写错误，保持原意。只返回修正后的文本：\n\n{text}",
            "扩展内容": f"请对以下内容进行扩展，补充更多细节和说明，使内容更加丰富完整：\n\n{text}",
        }
        if action == "自定义指令":
            if not user_prompt:
                return f"请帮我编辑以下文本：\n\n{text}"
            return f"{user_prompt}\n\n{text}"

        base_prompt = prompts.get(action, f"请润色以下文本：\n\n{text}")
        # 如果用户写了额外提示词，附加上去
        if user_prompt:
            base_prompt += f"\n\n【额外要求】{user_prompt}"
        return base_prompt

    def _call_ai(self, prompt, original_text, scope):
        try:
            api_url = self.api_url_var.get().strip()
            api_key = self.api_key_var.get().strip()
            model = self.model_var.get().strip() or "gpt-4o-mini"

            payload = json.dumps({
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的文本编辑助手。请直接返回处理后的文本，不要添加额外的解释或标记。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
            }).encode("utf-8")

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }

            req = urllib.request.Request(api_url, data=payload, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            ai_text = result["choices"][0]["message"]["content"].strip()
            self.frame.after(0, lambda: self._apply_ai_result(ai_text, scope))

        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(err_body)
                err_msg = err_json.get("error", {}).get("message", err_body)
            except Exception:
                err_msg = err_body
            self.frame.after(0, lambda: self.ai_status_var.set(f"AI 错误: {err_msg[:50]}"))
            self.frame.after(0, lambda: messagebox.showerror("AI 请求失败", f"HTTP {e.code}\n{err_msg}"))
        except Exception as e:
            self.frame.after(0, lambda: self.ai_status_var.set(f"错误: {str(e)[:50]}"))
            self.frame.after(0, lambda: messagebox.showerror("AI 错误", str(e)))
        finally:
            self.frame.after(0, lambda: self.ai_btn.config(state=tk.NORMAL))

    def _apply_ai_result(self, ai_text, scope):
        """弹出预览窗口，让用户确认是否应用 AI 结果"""
        self.ai_status_var.set("AI 处理完成，请确认结果")

        preview_win = tk.Toplevel(self.frame.winfo_toplevel())
        preview_win.title("AI 结果预览 - 确认是否应用")
        preview_win.geometry("800x600")
        preview_win.minsize(600, 400)
        preview_win.transient(self.frame.winfo_toplevel())

        # 按钮区放底部，先 pack 确保不被挤掉
        btn_frame = ttk.Frame(preview_win)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        def apply():
            final_text = preview_text.get("1.0", tk.END).rstrip("\n")
            if scope == "选中文本":
                try:
                    self.content_text.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    self.content_text.insert(tk.INSERT, final_text)
                except tk.TclError:
                    self.content_text.insert(tk.END, "\n" + final_text)
            else:
                self.content_text.delete("1.0", tk.END)
                self.content_text.insert("1.0", final_text)
            self.ai_status_var.set("已应用 AI 结果")
            preview_win.destroy()

        def discard():
            self.ai_status_var.set("已放弃 AI 结果")
            preview_win.destroy()

        ttk.Button(btn_frame, text="✓ 应用到笔记", command=apply).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="✗ 放弃", command=discard).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(btn_frame, text="（可在上方直接编辑微调后再应用）",
                  foreground="gray").pack(side=tk.LEFT)

        # 标题
        ttk.Label(preview_win, text="AI 生成结果（确认后将替换当前内容）：",
                  font=("", 11, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 5))

        # 预览文本框（填满剩余空间）
        preview_text = scrolledtext.ScrolledText(preview_win, font=("Consolas", 11),
                                                  wrap=tk.WORD)
        preview_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
        preview_text.insert("1.0", ai_text)


def create_note_editor(parent):
    """工厂函数，供主界面注册调用"""
    panel = NoteEditorPanel(parent)
    return panel.frame
