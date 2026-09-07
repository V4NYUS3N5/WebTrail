"""
Chrome / Chromium 浏览器适配器
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from core.extractor import BaseExtractor, ArtifactRecord
from core.hasher import record_hash
from utils import time_utils, sqlite_utils

logger = logging.getLogger(__name__)


class ChromeExtractor(BaseExtractor):
    """Google Chrome 痕迹提取器。"""

    def __init__(self, base_path: Path):
        super().__init__("Chrome", base_path)

    def detect_profiles(self) -> list[tuple[str, Path]]:
        profiles = []
        for item in self.base_path.iterdir():
            if item.is_dir() and (item.name == "Default" or item.name.startswith("Profile ")):
                profiles.append((item.name, item))
        return profiles

    def _connect(self, profile: Path, db_rel: str) -> tuple:
        """连接数据库，返回 (conn, source_path)。处理锁定/磁盘错误。"""
        source = profile / db_rel
        if not source.exists():
            return None, source
        try:
            conn = sqlite_utils.safe_connect_with_fallback(source)
            if conn:
                return conn, source
        except Exception as e:
            logger.warning("  [DB-ERR] %s: %s", source, e)
        return None, source

    # ------ History ------

    def extract_history(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        conn, source = self._connect(profile_path, "History")
        if not conn:
            return []
        rows = conn.execute(
            "SELECT url, title, visit_count, last_visit_time, "
            "typed_count FROM urls ORDER BY last_visit_time DESC"
        ).fetchall()
        conn.close()
        records = []
        for r in rows:
            ts = time_utils.chrome_micros_to_iso(r["last_visit_time"])
            rec = self._record("history", profile_name, str(source), {
                "url": r["url"], "title": r["title"],
                "visit_count": r["visit_count"],
                "last_visit": ts, "typed_count": r.get("typed_count"),
            }, ts)
            records.append(rec)
        return records

    # ------ Cookies ------

    def extract_cookies(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        conn, source = self._connect(profile_path, "Network/Cookies")
        if not conn:
            return []
        rows = conn.execute(
            "SELECT host_key, name, value, creation_utc, expires_utc, "
            "last_access_utc, has_expires, is_secure, is_httponly, is_persistent "
            "FROM cookies ORDER BY last_access_utc DESC"
        ).fetchall()
        conn.close()
        records = []
        for r in rows:
            ts = time_utils.chrome_micros_to_iso(r["last_access_utc"])
            records.append(self._record("cookie", profile_name, str(source), {
                "host": r["host_key"], "name": r["name"],
                "value_hash": record_hash({"v": r["value"]}),
                "secure": bool(r["is_secure"]),
                "persistent": bool(r.get("is_persistent", 0)),
                "last_access": ts,
            }, ts))
        return records

    # ------ Downloads ------

    def extract_downloads(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        conn, source = self._connect(profile_path, "History")
        if not conn:
            return []
        rows = conn.execute(
            "SELECT target_path, tab_url, referrer, start_time, end_time, "
            "total_bytes, received_bytes, state FROM downloads "
            "ORDER BY start_time DESC"
        ).fetchall()
        conn.close()
        records = []
        for r in rows:
            ts = time_utils.chrome_micros_to_iso(r["start_time"])
            records.append(self._record("download", profile_name, str(source), {
                "file_path": r["target_path"], "source_url": r["tab_url"],
                "referrer": r.get("referrer"),
                "size_total": r.get("total_bytes"),
                "size_received": r.get("received_bytes"),
                "state": r.get("state"),
                "start_time": ts,
            }, ts))
        return records

    # ------ Bookmarks (JSON) ------

    def extract_bookmarks(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        source = profile_path / "Bookmarks"
        if not source.exists():
            return []
        try:
            with open(source, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return []
        records = []
        roots = data.get("roots", {})
        for folder_name, folder in roots.items():
            self._parse_bookmark_node(folder, folder_name, profile_name, str(source), records)
        return records

    def _parse_bookmark_node(self, node: dict, folder: str,
                              profile_name: str, source: str,
                              records: list[ArtifactRecord]):
        if node.get("type") == "url":
            ts = time_utils.chrome_micros_to_iso(int(node.get("date_added", 0)))
            records.append(self._record("bookmark", profile_name, source, {
                "url": node.get("url"), "title": node.get("name"),
                "folder": folder, "date_added": ts,
            }, ts))
        children = node.get("children", [])
        for child in children:
            self._parse_bookmark_node(child, folder, profile_name, source, records)

    # ------ Logins ------

    def extract_logins(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        conn, source = self._connect(profile_path, "Login Data")
        if not conn:
            return []
        rows = conn.execute(
            "SELECT origin_url, username_value, date_created, "
            "date_last_used, times_used, blacklisted_by_user "
            "FROM logins ORDER BY date_last_used DESC"
        ).fetchall()
        conn.close()
        records = []
        for r in rows:
            ts = time_utils.chrome_micros_to_iso(r["date_last_used"])
            records.append(self._record("login", profile_name, str(source), {
                "url": r["origin_url"], "username": r["username_value"],
                "times_used": r.get("times_used", 0),
                "blacklisted": bool(r.get("blacklisted_by_user", 0)),
                "last_used": ts,
            }, ts))
        return records

    # ------ Cache Info (HSTS / WebCache) ------

    def extract_cache_info(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        records = []
        # 尝试读取 HSTS TransportSecurity（可能是 SQLite 或 JSON）
        source = profile_path / "Network" / "TransportSecurity"
        if source.is_file():
            try:
                conn = sqlite_utils.safe_connect_with_fallback(source)
                if conn:
                    rows = conn.execute("SELECT host, created, expiry FROM transport_security_state").fetchall()
                    conn.close()
                    for r in rows:
                        ts = time_utils.unix_millis_to_iso(r.get("created", 0))
                        records.append(self._record("cache", profile_name, str(source), {
                            "host": r["host"], "type": "HSTS",
                            "created": ts,
                        }, ts))
            except Exception:
                pass

        # 读取 Cache 元信息
        cache_dir = profile_path / "Cache" / "Cache_Data"
        if cache_dir.is_dir():
            file_count = len(list(cache_dir.rglob("*")))
            if file_count > 0:
                records.append(self._record("cache", profile_name, str(cache_dir), {
                    "type": "Cache_Data",
                    "file_count": file_count,
                }, None))
        return records

    # ------ helper ------

    def _record(self, atype: str, profile: str, source: str,
                data: dict, ts: str | None) -> ArtifactRecord:
        rec = ArtifactRecord(
            artifact_type=atype, browser=self.browser,
            timestamp=ts, profile=profile, source_file=source,
            data=data, extraction_time=datetime.now(timezone.utc).isoformat(),
        )
        rec.checksum = record_hash(rec.data)
        return rec
