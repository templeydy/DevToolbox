"""
SQL 数据导出工具 - 嵌入式版本
支持 MySQL / PostgreSQL / SQLite，导出 CSV / Excel
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import csv
import sqlite3
import threading


class SQLExporterPanel:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.conn = None
        self.columns = []
        self.rows = []
        self._build_ui()

    def _build_ui(self):
        # --- 数据库连接区 ---
        conn_frame = ttk.LabelFrame(self.frame, text="数据库连接", padding=10)
        conn_frame.pack(fill=tk.X, padx=5, pady=(5, 3))

        row0 = ttk.Frame(conn_frame)
        row0.pack(fill=tk.X, pady=2)
        ttk.Label(row0, text="类型:").pack(side=tk.LEFT)
        self.db_type = ttk.Combobox(row0, values=["MySQL", "PostgreSQL", "SQLite"],
                                     state="readonly", width=12)
        self.db_type.set("MySQL")
        self.db_type.pack(side=tk.LEFT, padx=(5, 15))
        self.db_type.bind("<<ComboboxSelected>>", self._on_db_type_change)

        ttk.Label(row0, text="主机:").pack(side=tk.LEFT)
        self.host_var = tk.StringVar(value="localhost")
        self.host_entry = ttk.Entry(row0, textvariable=self.host_var, width=18)
        self.host_entry.pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(row0, text="端口:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value="3306")
        self.port_entry = ttk.Entry(row0, textvariable=self.port_var, width=8)
        self.port_entry.pack(side=tk.LEFT)

        row1 = ttk.Frame(conn_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="用户:").pack(side=tk.LEFT)
        self.user_var = tk.StringVar(value="root")
        self.user_entry = ttk.Entry(row1, textvariable=self.user_var, width=15)
        self.user_entry.pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(row1, text="密码:").pack(side=tk.LEFT)
        self.pass_var = tk.StringVar()
        self.pass_entry = ttk.Entry(row1, textvariable=self.pass_var, show="*", width=15)
        self.pass_entry.pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(row1, text="数据库:").pack(side=tk.LEFT)
        self.db_var = tk.StringVar()
        self.db_entry = ttk.Entry(row1, textvariable=self.db_var, width=15)
        self.db_entry.pack(side=tk.LEFT, padx=(5, 15))

        # SQLite 文件选择
        self.sqlite_frame = ttk.Frame(conn_frame)
        ttk.Label(self.sqlite_frame, text="文件:").pack(side=tk.LEFT)
        self.sqlite_path_var = tk.StringVar()
        ttk.Entry(self.sqlite_frame, textvariable=self.sqlite_path_var, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.sqlite_frame, text="浏览...", command=self._browse_sqlite).pack(side=tk.LEFT)

        btn_frame = ttk.Frame(conn_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        self.connect_btn = ttk.Button(btn_frame, text="连接", command=self._connect)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.disconnect_btn = ttk.Button(btn_frame, text="断开", command=self._disconnect, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT)
        self.status_label = ttk.Label(btn_frame, text="未连接", foreground="gray")
        self.status_label.pack(side=tk.LEFT, padx=15)

        # --- SQL 输入区 ---
        sql_frame = ttk.LabelFrame(self.frame, text="SQL 查询", padding=10)
        sql_frame.pack(fill=tk.BOTH, padx=5, pady=3)

        self.sql_text = scrolledtext.ScrolledText(sql_frame, height=5, font=("Consolas", 11))
        self.sql_text.pack(fill=tk.BOTH, expand=True)
        self.sql_text.insert(tk.END, "SELECT * FROM ")

        action_frame = ttk.Frame(sql_frame)
        action_frame.pack(fill=tk.X, pady=(5, 0))
        self.exec_btn = ttk.Button(action_frame, text="执行查询", command=self._execute_query, state=tk.DISABLED)
        self.exec_btn.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(action_frame, text="导出格式:").pack(side=tk.LEFT, padx=(20, 5))
        self.export_fmt = ttk.Combobox(action_frame, values=["CSV", "Excel (.xlsx)"],
                                        state="readonly", width=14)
        self.export_fmt.set("CSV")
        self.export_fmt.pack(side=tk.LEFT, padx=(0, 10))
        self.export_btn = ttk.Button(action_frame, text="导出数据", command=self._export_data, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT)
        self.row_count_label = ttk.Label(action_frame, text="")
        self.row_count_label.pack(side=tk.RIGHT)

        # --- 数据预览区 ---
        preview_frame = ttk.LabelFrame(self.frame, text="数据预览", padding=10)
        preview_frame.pack(fill=tk.BOTH, padx=5, pady=(3, 5), expand=True)

        self.tree = ttk.Treeview(preview_frame, show="headings")
        vsb = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

    # ---------- 事件 ----------

    def _on_db_type_change(self, _event=None):
        db = self.db_type.get()
        if db == "SQLite":
            for w in (self.host_entry, self.port_entry, self.user_entry, self.pass_entry, self.db_entry):
                w.config(state=tk.DISABLED)
            self.sqlite_frame.pack(fill=tk.X, pady=2)
        else:
            for w in (self.host_entry, self.port_entry, self.user_entry, self.pass_entry, self.db_entry):
                w.config(state=tk.NORMAL)
            self.sqlite_frame.pack_forget()
            self.port_var.set("3306" if db == "MySQL" else "5432")

    def _browse_sqlite(self):
        path = filedialog.askopenfilename(
            filetypes=[("SQLite DB", "*.db *.sqlite *.sqlite3"), ("All", "*.*")])
        if path:
            self.sqlite_path_var.set(path)

    # ---------- 连接 ----------

    def _connect(self):
        db_type = self.db_type.get()
        try:
            if db_type == "MySQL":
                import pymysql
                self.conn = pymysql.connect(
                    host=self.host_var.get(), port=int(self.port_var.get()),
                    user=self.user_var.get(), password=self.pass_var.get(),
                    database=self.db_var.get(), charset="utf8mb4")
            elif db_type == "PostgreSQL":
                import psycopg2
                self.conn = psycopg2.connect(
                    host=self.host_var.get(), port=int(self.port_var.get()),
                    user=self.user_var.get(), password=self.pass_var.get(),
                    dbname=self.db_var.get())
            elif db_type == "SQLite":
                path = self.sqlite_path_var.get()
                if not path:
                    messagebox.showwarning("提示", "请选择 SQLite 文件")
                    return
                self.conn = sqlite3.connect(path)
            self.status_label.config(text=f"已连接 ({db_type})", foreground="green")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.exec_btn.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("连接失败", str(e))

    def _disconnect(self):
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None
        self.status_label.config(text="未连接", foreground="gray")
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.exec_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.DISABLED)

    # ---------- 查询 ----------

    def _execute_query(self):
        sql = self.sql_text.get("1.0", tk.END).strip()
        if not sql:
            messagebox.showwarning("提示", "请输入 SQL 语句")
            return
        self.exec_btn.config(state=tk.DISABLED)
        self.row_count_label.config(text="查询中...")
        threading.Thread(target=self._run_query, args=(sql,), daemon=True).start()

    def _run_query(self, sql):
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            if cursor.description is None:
                self.frame.after(0, lambda: messagebox.showinfo("完成", "语句已执行（无返回数据）"))
                self.frame.after(0, lambda: self.exec_btn.config(state=tk.NORMAL))
                self.frame.after(0, lambda: self.row_count_label.config(text=""))
                return
            self.columns = [desc[0] for desc in cursor.description]
            self.rows = cursor.fetchall()
            cursor.close()
            self.frame.after(0, self._display_results)
        except Exception as e:
            self.frame.after(0, lambda: messagebox.showerror("查询错误", str(e)))
            self.frame.after(0, lambda: self.exec_btn.config(state=tk.NORMAL))
            self.frame.after(0, lambda: self.row_count_label.config(text=""))

    def _display_results(self):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = self.columns
        for col in self.columns:
            self.tree.heading(col, text=col, anchor=tk.W)
            self.tree.column(col, width=120, anchor=tk.W)
        for row in self.rows[:500]:
            self.tree.insert("", tk.END, values=[str(v) if v is not None else "" for v in row])
        total = len(self.rows)
        self.row_count_label.config(text=f"共 {total} 行（预览 {min(total, 500)} 行）")
        self.exec_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.NORMAL)

    # ---------- 导出 ----------

    def _export_data(self):
        if not self.rows:
            messagebox.showwarning("提示", "没有数据可导出")
            return
        fmt = self.export_fmt.get()
        if fmt == "CSV":
            path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
            if path:
                self._export_csv(path)
        else:
            path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
            if path:
                self._export_excel(path)

    def _export_csv(self, path):
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(self.columns)
                for row in self.rows:
                    writer.writerow([str(v) if v is not None else "" for v in row])
            messagebox.showinfo("导出成功", f"已导出 {len(self.rows)} 行到\n{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def _export_excel(self, path):
        try:
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "查询结果"
            ws.append(self.columns)
            for row in self.rows:
                ws.append([str(v) if v is not None else "" for v in row])
            wb.save(path)
            messagebox.showinfo("导出成功", f"已导出 {len(self.rows)} 行到\n{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))


def create_sql_exporter(parent):
    """工厂函数，供主界面注册调用"""
    panel = SQLExporterPanel(parent)
    return panel.frame
