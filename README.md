# Call Transcription Agent

Portable pipeline for receiving completed-call events from Bitrix24, downloading the recording, transcribing it with local `faster-whisper`, storing an idempotent record in BigQuery, and making transcripts available to Codex or Claude through a read-only skill.

This folder is a standalone repository for one shareable agent product. It does not contain other agents from the local `агенты` catalog.

## Included

- n8n workflow with no credentials, customer IDs, domains, or production webhook paths.
- Local transcription and BigQuery storage API.
- Docker Compose deployment for n8n, PostgreSQL, and the call service.
- BigQuery schema and `activity_id` deduplication.
- Shared Codex/Claude skill with an SSH-based read-only query helper.
- Synthetic fixtures, package validation, secret scanning, and a health smoke test.

## Supported V1 Flow

```text
Bitrix24 call event
  -> n8n webhook
  -> Bitrix REST metadata and recording
  -> local faster-whisper large-v3-turbo
  -> BigQuery MERGE by activity_id
  -> read-only agent skill
```

## Start Here

1. Open [Start With Codex Or Claude](START_WITH_AGENT.md).
2. Read [Architecture](docs/architecture.md).
3. Read [Agent-assisted installation](docs/agent-installation.md).
4. Put secrets only in local files outside this package.
5. Run `python3 tests/validate_package.py`.
6. Deploy by following [Installation](docs/installation.md).

For a handoff archive, run `python3 scripts/package_release.py`. It creates a deterministic release under the sibling `call-transcription-agent-dist` directory with a manifest and SHA-256 checksum.

The user should give an installing agent filesystem paths or secret references. Secret values should not be pasted into chat, command arguments, workflow JSON, or documentation.

## Tested Baseline

- Ubuntu 24.04 LTS
- Docker Engine with Docker Compose v2
- n8n 2.39.6
- PostgreSQL 15
- Python 3.11
- faster-whisper 1.2.1
- BigQuery in an explicitly configured region

See [Server requirements](docs/server-requirements.md) before deployment.
