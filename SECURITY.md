# Security

## Secret Boundary

This package contains no credentials. Runtime secrets belong in protected files outside the release directory. `deploy/secrets/` is ignored and exists only as a local mount point.

Never commit or publish SSH private keys, Bitrix webhook URLs, Google service-account JSON, n8n encryption keys, database passwords, internal API tokens, real webhook payloads, recordings, or transcripts.

Ask users for filesystem paths or secret-store references. Do not ask them to paste secret values into chat. Never print a secret file during validation or installation.

## Network Boundary

Expose only ports 80 and 443. n8n binds to `127.0.0.1:5678`. PostgreSQL and call-service remain on the private Docker network. Do not expose ports 5432, 5678, or 8000 publicly.

## Agent Boundary

The analytics mode is read-only by default. Installation, workflow activation, credential rotation, deletion, and production retries require an explicit user request. Query helpers should return only data needed for the requested analysis.

## Before Distribution

Run `python3 tests/validate_package.py`, inspect `MANIFEST.sha256`, and verify the release archive checksum. Rotate any credential that has appeared in chat, command-line history, or an exported workflow.
