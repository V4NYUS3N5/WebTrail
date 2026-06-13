"""
分析报告格式化 — 将 AnalysisResult 渲染为可读文本
"""
from models import AnalysisResult


def format(analysis: AnalysisResult) -> str:
    """格式化为 Markdown 风格纯文本"""
    lines = ["", "=" * 80, "智能分析报告", "=" * 80, ""]

    # ---- 风险概览 ----
    score = analysis.risk_score
    level = analysis.risk_level
    level_icon = {"高风险": "🔴", "中风险": "🟡", "低风险": "🟢"}.get(level, "⚪")
    lines.append(f"  {level_icon} 风险评分: {score}/100  ({level})")
    lines.append("")

    # 逐项归因
    reasons = analysis.risk_reasons
    if reasons:
        lines.append("  ┌─ 风险归因明细 ───────────────────────────────────────┐")
        total_contrib = sum(r[1] for r in reasons)
        for reason, contrib, detail in reasons:
            bar = "█" * max(1, contrib // 2)
            lines.append(f"  │ {bar} +{contrib}分  {reason}")
            lines.append(f"  │    {detail}")
        lines.append("  └────────────────────────────────────────────────────────┘")
        lines.append("")

    # ---- 用户画像 ----
    traits = analysis.traits
    browsers = analysis.browsers
    if traits or browsers:
        lines.append("  ┌─ 行为画像 ──────────────────────────────────────────┐")
        lines.append(f"  │ 浏览器生态: {', '.join(browsers) if browsers else '未知'} "
                     f"(扩展{analysis.extension_count}个)  │")
        for trait in traits:
            lines.append(f"  │ {trait:<53}│")
        lines.append("  └────────────────────────────────────────────────────────┘")
        lines.append("")

    # ---- 搜索意图 ----
    queries = analysis.search_queries
    engine_counts = analysis.search_engine_counts
    if queries:
        lines.append(f"  【搜索行为分析】 ({len(queries)} 条独特搜索词)")
        if engine_counts:
            eng_str = ", ".join(f"{k}:{v}" for k, v in engine_counts.items())
            lines.append(f"    引擎分布: {eng_str}")
        topics = analysis.search_topics
        if topics:
            lines.append("    搜索主题分布:")
            for topic, kws in sorted(topics.items(), key=lambda x: -len(x[1])):
                kws_str = " / ".join(kws[:5])
                lines.append(f"      [{topic}] {kws_str}")
        lines.append("    最近搜索:")
        for q in queries[-15:]:
            topic_tag = f" [{q.get('topic', '')}]" if q.get("topic") != "综合" else ""
            lines.append(f"      {q['time']}  {q['engine']}{topic_tag}  {q['keyword'][:60]}")
        lines.append("")

    # ---- 兴趣分类 ----
    cat_dist = analysis.category_distribution
    if cat_dist:
        lines.append("  【兴趣分类雷达】")
        max_cnt = cat_dist[0][1] if cat_dist else 1
        for cat, cnt in cat_dist[:10]:
            bar_len = int(cnt / max_cnt * 25)
            bar = "█" * bar_len
            lines.append(f"    {cat:<6} {bar} {cnt}")
        lines.append("")

    # ---- 会话重建 ----
    if analysis.session_count:
        lines.append(f"  【浏览会话重建】 (共 {analysis.session_count} 个会话)")
        lines.append(f"    总浏览时长: {analysis.total_browse_min} 分钟")
        lines.append(f"    平均会话: {analysis.avg_session_min} 分钟")
        lines.append(f"    最长会话: {analysis.max_session_min} 分钟")
        lines.append(f"    长会话 (>2h): {analysis.long_sessions} 个")
        lines.append(f"    瞬时会话 (<1min): {analysis.short_sessions} 个")
        sessions = analysis.sessions
        if sessions:
            lines.append("    最近会话:")
            for s in sessions[-5:]:
                doms = ", ".join(s["domains"][:5])
                lines.append(f"      #{s['id']}  {s['start']}  "
                             f"{s['duration_min']}min  {s['page_count']}页  [{doms}...]")
        lines.append("")

    # ---- 浏览速度 ----
    if analysis.avg_gap_sec:
        flag = " ⚠️ 疑似自动化行为" if analysis.automated_suspect else ""
        lines.append(f"  【浏览速度检测】{flag}")
        lines.append(f"    平均间隔: {analysis.avg_gap_sec} 秒")
        lines.append(f"    快速跳转比例: {analysis.burst_ratio}%")
        if analysis.rapid_streaks:
            lines.append(f"    连续快速浏览段: {analysis.rapid_streaks}")
        lines.append("")

    # ---- 高风险URL ----
    high_risk = analysis.high_risk_urls
    if high_risk:
        lines.append(f"  ⚠️ 高风险URL ({len(high_risk)} 条)")
        for u in high_risk[:10]:
            lines.append(f"    {u}")
    else:
        lines.append("  【高风险URL】 未发现")
    lines.append("")

    # ---- 24小时分布 ----
    peak = analysis.peak_hour
    lines.append(f"  【24小时分布】  活跃高峰: {peak}:00" if peak else "  【24小时分布】")
    lines.append(f"    深夜 (00-05): {analysis.late_night_count} 条 "
                 f"({analysis.late_night_ratio}%)")
    for h, cnt, bar in analysis.hour_distribution:
        if cnt > 0:
            lines.append(f"    {h:02d}:00  {bar} ({cnt})")
    lines.append("")

    # ---- Top域名 ----
    top = analysis.top_domains
    if top:
        lines.append(f"  【访问Top域名】 (共 {analysis.total_domains} 个)")
        for i, (domain, cnt) in enumerate(top[:15], 1):
            lines.append(f"    {i:2d}. {domain}  ({cnt}次)")
    lines.append("")

    # ---- 下载风险 ----
    lines.append(f"  【下载风险】 总下载: {analysis.download_total}"
                 f"  可执行文件: {analysis.exe_count}")
    if analysis.download_risky:
        for fn in analysis.download_risky[:10]:
            lines.append(f"    [高风险] {fn}")
    lines.append("")

    # ---- 追踪器 ----
    lines.append(f"  【隐私追踪】 发现 {analysis.tracker_count} 个追踪/广告请求")
    if analysis.tracker_domains:
        for domain, cnt in analysis.tracker_domains[:10]:
            lines.append(f"    {domain} ({cnt}次)")
    lines.extend(["", "=" * 80])

    return "\n".join(lines)
