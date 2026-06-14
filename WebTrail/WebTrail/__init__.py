"""
WebTrail 顶层包（Layer 3 — 入口层）

对外暴露 6 个核心符号：
  - ChromiumExtractor / FirefoxExtractor / SystemExtractor — 提取器
  - analyze — 智能分析
  - generate / format_analysis — 报告生成与格式化

可通过 from WebTrail import analyze 等方式直接使用。
"""
from .extraction import ChromiumExtractor, FirefoxExtractor, SystemExtractor
from .analysis import analyze
from .reporting import generate, format_analysis

__all__ = [
    "ChromiumExtractor", "FirefoxExtractor", "SystemExtractor",
    "analyze", "generate", "format_analysis",
]
