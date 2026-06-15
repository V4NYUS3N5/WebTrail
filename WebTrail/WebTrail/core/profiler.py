"""
用户画像分析模块
基于提取的浏览器痕迹，对用户行为进行画像分析。
"""
from __future__ import annotations

from collections import Counter, defaultdict

from core.extractor import ArtifactRecord
from core.timeline import build_timeline, daily_domain_stats
from utils.url_utils import classify_url


def profile_user(records: list[ArtifactRecord]) -> dict:
    """对提取的所有痕迹进行综合分析，生成用户画像报告。"""
    if not records:
        return {"error": "无可用记录"}

    events = build_timeline(records)
    if not events:
        return {"error": "无可解析的时间线事件"}

    return {
        "overview":       _overview(records, events),
        "activity_heat":  _activity_heatmap(events),
        "top_domains":    _top_domains(events, top_n=20),
        "top_categories": _categorize(records),
        "behavior_insights": _behavior_insights(events, records),
        "browser_usage":  _browser_usage_stats(records),
        "risk_indicators": _risk_indicators(records),
    }


def _overview(records: list[ArtifactRecord], events: list[dict]) -> dict:
    """总览统计。"""
    browsers = Counter(r.browser for r in records)
    types = Counter(r.artifact_type for r in records)
    timestamps = [e["ts"] for e in events if e.get("ts")]

    return {
        "total_records":    len(records),
        "timeline_events":  len(events),
        "time_range_start": timestamps[0] if timestamps else None,
        "time_range_end":   timestamps[-1] if timestamps else None,
        "browsers":         dict(browsers),
        "artifact_types":   dict(types),
        "profiles":         sorted(set(r.profile for r in records)),
    }


def _activity_heatmap(events: list[dict]) -> dict:
    """按小时统计活跃度热力图数据。"""
    hours = Counter()
    days = Counter()
    for ev in events:
        ts = ev.get("ts", "")
        if len(ts) >= 10:
            days[ts[:10]] += 1
        if len(ts) >= 13:
            hours[ts[11:13]] += 1
    return {
        "by_hour": {h: hours.get(f"{h:02d}", 0) for h in range(24)},
        "by_day": dict(days.most_common(30)),
    }


def _top_domains(events: list[dict], top_n: int = 20) -> list[dict]:
    """排名靠前的访问域名。"""
    stats = daily_domain_stats(events)
    return [{"domain": d, "count": c} for d, c in list(stats.items())[:top_n]]


def _categorize(records: list[ArtifactRecord]) -> dict[str, int]:
    """对浏览记录按 URL 关键词进行粗分类。"""
    counts = Counter()
    for rec in records:
        url = rec.data.get("url", "") or rec.data.get("host_key", "") or ""
        counts[classify_url(url)] += 1
    return dict(counts.most_common())


def _behavior_insights(events: list[dict], records: list[ArtifactRecord]) -> dict:
    """行为洞察。"""
    insights = {}

    # 活跃时段
    hour_counts = Counter(e["ts"][11:13] for e in events if len(e.get("ts", "")) >= 13)
    if hour_counts:
        peak = hour_counts.most_common(1)[0][0]
        insights["peak_hour"] = f"{peak}:00"
        # 夜间活跃判定
        night_hours = sum(v for k, v in hour_counts.items() if k in {str(h).zfill(2) for h in range(0, 6)})
        total = sum(hour_counts.values())
        insights["night_ratio"] = round(night_hours / total, 3) if total > 0 else 0

    # 登录凭证数量
    login_count = sum(1 for r in records if r.artifact_type == "login")
    insights["saved_logins"] = login_count

    # Cookie 数量
    cookie_count = sum(1 for r in records if r.artifact_type == "cookie")
    insights["cookies_count"] = cookie_count

    return insights


def _browser_usage_stats(records: list[ArtifactRecord]) -> dict:
    """各浏览器使用统计。"""
    browsers = defaultdict(list)
    for r in records:
        browsers[r.browser].append(r.artifact_type)
    stats = {}
    for browser, types in browsers.items():
        stats[browser] = {
            "total_records": len(types),
            "breakdown": dict(Counter(types)),
        }
    return stats


def _risk_indicators(records: list[ArtifactRecord]) -> dict:
    """风险指标检测。"""
    indicators = {}

    # 检测隐私模式痕迹 (Firefox 开启隐私模式后 places.sqlite 可能无记录)
    indicators["private_mode_hint"] = len(records) < 10

    # 检测可疑域名关键词
    suspicious_keywords = ["torrent", "crack", "keygen", "warez", "pirate",
                           "darkweb", "onion", "hacktool"]
    suspicious_found = []
    for rec in records:
        url = str(rec.data.get("url", "") or "").lower()
        for kw in suspicious_keywords:
            if kw in url:
                suspicious_found.append({"keyword": kw, "url": url, "browser": rec.browser})

    indicators["suspicious_domains"] = suspicious_found

    # 大量清除痕迹的迹象
    history_count = sum(1 for r in records if r.artifact_type == "history")
    cookie_count = sum(1 for r in records if r.artifact_type == "cookie")
    if history_count == 0 and cookie_count > 0:
        indicators["history_cleared"] = True
    else:
        indicators["history_cleared"] = False

    return indicators
