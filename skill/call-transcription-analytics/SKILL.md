---
name: call-transcription-analytics
description: Install, validate, operate, and query the private Bitrix24 call transcription pipeline built with n8n, local faster-whisper, and BigQuery. Use when a user provides server access or credential-file paths, asks where to install the pipeline, wants deployment diagnostics, or requests transcript analysis from the calls table.
---

# Call Transcription Analytics

Support two modes: installation and read-only analysis. Establish the mode from the request and avoid loading unrelated references.

## Safety Invariants

- Accept credentials as local filesystem paths, environment-variable names, or secret-manager references. Ask the user to move a pasted secret into a protected file before continuing.
- Never echo secret values, put them in commands, commit them, or write them into workflow JSON or reports.
- Treat SSH access, Bitrix webhooks, BigQuery service-account JSON, n8n encryption keys, and internal API tokens as sensitive.
- Do not delete Bitrix recordings. The standard pipeline keeps audio only in a temporary file during transcription.
- Keep BigQuery writes idempotent by `activity_id`.
- Use synthetic webhook fixtures for testing unless the user explicitly authorizes a real call.
- Treat installation, workflow activation, firewall changes, DNS changes, and schema creation as mutations. Explain the exact target first and get explicit authorization immediately before the mutation if it was not already requested.

## Installation Mode

Read [installation.md](references/installation.md) before planning or changing infrastructure.

1. Locate the package root. If the user installed this skill separately, ask for the package path containing `deploy/docker-compose.yml`.
2. Inventory only the existence, permissions, account identity, scopes, and target IDs of supplied credentials. Redact all values in output.
3. Inspect the proposed host when SSH access is available: OS, architecture, CPU, RAM, free disk, Docker, Compose, open ports, DNS, and TLS termination.
4. Recommend a deployment target and explain why. Prefer `/opt/call-transcription-agent` on a dedicated Ubuntu host; use another path when the host's layout clearly requires it.
   If no host exists, use current provider information to compare suitable regions and instances against expected call volume, latency, and data-residency requirements. Separate infrastructure price from transcription capacity assumptions.
5. Produce a preflight report with `ready`, `warning`, and `blocked` findings. Do not begin a partial deployment with unresolved blockers.
6. After authorization, copy only the release package, create runtime secrets outside version control, initialize BigQuery, import the inactive workflow, test with a synthetic request, and then ask before activation if activation was not included in the request.
7. Report versions, paths, public webhook URL, health status, schema/table target, workflow activation state, and any remaining manual Bitrix step. Never include secret values.

## Analysis Mode

Read [schema.md](references/schema.md) before querying. Use `scripts/query_calls.py` instead of constructing shell commands from free-form user text.

- Resolve human language such as manager, stage, contact, deal, and date range into supported filters. If only IDs are stored, state that name resolution requires customer reference tables.
- Query the minimum date range and columns needed.
- Base conclusions on transcript evidence and distinguish observed facts from interpretation.
- For communication-quality reviews, read [analysis-rubric.md](references/analysis-rubric.md).
- Do not claim to have listened to audio when only transcript text was queried.

## Failure Handling

Stop and explain the exact blocker when access, scope, disk, memory, DNS, TLS, or a required target ID is missing. Preserve existing n8n and BigQuery state. Do not replace production workflows or tables merely because a smoke test fails.
