"""
图形界面入口（Layer 3 — 入口层）

技术栈：tkinter + ttk，纯标准库，无需额外依赖
主题：蓝白配色

界面布局：
  - 标题栏（WebTrail logo + 版本号 + 状态标签）
  - 统计摘要栏（痕迹数 / 可疑数 / 浏览器数 / 风险分 + 进度条）
  - 按钮栏（开始 / 停止 / 保存报告 / 导出JSON / 清空）
  - 双Tab（取证报告 / 取证分析）— ScrolledText + 语法高亮
  - 底部状态栏

线程模型：
  - 主线程：UI 渲染
  - Worker 线程：提取 + 分析（通过 self.running 标志位实现安全停止）
"""
import os
import sys
import json
import math
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext

# 确保模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraction import ChromiumExtractor, FirefoxExtractor, SystemExtractor
from reporting import generate, format_analysis
from analysis import analyze


class WebTrailGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WebTrail — 浏览器痕迹取证分析工具")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)

        self.traces = []
        self.report_text = ""
        self.analysis_text = ""
        self.running = False

        self._build_ui()
        self._center_window()

    # ======================== UI ========================

    def _build_ui(self):
        # 标题栏
        header = tk.Frame(self.root, bg="#1565c0", height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="WebTrail",
                 font=("Consolas", 22, "bold"), fg="#ffffff", bg="#1565c0")\
            .pack(side=tk.LEFT, padx=20, pady=10)
        tk.Label(header, text="浏览器痕迹取证分析工具  v1.0",
                 font=("Microsoft YaHei", 11), fg="#bbdefb", bg="#1565c0")\
            .pack(side=tk.LEFT, pady=18)

        self.status_label = tk.Label(
            header, text="就绪", font=("Microsoft YaHei", 10),
            fg="#ffffff", bg="#1565c0", anchor=tk.E)
        self.status_label.pack(side=tk.RIGHT, padx=20, pady=18)

        # 摘要栏
        summary = tk.Frame(self.root, bg="#e3f2fd", height=80)
        summary.pack(fill=tk.X)
        summary.pack_propagate(False)

        self.stat_total = tk.Label(summary, text="痕迹: --",
            font=("Consolas", 13, "bold"), fg="#1565c0", bg="#e3f2fd")
        self.stat_total.place(x=30, y=12)
        self.stat_sus = tk.Label(summary, text="可疑: --",
            font=("Consolas", 13, "bold"), fg="#d32f2f", bg="#e3f2fd")
        self.stat_sus.place(x=200, y=12)
        self.stat_browsers = tk.Label(summary, text="浏览器: --",
            font=("Consolas", 13, "bold"), fg="#2e7d32", bg="#e3f2fd")
        self.stat_browsers.place(x=370, y=12)
        self.stat_score = tk.Label(summary, text="风险: --",
            font=("Consolas", 13, "bold"), fg="#d32f2f", bg="#e3f2fd")
        self.stat_score.place(x=550, y=12)

        self.progress = ttk.Progressbar(summary, mode="indeterminate", length=250)
        self.progress.place(x=550, y=42)

        # 按钮栏
        btn = tk.Frame(self.root, bg="#1976d2", height=44)
        btn.pack(fill=tk.X)
        btn.pack_propagate(False)

        style = ttk.Style()
        style.configure("Run.TButton", font=("Microsoft YaHei", 11, "bold"), padding=(20, 4))
        style.configure("Action.TButton", font=("Microsoft YaHei", 10), padding=(10, 4))

        self.btn_run = ttk.Button(btn, text="▶  开始分析", style="Run.TButton",
                                  command=self._start)
        self.btn_run.pack(side=tk.LEFT, padx=6, pady=5)
        self.btn_stop = ttk.Button(btn, text="■  停止", style="Action.TButton",
                                   command=self._stop, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=4, pady=5)

        ttk.Separator(btn, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=6)

        self.btn_save = ttk.Button(btn, text="💾 保存报告", style="Action.TButton",
                                   command=self._save_report, state=tk.DISABLED)
        self.btn_save.pack(side=tk.LEFT, padx=4, pady=5)
        self.btn_json = ttk.Button(btn, text="📄 导出JSON", style="Action.TButton",
                                   command=self._export_json, state=tk.DISABLED)
        self.btn_json.pack(side=tk.LEFT, padx=4, pady=5)

        ttk.Separator(btn, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=6)

        self.btn_clear = ttk.Button(btn, text="🗑 清空", style="Action.TButton",
                                    command=self._clear)
        self.btn_clear.pack(side=tk.LEFT, padx=4, pady=5)

        # Tab区域
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        for tab_text, attr_name in [("  📋 取证报告  ", "text_report"),
                                     ("  🔍 智能分析  ", "text_analysis")]:
            frame = tk.Frame(self.notebook)
            self.notebook.add(frame, text=tab_text)
            widget = scrolledtext.ScrolledText(
                frame, wrap=tk.WORD, font=("Consolas", 10),
                bg="#ffffff", fg="#212121", insertbackground="#1565c0",
                relief=tk.FLAT, borderwidth=0)
            widget.pack(fill=tk.BOTH, expand=True)
            widget.insert(tk.END, "点击「开始分析」提取浏览器痕迹...\n")
            widget.config(state=tk.DISABLED)
            setattr(self, attr_name, widget)

        # 语法高亮
        for attr in ("text_report", "text_analysis"):
            w = getattr(self, attr)
            w.tag_configure("suspect", foreground="#d32f2f")
            w.tag_configure("header", foreground="#1565c0")
            w.tag_configure("section", foreground="#1976d2")
            w.tag_configure("warn", foreground="#d32f2f")
            w.tag_configure("dim", foreground="#9e9e9e")
            w.tag_configure("finding", foreground="#1b5e20")
            w.tag_configure("axis", foreground="#6a1b9a")

        # 可视化 Tab
        viz_frame = tk.Frame(self.notebook)
        self.notebook.add(viz_frame, text="  📊 风险可视化  ")

        left = tk.Frame(viz_frame, bg="#fafafa")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)
        right = tk.Frame(viz_frame, bg="#fafafa")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        tk.Label(left, text="风险维度雷达图", font=("Microsoft YaHei", 11, "bold"),
                 fg="#1565c0", bg="#fafafa").pack(pady=(8, 2))
        self.canvas_radar = tk.Canvas(left, bg="#ffffff", highlightthickness=1,
                                       highlightbackground="#e0e0e0",
                                       width=430, height=440)
        self.canvas_radar.pack(padx=8, pady=4)

        tk.Label(right, text="杀伤链覆盖热力图", font=("Microsoft YaHei", 11, "bold"),
                 fg="#1565c0", bg="#fafafa").pack(pady=(8, 2))
        self.canvas_heatmap = tk.Canvas(right, bg="#ffffff", highlightthickness=1,
                                         highlightbackground="#e0e0e0",
                                         width=520, height=440)
        self.canvas_heatmap.pack(padx=8, pady=4)

        # 状态栏
        self.statusbar = tk.Label(self.root, text="就绪 — 等待操作",
            font=("Microsoft YaHei", 9), fg="#bbdefb", bg="#1565c0",
            anchor=tk.W, padx=12, pady=3)
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM)

    def _center_window(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ======================== 业务 ========================

    def _start(self):
        if self.running:
            return
        self.running = True
        self._set_ui_state(True)
        self._clear_display()
        self._set_status("提取中...")

        def worker():
            try:
                self._update_stage("正在提取 Chromium 浏览器数据...")
                chrom = ChromiumExtractor().extract()
                if not self.running:
                    return
                self._update_stage("正在提取 Firefox 浏览器数据...")
                ff = FirefoxExtractor().extract()
                if not self.running:
                    return
                self._update_stage("正在提取系统级痕迹...")
                sys_traces = SystemExtractor().extract()
                if not self.running:
                    return

                self.traces = chrom + ff + sys_traces
                if not self.traces:
                    self.root.after(0, self._show_empty)
                    return

                self._update_stage("正在生成取证报告...")
                self.report_text = generate(self.traces)

                self._update_stage("正在执行智能分析...")
                result = analyze(self.traces)
                self.analysis_text = format_analysis(result)

                self.root.after(0, lambda: self._display_results(result))
            except Exception as e:
                self.root.after(0, lambda: self._show_error(str(e)))
            finally:
                self.running = False
                self.root.after(0, lambda: self._set_ui_state(False))

        threading.Thread(target=worker, daemon=True).start()

    def _stop(self):
        self.running = False
        self._set_status("已停止")

    def _update_stage(self, msg):
        self.root.after(0, lambda: self._set_status(msg))

    def _display_results(self, result):
        sus_count = sum(1 for t in self.traces if t.suspicious)
        # 按浏览器名聚合（去掉 [...] 后缀）
        browser_names = set()
        for t in self.traces:
            src = t.source.split(" [")[0].strip()
            if src in ("DNS缓存", "UserAssist", "Prefetch"):
                continue
            browser_names.add(src)

        self.stat_total.config(text=f"痕迹: {len(self.traces)}")
        self.stat_sus.config(text=f"可疑: {sus_count}")
        self.stat_browsers.config(text=f"浏览器: {len(browser_names)}")

        score = result.risk_score
        level = result.risk_level
        color = "#d32f2f" if score >= 70 else ("#f57c00" if score >= 40 else "#2e7d32")
        self.stat_score.config(text=f"风险: {score}/100 ({level})", fg=color)

        self._set_text(self.text_report, self.report_text)
        self._set_text(self.text_analysis, self.analysis_text)
        self.notebook.select(0)
        self._set_status(f"完成 — {len(self.traces)} 条痕迹 | 风险 {score}/100 ({level})")

        # 绘制可视化
        self._draw_radar(result.axis_scores or {})
        self._draw_heatmap(result.kill_chain_coverage or {}, result.findings or [])

    def _draw_radar(self, axis_scores: dict):
        """在 Canvas 上绘制四维风险雷达图"""
        c = self.canvas_radar
        c.delete("all")

        w, h = 430, 440
        cx, cy = w // 2, h // 2 + 5
        r = 155

        axes = [
            ("攻击工具\n与武器化", "attack_tooling", 45),
            ("侦查与\n信息收集", "recon_intel", 135),
            ("凭证窃取\n与持久化", "credential_persist", 225),
            ("反取证\n与隐匿", "anti_forensics", 315),
        ]

        scores = [axis_scores.get(k, 0) for _, k, _ in axes]
        max_score = max(max(scores), 1)
        max_score = max(max_score, 25)

        # 同心参考网格
        for level in (0.25, 0.5, 0.75, 1.0):
            pts = []
            for _, _, angle in axes:
                rad = math.radians(angle)
                lr = r * level
                pts.extend([cx + lr * math.cos(rad), cy - lr * math.sin(rad)])
            c.create_polygon(pts, outline="#e0e0e0", fill="", width=1)
            if level > 0:
                c.create_text(cx + r * level * 0.71 - 4, cy - r * level * 0.71 + 4,
                              text=str(int(max_score * level)), fill="#9e9e9e",
                              font=("Consolas", 8))

        # 轴线
        for _, _, angle in axes:
            rad = math.radians(angle)
            c.create_line(cx, cy, cx + r * math.cos(rad), cy - r * math.sin(rad),
                          fill="#bdbdbd", width=1)

        # 数据多边形
        data_pts = []
        for _, key, angle in axes:
            score = axis_scores.get(key, 0)
            dist = min(score / max_score, 1.0) * r if max_score > 0 else 0
            rad = math.radians(angle)
            data_pts.extend([cx + dist * math.cos(rad), cy - dist * math.sin(rad)])
        c.create_polygon(data_pts, fill="#1565c0", outline="#0d47a1",
                         width=2, stipple="gray50")

        # 数据点 + 标签
        for label, key, angle in axes:
            score = axis_scores.get(key, 0)
            dist = min(score / max_score, 1.0) * r if max_score > 0 else 0
            rad = math.radians(angle)
            px = cx + dist * math.cos(rad)
            py = cy - dist * math.sin(rad)
            c.create_oval(px - 5, py - 5, px + 5, py + 5,
                          fill="#0d47a1", outline="#ffffff", width=2)
            c.create_text(px, py - 14, text=str(score),
                          fill="#0d47a1", font=("Consolas", 10, "bold"))
            lx = cx + (r + 38) * math.cos(rad)
            ly = cy - (r + 38) * math.sin(rad)
            c.create_text(lx, ly, text=label, fill="#212121",
                          font=("Microsoft YaHei", 9, "bold"), justify=tk.CENTER)

    def _draw_heatmap(self, chain_map: dict, findings: list):
        """绘制杀伤链阶段 × 确信度热力图"""
        c = self.canvas_heatmap
        c.delete("all")

        stages = ["侦察", "武器化", "投递", "利用", "安装与\n持久化", "命令与\n控制", "目标行动"]
        conf_labels = ["确凿 HIGH", "间接 MEDIUM", "弱信号 LOW"]
        conf_keys = ["HIGH", "MEDIUM", "LOW"]

        matrix = [[0] * 3 for _ in range(7)]
        for stage_idx_str, fids in (chain_map or {}).items():
            si = int(stage_idx_str)
            for fid in fids:
                for f in findings:
                    if f.get("id") == fid:
                        try:
                            ci = conf_keys.index(f.get("confidence", "LOW"))
                        except ValueError:
                            ci = 2
                        matrix[si][ci] += 1

        max_val = max(max(row) for row in matrix) or 1

        def heat_color(count, max_v):
            if count == 0:
                return "#f5f5f5"
            ratio = count / max_v
            if ratio <= 0.33:
                return "#c8e6c9"
            elif ratio <= 0.66:
                return "#fff9c4"
            else:
                return "#ffcdd2"

        margin_left, margin_top = 120, 40
        cell_w, cell_h = 100, 44
        header_h = 30

        for ci, cl in enumerate(conf_labels):
            x = margin_left + ci * cell_w
            c.create_rectangle(x, margin_top, x + cell_w, margin_top + header_h,
                               fill="#1565c0", outline="#0d47a1")
            c.create_text(x + cell_w // 2, margin_top + header_h // 2,
                          text=cl, fill="#ffffff", font=("Microsoft YaHei", 9, "bold"))

        for si, stage in enumerate(stages):
            y = margin_top + header_h + si * cell_h
            c.create_text(margin_left - 10, y + cell_h // 2,
                          text=stage, fill="#212121",
                          font=("Microsoft YaHei", 9), anchor=tk.E, justify=tk.RIGHT)
            for ci in range(3):
                count = matrix[si][ci]
                x = margin_left + ci * cell_w
                color = heat_color(count, max_val)
                c.create_rectangle(x, y, x + cell_w, y + cell_h,
                                   fill=color, outline="#e0e0e0", width=1)
                text_color = "#212121" if count > 0 else "#bdbdbd"
                c.create_text(x + cell_w // 2, y + cell_h // 2,
                              text=str(count) if count > 0 else "—",
                              fill=text_color, font=("Consolas", 14, "bold"))

        ly = margin_top + header_h + 7 * cell_h + 18
        c.create_text(margin_left, ly, text="少 ←", fill="#9e9e9e",
                      font=("Microsoft YaHei", 8), anchor=tk.W)
        for i, col in enumerate(["#c8e6c9", "#fff9c4", "#ffcdd2"]):
            lx = margin_left + 55 + i * 30
            c.create_rectangle(lx, ly - 8, lx + 22, ly + 8, fill=col, outline="#e0e0e0")
        c.create_text(margin_left + 155, ly, text="→ 多", fill="#9e9e9e",
                      font=("Microsoft YaHei", 8), anchor=tk.W)

    def _set_text(self, widget, content):
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        widget.insert(tk.END, content)
        widget.see(tk.END)

        for line_no, line in enumerate(content.split("\n"), 1):
            start, end = f"{line_no}.0", f"{line_no}.end"
            if "!!可疑!!" in line:
                widget.tag_add("suspect", start, end)
            elif line.startswith("====") or line.startswith("----"):
                widget.tag_add("section", start, end)
            elif "取证风险评定" in line or "统计摘要" in line:
                widget.tag_add("header", start, end)
            elif line.startswith("⚠") or "高风险" in line:
                widget.tag_add("warn", start, end)
            elif line.startswith("  │") and ("●" in line or "◉" in line or "○" in line):
                widget.tag_add("finding", start, end)
            elif "分" in line and "杀伤链" in line:
                widget.tag_add("axis", start, end)

        widget.config(state=tk.DISABLED)

    def _show_empty(self):
        msg = "未提取到任何浏览器痕迹。\n请确保已安装支持的浏览器并有浏览历史。"
        self._set_text(self.text_report, msg)
        self._set_text(self.text_analysis, "无数据可供分析。")
        self.stat_total.config(text="痕迹: 0")
        self._set_status("未提取到痕迹")

    def _show_error(self, msg):
        self._set_text(self.text_report, f"发生错误:\n{msg}")
        self._set_status(f"错误: {msg[:60]}")

    def _save_report(self):
        if not self.report_text:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            title="保存取证报告")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.report_text + "\n\n" + self.analysis_text)
            self._set_status(f"报告已保存: {os.path.basename(path)}")

    def _export_json(self):
        if not self.traces:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            title="导出JSON")
        if path:
            data = [t.to_dict() for t in self.traces]
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._set_status(f"JSON已导出: {os.path.basename(path)}")

    def _clear(self):
        self.traces = []
        self.report_text = ""
        self.analysis_text = ""
        self._clear_display()
        self.stat_total.config(text="痕迹: --")
        self.stat_sus.config(text="可疑: --")
        self.stat_browsers.config(text="浏览器: --")
        self.stat_score.config(text="风险: --", fg="#d32f2f")
        self._set_status("已清空")

    def _clear_display(self):
        for w in (self.text_report, self.text_analysis):
            w.config(state=tk.NORMAL)
            w.delete(1.0, tk.END)
            w.config(state=tk.DISABLED)
        self.canvas_radar.delete("all")
        self.canvas_heatmap.delete("all")

    def _set_status(self, msg):
        self.statusbar.config(text=msg)
        self.status_label.config(text=msg if len(msg) < 30 else msg[:28] + "...")

    def _set_ui_state(self, running):
        if running:
            self.btn_run.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
            self.btn_save.config(state=tk.DISABLED)
            self.btn_json.config(state=tk.DISABLED)
            self.progress.start(15)
            self.status_label.config(fg="#ff9800")
        else:
            self.btn_run.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            self.btn_save.config(state=tk.NORMAL)
            self.btn_json.config(state=tk.NORMAL)
            self.progress.stop()
            self.status_label.config(fg="#ffffff")

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        self.running = False
        self.root.destroy()


def launch():
    app = WebTrailGUI()
    app.run()


if __name__ == "__main__":
    launch()
