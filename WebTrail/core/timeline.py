"""
时间线构建模块
将所有浏览器痕迹按时间排序，生成用户活动时间线。
"""
from __future__ import annotations

from collections import defaultdict

from core.extractor import ArtifactRecord
from utils.url_utils import extract_domain_from_record


def build_timeline(records: list[ArtifactRecord]) -> list[dict]:
    """构建带时间戳的全局时间线，按时间升序排列。"""
    events = []
    for rec in records:
        if rec.timestamp is None:
            continue
        events.append({
            "ts":         rec.timestamp,
            "browser":    rec.browser,
            "profile":    rec.profile,
            "type":       rec.artifact_type,
            "data":       rec.data,
        })
    events.sort(key=lambda e: e["ts"])
    return events


def daily_domain_stats(events: list[dict]) -> dict[str, int]:
    """统计域名访问频次。"""
    stats: dict[str, int] = defaultdict(int)
    for ev in events:
        domain = extract_domain_from_record(ev.get("data", {}))
        if domain:
            stats[domain] += 1
    return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
