# Architecture

## Components

`n8n` receives a Bitrix call-completion event, validates a shared webhook secret, filters unsuccessful or short calls, waits for the recording, and retrieves CRM metadata.

`call-service` accepts the recording over the private Docker network, transcribes it locally, cleans common hallucinated subtitle phrases, and returns plain text. The same service performs a parameterized BigQuery `MERGE` by `activity_id`.

`PostgreSQL` stores n8n workflows, credentials, and execution metadata. Audio is temporary. The product does not intentionally retain recordings after transcription.

`BigQuery` stores transcript rows. Repeated processing of the same `activity_id` produces no duplicate row.

The agent skill uses a read-only CLI over SSH. It does not require a copy of the BigQuery key on the analyst's computer.

## Trust Boundaries

- Internet -> Nginx/Caddy -> n8n webhook.
- n8n -> call-service on a private Docker network with `X-Internal-Token`.
- call-service -> BigQuery with a mounted service-account file.
- Codex/Claude -> server over SSH -> read-only CLI inside call-service.

## Data Contract

The required identity is `activity_id`. Other IDs are strings because CRM identifiers can cross system boundaries and may not remain numeric.

The workflow stores:

- `activity_id`;
- call timestamp;
- employee, stage, deal, and contact IDs;
- transcript and model name;
- source workflow and execution IDs;
- insertion timestamp.

Names and pipeline labels should live in reference tables or be resolved by the analytics layer. The core transcript table remains append-oriented and idempotent.
