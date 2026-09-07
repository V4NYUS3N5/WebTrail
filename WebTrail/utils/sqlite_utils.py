"""
SQLite 取证安全读取工具
- 只读模式，绝不修改原始证据
- 自动处理 WAL/Journal
- 连接超时保护
"""
from __future__ import annotations

import sqlite3
import shutil
import tempfile
from pathlib import Path


def _dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def safe_connect(source: Path, *, timeout: float = 5.0) -> sqlite3.Connection:
    """以只读模式连接 SQLite，自动处理 WAL。"""
    uri = source.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=timeout)
    conn.row_factory = _dict_factory
    conn.execute("PRAGMA journal_mode=off")
    conn.execute("PRAGMA query_only=ON")
    return conn


def copy_to_temp(source: Path) -> Path:
    """将数据库复制到临时文件，用于无法直接只读访问的场景。"""
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    shutil.copy2(source, tmp.name)
    return Path(tmp.name)


def safe_connect_with_fallback(source: Path) -> sqlite3.Connection | None:
    """尝试只读连接，失败时复制到临时文件再连接（用后自动清理临时文件）。"""
    try:
        return safe_connect(source)
    except Exception:
        pass
    try:
        tmp_path = copy_to_temp(source)
        conn = sqlite3.connect(str(tmp_path))
        conn.row_factory = _dict_factory
        _close = conn.close

        def _close_cleanup():
            _close()
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass

        conn.close = _close_cleanup  # type: ignore[method-assign]
        return conn
    except Exception:
        return None


def read_only_connect(filepath: Path) -> sqlite3.Connection:
    """标准只读连接，带错误处理。"""
    conn = sqlite3.connect(f"file:{filepath.resolve()}?mode=ro", uri=True)
    conn.row_factory = _dict_factory
    return conn
