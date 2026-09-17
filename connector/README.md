# Agent Connector

The portable integration uses an SSH host alias and the skill helper `scripts/query_calls.py`. `client.example.json` documents non-secret connection metadata only.

Keep SSH private keys in the user's SSH configuration or agent. Do not copy them into this directory. The helper executes the read-only `app.cli query` command inside call-service; it does not expose the BigQuery key to the client.
