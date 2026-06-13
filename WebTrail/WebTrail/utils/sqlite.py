"""
SQLite 安全读取 — 复制到临时文件避免锁竞争
"""
import os
import sqlite3
from typing import Optional, Tuple


def read_sqlite_copy(db_path: str) -> Tuple[Optional[sqlite3.Connection], Optional[str]]:
    """复制DB到临时文件并返回连接，调用方负责关闭连接并删除临时文件"""
    if not os.path.exists(db_path):
        return None, None
    tmp = db_path + ".tf_tmp"
    try:
        with open(db_path, 'rb') as src:
            with open(tmp, 'wb') as dst:
                dst.write(src.read())
        return sqlite3.connect(tmp), tmp
    except (OSError, sqlite3.Error):
        return None, None
