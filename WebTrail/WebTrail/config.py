"""
数字取证配置模块
定义浏览器痕迹提取的全局参数。
"""
from __future__ import annotations

import os
import platform
from pathlib import Path

# --- 取证工作目录 ---
CASE_NAME = "WebTrail_Forensics"
OUTPUT_DIR = Path.home() / CASE_NAME

# --- 浏览器数据路径映射 ---
SYSTEM = platform.system()

if SYSTEM == "Windows":
    CHROME_BASE = Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "User Data"
    EDGE_BASE = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Edge" / "User Data"
    FIREFOX_BASE = Path(os.environ.get("APPDATA", "")) / "Mozilla" / "Firefox" / "Profiles"
elif SYSTEM == "Darwin":
    CHROME_BASE = Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
    EDGE_BASE = Path.home() / "Library" / "Application Support" / "Microsoft Edge"
    FIREFOX_BASE = Path.home() / "Library" / "Application Support" / "Firefox" / "Profiles"
else:  # Linux
    CHROME_BASE = Path.home() / ".config" / "google-chrome"
    EDGE_BASE = Path.home() / ".config" / "microsoft-edge"
    FIREFOX_BASE = Path.home() / ".mozilla" / "firefox"

# --- 取证哈希算法 ---
HASH_ALGORITHM = "sha256"
