"""
风险评分引擎 — 7步加权评分 + 逐项归因
"""
import re
import logging
from typing import Dict, List, Tuple

from config import HIGH_RISK_URL_PATTERNS, RISK_WEIGHTS, SENSITIVE_TOPICS
from models import Trace
from analysis.classifier import extract_url

_log = logging.getLogger("WebTrail.analysis.risk")


def score(traces: List[Trace], partial: Dict) -> Dict:
    """综合风险评分，返回 (score, level, reasons, hr_detail)"""
    reasons: List[Tuple[str, int, str]] = []
    total = 0

    # 1. 可疑关键词
    sus_marked = sum(1 for t in traces if t.suspicious)
    s = min(sus_marked * RISK_WEIGHTS["suspicious_keyword"][1],
            RISK_WEIGHTS["suspicious_keyword"][0])
    total += s
    _log.info("步骤1-可疑关键词: sus_marked=%d, +%d, 累计=%d", sus_marked, s, total)
    if sus_marked:
        _log.debug("  可疑痕迹详情:")
        for t in traces:
            if t.suspicious:
                _log.debug("    [%s] %s  %s", t.type, t.time_str, t.content[:80])
        reasons.append(("可疑关键词标记", s,
                        f"{sus_marked} 条痕迹命中可疑关键词（密码/token/exploit/hack等）"))

    # 2. 高风险URL
    hr = 0
    hr_examples = []
    hr_detail = []
    for t in traces:
        if t.type == "浏览历史":
            url = extract_url(t.content)
            if not url:
                continue
            for pat, desc in HIGH_RISK_URL_PATTERNS:
                if re.search(pat, url, re.IGNORECASE):
                    hr += 1
                    hr_detail.append(f"  [{t.source}] {url[:90]}  ({desc})")
                    _log.debug("  高风险URL: pattern=%s desc=%s url=%s", pat, desc, url[:80])
                    if len(hr_examples) < 3:
                        hr_examples.append(f"{url[:60]} ({desc})")
                    break
    s = min(hr * RISK_WEIGHTS["high_risk_url"][1],
            RISK_WEIGHTS["high_risk_url"][0])
    total += s
    _log.info("步骤2-高风险URL: hr=%d, +%d, 累计=%d", hr, s, total)
    if hr:
        reasons.append(("高风险URL访问", s,
                        f"{hr} 条 — 示例: {'；'.join(hr_examples)}"))

    # 3. 深夜浏览
    ln = partial.get("late_night_ratio", 0)
    late_cnt = partial.get("late_night_count", 0)
    s = 0
    if ln > RISK_WEIGHTS["late_night_high"][1]:
        s = RISK_WEIGHTS["late_night_high"][0]
        total += s
        reasons.append(("深夜浏览", s,
                        f"深夜(00-05)浏览占比 {ln}%，共 {late_cnt} 条——作息异常"))
    elif ln > RISK_WEIGHTS["late_night_medium"][1]:
        s = RISK_WEIGHTS["late_night_medium"][0]
        total += s
        reasons.append(("深夜浏览", s,
                        f"深夜(00-05)浏览占比 {ln}%，共 {late_cnt} 条"))
    _log.info("步骤3-深夜浏览: ratio=%.1f%%, count=%d, +%d, 累计=%d", ln, late_cnt, s, total)

    # 4. 下载风险
    rd = len(partial.get("download_risky", []))
    exe_cnt = partial.get("exe_count", 0)
    dl_total_data = partial.get("download_total", 0)
    s = min(rd * RISK_WEIGHTS["download_risky"][1],
            RISK_WEIGHTS["download_risky"][0])
    total += s
    _log.info("步骤4-下载风险: total=%d, risky=%d, exe=%d, +%d, 累计=%d",
              dl_total_data, rd, exe_cnt, s, total)
    if rd:
        _log.debug("  可疑文件: %s", partial.get("download_risky", [])[:5])
        reasons.append(("可执行文件下载", s,
                        f"{rd} 个可疑文件（含 {exe_cnt} 个 .exe/.msi 等）"))

    # 5. 追踪器
    tc = partial.get("tracker_count", 0)
    s = 0
    if tc > RISK_WEIGHTS["tracker_high"][1]:
        s = RISK_WEIGHTS["tracker_high"][0]
        total += s
        reasons.append(("隐私追踪暴露", s, f"{tc} 个追踪/广告域名请求"))
    elif tc > RISK_WEIGHTS["tracker_medium"][1]:
        s = RISK_WEIGHTS["tracker_medium"][0]
        total += s
        reasons.append(("隐私追踪暴露", s, f"{tc} 个追踪/广告域名请求"))
    _log.info("步骤5-追踪器: count=%d, +%d, 累计=%d", tc, s, total)
    if tc:
        _log.debug("  追踪域名: %s", partial.get("tracker_domains", [])[:5])

    # 6. 敏感搜索
    sq = partial.get("search_queries", [])
    sus_topic_counts: Dict[str, int] = {}
    for q in sq:
        topic = q.get("topic", "")
        if topic in SENSITIVE_TOPICS:
            sus_topic_counts[topic] = sus_topic_counts.get(topic, 0) + 1
    sus_q = sum(sus_topic_counts.values())
    s = min(sus_q * RISK_WEIGHTS["sensitive_search"][1],
            RISK_WEIGHTS["sensitive_search"][0])
    total += s
    _log.info("步骤6-敏感搜索: total_queries=%d, sus=%d, topics=%s, +%d, 累计=%d",
              len(sq), sus_q, dict(sus_topic_counts), s, total)
    if sus_topic_counts:
        topic_str = ", ".join(f"{k}({v}条)" for k, v in sus_topic_counts.items())
        reasons.append(("敏感搜索词", s, topic_str))

    # 7. 自动化嫌疑
    s = 0
    if partial.get("automated_suspect", False):
        s = RISK_WEIGHTS["automation"][0]
        total += s
        burst = partial.get("burst_ratio", 0)
        reasons.append(("疑似自动化行为", s,
                        f"快速跳转比例 {burst}%——不似人工浏览"))
    _log.info("步骤7-自动化: suspect=%s, burst_ratio=%.1f%%, +%d, 累计=%d",
              partial.get("automated_suspect"), partial.get("burst_ratio", 0), s, total)

    total = min(total, 100)
    level = "高风险" if total >= 60 else ("中风险" if total >= 30 else "低风险")
    _log.info("========== 风险评分: %d/100 (%s) ==========", total, level)
    _log.info("归因明细: %s", [(r[0], r[1]) for r in reasons])

    return {
        "risk_score": total,
        "risk_level": level,
        "high_risk_urls": hr_detail,
        "risk_reasons": reasons,
    }
