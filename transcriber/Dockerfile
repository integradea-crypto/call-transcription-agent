FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/models/huggingface

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 callagent \
    && useradd --uid 10001 --gid callagent --create-home callagent

WORKDIR /app
COPY requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir --requirement /app/requirements.lock

COPY app /app/app
RUN mkdir -p /models/huggingface /config \
    && chown -R callagent:callagent /app /models /config

USER callagent
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl --fail --silent http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
