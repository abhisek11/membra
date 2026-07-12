# Architecture

```
                         ┌──────────────────────────────────────────┐
                         │              Sentra (one process)         │
   App / SDK  ──creds──▶ │  ┌─────────────┐   ┌───────────────────┐  │ ──▶ LLM Provider
   (OpenAI /             │  │ Control     │   │ Data plane        │  │     (OpenAI /
    Anthropic protocol)  │  │ plane       │   │ /v1/chat, /v1/msg │  │      Anthropic /
                         │  │ site, auth, │   │ /v1/agent/authorize│ │      Azure ...)
   Browser   ──────────▶ │  │ dashboard   │   │        │          │  │
                         │  └─────────────┘   │        ▼          │  │
                         │        │           │   ┌──────────┐    │  │
                         │        │           │   │  Engine  │    │  │
                         │        ▼           │   └────┬─────┘    │  │
                         │  ┌───────────┐     │  ┌─────┴──────────┐│  │
                         │  │TenantStore│◀────┼──│  Detectors:    ││  │
                         │  │  + Store  │     │  │  injection(ML) ││  │
                         │  │  (SQLite) │     │  │  dlp           ││  │
                         │  └───────────┘     │  │  anomaly       ││  │
                         │                    │  │  agent_guard   ││  │
                         │                    │  └────────────────┘│  │
                         └────────────────────┴────────────────────┴──┘
```

## Planes
- **Control plane** (`sentra/app.py` GET/marketing + auth + dashboard): signup,
  login, credential management, per-tenant threat feed. Backed by `auth.py`.
- **Data plane** (`sentra/app.py` `/v1/*`): authenticates each call with
  `client_id`/`client_secret`, runs the engine, forwards clean traffic upstream,
  logs a tenant-scoped audit event.

## Engine & detectors
`engine.Engine.inspect()` runs detectors in severity order and returns a
`Decision(action, reasons, safe_text, detail)`:

| Order | Detector | File | Action on hit |
|---|---|---|---|
| 1 | Injection/jailbreak (regex + ML ensemble) | `detectors/injection.py`, `detectors/ml_injection.py` | **block** |
| 2 | Behavioral anomaly (z-score) | `detectors/anomaly.py` | **quarantine** |
| 3 | AI-DLP (secrets + PII) | `detectors/dlp.py` | **redact** |
| — | Agent action guard | `detectors/agent_guard.py` | allow / approve / deny |

## Data model (SQLite, `data/sentra.db`)
- `tenants(id, org, email, salt, pw_hash, client_id, secret_hash, plan, created)`
- `sessions(token, tenant_id, created)`
- `events(id, tenant_id, ts, user, action, reasons, detail, preview)`

## Multitenancy
Every API call is bound to a tenant via credentials; every event carries
`tenant_id`; every dashboard/API read filters by the session's tenant. Tenants
cannot observe each other's traffic.

## Design principles
- **Zero dependencies** — pure stdlib core runs anywhere; ML is from-scratch.
- **Fail safe** — unknown agent tools default to human approval; upstream errors
  never leak unsanitized data.
- **Explainable** — every decision carries `reasons` and detector detail.
