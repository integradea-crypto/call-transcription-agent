# Agent-Assisted Installation

Give Codex or Claude this package and install `skill/call-transcription-analytics`. Then provide references to credentials, not the credential contents.

Example request:

```text
Install the Call Transcription Agent from /path/to/call-transcription-agent.
SSH host alias: customer-calls
BigQuery service-account file: /secure/customer-bq.json
Bitrix REST base URL file: /secure/bitrix-rest-url
Public hostname: calls.example.com
BigQuery target: project.dataset.calls, location EU

First inspect the host and credentials without printing secret values. Recommend
the installation path and server changes, then show me the exact deployment plan.
Do not activate the workflow until I approve the plan.
```

The agent should return a preflight report, selected placement, required manual steps, and an explicit mutation plan. Once approved, it can install, validate, and report the resulting webhook and workflow state.

If a secret has already been pasted into chat, rotate it and replace it with a protected file before deployment.
