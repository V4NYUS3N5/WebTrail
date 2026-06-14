"""
SQLite 安全读取 — 优先 URI immutable 直连，大库回退复制
"""
import os
import sqlite3
import logging
from typing import Optional, Tuple

_log = logging.getLogger("WebTrail.utils.sqlite")


def _db_uri(db_path: str) -> str:
    """将本地路径转为 SQLite URI (只读 + immutable 跳过锁)"""
    # Windows 上盘符需要特殊处理: C:/foo → /C:/foo
    abs_path = os.path.abspath(db_path).replace("\\", "/")
    if abs_path[1:3] == ":/":
        abs_path = "/" + abs_path[0] + ":" + abs_path[2:]
    return f"file:{abs_path}?mode=ro&immutable=1"


def read_sqlite_copy(db_path: str) -> Tuple[Optional[sqlite3.Connection], Optional[str]]:
    """
    安全打开浏览器 SQLite 数据库。
    策略：优先 URI immutable 直连（零拷贝）；失败则回退到临时文件复制。
    返回 (conn, tmp_path)。tmp_path 非空时调用方负责 conn.close() + os.remove(tmp_path)。
    """
    if not os.path.exists(db_path):
        return None, None

    # ── 策略 1：URI immutable 直连 ──
    uri = _db_uri(db_path)
    try:
        conn = sqlite3.connect(uri, uri=True)
        # 快速可用性检测：读一条 schema
        conn.execute("SELECT 1 FROM sqlite_master LIMIT 1")
        _log.debug("immutable 直连成功: %s", db_path)
        return conn, None  # tmp 为空 → 调用方知道无需删除临时文件
    except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
        _log.info("immutable 直连失败 (%s)，回退复制模式: %s", e, db_path)
    except Exception:
        _log.warning("immutable 直连异常，回退复制模式: %s", db_path, exc_info=True)

    # ── 策略 2：复制到临时文件 ──
    tmp = db_path + ".tf_tmp"
    try:
        with open(db_path, 'rb') as src:
            with open(tmp, 'wb') as dst:
                dst.write(src.read())
        conn = sqlite3.connect(tmp)
        _log.debug("复制模式连接成功 (%d bytes): %s", os.path.getsize(db_path), db_path)
        return conn, tmp
    except (OSError, sqlite3.Error) as e:
        _log.error("复制模式也失败: %s → %s", db_path, e)
        # 清理可能残留的临时文件
        try:
            os.remove(tmp)
        except OSError:
            pass
        return None, None
