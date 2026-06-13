"""
系统级浏览器痕迹提取 (UserAssist / DNS / Prefetch)
"""
import os
import subprocess
import winreg
from datetime import datetime
from typing import List

from config import BROWSER_EXECUTABLES, PREFETCH_BROWSER_PREFIXES, DNS_SKIP_KEYWORDS
from models import Trace
from utils import filetime_to_datetime
from extraction.base import BaseExtractor


class SystemExtractor(BaseExtractor):

    def extract(self) -> List[Trace]:
        results: List[Trace] = []
        results.extend(self._userassist())
        results.extend(self._dns_cache())
        results.extend(self._prefetch())
        return results

    # ---- UserAssist (浏览器启动记录) ----

    @staticmethod
    def _rot13(s: str) -> str:
        return s.translate(str.maketrans(
            "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"))

    def _userassist(self) -> List[Trace]:
        results: List[Trace] = []
        ua_key = (
            r"Software\Microsoft\Windows\CurrentVersion\Explorer"
            r"\UserAssist\{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}\Count"
        )
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ua_key)
            for i in range(winreg.QueryInfoKey(key)[1]):
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                except (OSError, ValueError):
                    continue
                decoded = self._rot13(name)
                if not any(b in decoded.lower() for b in BROWSER_EXECUTABLES):
                    continue
                if len(value) < 72:
                    continue
                dt = filetime_to_datetime(value[64:72])
                if dt:
                    results.append(Trace(
                        type="启动记录", source="UserAssist", time=dt,
                        time_str=dt.strftime("%Y-%m-%d %H:%M:%S"),
                        content=decoded,
                    ))
            winreg.CloseKey(key)
        except (OSError, FileNotFoundError):
            pass
        return results

    # ---- DNS 缓存 ----

    def _dns_cache(self) -> List[Trace]:
        results: List[Trace] = []
        seen: set = set()
        try:
            out = subprocess.check_output(
                "ipconfig /displaydns", shell=True, stderr=subprocess.STDOUT
            ).decode('gbk', errors='ignore')
            rec: dict = {}
            for line in out.split('\n'):
                line = line.strip()
                if line.startswith("\u8bb0\u5f55\u540d\u79f0"):
                    rec['name'] = line.split(":", 1)[1].strip()
                elif line.startswith("\u8bb0\u5f55\u7c7b\u578b"):
                    rec['type'] = line.split(":", 1)[1].strip()
                elif line.startswith("\u751f\u5b58\u65f6\u95f4"):
                    domain = rec.get('name', '')
                    if ('.' in domain
                            and not domain.endswith(('.lan', '.local', '.'))
                            and domain not in seen
                            and not any(k in domain.lower() for k in DNS_SKIP_KEYWORDS)):
                        seen.add(domain)
                        results.append(Trace(
                            type="DNS", source="DNS缓存", content=domain,
                        ))
                    rec = {}
        except subprocess.CalledProcessError:
            pass
        return results

    # ---- Prefetch ----

    def _prefetch(self) -> List[Trace]:
        results: List[Trace] = []
        pf_dir = r"C:\Windows\Prefetch"
        if not os.path.exists(pf_dir):
            return results
        try:
            for f in os.listdir(pf_dir):
                if not f.endswith('.pf'):
                    continue
                if not any(b in f.upper() for b in PREFETCH_BROWSER_PREFIXES):
                    continue
                mtime = datetime.fromtimestamp(
                    os.path.getmtime(os.path.join(pf_dir, f)))
                results.append(Trace(
                    type="Prefetch", source="Prefetch", time=mtime,
                    time_str=mtime.strftime("%Y-%m-%d %H:%M:%S"),
                    content=f[:-3],
                ))
        except OSError:
            pass
        return results
