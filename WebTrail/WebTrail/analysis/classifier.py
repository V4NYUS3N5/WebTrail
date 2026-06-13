"""
搜索词提取 & 域名分类
"""
import re
import logging
from collections import Counter, defaultdict
from typing import Dict, List
from urllib.parse import urlparse, parse_qs, unquote

from config import (
    SEARCH_ENGINE_PATTERNS, SEARCH_TOPIC_RULES,
    DOMAIN_CATEGORY_RULES, TRACKER_DOMAINS,
    SUS_DOWNLOAD_EXTENSIONS, EXECUTABLE_EXTENSIONS,
)
from models import Trace

_log = logging.getLogger("WebTrail.analysis.classifier")


def extract_url(content: str) -> str | None:
    m = re.search(r'https?://\S+', content)
    return m.group(0).rstrip(')') if m else None


def extract_domain(url: str | None) -> str | None:
    if not url or "://" not in url:
        return None
    try:
        host = urlparse(url).hostname
        return host[4:] if host and host.startswith("www.") else host
    except Exception:
        return None


def classify_search_topic(keyword: str) -> str:
    kw = keyword.lower()
    for pattern, topic in SEARCH_TOPIC_RULES:
        if re.search(pattern, kw):
            return topic
    return "综合"


def extract_search_queries(traces: List[Trace]) -> Dict:
    """从浏览历史URL中提取搜索关键词"""
    queries: List[Dict] = []
    engine_counts = Counter()
    topic_keywords = defaultdict(set)

    for t in traces:
        if t.type != "浏览历史":
            continue
        url = extract_url(t.content)
        if not url:
            continue
        for domain_frag, q_param, engine_name in SEARCH_ENGINE_PATTERNS:
            if domain_frag in url and q_param in url:
                try:
                    parsed = urlparse(url)
                    qs = parse_qs(parsed.query)
                    q_val = qs.get(q_param, [""])[0]
                    if q_val and len(q_val) > 1:
                        keyword = unquote(q_val)[:80]
                        engine_counts[engine_name] += 1
                        topic = classify_search_topic(keyword)
                        topic_keywords[topic].add(keyword)
                        queries.append({
                            "keyword": keyword,
                            "engine": engine_name,
                            "time": t.time_str,
                            "topic": topic,
                        })
                except Exception:
                    pass
                break

    # 去重
    seen = set()
    unique_queries = []
    for q in reversed(queries):
        key = q["keyword"].lower()
        if key not in seen:
            seen.add(key)
            unique_queries.append(q)

    _log.info("搜索词提取: unique=%d, engines=%s",
              len(unique_queries), dict(engine_counts.most_common()))
    return {
        "search_queries": unique_queries[-60:],
        "search_engine_counts": dict(engine_counts.most_common()),
        "search_topics": {k: list(v)[:10] for k, v in topic_keywords.items()},
    }


def domain_categories(traces: List[Trace]) -> Dict:
    """对浏览历史中的域名进行兴趣分类"""
    cat_count = Counter()
    cat_examples = defaultdict(list)
    uncategorized = set()

    for t in traces:
        if t.type != "浏览历史":
            continue
        url = extract_url(t.content)
        if not url:
            continue
        domain = extract_domain(url)
        if not domain:
            continue
        matched = False
        for pattern, cat, label in DOMAIN_CATEGORY_RULES:
            if re.search(pattern, domain, re.IGNORECASE):
                cat_count[cat] += 1
                if len(cat_examples[cat]) < 8 and domain not in cat_examples[cat]:
                    cat_examples[cat].append(domain)
                matched = True
                break
        if not matched:
            uncategorized.add(domain)

    _log.info("域名分类: categories=%s, uncategorized=%d",
              dict(cat_count.most_common(8)), len(uncategorized))
    return {
        "category_distribution": cat_count.most_common(),
        "category_examples": {k: v for k, v in cat_examples.items()},
        "uncategorized_count": len(uncategorized),
    }


def top_domains(traces: List[Trace]) -> Dict:
    domains = []
    for t in traces:
        if t.type == "浏览历史":
            url = extract_url(t.content)
            d = extract_domain(url) if url else None
            if d:
                domains.append(d)
    c = Counter(domains)
    return {"top_domains": c.most_common(20), "total_domains": len(c)}


def browsing_hours(traces: List[Trace]) -> Dict:
    hours = []
    late_night = 0
    total_timed = 0
    for t in traces:
        if t.type == "浏览历史" and t.time:
            total_timed += 1
            h = t.time.hour
            hours.append(h)
            if 0 <= h <= 5:
                late_night += 1
    hd = Counter(hours)
    return {
        "hour_distribution": [
            (h, hd.get(h, 0), "█" * min(hd.get(h, 0), 30)) for h in range(24)
        ],
        "late_night_count": late_night,
        "late_night_ratio": round(late_night / total_timed * 100, 1) if total_timed else 0,
        "peak_hour": hd.most_common(1)[0][0] if hd else None,
    }


def download_risk(traces: List[Trace]) -> Dict:
    risky, exe_cnt, total = [], 0, 0
    for t in traces:
        if t.type != "下载":
            continue
        total += 1
        fn = t.content.split(" ", 1)[0] if t.content else ""
        ext = fn[fn.rfind("."):].lower() if "." in fn else ""
        if ext in SUS_DOWNLOAD_EXTENSIONS:
            risky.append(fn)
        if ext in EXECUTABLE_EXTENSIONS:
            exe_cnt += 1
    return {"download_total": total, "download_risky": risky, "exe_count": exe_cnt}


def tracker_privacy(traces: List[Trace]) -> Dict:
    hits = Counter()
    for t in traces:
        if t.type == "浏览历史":
            url = extract_url(t.content)
            d = extract_domain(url) if url else None
        elif t.type == "Cookie":
            d = t.content.split(" ", 1)[0] if t.content else None
        else:
            continue
        if d:
            for td in TRACKER_DOMAINS:
                if d == td or d.endswith("." + td):
                    hits[td] += 1
    return {"tracker_count": sum(hits.values()), "tracker_domains": hits.most_common(15)}
