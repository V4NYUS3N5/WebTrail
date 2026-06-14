"""
WebTrail 顶层包（Layer 3 — 入口层）

对外暴露 6 个核心符号：
  - ChromiumExtractor / FirefoxExtractor / SystemExtractor — 提取器
  - analyze — 智能分析
  - generate / format_analysis — 报告生成与格式化

可通过 from WebTrail import analyze 等方式直接使用。
"""
import logging

# 默认日志配置：WARNING 及以上输出到 stderr，模块级日志器按需记录
logging.basicConfig(
    level=logging.WARNING,
    format="[%(levelname)s] %(name)s: %(message)s",
)

from .extraction import ChromiumExtractor, FirefoxExtractor, SystemExtractor
from .analysis import analyze
from .reporting import generate, format_analysis

__all__ = [
    "ChromiumExtractor", "FirefoxExtractor", "SystemExtractor",
    "analyze", "generate", "format_analysis",
]
