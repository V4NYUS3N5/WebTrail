"""
浏览速度检测 — 识别自动化/脚本行为
"""
import logging
from typing import Dict, List

from config import (VELOCITY_MIN_SAMPLES, AUTOMATION_BURST_RATIO,
                     AUTOMATION_RAPID_STREAK)
from models import Trace

_log = logging.getLogger("WebTrail.analysis.velocity")


def detect(traces: List[Trace]) -> Dict:
    """检测异常浏览速度——可能为自动化脚本"""
    items = [t for t in traces if t.type == "浏览历史" and t.time]
    if len(items) < VELOCITY_MIN_SAMPLES:
        return {}

    items.sort(key=lambda x: x.time)
    gaps_sec = []
    bursts = 0
    rapid_records = []
    for prev, curr in zip(items, items[1:]):
        gap = (curr.time - prev.time).total_seconds()
        gaps_sec.append(gap)

    avg_gap = sum(gaps_sec) / len(gaps_sec) if gaps_sec else 0
    burst_threshold = max(avg_gap / 5, 1.5)

    for i, gap in enumerate(gaps_sec):
        if 0 <= gap < burst_threshold:
            bursts += 1

    # 连续快速浏览段
    rapid_streaks = []
    streak = 0
    for gap in gaps_sec:
        if 0 <= gap < burst_threshold:
            streak += 1
        else:
            if streak >= 3:
                rapid_streaks.append(streak)
            streak = 0
    if streak >= 3:
        rapid_streaks.append(streak)

    for i, gap in enumerate(gaps_sec[:50]):
        if 0 <= gap < burst_threshold:
            t = items[i]
            rapid_records.append(
                f"  {t.time_str}  {t.content[:60]}  (间隔{gap:.1f}s)")

    burst_ratio = bursts / len(gaps_sec) * 100 if gaps_sec else 0
    is_automated = (burst_ratio > AUTOMATION_BURST_RATIO
                    or (rapid_streaks and max(rapid_streaks) > AUTOMATION_RAPID_STREAK))

    _log.info("浏览速度: items=%d, avg_gap=%.1fs, threshold=%.1fs, bursts=%d, ratio=%.1f%%, "
              "streaks=%s, automated=%s",
              len(items), avg_gap, burst_threshold, bursts, burst_ratio,
              rapid_streaks[:5], is_automated)
    if is_automated:
        _log.warning("疑似自动化行为: burst_ratio=%.1f%%, max_streak=%d",
                     burst_ratio, max(rapid_streaks) if rapid_streaks else 0)

    return {
        "avg_gap_sec": round(avg_gap, 1),
        "burst_ratio": round(burst_ratio, 1),
        "burst_count": bursts,
        "rapid_streaks": rapid_streaks[:10],
        "rapid_records": rapid_records[:15],
        "automated_suspect": is_automated,
    }
