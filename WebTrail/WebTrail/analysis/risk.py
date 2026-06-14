"""
数字取证风险评估引擎
基于 NIST SP 800-86 方法 + 网络杀伤链 (Cyber Kill-Chain) 模型
输出：多轴分项得分 / 证据确信度分级 / 杀伤链覆盖矩阵
"""
import re
import logging
from collections import defaultdict
from typing import Dict, List, Tuple

from config import (
    HIGH_RISK_URL_PATTERNS, FORENSIC_INDICATORS,
    KILL_CHAIN_STAGES, RISK_LEVELS,
    EVIDENCE_WEIGHTS, CORROBORATE_THRESHOLD, CORROBORATE_BONUS,
)
from models import Trace
from analysis.classifier import extract_url

_log = logging.getLogger("WebTrail.analysis.risk")

# ======================== 阶段1: 证据采集 ========================

def _collect_evidence(traces: List[Trace], partial: Dict) -> List[dict]:
    """
    遍历全部痕迹，按 FORENSIC_INDICATORS 定义的取证指标逐项采集证据。
    返回 findings 列表，每项包含证据ID、命中计数、详情。
    """
    evidence: Dict[str, dict] = {
        fid: {"id": fid, "count": 0, "details": []}
        for fid in FORENSIC_INDICATORS
    }

    # -- exploit_search: 搜索结果中安全攻防主题 --
    for q in partial.get("search_queries", []):
        if q.get("topic") == "安全攻防":
            evidence["exploit_search"]["count"] += 1
            evidence["exploit_search"]["details"].append(q["keyword"][:60])

    # -- hacktool_download: 高风险URL中攻击工具类 --
    # -- malware_access: 高风险URL中恶意软件类 --
    # -- phishing_exposure: 高风险URL中欺诈类 --
    # -- pastebin_use: 高风险URL中pastebin类 --
    # -- darkweb_access: 高风险URL中.onion类 --
    # -- encrypted_transfer: 高风险URL中MEGA类 --
    # -- crack_warez_use: 高风险URL中破解/盗版 + 搜索中破解主题 --
    url_category_map = {
        "破解/盗版资源": ("crack_warez_use",),
        "MEGA加密网盘":  ("encrypted_transfer",),
        "Pastebin文本分享": ("pastebin_use",),
        "暗网.onion站点":  ("darkweb_access",),
        "攻击工具":        ("hacktool_download",),
        "恶意软件":        ("malware_access", "hacktool_download"),
        "欺诈相关":        ("phishing_exposure",),
        "可疑免费域名":    ("malware_access",),
    }

    for t in traces:
        if t.type != "浏览历史":
            continue
        url = extract_url(t.content)
        if not url:
            continue
        for pat, desc in HIGH_RISK_URL_PATTERNS:
            if re.search(pat, url, re.IGNORECASE):
                for fid in url_category_map.get(desc, ()):
                    evidence[fid]["count"] += 1
                    if len(evidence[fid]["details"]) < 5:
                        evidence[fid]["details"].append(url[:80])
                break

    # -- crack_warez_use: 搜索词补充 --
    for q in partial.get("search_queries", []):
        if q.get("topic") == "破解/盗版":
            evidence["crack_warez_use"]["count"] += 1
            if q["keyword"] not in evidence["crack_warez_use"]["details"]:
                evidence["crack_warez_use"]["details"].append(q["keyword"][:60])

    # -- piracy_resource: 搜索主题中的资源下载 --
    for q in partial.get("search_queries", []):
        if q.get("topic") == "资源下载":
            evidence["piracy_resource"]["count"] += 1
            if q["keyword"] not in evidence["piracy_resource"]["details"]:
                evidence["piracy_resource"]["details"].append(q["keyword"][:60])

    # -- osint_research: 搜索社工/人肉 --
    for q in partial.get("search_queries", []):
        if q.get("topic") == "社工查询":
            evidence["osint_research"]["count"] += 1
            evidence["osint_research"]["details"].append(q["keyword"][:60])

    # -- security_research: 域名分类中"安全"类 + VirusTotal等 --
    cats = dict(partial.get("category_distribution", []))
    sec_access = cats.get("安全", 0)
    if sec_access > 0:
        evidence["security_research"]["count"] = sec_access
        evidence["security_research"]["details"].append(f"访问安全分析站点 {sec_access} 次")
    # 怀疑降低：如果也检测到hacktool/malware，则security_research不是单纯的研究
    if evidence["hacktool_download"]["count"] > 2 or evidence["malware_access"]["count"] > 0:
        # 安全研究 + 工具下载 → 不再是单纯研究，提升为攻击准备
        evidence["security_research"]["confidence_override"] = "MEDIUM"

    # -- vpn_circumvention: 搜索翻墙主题 --
    for q in partial.get("search_queries", []):
        if q.get("topic") == "翻墙工具":
            evidence["vpn_circumvention"]["count"] += 1
            evidence["vpn_circumvention"]["details"].append(q["keyword"][:60])

    # -- credential_harvest: 登录凭据数量 > 20 --
    credentials = partial.get("credential_sites", 0)
    if credentials > 50:
        evidence["credential_harvest"]["count"] = 1
        evidence["credential_harvest"]["details"].append(f"存储 {credentials} 个站点凭据")
    elif credentials > 20:
        evidence["credential_harvest"]["count"] = 1
        evidence["credential_harvest"]["details"].append(f"存储 {credentials} 个站点凭据（中量）")

    # -- anomalous_logins: 多浏览器 (>2) --
    if partial.get("browser_count", 0) >= 3:
        evidence["anomalous_logins"]["count"] = 1
        evidence["anomalous_logins"]["details"].append(
            f"使用 {partial.get('browser_count')} 个不同浏览器")

    # -- incognito_suspect: 无会话记录 --
    if partial.get("session_count", 1) == 0:
        evidence["incognito_suspect"]["count"] = 1

    # -- multi_browser_masking: 浏览器>2 --
    if partial.get("browser_count", 0) >= 3:
        evidence["multi_browser_masking"]["count"] = 1
        evidence["multi_browser_masking"]["details"].append(
            f"检测到 {partial.get('browser_count')} 个不同浏览器")

    # -- automation_behavior: 速度检测 --
    if partial.get("automated_suspect", False):
        evidence["automation_behavior"]["count"] = 1
        evidence["automation_behavior"]["details"].append(
            f"快速跳转比例 {partial.get('burst_ratio', 0)}%")

    # -- late_night_activity: 深夜占比 > 30% --
    if partial.get("late_night_ratio", 0) > 30:
        evidence["late_night_activity"]["count"] = 1
        evidence["late_night_activity"]["details"].append(
            f"深夜活跃 {partial.get('late_night_count', 0)} 条 ({partial.get('late_night_ratio', 0)}%)"
        )

    # -- piracy_resource: 下载中可执行文件 → 投递威胁 --
    dl_risky = partial.get("download_risky", [])
    if dl_risky:
        evidence["malware_access"]["count"] += len(dl_risky)
        for fn in dl_risky[:3]:
            evidence["malware_access"]["details"].append(fn[:60])

    # 过滤无命中项
    findings = [v for v in evidence.values() if v["count"] > 0]
    return findings


