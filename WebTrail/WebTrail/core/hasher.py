"""
取证哈希模块
对证据文件计算完整性哈希，确保链式保管要求。
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import config

logger = logging.getLogger(__name__)

BUFFER_SIZE = 64 * 1024  # 64 KB


def file_hash(filepath: Path, algorithm: str | None = None) -> str:
    """计算单个文件的哈希值。"""
    algo = algorithm or config.HASH_ALGORITHM
    h = hashlib.new(algo)
    with open(filepath, "rb") as f:
        while chunk := f.read(BUFFER_SIZE):
            h.update(chunk)
    return h.hexdigest()


def hash_evidence_files(file_map: dict[str, Path]) -> dict[str, str]:
    """对证据文件批量计算哈希。返回 {文件名: 哈希}。"""
    hashes = {}
    for label, path in file_map.items():
        if path.exists():
            try:
                hashes[label] = file_hash(path)
                logger.info("  [HASH] %s: %s", label, hashes[label])
            except OSError as e:
                logger.error("  [HASH-ERR] %s: %s", path, e)
    return hashes


def record_hash(record: dict) -> str:
    """对单条提取记录计算哈希，用于完整性校验。"""
    payload = json.dumps(record, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.new(config.HASH_ALGORITHM, payload).hexdigest()
