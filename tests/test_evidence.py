import json
from pathlib import Path

from collect_evidence import mock_items
from src.collectors.aws import AwsEvidenceCollector
from src.reporting import finalize, redact

ROOT = Path(__file__).parents[1]


def test_aws_dry_run_makes_plan_only():
    items = AwsEvidenceCollector(dry_run=True).collect()
    assert len(items) == 3
    assert all(item.status == "PLANNED" for item in items)


def test_redaction_removes_secret_values():
    cleaned, paths = redact({"User": "demo", "SecretAccessKey": "do-not-store", "nested": {"token": "abc"}})
    assert cleaned["SecretAccessKey"] == "[REDACTED]"
    assert cleaned["nested"]["token"] == "[REDACTED]"
    assert len(paths) == 2


def test_finalize_adds_hash_and_redactions():
    item = mock_items(ROOT / "fixtures/mock_evidence.json")[0]
    item.payload["client_secret"] = "fake-secret"
    finalized = finalize(item)
    assert len(finalized.sha256) == 64
    assert finalized.payload["client_secret"] == "[REDACTED]"
    assert "payload.client_secret" in finalized.redactions


def test_mock_fixture_is_synthetic_and_complete():
    items = mock_items(ROOT / "fixtures/mock_evidence.json")
    assert len(items) == 4
    assert {item.provider for item in items} == {"aws", "azure"}
    assert all("Synthetic" in item.summary for item in items)
