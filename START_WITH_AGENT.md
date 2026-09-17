# Start With Codex Or Claude

Install the bundled skill first:

```bash
# Codex
cp -R skill/call-transcription-analytics ~/.codex/skills/

# Claude Code
cp -R skill/call-transcription-analytics ~/.claude/skills/
```

Then give the agent this request with your own paths and non-secret identifiers:

```text
Use the call-transcription-analytics skill and this package.

Package path: /path/to/call-transcription-agent
Existing SSH host alias: <alias or "no server yet">
SSH private-key path: <path or "managed by SSH agent">
Google service-account JSON path: <path>
Bitrix REST URL file: <path>
BigQuery target: <project.dataset.calls>
BigQuery location: <EU, US, or region>
Public hostname: <hostname or "not selected">
Expected calls per business day: <number>
Typical and maximum call duration: <minutes>
Required transcript delay: <minutes or hours>
Required server country/region: <region or "no restriction">

Do not print or copy secret values into chat, logs, workflow JSON, or reports.
First validate only the credential types and access scopes, inspect the existing
server if one is supplied, and recommend the server, region, installation path,
and required changes. If there is no server, compare suitable current hosting
options and give a concrete size recommendation. Show the full preflight report
and deployment plan before making infrastructure changes. Keep the n8n workflow
inactive until I explicitly approve activation.
```

The agent should ask only for genuinely missing information. Credential values stay in protected files; the user shares paths or secret-manager references.
