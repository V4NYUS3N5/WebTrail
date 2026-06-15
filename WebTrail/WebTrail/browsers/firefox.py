"""
Mozilla Firefox 浏览器适配器
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


class FirefoxExtractor(BaseExtractor):
    """Mozilla Firefox 痕迹提取器。"""

    def __init__(self, base_path: Path):
        super().__init__("Firefox", base_path)

    def detect_profiles(self) -> list[tuple[str, Path]]:
        profiles = []
        # Firefox profiles.ini 位于基础路径的父目录
        ini = self.base_path / "profiles.ini"
        if ini.exists():
            # 解析 profiles.ini 获取路径
            import configparser
            cp = configparser.ConfigParser()
            cp.read(str(ini))
            for section in cp.sections():
                if section.startswith("Install"):
                    name = cp.get(section, "Default", fallback=None)
                    if name and (self.base_path / name).exists():
                        profiles.append((name, self.base_path / name))
                    continue
                if cp.get(section, "Path", fallback=None):
                    pname = cp.get(section, "Name", fallback=section)
                    ppath = cp.get(section, "Path")
                    profile_path = self.base_path / ppath if not Path(ppath).is_absolute() else Path(ppath)
                    if profile_path.exists():
                        profiles.append((pname, profile_path))

        # 回退：直接扫描目录
        if not profiles:
            for item in self.base_path.iterdir():
                if item.is_dir() and (item / "places.sqlite").exists():
                    profiles.append((item.name, item))
        return profiles

    def _connect(self, source: Path):
        """连接数据库，处理锁定/磁盘错误。"""
        if not source.exists():
            return None
        return sqlite_utils.safe_connect_with_fallback(source)

    # ------ History ------

    def extract_history(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        source = profile_path / "places.sqlite"
        conn = self._connect(source)
        if not conn:
            return []
        rows = conn.execute(
            "SELECT url, title, visit_count, last_visit_date, description "
            "FROM moz_places WHERE last_visit_date > 0 "
            "ORDER BY last_visit_date DESC"
        ).fetchall()
        conn.close()
        records = []
        for r in rows:
            ts = time_utils.firefox_micros_to_iso(r["last_visit_date"])
            records.append(self._record("history", profile_name, str(source), {
                "url": r["url"], "title": r["title"],
                "visit_count": r["visit_count"],
                "last_visit": ts,
            }, ts))
        return records

    # ------ Cookies ------

    def extract_cookies(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        source = profile_path / "cookies.sqlite"
        conn = self._connect(source)
        if not conn:
            return []
        rows = conn.execute(
            "SELECT host, name, value, creationTime, expiry, lastAccessed, "
            "isSecure, isHttpOnly FROM moz_cookies "
            "ORDER BY lastAccessed DESC"
        ).fetchall()
        conn.close()
        records = []
        for r in rows:
            ts = time_utils.firefox_micros_to_iso(r["lastAccessed"])
            records.append(self._record("cookie", profile_name, str(source), {
                "host": r["host"], "name": r["name"],
                "value_hash": record_hash({"v": r["value"]}),
                "secure": bool(r["isSecure"]),
                "last_access": ts,
            }, ts))
        return records

    # ------ Downloads (also in places.sqlite) ------

    def extract_downloads(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        source = profile_path / "places.sqlite"
        conn = self._connect(source)
        if not conn:
            return []
        # moz_annos.content 存储下载文件路径，place_id 关联 moz_places
        rows = conn.execute(
            "SELECT p.url, a.content, a.dateAdded "
            "FROM moz_annos a "
            "JOIN moz_anno_attributes aa ON a.anno_attribute_id = aa.id "
            "LEFT JOIN moz_places p ON a.place_id = p.id "
            "WHERE aa.name = 'downloads/destinationFileURI'"
        ).fetchall()
        conn.close()
        records = []
        for r in rows:
            ts = time_utils.firefox_micros_to_iso(r["dateAdded"])
            records.append(self._record("download", profile_name, str(source), {
                "download_url": r.get("url", ""),
                "file_path": r.get("content", ""),
                "date_added": ts,
            }, ts))
        return records

    # ------ Bookmarks (also in places.sqlite) ------

    def extract_bookmarks(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        source = profile_path / "places.sqlite"
        conn = self._connect(source)
        if not conn:
            return []
        rows = conn.execute(
            "SELECT b.id, p.url, b.title, b.dateAdded, b.parent "
            "FROM moz_bookmarks b LEFT JOIN moz_places p ON b.fk = p.id "
            "WHERE b.type = 1 AND p.url IS NOT NULL "
            "ORDER BY b.dateAdded DESC"
        ).fetchall()
        conn.close()
        records = []
        for r in rows:
            ts = time_utils.firefox_micros_to_iso(r["dateAdded"])
            records.append(self._record("bookmark", profile_name, str(source), {
                "url": r["url"], "title": r["title"],
                "date_added": ts,
            }, ts))
        return records

    # ------ Logins (logins.json) ------

    def extract_logins(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        source = profile_path / "logins.json"
        if not source.exists():
            return []
        try:
            with open(source, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
        records = []
        for entry in data.get("logins", []):
            ts = time_utils.unix_millis_to_iso(entry.get("timeLastUsed", 0))
            records.append(self._record("login", profile_name, str(source), {
                "url": entry.get("hostname"),
                "username": entry.get("encryptedUsername", "")[:20] + "...",
                "times_used": entry.get("timesUsed", 0),
            }, ts))
        return records

    # ------ Cache ------

    def extract_cache_info(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        source = profile_path / "cache2"
        records = []
        if source.exists():
            records.append(self._record("cache", profile_name, str(source), {
                "type": "Cache2",
                "path": str(source),
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
