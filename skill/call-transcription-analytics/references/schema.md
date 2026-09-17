# Calls Schema

The default table is `${BQ_PROJECT_ID}.${BQ_DATASET}.${BQ_CALLS_TABLE}`.

| Column | Type | Meaning |
| --- | --- | --- |
| `activity_id` | STRING, required | Stable Bitrix activity identifier and deduplication key |
| `call_datetime` | TIMESTAMP | Call start timestamp |
| `employee_id` | STRING | Responsible employee or call owner ID |
| `stage_id` | STRING | Deal stage at processing time |
| `deal_id` | STRING | Related deal ID |
| `contact_id` | STRING | Related contact ID |
| `transcript` | STRING | Cleaned transcript text |
| `transcript_model` | STRING | Whisper model used |
| `source_workflow_id` | STRING | n8n workflow ID for lineage |
| `source_execution_id` | STRING | n8n execution ID for lineage |
| `inserted_at` | TIMESTAMP | Ingestion timestamp |

The table is partitioned by `DATE(call_datetime)` and clustered by employee, stage, deal, and contact IDs. It contains IDs rather than names by design. Join customer-maintained reference tables when natural-language name resolution is required.

All writes use `MERGE ... ON activity_id`. A retry must return `duplicate_skipped=true` rather than creating another row.