# ======================== 阶段2: 确信度计算 ========================

def _assess_confidence(findings: List[dict]) -> None:
    """根据上下文调整确信度 (override_confidence 机制)"""
    fids = {f["id"] for f in findings}

    # 如果同时检测到 exploit_search + hacktool_download → 提升确信度
    if "exploit_search" in fids and ("hacktool_download" in fids or "malware_access" in fids):
        for f in findings:
            if f["id"] in ("exploit_search",):
                f["confidence_override"] = "HIGH"

    # 如果深夜活跃 + 加密传输 + 自动化 → 联动提升
    trifecta = {"late_night_activity", "encrypted_transfer", "automation_behavior"}
    if trifecta & fids:
        count_overlap = len(trifecta & fids)
        if count_overlap >= 2:
            for f in findings:
                if f["id"] in trifecta:
                    orig = FORENSIC_INDICATORS.get(f["id"], {}).get("confidence", "LOW")
                    promotion = {"LOW": "MEDIUM", "MEDIUM": "HIGH"}.get(orig, orig)
                    f["confidence_override"] = promotion


# ======================== 阶段3: 杀伤链覆盖 ========================

def _map_kill_chain(findings: List[dict]) -> dict:
    """
    将 findings 按杀伤链阶段聚合，检测覆盖完整度。
    返回 {stage_idx: [finding_id_list]} 和 corroboration 计数
    """
    chain_map: Dict[int, list] = defaultdict(list)
    for f in findings:
        fid = f["id"]
        info = FORENSIC_INDICATORS.get(fid)
        if info:
            chain_map[info["kill_chain"]].append(fid)

    # 交叉验证：同一阶段 ≥3 条独立证据 → 加标记
    corroborated = sum(
        1 for ids in chain_map.values() if len(ids) >= CORROBORATE_THRESHOLD
    )
    return dict(chain_map), corroborated


# ======================== 阶段4: 评分开具 ========================

