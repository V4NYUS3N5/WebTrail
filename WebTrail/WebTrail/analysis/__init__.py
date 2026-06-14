"""
分析层入口（Layer 2b — 智能分析）

导出 analyze() — 5 阶段分析流水线入口：

  子模块          阶段
  ──────────────────────
  classifier.py   阶段1: 搜索词提取 + 域名分类
  session.py      阶段2: 会话重建
  velocity.py     阶段2: 浏览速度检测
  profiler.py     阶段3: 用户画像
  risk.py         阶段5: 取证风险评估
  engine.py       编排器（主入口）
"""
from .engine import analyze

__all__ = ["analyze"]
