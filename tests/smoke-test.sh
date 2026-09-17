#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="call-transcription-agent-smoke:local"
container="call-transcription-agent-smoke-$$"
token_file="$(mktemp)"

cleanup() {
  docker rm -f "$container" >/dev/null 2>&1 || true
  rm -f "$token_file"
}
trap cleanup EXIT

printf 'synthetic-test-token' >"$token_file"
chmod 600 "$token_file"

docker build -t "$image" "$root/transcriber"
docker run -d --name "$container" \
  -p 127.0.0.1::8000 \
  -e CALLS_API_TOKEN_FILE=/run/secrets/internal-api-token \
  -v "$token_file:/run/secrets/internal-api-token:ro" \
  "$image" >/dev/null

port="$(docker port "$container" 8000/tcp | awk -F: '{print $NF}')"
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:$port/health" | grep -qx ok; then
    printf 'PASS: call-service health endpoint\n'
    exit 0
  fi
  sleep 1
done

docker logs "$container"
exit 1
