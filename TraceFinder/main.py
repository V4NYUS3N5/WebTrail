#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TraceFinder - 无痕用户行为取证关联分析工具
主程序入口
"""
import argparse
import sys
import json
import os
from datetime import datetime

# 支持直接运行 main.py 和 python -m TraceFinder.main 两种方式
if __name__ == "__main__" and __package__ is None:
    # 直接运行时，将父目录加入路径
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from TraceFinder.clipboard_extractor import get_clipboard_history
    from TraceFinder.browser_extractor import get_incognito_trace
    from TraceFinder.notification_extractor import get_notification_history
    from TraceFinder.social_extractor import get_social_app_traces
    from TraceFinder.basic_extractor import get_basic_traces
    from TraceFinder.timeline_analyzer import generate_timeline, format_timeline_report
except ImportError:
    from clipboard_extractor import get_clipboard_history
    from browser_extractor import get_incognito_trace
    from notification_extractor import get_notification_history
    from social_extractor import get_social_app_traces
    from basic_extractor import get_basic_traces
    from timeline_analyzer import generate_timeline, format_timeline_report


def print_banner():
    """打印工具横幅"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          TraceFinder 无痕用户行为取证关联分析工具         ║
║                                                          ║
║          版本: 1.0.0                                     ║
║          适用系统: Windows 10/11                         ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")


def run_extraction(verbose=True):
    """执行所有提取模块"""
    all_traces = []
    
    modules = [
        ("剪贴板历史", get_clipboard_history),
        ("无痕浏览器痕迹", get_incognito_trace),
        ("系统通知历史", get_notification_history),
        ("社交软件痕迹", get_social_app_traces),
        ("基础痕迹", get_basic_traces),
    ]
    
    for module_name, extract_func in modules:
        if verbose:
            print(f"[+] 正在提取 {module_name}...", end=" ", flush=True)
        
        try:
            traces = extract_func()
            all_traces.extend(traces)
            if verbose:
                print(f"完成 (获取 {len(traces)} 条)")
        except Exception as e:
            if verbose:
                print(f"失败 ({str(e)})")
    
    return all_traces


def main():
    parser = argparse.ArgumentParser(
        description="TraceFinder - 无痕用户行为取证关联分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 运行完整提取并显示时间线
  python main.py --output report.txt # 保存报告到文件
  python main.py --json output.json  # 导出JSON格式数据
  python main.py --module clipboard  # 仅提取剪贴板历史
        """
    )
    
    parser.add_argument(
        "--output", "-o",
        help="保存报告到指定文件"
    )
    parser.add_argument(
        "--json",
        help="导出JSON格式数据到指定文件"
    )
    parser.add_argument(
        "--module", "-m",
        choices=["clipboard", "browser", "notification", "social", "basic", "all"],
        default="all",
        help="指定提取模块 (默认: all)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="静默模式，仅输出最终报告"
    )
    
    args = parser.parse_args()
    
    if not args.quiet:
        print_banner()
    
    # 根据模块选择执行提取
    all_traces = []
    
    module_map = {
        "clipboard": ("剪贴板历史", get_clipboard_history),
        "browser": ("无痕浏览器痕迹", get_incognito_trace),
        "notification": ("系统通知历史", get_notification_history),
        "social": ("社交软件痕迹", get_social_app_traces),
        "basic": ("基础痕迹", get_basic_traces),
    }
    
    if args.module == "all":
        all_traces = run_extraction(verbose=not args.quiet)
    else:
        module_name, extract_func = module_map[args.module]
        if not args.quiet:
            print(f"[+] 正在提取 {module_name}...")
        all_traces = extract_func()
        if not args.quiet:
            print(f"[+] 提取完成，共 {len(all_traces)} 条痕迹")
    
    if not all_traces:
        print("\n[!] 未提取到任何痕迹")
        sys.exit(0)
    
    # 生成时间线并标记可疑行为
    timeline = generate_timeline(all_traces)
    
    # 格式化报告
    report = format_timeline_report(timeline)
    
    # 输出报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        if not args.quiet:
            print(f"\n[+] 报告已保存到: {args.output}")
    else:
        print("\n" + report)
    
    # 导出JSON
    if args.json:
        json_data = []
        for trace in timeline:
            json_data.append({
                "type": trace.get("type"),
                "time": trace.get("time_str"),
                "content": trace.get("content"),
                "suspicious": trace.get("suspicious", False),
                "suspicious_reason": trace.get("suspicious_reason", "")
            })
        
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        if not args.quiet:
            print(f"[+] JSON数据已保存到: {args.json}")
    
    # 统计信息
    if not args.quiet:
        suspicious_count = sum(1 for t in timeline if t.get("suspicious"))
        print(f"\n[+] 提取完成: 共 {len(timeline)} 条痕迹，其中 {suspicious_count} 条可疑")


if __name__ == "__main__":
    main()
