"""
数据模型 — 类型安全、可序列化的取证实体
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass(slots=True)
class Trace:
    """单条取证痕迹"""
    type: str                    # 浏览历史/书签/下载/Cookie/登录凭据/会话/扩展/DNS/Prefetch/启动记录
    source: str                  # Chrome / Edge / Firefox [xxx] / DNS缓存 / UserAssist / Prefetch
    content: str                 # 展示文本
    time: Optional[datetime] = None
    time_str: str = ""
    suspicious: bool = False     # 是否命中可疑关键词

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "source": self.source,
            "content": self.content,
            "time": self.time_str,
            "suspicious": self.suspicious,
        }


@dataclass
class AnalysisResult:
    """完整分析结果"""
    # ── 风险概览 ──
    risk_score: int = 0
    risk_level: str = "低风险"
    risk_summary: str = ""
    high_risk_urls: List[str] = field(default_factory=list)

    # ── 取证发现清单 (Forensic Findings) ──
    # 每项: {"id": str, "name": str, "axis": str, "kill_chain": int,
    #        "confidence": str, "desc": str, "detail": str, "count": int}
    findings: List[dict] = field(default_factory=list)

    # ── 证据统计 ──
    finding_stats: dict = field(default_factory=dict)
    # {"high_count": int, "medium_count": int, "low_count": int,
    #  "total_count": int, "corroborated_stages": int}

    # ── 分轴得分 ──
    axis_scores: dict = field(default_factory=dict)
    # {"attack_tooling": int, "recon_intel": int,
    #  "credential_persist": int, "anti_forensics": int}

    # ── 杀伤链覆盖 ──
    kill_chain_coverage: dict = field(default_factory=dict)
    # {stage_index: [finding_id_list]}

    # 搜索行为
    search_queries: List[Dict] = field(default_factory=list)
    search_engine_counts: Dict[str, int] = field(default_factory=dict)
    search_topics: Dict[str, List[str]] = field(default_factory=dict)

    # 域名分类
    category_distribution: List[tuple] = field(default_factory=list)
    category_examples: Dict[str, List[str]] = field(default_factory=dict)
    uncategorized_count: int = 0

    # 会话重建
    sessions: List[Dict] = field(default_factory=list)
    session_count: int = 0
    total_browse_min: float = 0
    avg_session_min: float = 0
    max_session_min: float = 0
    long_sessions: int = 0
    short_sessions: int = 0

    # 浏览速度
    avg_gap_sec: float = 0
    burst_ratio: float = 0
    burst_count: int = 0
    rapid_streaks: List[int] = field(default_factory=list)
    rapid_records: List[str] = field(default_factory=list)
    automated_suspect: bool = False

    # 用户画像
    traits: List[str] = field(default_factory=list)
    browser_count: int = 0
    browsers: List[str] = field(default_factory=list)
    extension_count: int = 0
    download_total: int = 0
    credential_sites: int = 0

    # 统计
    top_domains: List[tuple] = field(default_factory=list)
    total_domains: int = 0
    hour_distribution: List[tuple] = field(default_factory=list)
    late_night_count: int = 0
    late_night_ratio: float = 0
    peak_hour: Optional[int] = None
    download_risky: List[str] = field(default_factory=list)
    exe_count: int = 0
    tracker_count: int = 0
    tracker_domains: List[tuple] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """兼容旧 dict 接口"""
        return self.__dict__.copy()
