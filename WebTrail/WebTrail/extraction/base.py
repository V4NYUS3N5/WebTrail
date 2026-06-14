"""
提取器抽象基类 — 定义统一接口和公共方法
"""
from abc import ABC, abstractmethod
from typing import List

from models import Trace
from utils import read_sqlite_copy


class BaseExtractor(ABC):
    """所有提取器的抽象基类"""

    @abstractmethod
    def extract(self) -> List[Trace]:
        """提取痕迹，返回 Trace 列表"""
        ...

    @staticmethod
    def _safe_sqlite(db_path: str):
        """打开SQLite副本（调用方负责 conn.close()；若返回 tmp 非空还需 os.remove(tmp)）"""
        return read_sqlite_copy(db_path)
