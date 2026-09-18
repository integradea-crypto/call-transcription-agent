# Installation Guide For Agents

Use this reference when the user asks where or how to install the pipeline, or supplies access and credential locations.

## Required Inputs

Collect references to these inputs. A reference is a local path, environment-variable name, or secret-manager URI; it is not the value itself.

- SSH host, user, port, and private-key path, or an already configured SSH host alias.
- Public hostname that will receive Bitrix webhook requests.
- Bitrix REST webhook base URL secret reference.
- A separate random shared secret for the incoming workflow webhook.
- Google service-account JSON path with BigQuery job and destination-dataset permissions.
- BigQuery project, dataset, table, and location.
- Optional DNS provider access when the user wants the agent to configure DNS.

The Google key and Bitrix webhook serve different trust boundaries. Do not reuse them as n8n or internal service secrets.

## Credential Inspection

Check without printing values:

- files exist, are regular files, and are not group/world readable;
- the Google JSON has `type=service_account`, a client email, project ID, and private key fields;
- the selected service account can create query jobs and create/read/write the destination table;
- the Bitrix base URL has HTTPS and the expected `/rest/<user>/<token>` shape;
- SSH reaches the intended host and the user has Docker access or controlled sudo;
- the public hostname resolves to the host before requesting a certificate.

Prefer a dataset-scoped BigQuery role plus project-level `roles/bigquery.jobUser`. Avoid project Owner or Editor.

## Placement Decision

Default to one dedicated Linux host:

- install root: `/opt/call-transcription-agent`;
- runtime environment: `/etc/call-transcription-agent/runtime.env` with mode `0600`;
- BigQuery key: `/opt/call-transcription-agent/current/deploy/secrets/bigquery-service-account.json` with mode `0600`;
- internal token: `/opt/call-transcription-agent/current/deploy/secrets/internal-api-token` with mode `0600`;
- both secret files must live in the `deploy/secrets/` directory next to `docker-compose.yml`, because the compose file bind-mounts them from that relative path; do not place them under `/etc`;
- persistent Docker volumes for PostgreSQL, n8n, and Whisper model cache;
- only ports 22, 80, and 443 exposed publicly; n8n and call-service stay private.

For the CPU baseline and sizing rules, read the package file `docs/server-requirements.md`.

## Deployment Sequence

1. Validate the untouched release locally with `python3 tests/validate_package.py`.
2. Inspect the destination and present the selected path, hostname, versions, expected disk use, and mutation plan.
3. Copy the release to a versioned directory under the install root and use a `current` symlink for rollback.
4. Generate PostgreSQL password, n8n encryption key, incoming webhook secret, and internal API token on the host. Do not return them in chat.
5. Write the protected runtime environment and secret files.
6. Run `docker compose config`, build the call service, and start the stack.
7. Run `python -m app.cli init-schema` inside call-service.
8. Import `n8n/workflow.json`; confirm it remains inactive.
9. Test `/health`, `/ready`, and the synthetic webhook fixture. Verify one BigQuery row and retry the same `activity_id` to verify deduplication.
10. Configure TLS and the Bitrix robot/webhook. Activate only after the user authorizes production traffic.

## Completion Report

Return:

- server and install path;
- deployed product and container versions;
- hostname and public webhook URL with the secret redacted;
- workflow ID and active/inactive state;
- BigQuery table identifier and successful schema/readiness check;
- synthetic test activity ID, first insert result, and duplicate retry result;
- service health and backup location;
- manual actions and warnings.

Do not include passwords, tokens, private-key content, or full credential paths when the path itself exposes customer information.
