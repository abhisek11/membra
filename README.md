# ◈ Sentra — a security *immune system* for the AI era

Firewalls and antivirus were built for networks and files. When a company wires
LLMs, copilots and autonomous AI agents into its workflows, it opens a **new
attack surface those tools can't see** — the prompt/response channel and agent
actions. Sentra is the missing inline layer that inspects the AI conversation
itself, delivered as a **multitenant SaaS** you can also self-host.

| Immune concept | What Sentra does | Where |
|---|---|---|
| 🦠 Antigen detection | Block **prompt injection / jailbreaks** (regex + trained ML ensemble) | `detectors/injection.py`, `ml_injection.py` |
| 🩸 Barrier defense | **AI-DLP**: redact secrets & PII outbound | `detectors/dlp.py` |
| 🧠 Immune memory | Learn each user's usage, flag **behavioral anomalies** | `detectors/anomaly.py` |
| 🛡️ T-cell guardrails | Gate risky **autonomous-agent actions** | `detectors/agent_guard.py` |
| ⚡ Immune response | block / redact / quarantine + tenant-scoped audit trail | `engine.py`, `store.py` |

## What's here
A working product, not a mockup — **pure Python standard library, zero installs**:
- **Marketing site** (landing, product, pricing) + **full docs** with sequence diagrams
- **Multitenant dashboard**: sign up → get a **Client ID + Secret** → live threat feed
- **Inline API** (OpenAI `/v1/chat/completions` + Anthropic `/v1/messages`) authenticated per tenant
- **Agent authorization** endpoint (`/v1/agent/authorize`)
- **Trained ML injection classifier** (from-scratch logistic regression) ensembled with regex
- **SDK wrapper** (`guard(OpenAI())`) as an alternate integration
- **Docker** packaging

## Run it (no dependencies)
```bash
python3 -m sentra.detectors.ml_injection   # train the model once
python3 demo/mock_upstream.py &            # a fake model, so it runs fully offline
python3 -m sentra.app                       # -> http://localhost:8100
```
Then open **http://localhost:8100** — sign up, grab your keys, and watch the dashboard.

### See everything work at once
```bash
python3 demo/saas_demo.py            # 2 tenants, mixed traffic, proves isolation
python3 demo/agent_guard_demo.py     # agent action authorization tiers
python3 demo/real_world_example.py   # narrated attack walkthrough
```

## Integrate (one line)
```python
# Gateway: point your existing client at Sentra
client = OpenAI(base_url="http://localhost:8100/v1",
    default_headers={"X-Sentra-Client-Id": ID, "X-Sentra-Client-Secret": SECRET})
# ...or in-process:  client = guard(OpenAI())
```
Set `SENTRA_UPSTREAM=https://api.openai.com` (or `https://api.anthropic.com`) to
forward clean traffic to the real provider.

## Docs
- [docs/quickstart.md](docs/quickstart.md) — zero to guarded call in 2 min
- [docs/integration.md](docs/integration.md) — gateway vs SDK, OpenAI & Claude
- [docs/api-reference.md](docs/api-reference.md) — endpoints, headers, actions
- [docs/architecture.md](docs/architecture.md) — planes, engine, data model
- [docs/sequence-diagrams.md](docs/sequence-diagrams.md) — Mermaid diagrams
- [docs/self-hosting.md](docs/self-hosting.md) — env vars, Docker, hardening

## Layout
```
sentra/
  app.py            SaaS server: site + auth + dashboard + tenant API
  auth.py           tenants, sessions, client_id/secret issuance & verification
  engine.py         runs detectors -> policy Decision
  detectors/        injection · ml_injection · dlp · anomaly · agent_guard
  store.py          tenant-scoped SQLite audit log
  templates.py      marketing + dashboard HTML (offline, CSP-safe)
  docs_page.py      rendered docs page
  sdk.py            guard() client wrapper
  gateway.py        minimal single-tenant proxy (reference)
demo/               mock_upstream · customer_app · saas_demo · agent_guard_demo · real_world_example
docs/               markdown docs + sequence diagrams
Dockerfile · docker-compose.yml
```

## Roadmap
- Detectors: larger labeled corpus + embedding-similarity for injection; NER-based PII.
- Postgres + Redis for horizontal scaling; SSO/RBAC; per-team policies.
- Streaming responses; usage metering & billing; SIEM export; compliance reports.

> Built as an MVP that actually runs. The core has **no third-party dependencies**;
> ML upgrades are additive.
