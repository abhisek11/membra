# Sentra — Sequence Diagrams

Rendered by GitHub / any Mermaid viewer. ASCII fallbacks are in the web docs (`/docs`).

## 1. Signup & API credential issuance

```mermaid
sequenceDiagram
    actor U as User (org admin)
    participant W as Sentra Web
    participant DB as TenantStore (SQLite)
    U->>W: POST /signup (org, email, password)
    W->>W: gen client_id, client_secret
    W->>W: hash(password), hash(client_secret)
    W->>DB: INSERT tenant (pw_hash, secret_hash)
    DB-->>W: tenant_id
    W->>W: create session cookie
    W-->>U: client_id + client_secret (shown ONCE)
    Note over U,W: Only the HASH of the secret is stored.
```

## 2. Inline inspection of an AI request (data plane)

```mermaid
sequenceDiagram
    participant App as App / SDK
    participant GW as Sentra Gateway
    participant E as Engine
    participant LLM as LLM Provider
    App->>GW: POST /v1/chat/completions + client creds
    GW->>GW: verify_client(id, secret) -> tenant
    GW->>E: inspect(user, text)
    E->>E: injection? (regex + ML ensemble)
    E->>E: behavioral anomaly? (z-score)
    E->>E: DLP scan (secrets/PII)
    E-->>GW: Decision(action, reasons, safe_text)
    alt action = block / quarantine
        GW-->>App: safe refusal (never forwarded)
    else action = redact
        GW->>LLM: forward SANITIZED text
        LLM-->>GW: completion
        GW-->>App: completion + X-Sentra-Action: redact
    else action = allow
        GW->>LLM: forward as-is
        LLM-->>GW: completion
        GW-->>App: completion + X-Sentra-Action: allow
    end
    GW->>GW: log event to tenant audit trail
```

## 3. Autonomous-agent action authorization (T-cell layer)

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant GW as Sentra
    participant AG as AgentGuard
    Agent->>GW: POST /v1/agent/authorize {tool, args}
    GW->>AG: assess(tool, args)
    AG->>AG: dangerous arg signatures? (rm -rf, DROP TABLE, curl|sh)
    AG->>AG: data egress? (DLP on args)
    AG->>AG: destination allow-listed?
    AG->>AG: tool risk tier
    AG-->>GW: {decision, tier, reasons}
    GW-->>Agent: allow / approve / deny
    Note over Agent: execute the tool ONLY on "allow"
```

## 4. Multitenant isolation

```mermaid
sequenceDiagram
    participant A as Tenant A app
    participant B as Tenant B app
    participant GW as Sentra
    participant DB as Audit log
    A->>GW: call + A's creds
    GW->>DB: log(tenant_id = A, ...)
    B->>GW: call + B's creds
    GW->>DB: log(tenant_id = B, ...)
    A->>GW: GET /api/events (A's session)
    GW->>DB: SELECT WHERE tenant_id = A
    GW-->>A: only A's events
    Note over A,B: A can never see B's traffic and vice-versa.
```
