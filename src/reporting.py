"""Evidence normalization, redaction, hashing, and report export."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from .models import EvidenceItem

SENSITIVE_KEYS = {"secret", "secretaccesskey", "accesskey", "access_key", "token", "password", "clientsecret", "client_secret", "privatekey", "private_key"}


def redact(value: Any, path: str = "payload") -> tuple[Any, list[str]]:
    redactions: list[str] = []
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", key.lower())
            sensitive_suffixes = ("secret", "token", "password", "privatekey")
            if normalized in SENSITIVE_KEYS or normalized.endswith(sensitive_suffixes):
                result[key] = "[REDACTED]"
                redactions.append(f"{path}.{key}")
            else:
                cleaned, nested = redact(item, f"{path}.{key}")
                result[key] = cleaned
                redactions.extend(nested)
        return result, redactions
    if isinstance(value, list):
        result = []
        for index, item in enumerate(value):
            cleaned, nested = redact(item, f"{path}[{index}]")
            result.append(cleaned)
            redactions.extend(nested)
        return result, redactions
    return value, redactions


def finalize(item: EvidenceItem) -> EvidenceItem:
    cleaned, redactions = redact(item.payload)
    item.payload = cleaned
    item.redactions.extend(redactions)
    canonical = json.dumps(item.as_dict() | {"sha256": ""}, sort_keys=True, separators=(",", ":")).encode()
    item.sha256 = hashlib.sha256(canonical).hexdigest()
    return item


def write_json(items: Iterable[EvidenceItem], path: Path, metadata: dict[str, Any] | None = None) -> None:
    records = [finalize(item).as_dict() for item in items]
    document = {"report_metadata": metadata or {}, "evidence": records}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(items: Iterable[EvidenceItem], path: Path) -> None:
    records = [finalize(item).as_dict() for item in items]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["evidence_id", "provider", "category", "control_area", "source_api", "collected_at", "status", "summary", "sha256", "redactions"])
        writer.writeheader()
        for record in records:
            row = {key: record[key] for key in writer.fieldnames if key in record}
            row["redactions"] = ";".join(record.get("redactions", []))
            writer.writerow(row)
