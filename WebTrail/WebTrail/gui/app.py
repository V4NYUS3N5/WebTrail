"""
WebTrail GUI - 基于 tkinter 的图形界面
=======================================
数字取证浏览器痕迹提取与用户画像可视化。
"""
from __future__ import annotations

import sys
from pathlib import Path

# 支持直接运行 gui/app.py 或通过 main.py --gui 调用
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import config
from core.extractor import ArtifactRecord
from core.pipeline import create_extractors, run_extraction
from core.profiler import profile_user
from output.writer import write_report

FONT_TITLE = ("Microsoft YaHei UI", 16, "bold")
FONT_H2    = ("Microsoft YaHei UI", 12, "bold")
FONT_BODY  = ("Microsoft YaHei UI", 10)
FONT_MONO  = ("Consolas", 9)

COLOR_BG       = "#f0f2f5"
COLOR_PRIMARY  = "#1a73e8"
COLOR_SUCCESS  = "#0f9d58"
COLOR_WARNING  = "#f9ab00"
COLOR_DANGER   = "#ea4335"
COLOR_DARK     = "#202124"
COLOR_TEXT     = "#5f6368"


class WebTrailApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("WebTrail - 浏览器数字取证工具")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)
        self.root.configure(bg=COLOR_BG)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._setup_styles()

        self.records: list[ArtifactRecord] = []
        self.profile_result: dict = {}
        self.running = False

        self._build_ui()
        self._refresh_browser_status()

    # ---- 样式 ----

    def _setup_styles(self):
        self.style.configure("Title.TLabel", font=FONT_TITLE, background=COLOR_BG, foreground=COLOR_DARK)
        self.style.configure("H2.TLabel", font=FONT_H2, background=COLOR_BG, foreground=COLOR_DARK)
        self.style.configure("Body.TLabel", font=FONT_BODY, background=COLOR_BG, foreground=COLOR_TEXT)
        self.style.configure("Card.TFrame", background="white", relief="solid", borderwidth=1)
        self.style.configure("Primary.TButton", font=FONT_BODY, background=COLOR_PRIMARY)
        self.style.configure("Export.TButton", font=FONT_BODY)
        self.style.configure("Green.Horizontal.TProgressbar", troughcolor="#e8eaed",
                             background=COLOR_SUCCESS, thickness=8)
        self.style.configure("TNotebook", background=COLOR_BG, borderwidth=0)
        self.style.configure("TNotebook.Tab", font=FONT_BODY, padding=[18, 6])

    # ---- UI 构建 ----

    def _build_ui(self):
        # 顶部标题栏
        header = ttk.Frame(self.root, style="Card.TFrame", padding=15)
        header.pack(fill="x", padx=12, pady=(12, 0))

        ttk.Label(header, text="WebTrail 数字取证", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="浏览器痕迹提取 · 用户画像分析 · 取证报告",
                  style="Body.TLabel").pack(anchor="w", pady=(2, 0))

        # 浏览器状态栏
        self._build_browser_panel()

        # 内容区域（左右分栏）
        content = ttk.Frame(self.root)
        content.pack(fill="both", expand=True, padx=12, pady=8)

        # 左侧：控制面板 + 进度
        left = ttk.Frame(content, width=320)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)
        self._build_control_panel(left)

        # 右侧：结果区域
        right = ttk.Frame(content)
        right.pack(side="left", fill="both", expand=True)
        self._build_result_panel(right)

        # 底部状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                               relief="sunken", anchor="w", padding=(8, 3),
                               font=FONT_BODY)
        status_bar.pack(fill="x", padx=12, pady=(0, 8))

    def _build_browser_panel(self):
        """浏览器检测状态卡片。"""
        card = ttk.Frame(self.root, style="Card.TFrame", padding=12)
        card.pack(fill="x", padx=12, pady=(8, 0))

        ttk.Label(card, text="浏览器检测状态", style="H2.TLabel").grid(row=0, column=0, columnspan=6, sticky="w")

        self.browser_vars = {}
        self.browser_labels = {}
        browsers_info = [
            ("chrome", "Chrome", config.CHROME_BASE),
            ("edge", "Edge", config.EDGE_BASE),
            ("firefox", "Firefox", config.FIREFOX_BASE),
        ]

        for i, (key, name, path) in enumerate(browsers_info):
            col_offset = i * 2
            var = tk.BooleanVar(value=path.exists())
            var.trace_add("write", lambda *_, k=key: self._on_browser_toggle(k))
            self.browser_vars[key] = var

            cb = ttk.Checkbutton(card, text=name, variable=var,
                                  state="normal" if path.exists() else "disabled")
            cb.grid(row=1, column=col_offset, padx=(0, 10), pady=(6, 0), sticky="w")

            status_text = "已检测" if path.exists() else "未找到"
            fg = COLOR_SUCCESS if path.exists() else COLOR_TEXT
            lb = ttk.Label(card, text=status_text, foreground=fg, font=FONT_BODY)
            lb.grid(row=1, column=col_offset + 1, padx=(0, 15), pady=(6, 0), sticky="w")
            self.browser_labels[key] = (lb, path)

    def _on_browser_toggle(self, key: str):
        lb, path = self.browser_labels[key]
        if path.exists():
            lb.configure(text="已选择", foreground=COLOR_PRIMARY)

    def _build_control_panel(self, parent: ttk.Frame):
        """左侧控制面板。"""
        # 操作按钮
        btn_card = ttk.Frame(parent, style="Card.TFrame", padding=12)
        btn_card.pack(fill="x", pady=(0, 8))

        ttk.Label(btn_card, text="操作", style="H2.TLabel").pack(anchor="w")

        btn_frame = ttk.Frame(btn_card)
        btn_frame.pack(fill="x", pady=(8, 0))

        self.start_btn = ttk.Button(btn_frame, text="开始分析", style="Primary.TButton",
                                     command=self._start_analysis)
        self.start_btn.pack(side="left", padx=(0, 8))

        self.export_btn = ttk.Button(btn_frame, text="导出报告", style="Export.TButton",
                                      command=self._export_report, state="disabled")
        self.export_btn.pack(side="left")

        # 进度
        prog_card = ttk.Frame(parent, style="Card.TFrame", padding=12)
        prog_card.pack(fill="x", pady=(0, 8))

        ttk.Label(prog_card, text="进度", style="H2.TLabel").pack(anchor="w")

        self.progress = ttk.Progressbar(prog_card, mode="indeterminate",
                                         style="Green.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(8, 4))

        self.progress_text = tk.StringVar(value="等待执行...")
        ttk.Label(prog_card, textvariable=self.progress_text,
                  font=FONT_BODY, foreground=COLOR_TEXT).pack(anchor="w")

        # 统计摘要卡片
        self.summary_card = ttk.Frame(parent, style="Card.TFrame", padding=12)
        self.summary_card.pack(fill="both", expand=True)

        ttk.Label(self.summary_card, text="统计摘要", style="H2.TLabel").pack(anchor="w")

        self.summary_text = tk.Text(self.summary_card, height=14, font=FONT_MONO,
                                     bg="#fafafa", fg=COLOR_DARK, relief="flat",
                                     borderwidth=0, padx=4, pady=4, state="disabled")
        self.summary_text.pack(fill="both", expand=True, pady=(6, 0))

    def _build_result_panel(self, parent: ttk.Frame):
        """右侧结果面板（Notebook 选项卡）。"""
        card = ttk.Frame(parent, style="Card.TFrame", padding=8)
        card.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(card)

        # 概览页
        self.tab_overview = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_overview, text="概览")

        self.overview_text = tk.Text(self.tab_overview, font=FONT_MONO, wrap="word",
                                      bg="white", fg=COLOR_DARK, relief="flat",
                                      borderwidth=0, padx=10, pady=10, state="disabled")
        self.overview_text.pack(fill="both", expand=True)

        # 域名排名
        self.tab_domains = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_domains, text="TOP域名")

        self.domains_tree = ttk.Treeview(self.tab_domains,
                                          columns=("rank", "domain", "count"),
                                          show="headings", height=20)
        self.domains_tree.heading("rank", text="#")
        self.domains_tree.heading("domain", text="域名")
        self.domains_tree.heading("count", text="访问次数")
        self.domains_tree.column("rank", width=50, anchor="center")
        self.domains_tree.column("domain", width=380)
        self.domains_tree.column("count", width=100, anchor="center")

        domain_scroll = ttk.Scrollbar(self.tab_domains, orient="vertical",
                                       command=self.domains_tree.yview)
        self.domains_tree.configure(yscrollcommand=domain_scroll.set)
        self.domains_tree.pack(side="left", fill="both", expand=True)
        domain_scroll.pack(side="right", fill="y")

        # 时间线
        self.tab_timeline = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_timeline, text="活跃时段")

        self.timeline_text = tk.Text(self.tab_timeline, font=FONT_MONO, wrap="word",
                                      bg="white", fg=COLOR_DARK, relief="flat",
                                      borderwidth=0, padx=10, pady=10, state="disabled")
        self.timeline_text.pack(fill="both", expand=True)

        # 类别分布
        self.tab_category = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_category, text="访问类别")

        self.category_tree = ttk.Treeview(self.tab_category,
                                           columns=("category", "count"),
                                           show="headings", height=20)
        self.category_tree.heading("category", text="类别")
        self.category_tree.heading("count", text="记录数")
        self.category_tree.column("category", width=300)
        self.category_tree.column("count", width=120, anchor="center")

        cat_scroll = ttk.Scrollbar(self.tab_category, orient="vertical",
                                    command=self.category_tree.yview)
        self.category_tree.configure(yscrollcommand=cat_scroll.set)
        self.category_tree.pack(side="left", fill="both", expand=True)
        cat_scroll.pack(side="right", fill="y")

        # 风险指标
        self.tab_risk = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_risk, text="风险指标")

        self.risk_text = tk.Text(self.tab_risk, font=FONT_MONO, wrap="word",
                                  bg="white", fg=COLOR_DARK, relief="flat",
                                  borderwidth=0, padx=10, pady=10, state="disabled")
        self.risk_text.pack(fill="both", expand=True)

        self.notebook.pack(fill="both", expand=True)

    # ---- 业务逻辑 ----

    def _refresh_browser_status(self):
        for key, (lb, path) in self.browser_labels.items():
            if path.exists():
                var = self.browser_vars.get(key)
                selected = var and var.get()
                lb.configure(text="已选择" if selected else "已检测",
                             foreground=COLOR_PRIMARY if selected else COLOR_SUCCESS)
            else:
                lb.configure(text="未找到", foreground=COLOR_TEXT)

    def _get_selected_browsers(self) -> list[str]:
        selected = []
        name_map = {"chrome": "Chrome", "edge": "Edge", "firefox": "Firefox"}
        for key, name in name_map.items():
            var = self.browser_vars.get(key)
            if var and var.get():
                selected.append(name)
        return selected

    def _start_analysis(self):
        selected = self._get_selected_browsers()
        if not selected:
            messagebox.showwarning("提示", "请至少选择一个浏览器。")
            return

        if self.running:
            return

        self.running = True
        self.start_btn.configure(state="disabled")
        self.export_btn.configure(state="disabled")
        self.progress.start(3)
        self.progress_text.set("正在分析...")

        # 清空旧结果
        self.records = []
        self.profile_result = {}

        thread = threading.Thread(target=self._run_analysis, args=(selected,), daemon=True)
        thread.start()

    def _run_analysis(self, selected: list[str]):
        try:
            extractors = create_extractors(set(selected))
            if not extractors:
                self.root.after(0, lambda: self._analysis_done(False, "未检测到浏览器数据。"))
                return

            # 阶段 1：提取
            self.root.after(0, lambda: self.progress_text.set("阶段 1/2: 提取浏览器痕迹..."))
            self.records = run_extraction(extractors)

            if not self.records:
                self.root.after(0, lambda: self._analysis_done(False, "未提取到任何痕迹记录。"))
                return

            # 阶段 2：画像 + 呈现
            self.root.after(0, lambda: self.progress_text.set("阶段 2/2: 用户画像分析..."))
            self.profile_result = profile_user(self.records)
            self.root.after(100, lambda: self._analysis_done(True, "分析完成"))

        except Exception as e:
            self.root.after(0, lambda: self._analysis_done(False, f"分析失败: {e}"))

    def _analysis_done(self, success: bool, msg: str):
        self.running = False
        self.progress.stop()
        self.progress_text.set(msg)
        self.start_btn.configure(state="normal")

        if success:
            self.export_btn.configure(state="normal")
            self._show_results()
            self.status_var.set(f"分析完成 · 共 {len(self.records)} 条记录")
        else:
            self.export_btn.configure(state="disabled")
            self.status_var.set(msg)

    def _show_results(self):
        """渲染所有结果标签页。"""
        profile = self.profile_result
        overview = profile.get("overview", {})

        # --- 统计摘要 ---
        browsers = overview.get("browsers", {})
        types = overview.get("artifact_types", {})
        lines = [
            f"痕迹总数:     {overview.get('total_records', 0)}",
            f"时间线事件:   {overview.get('timeline_events', 0)}",
            f"时间范围:     {overview.get('time_range_start', 'N/A')}",
            f"              ~ {overview.get('time_range_end', 'N/A')}",
            "",
            "浏览器分布:",
        ]
        for b, c in browsers.items():
            lines.append(f"  {b:<12s} {c:>6d} 条")
        lines.append("\n痕迹类型:")
        for t, c in types.items():
            lines.append(f"  {t:<12s} {c:>6d} 条")

        behaviors = profile.get("behavior_insights", {})
        if behaviors:
            lines.append(f"\n保存登录:     {behaviors.get('saved_logins', 0)} 个")
            lines.append(f"Cookie 数量:  {behaviors.get('cookies_count', 0)} 个")
            peak = behaviors.get("peak_hour", "N/A")
            lines.append(f"活跃高峰:     {peak}")

        self._set_text(self.summary_text, "\n".join(lines))

        # --- 概览页 ---
        ov_lines = [
            "══════════════ 取证概览 ══════════════",
            "",
            f"  痕迹总数:      {overview.get('total_records', 0)}",
            f"  时间线事件:    {overview.get('timeline_events', 0)}",
            f"  时间范围:      {overview.get('time_range_start', 'N/A')}",
            f"               ~ {overview.get('time_range_end', 'N/A')}",
            f"  检测浏览器:    {', '.join(browsers.keys())}",
            f"  配置:          {', '.join(overview.get('profiles', []))}",
            "",
            "--- 痕迹类型分布 ---",
        ]
        for t, c in types.items():
            bar = "█" * min(c // 10, 40)
            ov_lines.append(f"  {t:<12s}  {bar}  {c}")

        self._set_text(self.overview_text, "\n".join(ov_lines))

        # --- TOP 域名 ---
        self.domains_tree.delete(*self.domains_tree.get_children())
        for i, d in enumerate(profile.get("top_domains", []), 1):
            self.domains_tree.insert("", "end", values=(i, d["domain"], d["count"]))

        # --- 活跃时段 ---
        heat = profile.get("activity_heat", {})
        tl_lines = ["══════════ 24小时活跃度 ══════════", ""]
        hour_data = heat.get("by_hour", {})
        max_h = max(hour_data.values()) if hour_data else 1
        for h in range(24):
            c = hour_data.get(h, 0)
            bar_len = int(c / max_h * 40) if max_h > 0 else 0
            bar = "▓" * bar_len
            tl_lines.append(f"  {h:02d}:00  {bar}  {c}")

        day_data = heat.get("by_day", {})
        if day_data:
            tl_lines.append("\n--- 最近 14 天活跃度 ---")
            for day, count in list(day_data.items())[:14]:
                tl_lines.append(f"  {day}  {count}")

        self._set_text(self.timeline_text, "\n".join(tl_lines))

        # --- 类别分布 ---
        self.category_tree.delete(*self.category_tree.get_children())
        for cat, count in profile.get("top_categories", {}).items():
            self.category_tree.insert("", "end", values=(cat, count))

        # --- 风险指标 ---
        risk = profile.get("risk_indicators", {})
        risk_lines = ["══════════ 风险指标检测 ══════════", ""]
        risk_lines.append(f"  隐私模式痕迹:  {'是' if risk.get('private_mode_hint') else '否'}")
        risk_lines.append(f"  历史清除痕迹:  {'是' if risk.get('history_cleared') else '否'}")

        sus = risk.get("suspicious_domains", [])
        risk_lines.append(f"\n  可疑域名:      {len(sus)} 个")
        for s in sus[:20]:
            risk_lines.append(f"    - [{s['keyword']}] {s['url'][:70]}")
            risk_lines.append(f"      浏览器: {s.get('browser', '?')}")

        if not sus:
            risk_lines.append("    (未检测到)")
        risk_lines.append("")
        risk_lines.append("请注意：以上指标仅作参考，需结合"
                          "具体上下文进行人工研判。")

        self._set_text(self.risk_text, "\n".join(risk_lines))

    def _export_report(self):
        if not self.records:
            messagebox.showwarning("提示", "没有可导出的数据，请先执行分析。")
            return

        output_dir = filedialog.askdirectory(
            title="选择报告导出目录",
            initialdir=str(config.OUTPUT_DIR)
        )
        if not output_dir:
            return

        try:
            report_dir = write_report(
                self.records, self.profile_result, {}, Path(output_dir)
            )
            messagebox.showinfo("导出成功", f"报告已保存至: \n{report_dir}")
            self.status_var.set(f"报告已导出: {report_dir}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    @staticmethod
    def _set_text(widget: tk.Text, content: str):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled")


def launch():
    root = tk.Tk()
    WebTrailApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch()
