from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime

from google.cloud import bigquery

from .server import get_bigquery_client, table_identifier


CALLS_SCHEMA = [
    bigquery.SchemaField("activity_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("call_datetime", "TIMESTAMP"),
    bigquery.SchemaField("employee_id", "STRING"),
    bigquery.SchemaField("stage_id", "STRING"),
    bigquery.SchemaField("deal_id", "STRING"),
    bigquery.SchemaField("contact_id", "STRING"),
    bigquery.SchemaField("transcript", "STRING"),
    bigquery.SchemaField("transcript_model", "STRING"),
    bigquery.SchemaField("source_workflow_id", "STRING"),
    bigquery.SchemaField("source_execution_id", "STRING"),
    bigquery.SchemaField("inserted_at", "TIMESTAMP"),
]


def emit(rows: list[dict[str, object]]) -> None:
    for row in rows:
        print(json.dumps(row, ensure_ascii=False, default=str))


def init_schema() -> None:
    client = get_bigquery_client()
    project = os.environ["BQ_PROJECT_ID"]
    dataset_name = os.environ["BQ_DATASET"]
    table_name = os.getenv("BQ_CALLS_TABLE", "calls")
    dataset_ref = bigquery.Dataset(f"{project}.{dataset_name}")
    dataset_ref.location = os.getenv("BQ_LOCATION", "EU")
    client.create_dataset(dataset_ref, exists_ok=True)
    table = bigquery.Table(f"{project}.{dataset_name}.{table_name}", schema=CALLS_SCHEMA)
    table.time_partitioning = bigquery.TimePartitioning(field="call_datetime")
    table.clustering_fields = ["employee_id", "stage_id", "deal_id", "contact_id"]
    client.create_table(table, exists_ok=True)
    print(json.dumps({"ok": True, "table": table_identifier()}))


def parse_date(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def query_calls(args: argparse.Namespace) -> None:
    filters = []
    parameters: list[bigquery.ScalarQueryParameter] = []
    for column in ("activity_id", "employee_id", "stage_id", "deal_id", "contact_id"):
        value = getattr(args, column, None)
        if value:
            filters.append(f"{column} = @{column}")
            parameters.append(bigquery.ScalarQueryParameter(column, "STRING", value))
    if getattr(args, "date_from", None):
        filters.append("call_datetime >= @date_from")
        parameters.append(bigquery.ScalarQueryParameter("date_from", "TIMESTAMP", parse_date(args.date_from)))
    if getattr(args, "date_to", None):
        filters.append("call_datetime < @date_to")
        parameters.append(bigquery.ScalarQueryParameter("date_to", "TIMESTAMP", parse_date(args.date_to)))
    if getattr(args, "text", None):
        filters.append("REGEXP_CONTAINS(LOWER(transcript), @text_pattern)")
        parameters.append(
            bigquery.ScalarQueryParameter("text_pattern", "STRING", re.escape(args.text.lower()))
        )

    where = "WHERE " + " AND ".join(filters) if filters else ""
    limit = min(max(int(args.limit), 1), 1000)
    query = f"""
      SELECT activity_id, call_datetime, employee_id, stage_id, deal_id, contact_id,
             transcript, transcript_model, inserted_at
      FROM `{table_identifier()}`
      {where}
      ORDER BY call_datetime DESC
      LIMIT {limit}
    """
    rows = get_bigquery_client().query(
        query,
        job_config=bigquery.QueryJobConfig(query_parameters=parameters),
    ).result()
    emit([dict(row.items()) for row in rows])


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Call Transcription Agent CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init-schema")

    query_parser = subparsers.add_parser("query")
    for flag in ("activity-id", "employee-id", "stage-id", "deal-id", "contact-id"):
        query_parser.add_argument(f"--{flag}")
    query_parser.add_argument("--from", dest="date_from")
    query_parser.add_argument("--to", dest="date_to")
    query_parser.add_argument("--text")
    query_parser.add_argument("--limit", type=int, default=100)

    args = parser.parse_args()
    if args.command == "init-schema":
        init_schema()
    elif args.command == "query":
        query_calls(args)


if __name__ == "__main__":
    main()