def _compute_score(findings: List[dict],
                    chain_map: dict,
                    corroborated_stages: int) -> Tuple[
    int, str, str, dict, dict]:
    """
    计算总分、等级、分轴得分，返回 (total, level, summary, axis_scores, stats)
    - 主得分：Σ(证据等级权重 × 命中计数，上限=权重 × 2)
    - 交叉验证加成：每阶段交叉验证 +CORROBORATE_BONUS
    - 分轴汇总
    """
    axis_totals: Dict[str, int] = defaultdict(int)
    confidence_counts: Dict[str, int] = defaultdict(int)
    total = 0

    for f in findings:
        fid = f["id"]
        info = FORENSIC_INDICATORS.get(fid, {})
        confidence = f.get("confidence_override") or info.get("confidence", "LOW")
        weight = EVIDENCE_WEIGHTS[confidence]

        # 命中计分：首次命中 = weight，超出1条额外 + min(weight//2, count-1)*2
        cnt = f["count"]
        contrib = weight + min(weight // 2, max(0, cnt - 1) * 2)
        contrib = min(contrib, weight * 2)  # 单指标上限 = weight × 2
        total += contrib

        axis = info.get("axis", "")
        axis_totals[axis] += contrib
        confidence_counts[confidence] += 1
        f["_score_contrib"] = contrib

    # 交叉验证加成
    cross_bonus = corroborated_stages * CORROBORATE_BONUS
    total += cross_bonus

    # 上限
    total = min(total, 100)

    # 等级判定
    level = ""
    summary = ""
    for threshold, lvl, desc in RISK_LEVELS:
        if total >= threshold:
            level = lvl
            summary = desc
            break

    stats = {
        "high_count": confidence_counts.get("HIGH", 0),
        "medium_count": confidence_counts.get("MEDIUM", 0),
        "low_count": confidence_counts.get("LOW", 0),
        "total_count": len(findings),
        "corroborated_stages": corroborated_stages,
        "cross_bonus": cross_bonus,
    }

    return total, level, summary, dict(axis_totals), stats


# ======================== 主入口 ========================

def score(traces: List[Trace], partial: Dict) -> Dict:
    """
    取证风险评估主流程
    阶段1: 证据采集 → 阶段2: 确信度评估 → 阶段3: 杀伤链映射 → 阶段4: 评分开具
    """
    _log.info("========== 取证风险评估开始 ==========")

    # 阶段1: 采集证据
    _log.info(">>> 阶段1: 证据采集...")
    findings = _collect_evidence(traces, partial)
    _log.info("采集到 %d 项证据指标", len(findings))
    for f in findings:
        _log.info("  [%s] %s ×%d (确信度:%s)",
                  f["id"], FORENSIC_INDICATORS.get(f["id"], {}).get("name", "?"),
                  f["count"], FORENSIC_INDICATORS.get(f["id"], {}).get("confidence", "?"))

    if not findings:
        _log.info(">>> 未发现任何取证指标，评估结果为低风险")
        return {
            "risk_score": 0,
            "risk_level": "低风险",
            "risk_summary": "未发现明确威胁指标，行为模式大致正常",
            "high_risk_urls": [],
            "findings": [],
            "finding_stats": {
                "high_count": 0, "medium_count": 0, "low_count": 0,
                "total_count": 0, "corroborated_stages": 0, "cross_bonus": 0,
            },
            "axis_scores": {"attack_tooling": 0, "recon_intel": 0,
                            "credential_persist": 0, "anti_forensics": 0},
            "kill_chain_coverage": {},
        }

    # 阶段2: 确信度评估
    _log.info(">>> 阶段2: 确信度评估...")
    _assess_confidence(findings)
    for f in findings:
        if "confidence_override" in f:
            _log.info("  确信度调整: [%s] → %s", f["id"], f["confidence_override"])

    # 阶段3: 杀伤链覆盖
    _log.info(">>> 阶段3: 杀伤链映射...")
    chain_map, corroborated = _map_kill_chain(findings)
    _log.info("  杀伤链覆盖率: %d/%d 阶段, %d 阶段达到交叉验证",
              len(chain_map), len(KILL_CHAIN_STAGES), corroborated)

    # 阶段4: 评分
    _log.info(">>> 阶段4: 综合评分...")
    total, level, summary, axis_scores, stats = _compute_score(
        findings, chain_map, corroborated,
    )
    _log.info("========== 评估结果: %d/100 (%s) ==========", total, level)
    _log.info("分轴得分: %s", axis_scores)
    _log.info("证据统计: HIGH=%d MEDIUM=%d LOW=%d",
              stats["high_count"], stats["medium_count"], stats["low_count"])

    # 为 output 补充 finding name/desc
    for f in findings:
        info = FORENSIC_INDICATORS.get(f["id"], {})
        f["name"] = info.get("name", f["id"])
        f["desc"] = info.get("desc", "")
        f["confidence"] = f.get("confidence_override") or info.get("confidence", "LOW")
        f["kill_chain"] = info.get("kill_chain", -1)
        f["axis"] = info.get("axis", "")
        f.pop("confidence_override", None)

    # 收集 high_risk_urls（兼容旧格式）
    hr_detail = []
    for t in traces:
        if t.type == "浏览历史":
            url = extract_url(t.content)
            if not url:
                continue
            for pat, desc in HIGH_RISK_URL_PATTERNS:
                if re.search(pat, url, re.IGNORECASE):
                    hr_detail.append(f"  [{t.source}] {url[:90]}  ({desc})")
                    break

    return {
        "risk_score": total,
        "risk_level": level,
        "risk_summary": summary,
        "high_risk_urls": hr_detail,
        "findings": findings,
        "finding_stats": stats,
        "axis_scores": axis_scores,
        "kill_chain_coverage": chain_map,
    }
