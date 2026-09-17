#!/usr/bin/env bash
set -euo pipefail

failures=0

check_command() {
  if command -v "$1" >/dev/null 2>&1; then
    printf 'ready: %s\n' "$1"
  else
    printf 'blocked: missing %s\n' "$1"
    failures=$((failures + 1))
  fi
}

check_command docker
check_command openssl
check_command curl

if docker compose version >/dev/null 2>&1; then
  printf 'ready: docker compose\n'
else
  printf 'blocked: docker compose v2 unavailable\n'
  failures=$((failures + 1))
fi

if [ "$(uname -s)" = "Linux" ]; then
  printf 'ready: linux host\n'
else
  printf 'warning: production baseline is Ubuntu Linux\n'
fi

if [ -r /proc/meminfo ]; then
  memory_kb="$(awk '/MemTotal/ {print $2}' /proc/meminfo)"
  if [ "${memory_kb:-0}" -lt 12000000 ]; then
    printf 'blocked: less than 12 GB RAM detected\n'
    failures=$((failures + 1))
  else
    printf 'ready: memory baseline met\n'
  fi
fi

free_kb="$(df -Pk . | awk 'NR==2 {print $4}')"
if [ "${free_kb:-0}" -lt 52428800 ]; then
  printf 'warning: less than 50 GB free in current filesystem\n'
else
  printf 'ready: disk baseline met\n'
fi

exit "$failures"
