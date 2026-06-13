"""
用户画像 — 多维度行为特征分析
"""
import re
import logging
from typing import Dict, List

from models import Trace

_log = logging.getLogger("WebTrail.analysis.profiler")


def build(traces: List[Trace], cat_result: Dict, search_result: Dict) -> Dict:
    """根据浏览模式构建多维度用户画像"""
    traits: List[str] = []

    # --- 浏览器多样性 ---
    browsers = set()
    known = {"Chrome", "Edge", "Brave", "Opera", "360浏览器", "Firefox"}
    for t in traces:
        src = t.source.split(" [")[0] if "[" in t.source else t.source
        if src in known:
            browsers.add(src)
    if len(browsers) >= 3:
        traits.append("多浏览器用户（可能多身份/多用途）")
    elif len(browsers) == 2:
        traits.append(f"双浏览器用户 ({' / '.join(sorted(browsers))})")

    # --- 扩展数量 ---
    ext_count = sum(1 for t in traces if t.type == "扩展")
    if ext_count > 15:
        traits.append("扩展重度用户（高度自定义浏览器）")
    elif ext_count > 5:
        traits.append("扩展中度用户")

    # --- 兴趣画像 ---
    cats = dict(cat_result.get("category_distribution", []))
    top_cats = sorted(cats.items(), key=lambda x: -x[1])[:4]
    if top_cats:
        labels = [c[0] for c in top_cats]
        traits.append(f"兴趣倾向: {' > '.join(labels)}")

    # --- 搜索偏好 ---
    search_data = search_result.get("search_engine_counts", {})
    if search_data:
        top_eng = max(search_data, key=search_data.get)
        total_q = sum(search_data.values())
        traits.append(f"搜索引擎偏好: {top_eng} (共{total_q}次搜索)")

    # --- 下载习惯 ---
    dl_total = sum(1 for t in traces if t.type == "下载")
    exe_dl = sum(1 for t in traces if t.type == "下载"
                 and any(t.content.lower().endswith(e) for e in (".exe", ".msi")))
    if dl_total > 30:
        traits.append(f"频繁下载用户 ({dl_total}次)")
    if exe_dl > 10:
        traits.append("大量可执行文件下载（软件安装/测试频繁）")

    # --- 登录凭据 ---
    credential_sites = 0
    for t in traces:
        if t.type == "登录凭据":
            m = re.search(r'(\d+)', str(t.content))
            if m:
                credential_sites += int(m.group(1))
    if credential_sites > 50:
        traits.append("高在线账户数量（可能复用密码风险）")
    elif credential_sites > 20:
        traits.append("中等在线账户数量")

    # --- 安全/黑客兴趣 ---
    sec_domains = sum(cats.get(c, 0) for c in ["安全", "技术"])
    sus_topics = search_result.get("search_topics", {})
    sec_topics = {t: sus_topics[t] for t in ("安全攻防", "翻墙工具", "暗网相关") if t in sus_topics}
    if sec_domains > 10 or sec_topics:
        if sec_topics:
            topics_str = ", ".join(sec_topics.keys())
            traits.append(f"⚠️ 安全/黑客技术关注者 (搜索主题: {topics_str})")

    # --- 深夜活动 ---
    late_night = 0
    total_timed = 0
    for t in traces:
        if t.type == "浏览历史" and t.time:
            total_timed += 1
            if 0 <= t.time.hour <= 5:
                late_night += 1
    if total_timed and late_night / total_timed > 0.3:
        traits.append("重度深夜活跃（作息异常）")

    # --- 无痕/隐私 ---
    has_sessions = any(t.type == "会话" for t in traces)
    if not has_sessions:
        traits.append("可能使用无痕模式（无会话记录）")

    _log.info("用户画像: traits=%s", traits)

    return {
        "traits": traits,
        "browser_count": len(browsers),
        "browsers": sorted(browsers),
        "extension_count": ext_count,
        "download_total": dl_total,
        "credential_sites": credential_sites,
    }
