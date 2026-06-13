"""
分析编排器 — 统一入口，串联所有分析模块
"""
import logging
from typing import Dict, List

from models import Trace, AnalysisResult
from analysis import classifier
from analysis import session
from analysis import velocity
from analysis import profiler
from analysis import risk

_log = logging.getLogger("WebTrail.analysis.engine")


def analyze(traces: List[Trace]) -> AnalysisResult:
    """执行完整分析流水线，返回结构化结果"""
    _log.info("========== 智能分析启动, 输入痕迹 %d 条 ==========", len(traces))

    result = AnalysisResult()

    # 阶段1: 分类
    _log.info(">>> 提取搜索词...")
    search_result = classifier.extract_search_queries(traces)
    _assign_fields(result, search_result)

    _log.info(">>> 域名分类...")
    cat_result = classifier.domain_categories(traces)
    _assign_fields(result, cat_result)

    # 阶段2: 时序分析
    _log.info(">>> 会话重建...")
    _assign_fields(result, session.reconstruct(traces))

    _log.info(">>> 浏览速度检测...")
    _assign_fields(result, velocity.detect(traces))

    # 阶段3: 画像
    _log.info(">>> 用户画像...")
    _assign_fields(result, profiler.build(traces, cat_result, search_result))

    # 阶段4: 统计
    _log.info(">>> Top域名...")
    _assign_fields(result, classifier.top_domains(traces))

    _log.info(">>> 浏览时段...")
    _assign_fields(result, classifier.browsing_hours(traces))

    _log.info(">>> 下载风险...")
    _assign_fields(result, classifier.download_risk(traces))

    _log.info(">>> 隐私追踪...")
    _assign_fields(result, classifier.tracker_privacy(traces))

    # 阶段5: 综合评分
    intermediate = result.to_dict()
    _log.info(">>> 综合风险评分...")
    _assign_fields(result, risk.score(traces, intermediate))

    _log.info("========== 分析完成 ==========")
    return result


def _assign_fields(obj: AnalysisResult, data: Dict):
    for key, value in data.items():
        if hasattr(obj, key):
            setattr(obj, key, value)
