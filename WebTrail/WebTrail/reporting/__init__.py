"""
展示层入口（Layer 2c — 报告展示）

导出 2 个函数：
  generate(traces)          — 取证时间线报告（含可疑标记）
  format_analysis(result)   — 将 AnalysisResult 格式化为可读文本
"""
from .report import generate
from .formatter import format as format_analysis

__all__ = ["generate", "format_analysis"]
