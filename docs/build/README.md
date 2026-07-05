# Building Membra — a step-by-step guide

> **Membra** — the open-source *immune system* for AI agents. It learns your
> normal, guards every tool call, and (opt-in) gets smarter across every
> deployment via a shared-threat network.

This is a **teaching guide**, not a finished codebase. You read a module, type
the code yourself, run it, watch it work — then move to the next. Each step ends
with a **✅ Done when…** check so you always know you're on solid ground.

---

## What you're building

One installable Python package, `membra`, that is three things at once:

- a **FastAPI app** — marketing site + multitenant dashboard + the `/v1` data plane
- an **SDK** — `guard(client)` to inspect calls in-process
- a **CLI** — `membra serve`, `membra demo`

All three share **one tenant identity** (a `client_id` + `client_secret`), so
whether traffic arrives through the gateway URL or the SDK, it lands in the
**same dashboard** under the **same tenant**.

### The decisions we locked in
| Decision | Choice |
|---|---|
| Billing | **Simulated plans + usage limits** (Free/Team/Enterprise, enforced in-app, no real money) |
| Package | **One full package**: server + SDK + CLI, with FastAPI as an optional extra |
| Brand | **Membra**, import name `membra`, command `membra`, headers `X-Membra-*` |
| Hero feature | **Herd Immunity** — opt-in shared-threat network |

---

## Architecture at a glance

```
                 ┌───────────────────────── Membra package ─────────────────────────┐
  Browser ─────▶ │  Control plane            Data plane (/v1/*)                       │
                 │  site · auth · dashboard   chat · messages · agent · events        │
  App/SDK ──id──▶│        │                          │                               │──▶ LLM
   +secret       │        ▼                          ▼                               │   provider
                 │   ┌──────────┐            ┌──────────────┐   ┌──────────────┐      │
                 │   │TenantStore│◀──────────│  Plan/quota  │──▶│    Engine    │      │
                 │   │  + Store  │  usage     │  gate (402)  │   │  detectors   │      │
                 │   │ (SQLite)  │◀───────────┴──────────────┴───│  + decision  │      │
                 │   └──────────┘   audit log (per tenant, incl. source=gw|sdk|agent) │
                 └───────────────────────────────────────────────────────────────────┘
```

One SQLite DB (`data/membra.db`) is the shared spine: **tenants**, **sessions**,
and **events** (every inspected call, tagged by tenant *and* source).

---

## The curriculum

| # | Module | You'll learn | Outcome |
|---|--------|--------------|---------|
| [1](01-package.md) | **Package skeleton** | `pyproject.toml`, src-layout, editable install, CLI entry point | `membra version` works |
| [2](02-server.md) | **FastAPI unification** | Port the server to FastAPI: site + dashboard + `/v1` | `membra serve` runs it all |
| [3](03-subscription.md) | **Metering + plans** | Count calls per tenant, enforce quota, 402 on overage | Simulated subscription live |
| [4](04-integrations.md) | **Gateway + SDK → one tenant** | Shared creds; both paths log to one dashboard | Three doors, one tenant |
| [5](05-demo.md) | **Hello-world agent** | A script driving clean/attack/PII/agent traffic | `membra demo` proves it |
| [6](06-herd-immunity.md) | **Herd Immunity (hero)** | Opt-in shared-threat signatures across deployments | Your moat, working |
| [7](07-publish.md) | **Publish to PyPI** | `build`, `twine`, TestPyPI → PyPI, tokens | Live on `pip install` |
| [8](08-cloud-agents.md) | **Cloud agents pipeline** | Automate tests/build/release with agents | Hands-off eng pipeline |

---

## Prerequisites

```bash
python --version          # need 3.10+
pip install --upgrade pip
```

You already have the **detection core** from the prototype (`engine.py`,
`detectors/`). This guide **reuses** it and builds the package, the unified
server, metering, the SDK, and the demo *around* it. Where a module says
"reuse," you keep your existing file (renamed under `membra/`).

> **Naming reminder:** before Module 7, verify `membra` is free on PyPI
> (`pip index versions membra`) and grab the matching domain. If taken, pick a
> distribution name like `membra-ai` — you can keep `import membra` either way
> (Module 1 explains how).

**Start here → [Module 1: Package skeleton](01-package.md)**
