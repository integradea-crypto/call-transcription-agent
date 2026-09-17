# Server Requirements

## Recommended CPU Deployment

- Ubuntu 24.04 LTS, x86_64;
- 8 vCPU;
- 16 GB RAM;
- 80 GB SSD;
- stable outbound HTTPS access;
- public IPv4 and a DNS name for the n8n webhook;
- Docker Engine and Docker Compose v2.

The practical minimum is 4 vCPU, 12 GB RAM, and 50 GB SSD for low call volume. `large-v3-turbo` runs locally and is the main resource consumer. More CPU reduces transcript latency; more memory prevents contention between Whisper, n8n, and PostgreSQL.

Use 16 vCPU and 32 GB RAM when calls arrive in bursts, fast turnaround matters, or several transcriptions must run concurrently. A CUDA GPU is optional and requires a separate Compose override, NVIDIA drivers, and a CUDA-compatible build.

## Placement

A dedicated server is preferred. A shared host is acceptable only when at least 12 GB RAM and 6 CPU cores can be reserved and the existing workload is measured. Keep the server in a region allowed by the customer's data policy and, where possible, near the Bitrix account and BigQuery dataset.

The machine does not need Metabase. The public surface is HTTPS to n8n; PostgreSQL and call-service remain on the private Docker network.

## Capacity Notes

- The Whisper model cache consumes several gigabytes.
- Temporary audio is bounded by `MAX_UPLOAD_MB` and deleted after each request.
- n8n execution history is pruned; PostgreSQL and model cache need persistent volumes.
- Begin with `WHISPER_CONCURRENCY=1` on CPU. Increase only after observing CPU, memory, and queue latency.
