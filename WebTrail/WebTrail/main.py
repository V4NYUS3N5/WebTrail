"""
CLI 命令行入口（Layer 3 — 入口层）

支持的命令行参数：
  -o/--output  保存报告到指定文件
  --json       导出原始数据为 JSON
  -q/--quiet   静默模式（仅输出摘要）
  -g/--gui     启动图形界面

执行流程：
  参数解析 → 三路提取 → 取证报告 → 智能分析 → 输出/保存
"""
import argparse
import json
import sys
import os
import logging

# 确保以包模式运行
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraction import ChromiumExtractor, FirefoxExtractor, SystemExtractor
from reporting import generate, format_analysis
from analysis import analyze

_log = logging.getLogger("WebTrail.main")

BANNER = """
╔══════════════════════════════════════════════════════════╗
║           WebTrail 浏览器痕迹取证提取工具                    ║
║           v1.0  |  Windows 10/11                         ║
╚══════════════════════════════════════════════════════════╝
"""


def main():
    p = argparse.ArgumentParser(description="WebTrail - 浏览器痕迹取证提取工具")
    p.add_argument("--output", "-o", help="保存报告到指定文件")
    p.add_argument("--json", help="导出JSON到指定文件")
    p.add_argument("--quiet", "-q", action="store_true", help="静默模式")
    p.add_argument("--gui", "-g", action="store_true", help="启动图形界面")
    args = p.parse_args()

    if args.gui:
        from gui import launch
        launch()
        return

    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        _log.debug("stdout reconfigure 失败（非关键）", exc_info=True)

    if not args.quiet:
        print(BANNER)

    # 提取
    traces = (ChromiumExtractor().extract()
              + FirefoxExtractor().extract()
              + SystemExtractor().extract())

    if not traces:
        print("\n[!] 未提取到浏览器痕迹")
        return

    report = generate(traces)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"[+] 报告已保存: {args.output}")
    else:
        _safe_print(report)

    sus = sum(1 for t in traces if t.suspicious)
    print(f"\n[+] 总计 {len(traces)} 条痕迹, 其中可疑 {sus} 条")

    # 智能分析
    print("\n[+] 正在执行智能分析...")
    try:
        analysis_result = analyze(traces)
        analysis_text = format_analysis(analysis_result)
        if args.output:
            with open(args.output, 'a', encoding='utf-8') as f:
                f.write(analysis_text)
            print(f"[+] 分析结果已追加到: {args.output}")
        else:
            _safe_print(analysis_text)
    except Exception as e:
        print(f"[!] 分析异常: {e}")

    if args.json:
        data = [t.to_dict() for t in traces]
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[+] JSON已保存: {args.json}")


def _safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('utf-8', errors='replace')
              .decode('utf-8', errors='replace'))


if __name__ == "__main__":
    main()
