"""
痕迹提取器基类
定义数字取证提取的标准流程：定位 → 验证 → 提取 → 记录。
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ArtifactRecord:
    """单一痕迹记录的数据结构。"""
    artifact_type: str          # history / cookie / bookmark / download / login
    browser: str                # Chrome / Firefox / Edge
    timestamp: str | None       # ISO 8601
    profile: str                # Default / Profile 1
    source_file: str            # 证据文件路径
    data: dict[str, Any]        # 痕迹具体内容
    extraction_time: str        # 提取时间
    checksum: str = ""          # 记录级别的哈希


@dataclass
class ExtractionResult:
    """一次提取操作的整体结果。"""
    browser: str
    profiles: list[str] = field(default_factory=list)
    records: list[ArtifactRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    file_hashes: dict[str, str] = field(default_factory=dict)


class BaseExtractor(ABC):
    """浏览器痕迹提取器基类。

    确保取证科学性：
    - 对证据文件做哈希校验
    - 只读访问，不修改原始证据
    - 记录提取时间戳
    """

    def __init__(self, browser_name: str, base_path: Path):
        self.browser = browser_name
        self.base_path = base_path
        self.result = ExtractionResult(browser=browser_name)

    # ---------- 子类必须实现 ----------

    @abstractmethod
    def detect_profiles(self) -> list[tuple[str, Path]]:
        """返回 [(profile_name, profile_path), ...]"""
        ...

    @abstractmethod
    def extract_history(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        ...

    @abstractmethod
    def extract_cookies(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        ...

    @abstractmethod
    def extract_downloads(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        ...

    @abstractmethod
    def extract_bookmarks(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        ...

    @abstractmethod
    def extract_logins(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        ...

    @abstractmethod
    def extract_cache_info(self, profile_path: Path, profile_name: str) -> list[ArtifactRecord]:
        ...

    # ---------- 通用提取流程 ----------

    def run(self) -> ExtractionResult:
        """执行完整提取流程。"""
        logger.info("[%s] 开始提取，基础路径: %s", self.browser, self.base_path)

        if not self.base_path.exists():
            err = f"[{self.browser}] 路径不存在: {self.base_path}"
            logger.error(err)
            self.result.errors.append(err)
            return self.result

        profiles = self.detect_profiles()
        if not profiles:
            err = f"[{self.browser}] 未检测到用户配置文件"
            logger.warning(err)
            self.result.errors.append(err)
            return self.result

        self.result.profiles = [p[0] for p in profiles]
        logger.info("[%s] 检测到 %d 个配置: %s", self.browser, len(profiles),
                     [p[0] for p in profiles])

        for profile_name, profile_path in profiles:
            logger.info("[%s/%s] 提取痕迹...", self.browser, profile_name)
            for method in [
                self.extract_history,
                self.extract_cookies,
                self.extract_downloads,
                self.extract_bookmarks,
                self.extract_logins,
                self.extract_cache_info,
            ]:
                try:
                    records = method(profile_path, profile_name)
                    self.result.records.extend(records)
                except Exception as e:
                    err_msg = f"[{self.browser}/{profile_name}] {method.__name__}: {e}"
                    logger.error(err_msg)
                    self.result.errors.append(err_msg)

        logger.info("[%s] 提取完成: %d 条记录, %d 个错误",
                     self.browser, len(self.result.records), len(self.result.errors))
        return self.result
