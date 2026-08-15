"""Collect cloud evidence in dry-run, mock, or explicit live mode."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.collectors.aws import AwsEvidenceCollector
from src.collectors.azure import AzureEvidenceCollector
from src.models import EvidenceItem
from src.reporting import write_csv, write_json


def mock_items(path: Path) -> list[EvidenceItem]:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    return [EvidenceItem.create(item["evidence_id"], item["provider"], item["category"], item["control_area"], item["source_api"], item["status"], item["summary"], item.get("payload", {})) for item in fixture["evidence"]]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SOC 2 evidence inventory from AWS, Azure, or safe mock fixtures.")
    parser.add_argument("--provider", choices=["mock", "aws", "azure", "both"], default="mock")
    parser.add_argument("--live", action="store_true", help="Explicitly permit read-only cloud API calls; default is dry-run.")
    parser.add_argument("--subscription-id", help="Azure subscription ID for live mode.")
    parser.add_argument("--fixture", default="fixtures/mock_evidence.json")
    parser.add_argument("--out-dir", default="reports")
    args = parser.parse_args()

    if args.provider == "mock":
        items = mock_items(Path(args.fixture))
    else:
        dry_run = not args.live
        items = []
        if args.provider in {"aws", "both"}:
            items.extend(AwsEvidenceCollector(dry_run=dry_run).collect())
        if args.provider in {"azure", "both"}:
            items.extend(AzureEvidenceCollector(subscription_id=args.subscription_id, dry_run=dry_run).collect())

    out_dir = Path(args.out_dir)
    metadata = {"provider": args.provider, "mode": "live-read-only" if args.live else "dry-run-or-fixture", "source_note": "Evidence metadata is not a SOC 2 opinion and must be reviewed by the control owner and auditor."}
    write_json(items, out_dir / "evidence_report.json", metadata)
    write_csv(items, out_dir / "evidence_index.csv")
    print(json.dumps({"evidence_items": len(items), "output_directory": str(out_dir), "mode": metadata["mode"]}, indent=2))


if __name__ == "__main__":
    main()
