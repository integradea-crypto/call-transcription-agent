from __future__ import annotations

import asyncio
import hmac
import os
import re
import tempfile
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import PlainTextResponse
from faster_whisper import WhisperModel
from google.cloud import bigquery
from pydantic import BaseModel, Field


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def read_secret(file_env: str, value_env: str) -> str:
    path = os.getenv(file_env, "").strip()
    if path:
        return Path(path).read_text(encoding="utf-8").strip()
    return os.getenv(value_env, "").strip()


def initial_prompt() -> str:
    path = os.getenv("WHISPER_INITIAL_PROMPT_FILE", "").strip()
    if path and Path(path).exists():
        return Path(path).read_text(encoding="utf-8").strip()
    return os.getenv("WHISPER_INITIAL_PROMPT", "").strip()


MAX_UPLOAD_BYTES = env_int("MAX_UPLOAD_MB", 250) * 1024 * 1024
TRANSCRIBE_SEMAPHORE = asyncio.Semaphore(env_int("WHISPER_CONCURRENCY", 1))
INTERNAL_TOKEN = read_secret("CALLS_API_TOKEN_FILE", "CALLS_API_TOKEN")

app = FastAPI(title="Call transcription agent API", version="1.0.0")


class CallRecord(BaseModel):
    activity_id: str = Field(min_length=1, max_length=128)
    call_datetime: datetime | None = None
    employee_id: str = Field(default="", max_length=128)
    stage_id: str = Field(default="", max_length=256)
    deal_id: str = Field(default="", max_length=128)
    contact_id: str = Field(default="", max_length=128)
    transcript: str = Field(min_length=1)
    transcript_model: str = Field(default="large-v3-turbo", max_length=128)
    source_workflow_id: str = Field(default="", max_length=128)
    source_execution_id: str = Field(default="", max_length=128)
    inserted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def require_internal_token(x_internal_token: str = Header(default="")) -> None:
    if not INTERNAL_TOKEN:
        raise HTTPException(status_code=503, detail="internal API token is not configured")
    if not hmac.compare_digest(x_internal_token, INTERNAL_TOKEN):
        raise HTTPException(status_code=401, detail="invalid internal API token")


@lru_cache(maxsize=4)
def get_model(model_name: str, device: str, compute_type: str) -> WhisperModel:
    return WhisperModel(model_name, device=device, compute_type=compute_type)


@lru_cache(maxsize=1)
def get_bigquery_client() -> bigquery.Client:
    project = required_env("BQ_PROJECT_ID")
    return bigquery.Client(project=project)


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def table_identifier() -> str:
    project = required_env("BQ_PROJECT_ID")
    dataset = required_env("BQ_DATASET")
    table = os.getenv("BQ_CALLS_TABLE", "calls").strip() or "calls"
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,61}[a-z0-9]", project):
        raise RuntimeError("BQ_PROJECT_ID has an invalid format")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,1023}", dataset):
        raise RuntimeError("BQ_DATASET has an invalid format")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,1023}", table):
        raise RuntimeError("BQ_CALLS_TABLE has an invalid format")
    return f"{project}.{dataset}.{table}"


def clean_text(text: str) -> str:
    text = text or ""
    patterns = [
        r"(?i)\bсубтитры\s+(?:создавал[аи]?|сделал[аи]?|подготовил[аи]?|редактировал[аи]?)[^.!?\n]*[.!?]?",
        r"(?i)\bредактор\s+субтитров[^.!?\n]*[.!?]?",
        r"(?i)\bпродолжение\s+следует\b[^.!?\n]*[.!?]?",
    ]
    for pattern in patterns:
        text = re.sub(pattern, " ", text)
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    return " ".join(text.split()).strip()


def transcribe_file(
    path: str,
    model: str,
    language: str,
    beam_size: int,
    device: str,
    compute_type: str,
) -> str:
    whisper_model = get_model(model, device, compute_type)
    segments, _ = whisper_model.transcribe(
        path,
        language=language,
        beam_size=beam_size,
        initial_prompt=initial_prompt() or None,
        vad_filter=env_bool("WHISPER_VAD_FILTER", False),
    )
    return clean_text(" ".join(segment.text for segment in segments))


@app.get("/health", response_class=PlainTextResponse)
def health() -> str:
    return "ok"


