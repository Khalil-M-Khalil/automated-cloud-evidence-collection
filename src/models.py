"""Shared evidence models used by cloud collectors and report writers."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class EvidenceItem:
    evidence_id: str
    provider: str
    category: str
    control_area: str
    source_api: str
    collected_at: str
    status: str
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)
    redactions: list[str] = field(default_factory=list)
    sha256: str = ""

    @classmethod
    def create(cls, evidence_id: str, provider: str, category: str, control_area: str, source_api: str, status: str, summary: str, payload: dict[str, Any] | None = None) -> "EvidenceItem":
        return cls(
            evidence_id=evidence_id,
            provider=provider,
            category=category,
            control_area=control_area,
            source_api=source_api,
            collected_at=datetime.now(timezone.utc).isoformat(),
            status=status,
            summary=summary,
            payload=payload or {},
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
