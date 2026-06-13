"""
会话重建 — 基于时间间隔分组
"""
import logging
from typing import Dict, List

from config import (SESSION_GAP_SECONDS, LONG_SESSION_MINUTES,
                     SHORT_SESSION_MINUTES)
from models import Trace
from analysis.classifier import extract_url, extract_domain

_log = logging.getLogger("WebTrail.analysis.session")


def reconstruct(traces: List[Trace]) -> Dict:
    """>SESSION_GAP_SECONDS 无操作视为新会话"""
    items = [t for t in traces if t.type == "浏览历史" and t.time]
    if not items:
        return {"sessions": [], "session_count": 0}

    items.sort(key=lambda x: x.time)

    sessions = []
    current = [items[0]]
    for prev, curr in zip(items, items[1:]):
        gap = (curr.time - prev.time).total_seconds()
        if gap <= SESSION_GAP_SECONDS:
            current.append(curr)
        else:
            sessions.append(current)
            current = [curr]
    if current:
        sessions.append(current)

    session_summary: List[Dict] = []
    for i, sess in enumerate(sessions, 1):
        start = sess[0].time
        end = sess[-1].time
        duration = (end - start).total_seconds() / 60
        urls = [extract_url(t.content) for t in sess]
        domains = set()
        for u in urls:
            d = extract_domain(u)
            if d:
                domains.add(d)
        session_summary.append({
            "id": i,
            "start": start.strftime("%m-%d %H:%M"),
            "duration_min": round(duration, 1),
            "page_count": len(sess),
            "domain_count": len(domains),
            "domains": list(domains)[:8],
        })

    total_time = sum(s["duration_min"] for s in session_summary)
    long_sessions = sum(1 for s in session_summary if s["duration_min"] > LONG_SESSION_MINUTES)
    short_sessions = sum(1 for s in session_summary if s["duration_min"] < SHORT_SESSION_MINUTES)
    avg = round(total_time / len(sessions), 1) if sessions else 0
    maximum = round(max(s["duration_min"] for s in session_summary), 1) if session_summary else 0

    _log.info("会话重建: sessions=%d, total=%.1fmin, avg=%.1fmin, max=%.1fmin, long=%d, short=%d",
              len(sessions), total_time, avg, maximum, long_sessions, short_sessions)

    return {
        "sessions": session_summary,
        "session_count": len(sessions),
        "total_browse_min": round(total_time, 1),
        "avg_session_min": avg,
        "long_sessions": long_sessions,
        "short_sessions": short_sessions,
        "max_session_min": maximum,
    }
