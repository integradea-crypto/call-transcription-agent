# Data Dictionary

The canonical field definitions are maintained in the skill reference at `skill/call-transcription-analytics/references/schema.md`. The executable schema is `schema/bigquery-schema.sql`.

Customer-specific lookup tables for employees, contacts, stages, and pipelines are optional and intentionally excluded from the portable core. Add them as separate tables and preserve stable CRM IDs as join keys.
