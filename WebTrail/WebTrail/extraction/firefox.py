"""
Firefox 浏览器提取器
"""
import os
import json
from typing import List

from config import FIREFOX_PROFILES_DIR
from models import Trace
from utils import firefox_time_to_dt
from extraction.base import BaseExtractor


class FirefoxExtractor(BaseExtractor):

    def extract(self) -> List[Trace]:
        results: List[Trace] = []
        profiles_dir = os.path.expanduser(FIREFOX_PROFILES_DIR)
        if not os.path.exists(profiles_dir):
            return results
        for profile_name in os.listdir(profiles_dir):
            profile_path = os.path.join(profiles_dir, profile_name)
            if not os.path.isdir(profile_path):
                continue
            places_db = os.path.join(profile_path, "places.sqlite")
            if os.path.exists(places_db):
                results.extend(self._history(profile_name, places_db))
                results.extend(self._bookmarks(profile_name, places_db))
                results.extend(self._downloads(profile_name, places_db))
            cookies_db = os.path.join(profile_path, "cookies.sqlite")
            if os.path.exists(cookies_db):
                results.extend(self._cookies(profile_name, cookies_db))
            logins_json = os.path.join(profile_path, "logins.json")
            if os.path.exists(logins_json):
                results.extend(self._logins(profile_name, logins_json))
            ext_json = os.path.join(profile_path, "extensions.json")
            if os.path.exists(ext_json):
                results.extend(self._extensions(profile_name, ext_json))
        return results

    # ---- 各维度提取 ----

    def _history(self, profile_name: str, places_db: str) -> List[Trace]:
        results: List[Trace] = []
        conn, tmp = self._safe_sqlite(places_db)
        if not conn:
            return results
        try:
            for url, title, last_visit, visit_count in conn.execute(
                "SELECT url, title, last_visit_date, visit_count FROM moz_places "
                "WHERE last_visit_date > 0 ORDER BY last_visit_date DESC LIMIT 200"
            ):
                dt = firefox_time_to_dt(last_visit)
                results.append(Trace(
                    type="浏览历史", source=f"Firefox [{profile_name}]", time=dt,
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

    def _bookmarks(self, profile_name: str, places_db: str) -> List[Trace]:
        results: List[Trace] = []
        conn, tmp = self._safe_sqlite(places_db)
        if not conn:
            return results
        try:
            for title, url, date_added in conn.execute(
                "SELECT b.title, p.url, b.dateAdded "
                "FROM moz_bookmarks b JOIN moz_places p ON b.fk = p.id "
                "WHERE b.type = 1 AND b.title IS NOT NULL "
                "ORDER BY b.dateAdded DESC LIMIT 100"
            ):
                dt = firefox_time_to_dt(date_added)
                results.append(Trace(
                    type="书签", source=f"Firefox [{profile_name}]", time=dt,
                    time_str=dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "",
                    content=(title or url)[:80],
                ))
        except Exception:
            pass
        finally:
            conn.close()
            try: os.remove(tmp)
            except OSError: pass
        return results

    def _downloads(self, profile_name: str, places_db: str) -> List[Trace]:
        results: List[Trace] = []
        conn, tmp = self._safe_sqlite(places_db)
        if not conn:
            return results
        try:
            for source_url, date_added in conn.execute(
                "SELECT p.url, a.dateAdded "
                "FROM moz_annos a JOIN moz_places p ON a.place_id = p.id "
                "WHERE a.anno_attribute_id = ("
                "  SELECT id FROM moz_anno_attributes WHERE name='downloads/destinationFileURI'"
                ") ORDER BY a.dateAdded DESC LIMIT 50"
            ):
                dt = firefox_time_to_dt(date_added)
                results.append(Trace(
                    type="下载", source=f"Firefox [{profile_name}]", time=dt,
                    time_str=dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "",
                    content=source_url[:80],
                ))
        except Exception:
            pass
        finally:
            conn.close()
            try: os.remove(tmp)
            except OSError: pass
        return results

    def _cookies(self, profile_name: str, cookies_db: str) -> List[Trace]:
        results: List[Trace] = []
        conn, tmp = self._safe_sqlite(cookies_db)
        if not conn:
            return results
        try:
            for host, cnt in conn.execute(
                "SELECT host, COUNT(*) FROM moz_cookies GROUP BY host ORDER BY 2 DESC LIMIT 50"
            ):
                results.append(Trace(
                    type="Cookie", source=f"Firefox [{profile_name}]",
                    content=f"{host} ({cnt}条)",
                ))
        except Exception:
            pass
        finally:
            conn.close()
            try: os.remove(tmp)
            except OSError: pass
        return results

    def _logins(self, profile_name: str, logins_json: str) -> List[Trace]:
        results: List[Trace] = []
        try:
            with open(logins_json, 'r', encoding='utf-8') as f:
                logins = json.load(f).get('logins', [])
            counts: dict = {}
            for l in logins:
                h = l.get('hostname', '')
                counts[h] = counts.get(h, 0) + 1
            for host, cnt in sorted(counts.items(), key=lambda x: -x[1])[:30]:
                results.append(Trace(
                    type="登录凭据", source=f"Firefox [{profile_name}]",
                    content=f"{host} ({cnt}条)",
                ))
        except Exception:
            pass
        return results

    def _extensions(self, profile_name: str, ext_json: str) -> List[Trace]:
        results: List[Trace] = []
        try:
            with open(ext_json, 'r', encoding='utf-8') as f:
                addons = json.load(f).get('addons', [])
            for a in addons[:30]:
                if a.get('active'):
                    name = a.get('defaultLocale', {}).get('name', a.get('id', ''))
                    results.append(Trace(
                        type="扩展", source=f"Firefox [{profile_name}]",
                        content=name,
                    ))
        except Exception:
            pass
        return results
