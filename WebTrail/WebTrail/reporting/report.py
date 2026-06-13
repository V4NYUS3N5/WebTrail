"""
取证报告生成 — 时间线排序 / 可疑标记 / 统计摘要
"""
from typing import List

from config import SUSPICIOUS_KEYWORDS, SUSPICIOUS_DOMAINS
from models import Trace


def _mark_suspicious(traces: List[Trace]) -> List[Trace]:
    for t in traces:
        content = t.content.lower()
        is_sus = any(kw in content for kw in SUSPICIOUS_KEYWORDS)
        is_sus |= any(d in content for d in SUSPICIOUS_DOMAINS)
        t.suspicious = is_sus
    return traces


def _build_summary(traces: List[Trace]) -> str:
    types: dict = {}
    sources: dict = {}
    sus_count = 0
    sus_items: List[str] = []

    for t in traces:
        types[t.type] = types.get(t.type, 0) + 1
        sources[t.source] = sources.get(t.source, 0) + 1
        if t.suspicious:
            sus_count += 1
            sus_items.append(f"  [{t.type}] [{t.source}] {t.time_str}  {t.content}")

    lines = ["", "=" * 80, "统计摘要", "=" * 80, "",
             f"  总痕迹数: {len(traces)}", "",
             "  【按类型统计】"]

    for tp, cnt in sorted(types.items(), key=lambda x: -x[1]):
        lines.append(f"    {tp}: {cnt}")

    lines.append("")
    lines.append("  【按来源统计】")
    for src, cnt in sorted(sources.items(), key=lambda x: -x[1]):
        lines.append(f"    {src}: {cnt}")

    lines.append("")
    if sus_count:
        lines.append(f"  【可疑标记: {sus_count} 条】")
        lines.extend(sus_items)
    else:
        lines.append("  【可疑标记: 0】 未发现明显可疑行为")

    lines.extend(["", "=" * 80])
    return "\n".join(lines)


def generate(traces: List[Trace]) -> str:
    """生成完整取证报告（时间线 + 摘要）"""
    _mark_suspicious(traces)

    timed = sorted(
        [t for t in traces if t.time is not None],
        key=lambda x: x.time, reverse=True,
    )
    untimed = [t for t in traces if t.time is None]

    lines = ["=" * 80, "WebTrail 浏览器痕迹取证报告", "=" * 80, ""]

    if not traces:
        lines.append("未提取到任何痕迹")
        return "\n".join(lines)

    lines.append(f"共 {len(traces)} 条痕迹 "
                 f"({len(timed)} 条带时间戳, {len(untimed)} 条统计信息)")
    lines.extend(["", "-" * 80])

    for t in timed:
        flag = " !!可疑!!" if t.suspicious else ""
        lines.append(f"{t.time_str}  {t.type} [{t.source}]  {t.content}{flag}")

    lines.append("-" * 80)

    if untimed:
        lines.extend(["", "【统计信息】"])
        for t in untimed:
            lines.append(f"  {t.type} [{t.source}]  {t.content}")

    lines.append(_build_summary(traces))
    return "\n".join(lines)
