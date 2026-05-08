"""
Doris 数据导入工具
支持从 CSV 文件导入数据到 Apache Doris，可自定义字段映射
支持跳过前N行、手动标记错误行跳过重导
使用 Doris Stream Load API 进行数据导入
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import threading
import urllib.request
import base64
import json


class DorisLoaderPanel:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.csv_columns = []       # CSV 文件的列名
        self.csv_preview = []       # CSV 前几行预览数据
        self.csv_all_rows = []      # CSV 所有数据行（不含表头）
        self.table_columns = []     # Doris 表的列名
        self.mapping_widgets = []   # 字段映射控件
        self.skip_rows = set()      # 手动标记跳过的行号（从1开始，对应数据行）
        self._build_ui()

    def _build_ui(self):
        # --- Doris 连接区 ---
        conn_frame = ttk.LabelFrame(self.frame, text="Doris 连接", padding=10)
        conn_frame.pack(fill=tk.X, padx=5, pady=(5, 3))

        row0 = ttk.Frame(conn_frame)
        row0.pack(fill=tk.X, pady=2)
        ttk.Label(row0, text="FE 地址:").pack(side=tk.LEFT)
        self.host_var = tk.StringVar(value="localhost")
        ttk.Entry(row0, textvariable=self.host_var, width=18).pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(row0, text="HTTP 端口:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value="8030")
        ttk.Entry(row0, textvariable=self.port_var, width=8).pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(row0, text="查询端口:").pack(side=tk.LEFT)
        self.query_port_var = tk.StringVar(value="9030")
        ttk.Entry(row0, textvariable=self.query_port_var, width=8).pack(side=tk.LEFT)

        row1 = ttk.Frame(conn_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="用户:").pack(side=tk.LEFT)
        self.user_var = tk.StringVar(value="root")
        ttk.Entry(row1, textvariable=self.user_var, width=15).pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(row1, text="密码:").pack(side=tk.LEFT)
        self.pass_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.pass_var, show="*", width=15).pack(side=tk.LEFT, padx=(5, 15))

        btn_frame = ttk.Frame(conn_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        self.connect_btn = ttk.Button(btn_frame, text="连接", command=self._connect)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.disconnect_btn = ttk.Button(btn_frame, text="断开", command=self._disconnect, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.conn_status = ttk.Label(btn_frame, text="未连接", foreground="gray")
        self.conn_status.pack(side=tk.LEFT)

        # --- 库表选择区 ---
        db_table_frame = ttk.LabelFrame(self.frame, text="选择库和表", padding=10)
        db_table_frame.pack(fill=tk.X, padx=5, pady=3)

        dt_row = ttk.Frame(db_table_frame)
        dt_row.pack(fill=tk.X, pady=2)

        ttk.Label(dt_row, text="数据库:").pack(side=tk.LEFT)
        self.db_var = tk.StringVar()
        self.db_combo = ttk.Combobox(dt_row, textvariable=self.db_var, width=20, state="disabled")
        self.db_combo.pack(side=tk.LEFT, padx=(5, 20))
        self.db_combo.bind("<<ComboboxSelected>>", self._on_db_select)

        ttk.Label(dt_row, text="表名:").pack(side=tk.LEFT)
        self.table_var = tk.StringVar()
        self.table_combo = ttk.Combobox(dt_row, textvariable=self.table_var, width=20, state="disabled")
        self.table_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.table_combo.bind("<<ComboboxSelected>>", self._on_table_select)

        # --- CSV 文件选择区 ---
        csv_frame = ttk.LabelFrame(self.frame, text="CSV 文件", padding=10)
        csv_frame.pack(fill=tk.X, padx=5, pady=3)

        csv_row = ttk.Frame(csv_frame)
        csv_row.pack(fill=tk.X, pady=2)
        ttk.Label(csv_row, text="文件:").pack(side=tk.LEFT)
        self.csv_path_var = tk.StringVar()
        ttk.Entry(csv_row, textvariable=self.csv_path_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(csv_row, text="浏览...", command=self._browse_csv).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(csv_row, text="解析", command=self._parse_csv).pack(side=tk.LEFT)

        csv_opt_row = ttk.Frame(csv_frame)
        csv_opt_row.pack(fill=tk.X, pady=2)
        ttk.Label(csv_opt_row, text="分隔符:").pack(side=tk.LEFT)
        self.delimiter_var = tk.StringVar(value=",")
        ttk.Combobox(csv_opt_row, textvariable=self.delimiter_var,
                     values=[",", "\\t", "|", ";"], width=5).pack(side=tk.LEFT, padx=(5, 15))
        ttk.Label(csv_opt_row, text="编码:").pack(side=tk.LEFT)
        self.encoding_var = tk.StringVar(value="utf-8")
        ttk.Combobox(csv_opt_row, textvariable=self.encoding_var,
                     values=["utf-8", "utf-8-sig", "gbk", "gb2312", "latin-1"], width=10).pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(csv_opt_row, text="跳过前N行:").pack(side=tk.LEFT, padx=(10, 0))
        self.skip_n_var = tk.StringVar(value="0")
        ttk.Entry(csv_opt_row, textvariable=self.skip_n_var, width=6).pack(side=tk.LEFT, padx=(5, 15))

        self.csv_info_label = ttk.Label(csv_opt_row, text="")
        self.csv_info_label.pack(side=tk.LEFT, padx=10)

        # --- 跳过行管理区 ---
        skip_frame = ttk.LabelFrame(self.frame, text="跳过行管理", padding=10)
        skip_frame.pack(fill=tk.X, padx=5, pady=3)

        skip_input_row = ttk.Frame(skip_frame)
        skip_input_row.pack(fill=tk.X, pady=2)
        ttk.Label(skip_input_row, text="标记跳过行号（逗号分隔）:").pack(side=tk.LEFT)
        self.skip_input_var = tk.StringVar()
        ttk.Entry(skip_input_row, textvariable=self.skip_input_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(skip_input_row, text="添加", command=self._add_skip_rows).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(skip_input_row, text="清除所有", command=self._clear_skip_rows).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(skip_input_row, text="查看详情", command=self._show_skip_details).pack(side=tk.LEFT)

        self.skip_summary_var = tk.StringVar(value="当前无跳过行")
        ttk.Label(skip_frame, textvariable=self.skip_summary_var, foreground="blue").pack(anchor=tk.W, pady=(2, 0))

        # --- 字段映射区 ---
        mapping_frame = ttk.LabelFrame(self.frame, text="字段映射（CSV 列 → Doris 列）", padding=10)
        mapping_frame.pack(fill=tk.BOTH, padx=5, pady=3, expand=True)

        # 映射区头部
        map_header = ttk.Frame(mapping_frame)
        map_header.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(map_header, text="CSV 列", width=25, anchor=tk.W,
                  font=("", 10, "bold")).pack(side=tk.LEFT, padx=(10, 30))
        ttk.Label(map_header, text="→", width=3).pack(side=tk.LEFT)
        ttk.Label(map_header, text="Doris 列", width=25, anchor=tk.W,
                  font=("", 10, "bold")).pack(side=tk.LEFT, padx=(30, 0))

        # 可滚动映射列表
        self.map_canvas = tk.Canvas(mapping_frame, highlightthickness=0)
        map_scrollbar = ttk.Scrollbar(mapping_frame, orient=tk.VERTICAL, command=self.map_canvas.yview)
        self.map_inner_frame = ttk.Frame(self.map_canvas)

        self.map_inner_frame.bind("<Configure>",
                                   lambda e: self.map_canvas.configure(scrollregion=self.map_canvas.bbox("all")))
        self.map_canvas.create_window((0, 0), window=self.map_inner_frame, anchor="nw")
        self.map_canvas.configure(yscrollcommand=map_scrollbar.set)

        self.map_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        map_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- 导入操作区 ---
        action_frame = ttk.LabelFrame(self.frame, text="导入操作", padding=10)
        action_frame.pack(fill=tk.X, padx=5, pady=(3, 5))

        act_row = ttk.Frame(action_frame)
        act_row.pack(fill=tk.X)

        ttk.Label(act_row, text="最大容错行数:").pack(side=tk.LEFT)
        self.max_filter_ratio_var = tk.StringVar(value="0")
        ttk.Entry(act_row, textvariable=self.max_filter_ratio_var, width=8).pack(side=tk.LEFT, padx=(5, 20))

        self.import_btn = ttk.Button(act_row, text="开始导入", command=self._start_import, state=tk.DISABLED)
        self.import_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.progress_var = tk.StringVar(value="")
        ttk.Label(act_row, textvariable=self.progress_var).pack(side=tk.LEFT, padx=10)

    # ---------- 跳过行管理 ----------

    def _add_skip_rows(self):
        """添加要跳过的行号"""
        text = self.skip_input_var.get().strip()
        if not text:
            return
        try:
            parts = [p.strip() for p in text.replace("，", ",").split(",") if p.strip()]
            for p in parts:
                if "-" in p:
                    # 支持范围，如 5-10
                    start, end = p.split("-", 1)
                    for n in range(int(start.strip()), int(end.strip()) + 1):
                        if n > 0:
                            self.skip_rows.add(n)
                else:
                    n = int(p)
                    if n > 0:
                        self.skip_rows.add(n)
            self.skip_input_var.set("")
            self._update_skip_summary()
        except ValueError:
            messagebox.showwarning("格式错误", "请输入有效的行号，如: 1,3,5 或 2-8")

    def _clear_skip_rows(self):
        """清除所有跳过行"""
        self.skip_rows.clear()
        self._update_skip_summary()

    def _update_skip_summary(self):
        """更新跳过行摘要显示"""
        if not self.skip_rows:
            self.skip_summary_var.set("当前无跳过行")
            return
        sorted_rows = sorted(self.skip_rows)
        count = len(sorted_rows)
        # 简要显示：最多显示前10个行号
        if count <= 10:
            display = ", ".join(str(r) for r in sorted_rows)
        else:
            display = ", ".join(str(r) for r in sorted_rows[:10]) + f" ... (共 {count} 行)"
        self.skip_summary_var.set(f"已标记跳过 {count} 行: [{display}]")

    def _show_skip_details(self):
        """弹窗显示跳过行的详细信息"""
        if not self.skip_rows:
            messagebox.showinfo("跳过行详情", "当前没有标记跳过的行")
            return

        detail_win = tk.Toplevel(self.frame)
        detail_win.title("跳过行详情")
        detail_win.geometry("600x400")
        detail_win.transient(self.frame.winfo_toplevel())

        ttk.Label(detail_win, text=f"共标记 {len(self.skip_rows)} 行跳过",
                  font=("", 11, "bold")).pack(pady=(10, 5))

        # 行号列表
        list_frame = ttk.Frame(detail_win)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("row_num", "content")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        tree.heading("row_num", text="数据行号")
        tree.heading("content", text="行内容预览")
        tree.column("row_num", width=80, anchor=tk.CENTER)
        tree.column("content", width=480, anchor=tk.W)

        vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        sorted_rows = sorted(self.skip_rows)
        for row_num in sorted_rows:
            # 尝试显示该行的内容
            content = ""
            if self.csv_all_rows and 0 < row_num <= len(self.csv_all_rows):
                row_data = self.csv_all_rows[row_num - 1]
                content = ", ".join(str(v) for v in row_data)
                if len(content) > 80:
                    content = content[:80] + "..."
            tree.insert("", tk.END, values=(row_num, content))

        # 操作按钮
        btn_frame = ttk.Frame(detail_win)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        def remove_selected():
            selected = tree.selection()
            for item in selected:
                row_num = int(tree.item(item)["values"][0])
                self.skip_rows.discard(row_num)
                tree.delete(item)
            self._update_skip_summary()

        ttk.Button(btn_frame, text="移除选中行的标记", command=remove_selected).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="关闭", command=detail_win.destroy).pack(side=tk.RIGHT)

    # ---------- CSV 操作 ----------

    def _browse_csv(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV 文件", "*.csv"), ("文本文件", "*.txt"), ("所有文件", "*.*")])
        if path:
            self.csv_path_var.set(path)

    def _parse_csv(self):
        path = self.csv_path_var.get().strip()
        if not path:
            messagebox.showwarning("提示", "请先选择 CSV 文件")
            return

        delimiter = self.delimiter_var.get()
        if delimiter == "\\t":
            delimiter = "\t"
        encoding = self.encoding_var.get()

        try:
            skip_n = int(self.skip_n_var.get().strip() or "0")
        except ValueError:
            skip_n = 0

        try:
            with open(path, "r", encoding=encoding) as f:
                # 跳过前N行
                for _ in range(skip_n):
                    next(f, None)

                reader = csv.reader(f, delimiter=delimiter)
                header = next(reader)
                self.csv_columns = [col.strip() for col in header]
                self.csv_all_rows = []
                for row in reader:
                    self.csv_all_rows.append(row)

            total_lines = len(self.csv_all_rows)
            info = f"共 {len(self.csv_columns)} 列, {total_lines} 行数据"
            if skip_n > 0:
                info += f"（已跳过前 {skip_n} 行）"
            self.csv_info_label.config(text=info)
            self._refresh_mapping()
        except Exception as e:
            messagebox.showerror("解析失败", str(e))

    # ---------- Doris 连接 ----------

    def _connect(self):
        """连接 Doris，获取数据库列表"""
        try:
            import pymysql
            conn = pymysql.connect(
                host=self.host_var.get(),
                port=int(self.query_port_var.get()),
                user=self.user_var.get(),
                password=self.pass_var.get(),
                charset="utf8mb4"
            )
            cursor = conn.cursor()
            cursor.execute("SHOW DATABASES")
            databases = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()

            # 过滤系统库
            system_dbs = {"information_schema", "__internal_schema", "mysql", "performance_schema"}
            databases = [db for db in databases if db not in system_dbs]

            self.db_combo["values"] = databases
            self.db_combo.config(state="readonly")
            if databases:
                self.db_combo.set(databases[0])
                self._on_db_select()

            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.conn_status.config(text=f"已连接（{len(databases)} 个库）", foreground="green")
        except Exception as e:
            messagebox.showerror("连接失败", str(e))
            self.conn_status.config(text="连接失败", foreground="red")

    def _disconnect(self):
        """断开连接，重置状态"""
        self.db_combo.set("")
        self.db_combo["values"] = []
        self.db_combo.config(state="disabled")
        self.table_combo.set("")
        self.table_combo["values"] = []
        self.table_combo.config(state="disabled")
        self.table_columns = []
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.import_btn.config(state=tk.DISABLED)
        self.conn_status.config(text="未连接", foreground="gray")
        for widget in self.map_inner_frame.winfo_children():
            widget.destroy()
        self.mapping_widgets.clear()

    def _on_db_select(self, _event=None):
        """选择数据库后，加载该库的表列表"""
        db = self.db_var.get().strip()
        if not db:
            return
        try:
            import pymysql
            conn = pymysql.connect(
                host=self.host_var.get(),
                port=int(self.query_port_var.get()),
                user=self.user_var.get(),
                password=self.pass_var.get(),
                database=db,
                charset="utf8mb4"
            )
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()

            self.table_combo["values"] = tables
            self.table_combo.config(state="readonly")
            if tables:
                self.table_combo.set(tables[0])
                self._on_table_select()
            else:
                self.table_combo.set("")
                self.table_columns = []
                self._refresh_mapping()
        except Exception as e:
            messagebox.showerror("获取表列表失败", str(e))

    def _on_table_select(self, _event=None):
        """选择表后，加载该表的列信息"""
        self._load_table_columns()

    def _load_table_columns(self):
        """获取选中表的列信息"""
        table = self.table_var.get().strip()
        db = self.db_var.get().strip()
        if not table or not db:
            return
        try:
            import pymysql
            conn = pymysql.connect(
                host=self.host_var.get(),
                port=int(self.query_port_var.get()),
                user=self.user_var.get(),
                password=self.pass_var.get(),
                database=db,
                charset="utf8mb4"
            )
            cursor = conn.cursor()
            cursor.execute(f"DESCRIBE `{table}`")
            self.table_columns = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            self._refresh_mapping()
        except Exception as e:
            messagebox.showerror("获取列信息失败", str(e))

    # ---------- 字段映射 ----------

    def _refresh_mapping(self):
        """刷新字段映射 UI"""
        for widget in self.map_inner_frame.winfo_children():
            widget.destroy()
        self.mapping_widgets.clear()

        if not self.csv_columns:
            return

        doris_options = ["（不导入）"] + self.table_columns

        for i, csv_col in enumerate(self.csv_columns):
            row_frame = ttk.Frame(self.map_inner_frame)
            row_frame.pack(fill=tk.X, pady=2)

            ttk.Label(row_frame, text=csv_col, width=25, anchor=tk.W).pack(side=tk.LEFT, padx=(10, 30))
            ttk.Label(row_frame, text="→", width=3).pack(side=tk.LEFT)

            var = tk.StringVar()
            combo = ttk.Combobox(row_frame, textvariable=var, values=doris_options,
                                 state="readonly", width=25)
            combo.pack(side=tk.LEFT, padx=(30, 0))

            # 自动匹配
            matched = False
            for doris_col in self.table_columns:
                if csv_col.lower() == doris_col.lower():
                    var.set(doris_col)
                    matched = True
                    break
            if not matched:
                var.set("（不导入）")

            self.mapping_widgets.append((csv_col, var))

        self.import_btn.config(state=tk.NORMAL)

    # ---------- 导入 ----------

    def _start_import(self):
        # 验证映射
        mappings = []
        for csv_col, var in self.mapping_widgets:
            doris_col = var.get()
            if doris_col != "（不导入）":
                mappings.append((csv_col, doris_col))

        if not mappings:
            messagebox.showwarning("提示", "请至少映射一个字段")
            return

        if not self.csv_path_var.get().strip():
            messagebox.showwarning("提示", "请选择 CSV 文件")
            return

        if not self.table_var.get().strip():
            messagebox.showwarning("提示", "请选择目标表")
            return

        if not self.db_var.get().strip():
            messagebox.showwarning("提示", "请选择数据库")
            return

        self.import_btn.config(state=tk.DISABLED)
        self.progress_var.set("导入中...")
        threading.Thread(target=self._do_import, args=(mappings,), daemon=True).start()

    def _do_import(self, mappings):
        """使用 Stream Load 导入数据到 Doris"""
        try:
            delimiter = self.delimiter_var.get()
            if delimiter == "\\t":
                delimiter = "\t"

            # 读取 CSV 并按映射重组数据
            csv_col_indices = []
            doris_cols = []
            for csv_col, doris_col in mappings:
                idx = self.csv_columns.index(csv_col)
                csv_col_indices.append(idx)
                doris_cols.append(doris_col)

            # 构建要发送的 CSV 数据（只包含映射的列，跳过标记行）
            lines = []
            skipped_count = 0
            for row_idx, row in enumerate(self.csv_all_rows):
                row_num = row_idx + 1  # 数据行号从1开始
                if row_num in self.skip_rows:
                    skipped_count += 1
                    continue
                selected = [row[i] if i < len(row) else "" for i in csv_col_indices]
                lines.append(",".join(selected))

            if not lines:
                self.frame.after(0, lambda: messagebox.showwarning("提示", "没有可导入的数据（全部被跳过）"))
                self.frame.after(0, lambda: self.import_btn.config(state=tk.NORMAL))
                self.frame.after(0, lambda: self.progress_var.set(""))
                return

            body = "\n".join(lines).encode("utf-8")

            # Stream Load 请求
            host = self.host_var.get()
            port = self.port_var.get()
            db = self.db_var.get()
            table = self.table_var.get()
            user = self.user_var.get()
            password = self.pass_var.get()

            url = f"http://{host}:{port}/api/{db}/{table}/_stream_load"

            # 认证
            auth_str = f"{user}:{password}"
            auth_bytes = base64.b64encode(auth_str.encode()).decode()

            # 构建请求头
            headers = {
                "Authorization": f"Basic {auth_bytes}",
                "Expect": "100-continue",
                "column_separator": ",",
                "columns": ",".join(doris_cols),
                "format": "csv",
            }

            max_filter = self.max_filter_ratio_var.get().strip()
            if max_filter and max_filter != "0":
                try:
                    ratio = int(max_filter) / len(lines) if lines else 0
                    headers["max_filter_ratio"] = str(min(ratio, 1.0))
                except ValueError:
                    pass

            req = urllib.request.Request(url, data=body, headers=headers, method="PUT")

            with urllib.request.urlopen(req, timeout=300) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            status = result.get("Status", "Unknown")
            msg = result.get("Message", "")
            loaded = result.get("NumberLoadedRows", 0)
            filtered = result.get("NumberFilteredRows", 0)
            total = result.get("NumberTotalRows", 0)

            skip_info = f"（跳过 {skipped_count} 行）" if skipped_count > 0 else ""

            if status == "Success":
                self.frame.after(0, lambda: self.progress_var.set(
                    f"导入成功！发送 {len(lines)} 行{skip_info}，成功 {loaded} 行，过滤 {filtered} 行"))
                self.frame.after(0, lambda: messagebox.showinfo("导入成功",
                    f"状态: {status}\n发送行数: {len(lines)}{skip_info}\n成功: {loaded}\n过滤: {filtered}"))
            elif status == "Publish Timeout":
                self.frame.after(0, lambda: self.progress_var.set(
                    f"导入超时，但数据可能已写入。成功 {loaded} 行"))
                self.frame.after(0, lambda: messagebox.showwarning("导入超时",
                    f"状态: {status}\n消息: {msg}\n成功行数: {loaded}"))
            else:
                self.frame.after(0, lambda: self.progress_var.set(f"导入失败: {status}"))
                self.frame.after(0, lambda: messagebox.showerror("导入失败",
                    f"状态: {status}\n消息: {msg}\n"
                    f"错误URL: {result.get('ErrorURL', 'N/A')}"))

        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(err_body)
                err_msg = err_json.get("Message", err_body)
            except Exception:
                err_msg = err_body
            self.frame.after(0, lambda: self.progress_var.set("导入失败"))
            self.frame.after(0, lambda: messagebox.showerror("HTTP 错误",
                f"状态码: {e.code}\n{err_msg}"))
        except Exception as e:
            self.frame.after(0, lambda: self.progress_var.set("导入失败"))
            self.frame.after(0, lambda: messagebox.showerror("导入错误", str(e)))
        finally:
            self.frame.after(0, lambda: self.import_btn.config(state=tk.NORMAL))


def create_doris_loader(parent):
    """工厂函数，供主界面注册调用"""
    panel = DorisLoaderPanel(parent)
    return panel.frame
