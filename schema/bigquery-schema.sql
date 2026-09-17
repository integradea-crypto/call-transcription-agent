CREATE TABLE IF NOT EXISTS `${BQ_PROJECT_ID}.${BQ_DATASET}.${BQ_CALLS_TABLE}` (
  activity_id STRING NOT NULL,
  call_datetime TIMESTAMP,
  employee_id STRING,
  stage_id STRING,
  deal_id STRING,
  contact_id STRING,
  transcript STRING,
  transcript_model STRING,
  source_workflow_id STRING,
  source_execution_id STRING,
  inserted_at TIMESTAMP
)
PARTITION BY DATE(call_datetime)
CLUSTER BY employee_id, stage_id, deal_id, contact_id;
