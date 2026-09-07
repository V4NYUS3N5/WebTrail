"""
取证报告生成模块
输出结构化 JSON/CSV 报告，确保可复现性与可审计性。
"""
from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from core.extractor import ArtifactRecord
from core.hasher import file_hash
from utils.url_utils import extract_domain_from_record

logger = logging.getLogger(__name__)


def write_report(records: list[ArtifactRecord], profile: dict,
                 evidence_hashes: dict, output_dir: Path) -> Path:
    """生成完整取证报告到指定目录，返回报告目录路径。"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = output_dir / f"report_{ts}"
    report_dir.mkdir(parents=True, exist_ok=True)

    _write_json(records, profile, evidence_hashes, report_dir)
    _write_csv(records, report_dir)
    _write_timeline_csv(records, report_dir)

    # 对生成的报告做哈希
    report_hashes = {}
    for f in sorted(report_dir.rglob("*")):
        if f.is_file():
            report_hashes[f.name] = file_hash(f)

    with open(report_dir / "report_checksums.json", "w", encoding="utf-8") as fh:
        json.dump({"generated_at": ts, "files": report_hashes}, fh,
                  ensure_ascii=False, indent=2)

    logger.info("报告已生成: %s", report_dir)
    return report_dir


def _write_json(records: list[ArtifactRecord], profile: dict,
                hashes: dict, report_dir: Path):
    data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_records": len(records),
            "evidence_hashes": hashes,
        },
        "profile": profile,
        "records": [_serialize(r) for r in records],
    }
    path = report_dir / "forensic_report.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    logger.info("  -> %s", path)


def _write_csv(records: list[ArtifactRecord], report_dir: Path):
    path = report_dir / "records.csv"
    if not records:
        Path(path).touch()
        return
    fieldnames = ["browser", "profile", "artifact_type", "timestamp",
                  "url", "title", "domain", "extra"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            data = r.data
            extra = {k: v for k, v in data.items() if k not in ("url", "title", "host")}
            writer.writerow({
                "browser": r.browser,
                "profile": r.profile,
                "artifact_type": r.artifact_type,
                "timestamp": r.timestamp or "",
                "url": data.get("url", "") or data.get("host", ""),
                "title": data.get("title", ""),
                "domain": extract_domain_from_record(data),
                "extra": json.dumps(extra, ensure_ascii=False) if extra else "",
            })
    logger.info("  -> %s", path)


def _write_timeline_csv(records: list[ArtifactRecord], report_dir: Path):
    """生成按时间排序的活动时间线 CSV。"""
    path = report_dir / "timeline.csv"
    events = sorted(
        (r for r in records if r.timestamp),
        key=lambda r: r.timestamp or ""
    )
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "browser", "profile", "type",
                          "domain", "url", "detail"])
        for r in events:
            domain = extract_domain_from_record(r.data)
            url = r.data.get("url", "") or r.data.get("host", "")
            extra = {k: v for k, v in r.data.items() if k not in ("url", "title", "host")}
            detail = "; ".join(f"{k}={v}" for k, v in extra.items()) if extra else ""
            writer.writerow([r.timestamp, r.browser, r.profile, r.artifact_type,
                             domain, url, detail])
    logger.info("  -> %s", path)


def _serialize(r: ArtifactRecord) -> dict[str, Any]:
    return {
        "artifact_type": r.artifact_type,
        "browser": r.browser,
        "timestamp": r.timestamp,
        "profile": r.profile,
        "source_file": r.source_file,
        "data": r.data,
        "extraction_time": r.extraction_time,
        "checksum": r.checksum,
    }
