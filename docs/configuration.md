# Configuration

Copy `deploy/.env.example` to a protected runtime environment outside the release directory. Never distribute the populated file.

## Required Customer Values

- `N8N_HOST`: public DNS name;
- `BITRIX_REST_BASE_URL`: Bitrix REST webhook base URL;
- `BQ_PROJECT_ID`, `BQ_DATASET`, `BQ_CALLS_TABLE`, `BQ_LOCATION`;
- `POSTGRES_PASSWORD`, `N8N_ENCRYPTION_KEY`, `BITRIX_WEBHOOK_SECRET`, `CALLS_API_TOKEN`.

Generate the four local secrets independently with a cryptographically secure generator. Keep the Google service-account JSON and internal API token in protected files mounted into call-service.

## Whisper Defaults

The package defaults to `large-v3-turbo`, Russian, CPU, and `int8`. The initial prompt is in `deploy/initial-prompt.txt`; replace company-specific vocabulary during installation without including personal data.

## Processing Policy

`MIN_CALL_DURATION_SECONDS` filters short calls. The processing window uses Moscow time and defaults to the full day. Set start and end hours only when the customer intentionally wants delayed or limited processing.
