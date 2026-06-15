"""
取证分析管道
定义标准三阶段流程：证据哈希 → 痕迹提取 → 画像分析。
"""

from __future__ import annotations

import logging

import config
from browsers.chrome import ChromeExtractor
from browsers.edge import EdgeExtractor
from browsers.firefox import FirefoxExtractor
from core.extractor import BaseExtractor, ArtifactRecord
from core.hasher import hash_evidence_files
from core.profiler import profile_user

logger = logging.getLogger(__name__)

_EXTRACTOR_MAP = {
    "chrome":  (ChromeExtractor,  config.CHROME_BASE),
    "edge":    (EdgeExtractor,    config.EDGE_BASE),
    "firefox": (FirefoxExtractor, config.FIREFOX_BASE),
}


def create_extractors(selected: str | set | None = None) -> list[BaseExtractor]:
    """根据参数创建提取器列表。None=全部，str=单个，set=多个。"""
    if isinstance(selected, str):
        selected = {selected.lower()}
    elif selected is not None:
        selected = {s.lower() for s in selected}
    extractors = []
    for name, (cls, base) in _EXTRACTOR_MAP.items():
        if selected and name not in selected:
            continue
        if base.exists():
            extractors.append(cls(base))
        else:
            logger.warning("%s 路径不存在: %s", name.title(), base)
    return extractors


def collect_evidence_hashes(extractors: list[BaseExtractor]) -> dict[str, str]:
    """阶段1：收集证据文件哈希（链式保管）。"""
    logger.info("%s", "=" * 50)
    logger.info("阶段 1/3: 证据文件哈希校验")
    logger.info("%s", "=" * 50)
    all_hashes: dict[str, str] = {}
    for ext in extractors:
        for name, path in ext.detect_profiles():
            for f in path.rglob("*"):
                if not f.is_file():
                    continue
                if f.suffix in (".sqlite", ".json"):
                    label = f"{ext.browser}/{name}/{f.name}"
                    all_hashes[label] = hash_evidence_files({label: f}).get(label, "N/A")
    logger.info("证据哈希收集完成: %d 个文件", len(all_hashes))
    return all_hashes


def run_extraction(extractors: list[BaseExtractor]) -> list[ArtifactRecord]:
    """阶段2：执行痕迹提取。"""
    logger.info("%s", "=" * 50)
    logger.info("阶段 2/3: 浏览器痕迹提取")
    logger.info("%s", "=" * 50)
    all_records: list[ArtifactRecord] = []
    for ext in extractors:
        result = ext.run()
        all_records.extend(result.records)
        for e in result.errors[:10]:
            logger.warning("  [ERR] %s", e)
    logger.info("提取完成: 共计 %d 条痕迹记录", len(all_records))
    return all_records


def run_profiling(records: list[ArtifactRecord]) -> dict:
    """阶段3：用户行为画像分析。"""
    logger.info("%s", "=" * 50)
    logger.info("阶段 3/3: 用户画像分析")
    logger.info("%s", "=" * 50)
    return profile_user(records)


def print_summary(profile: dict):
    """终端打印摘要信息。"""
    ov = profile.get("overview", {})
    print("\n" + "=" * 50)
    print("   WebTrail 数字取证报告摘要")
    print("=" * 50)
    print(f"  痕迹总数:      {ov.get('total_records', 0)}")
    print(f"  时间线事件:    {ov.get('timeline_events', 0)}")
    print(f"  时间范围:      {ov.get('time_range_start', 'N/A')} "
          f"~ {ov.get('time_range_end', 'N/A')}")
    print(f"  检测浏览器:    {', '.join(ov.get('browsers', {}).keys())}")
    print(f"  配置数:        {', '.join(ov.get('profiles', []))}")

    top = profile.get("top_domains", [])
    if top:
        print("\n  TOP 10 域名:")
        for item in top[:10]:
            print(f"    {item['domain']:<40s} {item['count']:>5d}")

    risk = profile.get("risk_indicators", {})
    if risk.get("history_cleared"):
        print("\n  [风险] 检测到可能清除过浏览历史")
    sus = risk.get("suspicious_domains", [])
    if sus:
        print(f"\n  [风险] 发现 {len(sus)} 个可疑域名访问")
        for s in sus[:5]:
            print(f"    - {s['keyword']}: {s['url'][:60]}")

    cats = profile.get("top_categories", {})
    if cats:
        print("\n  访问类别分布:")
        for cat, count in cats.items():
            print(f"    {cat:<20s} {count:>5d}")
    print("=" * 50)
