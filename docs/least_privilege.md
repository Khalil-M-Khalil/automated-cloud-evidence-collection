# Least-privilege collection profile

The collector is designed to run from an approved audit role rather than a personal administrator identity. The exact permission boundary must be reviewed against the organization’s account structure and the evidence period.

| Provider | API action used by this repository | Purpose | Mutating action? |
| --- | --- | --- | --- |
| AWS | `iam:GenerateCredentialReport` | Request IAM credential report generation | No resource mutation; creates a report artifact in IAM |
| AWS | `iam:GetCredentialReport` | Read IAM credential report | No |
| AWS | `iam:GetAccountSummary` | Read account-level IAM summary | No |
| AWS | `cloudtrail:DescribeTrails` | Read trail configuration | No |
| AWS | `cloudtrail:GetTrailStatus` | Read delivery and logging status | No |
| Azure | Activity Log read operation | Read control-plane event metadata | No |
| Azure | Diagnostic settings list operation | Read monitoring configuration metadata | No |

Before a live run, the control owner should confirm the collection role, scope, time window, evidence destination, retention, and approval record. The AWS credential report has its own documented generation frequency and scope limitations, and the Azure Activity Log has a documented 90-day default retention window. Those service behaviors must be reflected in the evidence narrative rather than hidden by the script.

The tool does not request write, delete, update, role-assumption, secret-reading, or data-plane permissions. If a future collector needs any of those capabilities, it should be implemented as a separate module with a separate approval and an explicit command-line opt-in.
