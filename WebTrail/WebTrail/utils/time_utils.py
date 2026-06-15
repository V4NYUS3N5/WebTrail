"""
时间转换工具 - 统一处理各浏览器时间戳格式。
"""
from __future__ import annotations

import datetime as dt


# Chrome: 1601-01-01 以来的微秒数 (Windows FILETIME / WebKit)
_CHROME_EPOCH = dt.datetime(1601, 1, 1, tzinfo=dt.timezone.utc)
# Unix epoch (1970-01-01) 以来的秒/毫秒/微秒
_UNIX_EPOCH = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)


def chrome_micros_to_iso(timestamp: int) -> str | None:
    """Chrome/WebKit 微秒时间戳 → ISO 8601 字符串。"""
    if not timestamp or timestamp <= 0:
        return None
    try:
        return (_CHROME_EPOCH + dt.timedelta(microseconds=timestamp)).isoformat()
    except (OverflowError, ValueError):
        return None


def firefox_micros_to_iso(timestamp: int) -> str | None:
    """Firefox PRTime (1970 epoch 微秒) → ISO 8601 字符串。"""
    if not timestamp or timestamp <= 0:
        return None
    try:
        return (_UNIX_EPOCH + dt.timedelta(microseconds=timestamp)).isoformat()
    except (OverflowError, ValueError):
        return None


def unix_millis_to_iso(timestamp: int) -> str | None:
    """Unix 毫秒时间戳 → ISO 8601 字符串。"""
    if not timestamp or timestamp <= 0:
        return None
    try:
        return (_UNIX_EPOCH + dt.timedelta(milliseconds=timestamp)).isoformat()
    except (OverflowError, ValueError):
        return None
