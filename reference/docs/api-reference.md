# API Reference

Base URL (self-hosted): `http://localhost:8100`

## Authentication
All `/v1/*` endpoints require tenant credentials as headers:

| Header | Required | Description |
|---|---|---|
| `X-Sentra-Client-Id` | yes | Your tenant's client id |
| `X-Sentra-Client-Secret` | yes | Your tenant's secret |
| `X-Sentra-User` | no | End-user identifier (drives per-user anomaly baselines) |

Missing/invalid credentials → `401 Unauthorized`.

Every inspected response includes:
- `X-Sentra-Action`: `allow` | `redact` | `quarantine` | `block`
- `X-Sentra-Reasons`: human-readable reason list

---

## POST /v1/chat/completions
OpenAI-compatible. Inspects the latest user message, then forwards clean/redacted
traffic to `SENTRA_UPSTREAM`. On block/quarantine returns an OpenAI-shaped refusal
(HTTP 200, `finish_reason: content_filter`) so callers don't break.

**Request** — identical to OpenAI's schema.
**Response** — the upstream completion, or a refusal object.

## POST /v1/messages
Anthropic/Claude-compatible. Same inspection; handles string or content-block
message content (text blocks redacted individually).

## POST /v1/agent/authorize
Authorize an autonomous-agent tool action.

**Request**
```json
{ "tool": "shell_exec", "args": { "cmd": "rm -rf /" } }
```
**Response**
```json
{ "decision": "deny", "tier": "critical",
  "reasons": ["destructive_shell"], "tool": "shell_exec" }
```
`decision`: `allow` (auto-run) · `approve` (needs human) · `deny` (refuse).

## GET /api/events
Session-authenticated (dashboard cookie). Returns the tenant's recent events and
aggregate stats.
```json
{ "events": [ { "ts": 1720000000.0, "user": "alice", "action": "block",
                "reasons": "[\"prompt_injection(...)\"]", "preview": "..." } ],
  "stats": { "allow": 12, "redact": 3, "block": 1 } }
```

---

## Actions reference
| Action | Meaning | Traffic forwarded? |
|---|---|---|
| `allow` | clean | yes, as-is |
| `redact` | secrets/PII removed | yes, sanitized |
| `quarantine` | behavioral anomaly | no |
| `block` | injection/jailbreak | no |
