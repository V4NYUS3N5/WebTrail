"""
时间转换工具
"""
from datetime import datetime, timedelta
from typing import Optional


def filetime_to_datetime(filetime_bytes: bytes) -> Optional[datetime]:
    """Windows FILETIME (8字节小端) -> datetime"""
    if len(filetime_bytes) < 8:
        return None
    filetime = int.from_bytes(filetime_bytes, byteorder='little')
    if filetime == 0:
        return None
    timestamp = filetime / 10_000_000 - 11644473600
    try:
        return datetime.fromtimestamp(timestamp)
    except (OSError, ValueError, OverflowError):
        return None


def chrome_time_to_dt(usec_val: int) -> Optional[datetime]:
    """Chromium 时间戳 (1601年起微秒数) -> datetime"""
    if not usec_val or usec_val == 0:
        return None
    try:
        return datetime(1601, 1, 1) + timedelta(microseconds=usec_val)
    except (OSError, OverflowError):
        return None


def firefox_time_to_dt(usec_val: int) -> Optional[datetime]:
    """Firefox PRTime (1970年起微秒数) -> datetime"""
    if not usec_val or usec_val == 0:
        return None
    try:
        return datetime(1970, 1, 1) + timedelta(microseconds=usec_val)
    except (OSError, OverflowError):
        return None
