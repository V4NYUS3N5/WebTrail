"""
Microsoft Edge 浏览器适配器
与 Chrome 共享 Chromium 内核，直接继承 ChromeExtractor。
"""
from __future__ import annotations

from pathlib import Path

from browsers.chrome import ChromeExtractor


class EdgeExtractor(ChromeExtractor):
    """Microsoft Edge 痕迹提取器 (Chromium 内核，格式与 Chrome 一致)。"""

    def __init__(self, base_path: Path):
        super().__init__(base_path)
        self.browser = "Edge"
        self.result.browser = "Edge"
