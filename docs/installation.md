# Installation

## 1. Prepare The Host

Install Docker Engine, Compose v2, a TLS reverse proxy, and basic monitoring. Create `/opt/call-transcription-agent/releases` and `/etc/call-transcription-agent/secrets` with root-owned permissions.

## 2. Place The Release

Extract the release into `/opt/call-transcription-agent/releases/<version>` and point `/opt/call-transcription-agent/current` to it. Work from the `deploy` directory.

## 3. Configure Runtime Secrets

Create `/etc/call-transcription-agent/runtime.env` from `deploy/.env.example`, replacing placeholders. Put the BigQuery service-account JSON and internal token in `/etc/call-transcription-agent/secrets` with mode `0600`.

The provided Compose file uses paths under `deploy/secrets`. For production, either bind-mount `/etc/call-transcription-agent/secrets` there or maintain a small customer-specific override file outside the release.

## 4. Validate And Start

```bash
cd /opt/call-transcription-agent/current/deploy
docker compose --env-file /etc/call-transcription-agent/runtime.env config
docker compose --env-file /etc/call-transcription-agent/runtime.env build call-service
docker compose --env-file /etc/call-transcription-agent/runtime.env up -d
docker compose --env-file /etc/call-transcription-agent/runtime.env exec -T call-service \
  python -m app.cli init-schema
```

## 5. Import n8n Workflow

```bash
docker compose --env-file /etc/call-transcription-agent/runtime.env exec -T n8n \
  n8n import:workflow --input=/workflows/workflow.json
```

Open n8n, inspect the imported inactive workflow, and copy its production webhook URL. Add `?secret=<BITRIX_WEBHOOK_SECRET>` to the Bitrix outgoing webhook target without exposing the secret elsewhere.

## 6. Test And Activate

Run health checks and a synthetic webhook. Confirm one row in BigQuery, then replay the same `activity_id` and confirm there is still one row. Activate the workflow only after this check and after the Bitrix target is configured.

See `docs/operations.md` for routine checks and rollback.
