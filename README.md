# Automated Cloud Evidence Collection

A portfolio-grade Python tool that creates a structured evidence inventory from AWS and Azure for audit preparation. The project is deliberately conservative: it defaults to a synthetic fixture or dry-run plan, separates provider adapters from report generation, redacts sensitive-looking fields, and records a SHA-256 fingerprint for each normalized evidence item.

> This tool prepares evidence for review. It does not issue a SOC 2 report, determine control effectiveness, replace an auditor, or guarantee compliance.

## Why this project exists

Audit evidence collection is often repetitive and inconsistent. A control owner may need to demonstrate identity hygiene, logging, and monitoring across more than one cloud provider while preserving collection time, source API, scope, evidence status, and integrity metadata. This repository provides a transparent starting point for that workflow without embedding credentials or requiring a cloud account for review.

The tool collects metadata rather than customer content. It can record the existence and configuration of AWS IAM reports, CloudTrail trails, Azure Activity Log windows, and Azure diagnostic settings. It does not download CloudTrail log bodies, secrets, database contents, or application payloads by default.

## Evidence coverage

| Provider | Evidence item | Primary source | Audit area |
| --- | --- | --- | --- |
| AWS | IAM credential report metadata | `iam:GenerateCredentialReport`, `iam:GetCredentialReport` | Identity and access |
| AWS | IAM account summary | `iam:GetAccountSummary` | Identity and access |
| AWS | CloudTrail trail and delivery status | `cloudtrail:DescribeTrails`, `cloudtrail:GetTrailStatus` | Logging and monitoring |
| Azure | Activity Log summary for a bounded window | `Microsoft.Insights/activityLogs` | Logging and monitoring |
| Azure | Diagnostic settings inventory | `Microsoft.Insights/diagnosticSettings` | Logging and monitoring |

AWS documents that its IAM credential report contains the status of IAM-managed passwords, access keys, MFA devices, and certificates, while also noting that it does not cover every service-specific credential [1]. AWS documents that CloudTrail records IAM and STS API activity and can deliver ongoing trail events to S3 [2]. Microsoft documents that Azure Activity Log records management-plane operations, is available by default, and retains events for 90 days unless exported for longer retention [3].

## Safety model

The default CLI path is safe for demonstrations. `--provider mock` reads a synthetic fixture, and `--provider aws` or `--provider azure` without `--live` emits a planned collection list without calling cloud APIs. Live mode is explicit and remains read-only at the API operation level.

The project does not create, update, delete, rotate, disable, or grant cloud resources. It never writes credentials to a report. The report writer recursively redacts key names associated with secrets, tokens, passwords, private keys, and access keys before hashing the normalized record. Evidence reports are ignored by Git by default because operational reports can contain account metadata and should be stored in an approved evidence repository.

## Installation

Python 3.10 or newer is required. For local testing, the core package has no mandatory cloud SDK dependency:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

For a real AWS collection, use an approved IAM role with the narrow read-only permissions required by the selected collectors. For Azure, use an approved identity with read access to the subscription and monitoring metadata. Follow the organization’s credential and secrets-management rules; do not place access keys in `.env` files committed to Git.

## Quick start with synthetic evidence

```bash
python collect_evidence.py --provider mock
```

The command writes `reports/evidence_report.json` and `reports/evidence_index.csv`. These files are ignored by Git and can be generated locally for review.

## Dry-run plans

```bash
python collect_evidence.py --provider aws
python collect_evidence.py --provider azure
python collect_evidence.py --provider both
```

Dry-run output describes the APIs that would be called but does not contact AWS or Azure.

## Explicit live read-only collection

Live collection must be explicitly enabled:

```bash
python collect_evidence.py --provider aws --live
python collect_evidence.py --provider azure --live --subscription-id "SUBSCRIPTION_ID"
python collect_evidence.py --provider both --live --subscription-id "SUBSCRIPTION_ID"
```

AWS authentication is resolved through the standard boto3 session chain. Azure authentication is intentionally left to the caller’s approved environment and is not hard-coded in this repository. The tool should be run from a controlled evidence-collection environment with an approved time window and an evidence storage location.

## Report design

Every normalized evidence record includes an evidence ID, provider, category, mapped audit area, source API, collection timestamp, status, summary, redaction paths, payload metadata, and SHA-256 fingerprint. The fingerprint is an integrity aid for the generated record; it is not a cryptographic signature of the cloud account or an attestation that the underlying control operated effectively.

A report metadata note explicitly states that the result is not a SOC 2 opinion. AICPA describes SOC as a suite of service offerings in which CPAs provide assurance reports about system-level or entity-level controls [4]. Therefore, the report generated here is a workpaper input for control owners and auditors, not a substitute for the engagement process.

## Testing

The repository includes tests for AWS dry-run behavior, mock fixture loading, secret redaction, and evidence hashing:

```bash
pytest
```

No cloud credentials are required to run the tests.

## Repository structure

```text
.
├── collect_evidence.py
├── fixtures/mock_evidence.json
├── src/
│   ├── models.py
│   ├── reporting.py
│   └── collectors/
│       ├── aws.py
│       └── azure.py
├── tests/test_evidence.py
├── reports/README.md
├── requirements.txt
└── README.md
```

## Limitations and responsible use

The collectors are intentionally narrow and should be extended only after the organization approves new evidence scopes and permissions. Cloud APIs evolve, and the repository does not guarantee compatibility with every account structure, region, tenant, management group, policy, or SDK release. Evidence completeness, retention, chain of custody, population selection, sampling, and control operating effectiveness remain professional responsibilities of the control owner and auditor.

The mock fixture is fictional and contains no customer, account, token, or production data. It exists to make the project demonstrable and testable without cloud access.

## Roadmap

Potential extensions include AWS Organizations evidence, S3 and Azure Storage encryption metadata, evidence manifests signed outside the application, configurable control mappings, bounded log samples with explicit authorization, and CI checks that prevent accidental credential patterns. Each extension should preserve the read-only default and redaction boundary.

## References

[1]: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_getting-report.html "AWS IAM credential reports"

[2]: https://docs.aws.amazon.com/IAM/latest/UserGuide/cloudtrail-integration.html "AWS CloudTrail and IAM/STS API logging"

[3]: https://learn.microsoft.com/en-us/azure/azure-monitor/platform/activity-log "Azure Monitor Activity Log"

[4]: https://www.aicpa-cima.com/resources/landing/system-and-organization-controls-soc-suite-of-services "AICPA System and Organization Controls SOC Suite"

## License

MIT. See `LICENSE` for details.
