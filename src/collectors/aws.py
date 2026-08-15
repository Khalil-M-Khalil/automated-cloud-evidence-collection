"""Read-only AWS evidence collector.

The collector never mutates cloud resources. It requires boto3 only when used
against AWS; tests and dry-run demonstrations do not need cloud credentials.
"""
from __future__ import annotations

from typing import Any

from ..models import EvidenceItem


class AwsEvidenceCollector:
    provider = "aws"

    def __init__(self, session: Any = None, dry_run: bool = True):
        self.dry_run = dry_run
        self._boto3 = None
        if session is not None:
            self.session = session
        else:
            try:
                import boto3
                self._boto3 = boto3
                self.session = boto3.Session()
            except ImportError:
                self.session = None

    def collect(self) -> list[EvidenceItem]:
        if self.dry_run:
            return self.plan()
        if self.session is None:
            raise RuntimeError("boto3 is required for live AWS collection; use --provider mock for demonstrations.")
        return [self.credential_report(), self.account_summary(), *self.cloudtrail_configuration()]

    def plan(self) -> list[EvidenceItem]:
        return [
            EvidenceItem.create("AWS-IAM-001", "aws", "identity", "CC6.1", "iam:GenerateCredentialReport + iam:GetCredentialReport", "PLANNED", "IAM credential report collection planned; no API call made in dry-run mode."),
            EvidenceItem.create("AWS-IAM-002", "aws", "identity", "CC6.1", "iam:GetAccountSummary", "PLANNED", "IAM account summary collection planned; no API call made in dry-run mode."),
            EvidenceItem.create("AWS-LOG-001", "aws", "logging", "CC7.2", "cloudtrail:DescribeTrails + cloudtrail:GetTrailStatus", "PLANNED", "CloudTrail trail and status collection planned; no API call made in dry-run mode."),
        ]

    def credential_report(self) -> EvidenceItem:
        iam = self.session.client("iam")
        iam.generate_credential_report()
        report = iam.get_credential_report()
        content = report["Content"].decode("utf-8") if isinstance(report["Content"], bytes) else str(report["Content"])
        rows = content.splitlines()
        return EvidenceItem.create("AWS-IAM-001", "aws", "identity", "CC6.1", "iam:GetCredentialReport", "COLLECTED", f"IAM credential report contains {max(len(rows) - 1, 0)} user rows.", {"headers": rows[0].split(",") if rows else [], "row_count": max(len(rows) - 1, 0), "generated_at": report.get("GeneratedTime").isoformat() if report.get("GeneratedTime") else None})

    def account_summary(self) -> EvidenceItem:
        summary = self.session.client("iam").get_account_summary()
        return EvidenceItem.create("AWS-IAM-002", "aws", "identity", "CC6.1", "iam:GetAccountSummary", "COLLECTED", "IAM account summary collected.", {"summary_map": summary.get("SummaryMap", {})})

    def cloudtrail_configuration(self) -> list[EvidenceItem]:
        client = self.session.client("cloudtrail")
        trails = client.describe_trails(includeShadowTrails=False).get("trailList", [])
        results = []
        for trail in trails:
            name = trail.get("Name", "unnamed")
            status = client.get_trail_status(Name=name)
            results.append(EvidenceItem.create(f"AWS-LOG-{len(results) + 1:03d}", "aws", "logging", "CC7.2", "cloudtrail:DescribeTrails + cloudtrail:GetTrailStatus", "COLLECTED", f"CloudTrail trail {name} configuration and delivery status collected.", {"name": name, "home_region": trail.get("HomeRegion"), "is_multi_region": trail.get("IsMultiRegionTrail"), "log_file_validation_enabled": trail.get("LogFileValidationEnabled"), "latest_delivery_time": status.get("LatestDeliveryTime").isoformat() if status.get("LatestDeliveryTime") else None, "is_logging": status.get("IsLogging")}))
        if not results:
            results.append(EvidenceItem.create("AWS-LOG-000", "aws", "logging", "CC7.2", "cloudtrail:DescribeTrails", "COLLECTED", "No CloudTrail trails were returned for the selected account and session.", {"trail_count": 0}))
        return results
