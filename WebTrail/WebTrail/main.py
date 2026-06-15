"""
WebTrail - 浏览器数字取证工具
===============================
用法:
    python main.py                          # 全量分析（命令行模式）
    python main.py --gui                    # 图形界面模式
    python main.py --browser Chrome         # 仅分析 Chrome
    python main.py --output /path/to/case   # 指定输出目录
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import config
from core.pipeline import (
    create_extractors,
    collect_evidence_hashes,
    run_extraction,
    run_profiling,
    print_summary,
)
from output.writer import write_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)


def main():
    parser = argparse.ArgumentParser(
        description="WebTrail - 浏览器数字取证与用户画像工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n"
               "  python main.py                     # 全量分析\n"
               "  python main.py --gui               # 图形界面\n"
               "  python main.py --browser Chrome    # 仅 Chrome",
    )
    parser.add_argument("--browser", choices=["Chrome", "Firefox", "Edge"],
                        default=None)
    parser.add_argument("--output", type=Path, default=config.OUTPUT_DIR)
    parser.add_argument("--no-profile", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--gui", action="store_true", help="启动图形界面")
    args = parser.parse_args()

    if args.gui:
        from gui.app import launch
        launch()
        return

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    args.output.mkdir(parents=True, exist_ok=True)

    extractors = create_extractors(args.browser)
    if not extractors:
        print("错误：未检测到任何浏览器数据。")
        sys.exit(1)

    evidence_hashes = collect_evidence_hashes(extractors)
    records = run_extraction(extractors)

    if not records:
        print("未提取到任何痕迹记录，请确认浏览器已安装且有浏览活动。")
        sys.exit(0)

    profile = {} if args.no_profile else run_profiling(records)
    report_dir = write_report(records, profile, evidence_hashes, args.output)

    if profile:
        print_summary(profile)

    print(f"\n完整报告已生成: {report_dir}")


if __name__ == "__main__":
    main()
