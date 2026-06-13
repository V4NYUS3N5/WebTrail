"""
Chromium 内核浏览器提取器 (Chrome / Edge / Brave / Opera / 360)
"""
import os
import json
from datetime import datetime
from typing import List

from config import CHROMIUM_BROWSERS
from models import Trace
from utils import chrome_time_to_dt
from extraction.base import BaseExtractor


class ChromiumExtractor(BaseExtractor):

    def extract(self) -> List[Trace]:
        results: List[Trace] = []
        for name, path in CHROMIUM_BROWSERS:
            data_path = os.path.expanduser(path)
            if not os.path.exists(data_path):
                continue
            for profile in self._list_profiles(data_path):
                profile_path = os.path.join(data_path, profile)
                if not os.path.isdir(profile_path):
                    continue
                src = f"{name}" + (f" [{profile}]" if profile != "Default" else "")
                results.extend(self._history(src, profile_path))
                results.extend(self._bookmarks(src, profile_path))
                results.extend(self._downloads(src, profile_path))
                results.extend(self._cookies(src, profile_path))
                results.extend(self._logins(src, profile_path))
                results.extend(self._sessions(src, profile_path))
                results.extend(self._extensions(src, profile_path))
        return results

    # ---- 辅助 ----

    @staticmethod
    def _list_profiles(data_path: str) -> List[str]:
        profiles = ["Default"]
        local_state = os.path.join(data_path, "Local State")
        if not os.path.exists(local_state):
            return profiles
        try:
            with open(local_state, 'r', encoding='utf-8') as f:
                ls = json.load(f)
            keys = ls.get("profile", {}).get("profiles_order", [])
            if keys:
                return keys
        except Exception:
            pass
        return profiles

    # ---- 各维度提取 ----

    def _history(self, browser_name: str, profile_path: str) -> List[Trace]:
        results: List[Trace] = []
        conn, tmp = self._safe_sqlite(os.path.join(profile_path, "History"))
        if not conn:
            return results
        try:
            for url, title, last_visit, visit_count in conn.execute(
                "SELECT url, title, last_visit_time, visit_count FROM urls "
                "ORDER BY last_visit_time DESC LIMIT 200"
            ):
                dt = chrome_time_to_dt(last_visit)
                results.append(Trace(
                    type="浏览历史", source=browser_name, time=dt,
                    time_str=dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "",
                    content=(title or url)[:120],
                ))
        except Exception:
            pass
        finally:
            conn.close()
            try: os.remove(tmp)
            except OSError: pass
        return results

    def _bookmarks(self, browser_name: str, profile_path: str) -> List[Trace]:
        bm_file = os.path.join(profile_path, "Bookmarks")
        if not os.path.exists(bm_file):
            return []
        results: List[Trace] = []
        try:
            with open(bm_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for root in data.get('roots', {}).values():
                if isinstance(root, dict) and 'children' in root:
                    for name, dt in self._walk_bookmarks(root['children']):
                        results.append(Trace(
                            type="书签", source=browser_name, time=dt,
                            time_str=dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "",
                            content=name[:80],
                        ))
        except Exception:
            pass
        return results

    @staticmethod
    def _walk_bookmarks(nodes):
        out = []
        if not isinstance(nodes, list):
            return out
        for n in nodes:
            if n.get('type') == 'url':
                out.append((n.get('name', ''), chrome_time_to_dt(n.get('date_added', 0))))
            if 'children' in n:
                out.extend(ChromiumExtractor._walk_bookmarks(n['children']))
        return out

    def _downloads(self, browser_name: str, profile_path: str) -> List[Trace]:
        results: List[Trace] = []
        conn, tmp = self._safe_sqlite(os.path.join(profile_path, "History"))
        if not conn:
            return results
        try:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='downloads'")
            if cur.fetchone():
                for target_path, start_time, total_bytes, state in conn.execute(
                    "SELECT target_path, start_time, total_bytes, state FROM downloads "
                    "ORDER BY start_time DESC LIMIT 100"
                ):
                    dt = chrome_time_to_dt(start_time)
                    filename = os.path.basename(target_path or "")
                    state_map = {1: "已完成", 2: "已取消", 3: "中断", 4: "中断"}
                    size_mb = f"{total_bytes/1024/1024:.1f}MB" if total_bytes else ""
                    results.append(Trace(
                        type="下载", source=browser_name, time=dt,
                        time_str=dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "",
                        content=f"{filename[:60]} {size_mb} {state_map.get(state, '')}"
                    ))
        except Exception:
            pass
        finally:
            conn.close()
            try: os.remove(tmp)
            except OSError: pass
        return results

    def _cookies(self, browser_name: str, profile_path: str) -> List[Trace]:
        results: List[Trace] = []
        db = os.path.join(profile_path, "Network", "Cookies")
        if not os.path.exists(db):
            db = os.path.join(profile_path, "Cookies")
        conn, tmp = self._safe_sqlite(db)
        if not conn:
            return results
        try:
            for host_key, cnt, last_ts in conn.execute(
                "SELECT host_key, COUNT(*), MAX(last_access_utc) FROM cookies "
                "GROUP BY host_key ORDER BY 2 DESC LIMIT 50"
            ):
                dt = chrome_time_to_dt(last_ts)
                results.append(Trace(
                    type="Cookie", source=browser_name, time=dt,
                    time_str=dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "",
                    content=f"{host_key} ({cnt}条)",
                ))
        except Exception:
            pass
        finally:
            conn.close()
            try: os.remove(tmp)
            except OSError: pass
        return results

    def _logins(self, browser_name: str, profile_path: str) -> List[Trace]:
        results: List[Trace] = []
        conn, tmp = self._safe_sqlite(os.path.join(profile_path, "Login Data"))
        if not conn:
            return results
        try:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='logins'"
            )
            if cur.fetchone():
                for origin_url, cnt in conn.execute(
                    "SELECT origin_url, COUNT(*) FROM logins GROUP BY origin_url "
                    "ORDER BY COUNT(*) DESC LIMIT 30"
                ):
                    results.append(Trace(
                        type="登录凭据", source=browser_name, time=None,
                        content=f"{origin_url[:100]} ({cnt}条)",
                    ))
        except Exception:
            pass
        finally:
            conn.close()
            try: os.remove(tmp)
            except OSError: pass
        return results

    def _sessions(self, browser_name: str, profile_path: str) -> List[Trace]:
        results: List[Trace] = []
        sessions_dir = os.path.join(profile_path, "Sessions")
        if not os.path.exists(sessions_dir):
            return results
        try:
            for fname in os.listdir(sessions_dir):
                if fname.startswith("Session_") or fname.startswith("Tabs_"):
                    fpath = os.path.join(sessions_dir, fname)
                    mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                    results.append(Trace(
                        type="会话", source=browser_name, time=mtime,
                        time_str=mtime.strftime("%Y-%m-%d %H:%M:%S"),
                        content=f"{fname} ({os.path.getsize(fpath)/1024:.1f}KB)",
                    ))
        except OSError:
            pass
        return results

    def _extensions(self, browser_name: str, profile_path: str) -> List[Trace]:
        results: List[Trace] = []
        ext_dir = os.path.join(profile_path, "Extensions")
        if not os.path.exists(ext_dir):
            return results
        try:
            for ext_id in os.listdir(ext_dir)[:30]:
                ext_path = os.path.join(ext_dir, ext_id)
                if not os.path.isdir(ext_path):
                    continue
                name = ext_id[:16]
                for ver in os.listdir(ext_path):
                    mf = os.path.join(ext_path, ver, "manifest.json")
                    if os.path.exists(mf):
                        try:
                            with open(mf, 'r', encoding='utf-8') as f:
                                name = json.load(f).get('name', name)
                            break
                        except Exception:
                            pass
                mtime = datetime.fromtimestamp(os.path.getmtime(ext_path))
                results.append(Trace(
                    type="扩展", source=browser_name, time=mtime,
                    time_str=mtime.strftime("%Y-%m-%d %H:%M:%S"),
                    content=name,
                ))
        except OSError:
            pass
        return results