@app.get("/ready")
def ready(_: None = Depends(require_internal_token)) -> dict[str, str]:
    list(get_bigquery_client().query("SELECT 1").result())
    return {"status": "ok", "table": table_identifier()}


@app.post("/transcribe", response_class=PlainTextResponse)
async def transcribe(
    audio: UploadFile = File(...),
    model: str = Query(default_factory=lambda: os.getenv("WHISPER_MODEL", "large-v3-turbo")),
    language: str = Query(default_factory=lambda: os.getenv("WHISPER_LANGUAGE", "ru")),
    beam_size: int = Query(default_factory=lambda: env_int("WHISPER_BEAM_SIZE", 1), ge=1, le=10),
    device: str = Query(default_factory=lambda: os.getenv("WHISPER_DEVICE", "cpu")),
    compute_type: str = Query(default_factory=lambda: os.getenv("WHISPER_COMPUTE_TYPE", "int8")),
    _: None = Depends(require_internal_token),
) -> str:
    suffix = os.path.splitext(audio.filename or "audio.mp3")[1] or ".mp3"
    fd, path = tempfile.mkstemp(prefix="call-agent-", suffix=suffix)
    total = 0
    try:
        with os.fdopen(fd, "wb") as file_handle:
            while chunk := await audio.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="audio file is too large")
                file_handle.write(chunk)

        async with TRANSCRIBE_SEMAPHORE:
            text = await run_in_threadpool(
                transcribe_file,
                path,
                model,
                language,
                beam_size,
                device,
                compute_type,
            )
        if not text:
            raise HTTPException(status_code=422, detail="empty transcript")
        return text
    finally:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


@app.post("/calls/upsert")
def upsert_call(record: CallRecord, _: None = Depends(require_internal_token)) -> dict[str, object]:
    table = table_identifier()
    query = f"""
    MERGE `{table}` T
    USING (
      SELECT
        @activity_id AS activity_id,
        @call_datetime AS call_datetime,
        @employee_id AS employee_id,
        @stage_id AS stage_id,
        @deal_id AS deal_id,
        @contact_id AS contact_id,
        @transcript AS transcript,
        @transcript_model AS transcript_model,
        @source_workflow_id AS source_workflow_id,
        @source_execution_id AS source_execution_id,
        @inserted_at AS inserted_at
    ) S
    ON T.activity_id = S.activity_id
    WHEN NOT MATCHED THEN INSERT (
      activity_id, call_datetime, employee_id, stage_id, deal_id, contact_id,
      transcript, transcript_model, source_workflow_id, source_execution_id, inserted_at
    ) VALUES (
      S.activity_id, S.call_datetime, S.employee_id, S.stage_id, S.deal_id, S.contact_id,
      S.transcript, S.transcript_model, S.source_workflow_id, S.source_execution_id, S.inserted_at
    )
    """
    parameters = [
        bigquery.ScalarQueryParameter("activity_id", "STRING", record.activity_id),
        bigquery.ScalarQueryParameter("call_datetime", "TIMESTAMP", record.call_datetime),
        bigquery.ScalarQueryParameter("employee_id", "STRING", record.employee_id),
        bigquery.ScalarQueryParameter("stage_id", "STRING", record.stage_id),
        bigquery.ScalarQueryParameter("deal_id", "STRING", record.deal_id),
        bigquery.ScalarQueryParameter("contact_id", "STRING", record.contact_id),
        bigquery.ScalarQueryParameter("transcript", "STRING", record.transcript),
        bigquery.ScalarQueryParameter("transcript_model", "STRING", record.transcript_model),
        bigquery.ScalarQueryParameter("source_workflow_id", "STRING", record.source_workflow_id),
        bigquery.ScalarQueryParameter("source_execution_id", "STRING", record.source_execution_id),
        bigquery.ScalarQueryParameter("inserted_at", "TIMESTAMP", record.inserted_at),
    ]
    job = get_bigquery_client().query(
        query,
        job_config=bigquery.QueryJobConfig(query_parameters=parameters),
    )
    job.result()
    affected = int(job.num_dml_affected_rows or 0)
    return {
        "ok": True,
        "activity_id": record.activity_id,
        "affected_rows": affected,
        "duplicate_skipped": affected == 0,
    }
