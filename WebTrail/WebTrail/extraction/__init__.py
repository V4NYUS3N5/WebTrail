"""
提取层入口（Layer 2a — 痕迹提取）

导出 4 个提取器：
  BaseExtractor       — 抽象基类，定义统一契约
  ChromiumExtractor   — 5浏览器 × 7维度
  FirefoxExtractor    — 1浏览器 × 6维度
  SystemExtractor     — UserAssist / DNS / Prefetch
"""
from .base import BaseExtractor
from .chromium import ChromiumExtractor
from .firefox import FirefoxExtractor
from .system import SystemExtractor

__all__ = ["BaseExtractor", "ChromiumExtractor", "FirefoxExtractor", "SystemExtractor"]
