"""Read-only Azure evidence collector.

Live collection is intentionally explicit. The default CLI path is dry-run or
mock, so no Azure credentials are required to review the repository.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from ..models import EvidenceItem


class AzureEvidenceCollector:
    provider = "azure"

    def __init__(self, credential: Any = None, subscription_id: str | None = None, resource_client: Any = None, monitor_client: Any = None, dry_run: bool = True):
        self.credential = credential
        self.subscription_id = subscription_id
        self.resource_client = resource_client
        self.monitor_client = monitor_client
        self.dry_run = dry_run

    def collect(self) -> list[EvidenceItem]:
        if self.dry_run:
            return self.plan()
        if not self.subscription_id or not self.credential:
            raise RuntimeError("Azure credential and subscription_id are required for live collection; use --provider mock for demonstrations.")
        self._ensure_clients()
        return [self.activity_log_summary(), self.diagnostic_settings_summary()]

    def plan(self) -> list[EvidenceItem]:
        return [
            EvidenceItem.create("AZ-ACT-001", "azure", "logging", "CC7.2", "Microsoft.Insights/activityLogs", "PLANNED", "Azure Activity Log collection planned for the selected subscription; no API call made in dry-run mode."),
            EvidenceItem.create("AZ-LOG-001", "azure", "logging", "CC7.2", "Microsoft.Insights/diagnosticSettings", "PLANNED", "Diagnostic settings inventory planned; no API call made in dry-run mode."),
        ]

    def _ensure_clients(self) -> None:
        if self.resource_client is not None and self.monitor_client is not None:
            return
        try:
            from azure.mgmt.monitor import MonitorManagementClient
            from azure.mgmt.resource import ResourceManagementClient
        except ImportError as exc:
            raise RuntimeError("azure-identity and Azure management SDK packages are required for live collection.") from exc
        self.resource_client = ResourceManagementClient(self.credential, self.subscription_id)
        self.monitor_client = MonitorManagementClient(self.credential, self.subscription_id)

    def activity_log_summary(self) -> EvidenceItem:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=7)
        filter_value = f"eventTimestamp ge '{start.isoformat()}' and eventTimestamp le '{end.isoformat()}'"
        events = list(self.monitor_client.activity_logs.list(filter=filter_value))
        status_counts: dict[str, int] = {}
        for event in events:
            status = getattr(getattr(event, "status", None), "value", None) or "unknown"
            status_counts[status] = status_counts.get(status, 0) + 1
        return EvidenceItem.create("AZ-ACT-001", "azure", "logging", "CC7.2", "Microsoft.Insights/activityLogs", "COLLECTED", f"Azure Activity Log summary collected for a seven-day window with {len(events)} events.", {"window_start": start.isoformat(), "window_end": end.isoformat(), "event_count": len(events), "status_counts": status_counts})

    def diagnostic_settings_summary(self) -> EvidenceItem:
        settings = list(self.monitor_client.diagnostic_settings.list())
        return EvidenceItem.create("AZ-LOG-001", "azure", "logging", "CC7.2", "Microsoft.Insights/diagnosticSettings", "COLLECTED", f"Diagnostic settings inventory collected with {len(settings)} entries.", {"setting_count": len(settings), "categories": sorted({str(getattr(setting, "name", "unknown")) for setting in settings})})
