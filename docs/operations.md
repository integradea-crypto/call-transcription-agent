# Operations

## Health Checks

- `GET /health` checks the call-service process.
- Authenticated `GET /ready` checks BigQuery connectivity and the configured table identifier.
- `docker compose ps` should show PostgreSQL and call-service healthy.
- n8n execution history should show successful upserts and no growing queue.

## Backups

Back up PostgreSQL and the n8n encryption key together. BigQuery is the transcript system of record; apply the customer's retention and recovery policy there. The Whisper model cache can be recreated.

## Upgrades

Deploy a new version to a new release directory, validate its package and Compose configuration, back up PostgreSQL, then switch the `current` symlink and recreate containers. Keep the previous release available for rollback. Read n8n release notes before crossing a major version.

## Incident Checks

- repeated `401`: compare secret references and proxy header behavior without printing tokens;
- missing recordings: inspect Bitrix activity metadata and whether the recording URL expired;
- duplicate activity IDs: verify all writes still pass through the BigQuery `MERGE` endpoint;
- growing queue: check CPU, memory, call duration, and `WHISPER_CONCURRENCY`;
- empty transcripts: preserve execution metadata, confirm supported audio, and test the file locally without storing it permanently.

The standard workflow never deletes recordings from Bitrix.
