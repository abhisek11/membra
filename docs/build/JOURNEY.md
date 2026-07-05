# Project journey — decisions & conversation log

A running record of how this project evolved in conversation, so anyone (or
future-you) can see *why* things are the way they are. Reverse-chronology of
decisions at the top; full turn-by-turn log below.

_Last updated: 2026-07-04._

---

## Decisions locked in (the TL;DR)

| Topic | Decision | Where it lives |
|---|---|---|
| **Product name** | **Membra** (was "Sentra"; that name/domain was taken). Import `membra`, CLI `membra`, headers `X-Membra-*`. | Brand pivot, turn 8 |
| **What it is** | Open-source *immune system for AI agents*: injection defense, AI-DLP, behavioral anomaly, agent guardrails. | Original prototype |
| **Framework** | **FastAPI** app (was pure-stdlib `http.server`). | Module 2 |
| **Packaging** | **One full package**: server + SDK + CLI. FastAPI is an optional extra (`membra[server]`); base install is a zero-dep SDK. | Modules 1, 7 |
| **Billing** | **Simulated plans + usage limits** (Free/Team/Enterprise), enforced in-app with HTTP 402. No real payments. | Module 3 |
| **Unified tenant** | Gateway, SDK, and agent paths all use the **same `client_id`/`client_secret`** → same dashboard, tagged by `source`. | Module 4 |
| **Hero feature** | **Herd Immunity** — opt-in shared-threat signature network (privacy-safe, network-effect moat). | Module 6 |
| **Distribution** | Open source (MIT), publish to PyPI (TestPyPI → PyPI). | Module 7 |
| **Working style** | **Teach step-by-step; the user types the code.** Guide lives in `docs/build/`. | turn 7 |
| **Ops** | Cloud agents (on-demand + scheduled) for tests/build/release. | Module 8 |

---

## Open questions / to verify

- **Domain + PyPI name availability for "membra"** — not yet verified. Check
  `pip index versions membra` and a registrar before Module 7. Fallback:
  `membra-ai` as the distribution name (keep `import membra`).
- **Federation for Herd Immunity** — Module 6 ships the single-node version;
  cross-deployment sharing (`/v1/herd/*`) is designed but not built.
- **Packaged data files** — the ML model must move under `src/membra/data/` to
  ship inside the wheel (noted in Module 7.3).

---

## Turn-by-turn log

**1. "Show the flow diagram."**
Displayed the ASCII architecture diagram from `docs/architecture.md` (planes,
engine, detectors) and explained the request flow in words.

**2. "Design a component flow — how to use this."**
Read the code (`sdk.py`, `engine.py`, sequence diagrams) and built an HTML
**Artifact**: a 3-stage component-flow diagram — Onboard → Integrate
(gateway/SDK) → Inspect (detector pipeline + decision outcomes), plus the
agent-authorization parallel path. Semantic colors for block/quarantine/redact/allow.

**3. "How is app used, how is gateway used, how is sdk."**
Explained the three original surfaces from the code:
- `app.py` = full multitenant SaaS server (auth, dashboard, `/v1`).
- `gateway.py` = minimal single-tenant reference proxy (no auth).
- `sdk.py` = in-process `guard(OpenAI())` wrapper (no server).
Noted all three converge on `engine.py`, with a side-by-side comparison table.

**4. "Make this a whole FastAPI app; keep dashboard + multitenancy; unify
gateway + SDK to the same tenant + dashboard; add a demo agent."**
Read the full codebase (`auth.py`, `store.py`, `templates.py`, detectors,
demos). Installed FastAPI + uvicorn. Began scoping the unification.

**5. "Also make it a pip package + PyPI + free tier + usage monitoring +
subscription; teach me the steps in a reviewable document."**
Scope expanded significantly. Asked three scoping questions →
**Answers: simulated plans; one full package (server+SDK+CLI); build core +
doc alongside.**

**6. "Don't write the code — teach me each step with the code; also set up
cloud agents for my engineering pipeline."**
Mode changed to **teaching**. Delivered the curriculum + a full in-chat lesson
for Step 1 (package skeleton). Flagged cloud agents as a later module needing
explicit go-ahead (billable).

**7. "Rename it — 'sentra' is taken. This space has ~185 startups; how am I
different? Add features no one is doing; make a hero product. I want to build a
cybersecurity firm."**
Delivered a positioning strategy: honest note that domain availability can't be
guaranteed; naming shortlist across 3 themes; the market's 3 clusters and their
gaps; the wedge (OSS + agent-native + adaptive); the **Herd Immunity** hero
concept; and an open-core GTM sketch.

**8. "I'll go with Membra. Make the docs I can read to build the app step by
step."**
Wrote this step-by-step guide under `docs/build/` (README + Modules 1–8),
rebranded to Membra, with all locked decisions baked in.

**9. "Also document our whole chat for reference."**
This file.

**10. "Make the demo real — use the OpenAI package, swap in my Membra URL."**
Rewrote Module 5 to use the genuine `openai` Python SDK. The only integration
change is `base_url` → the Membra URL (via `MEMBRA_URL` env), so the identical
demo runs offline (mock) or against a deployed Membra with zero code change.
Uses `with_raw_response` to read the `X-Membra-Action` header.

---

## Artifacts produced this project

- **Component-flow diagram** (HTML Artifact) — how to use Membra, 3 stages + agent path.
- **`docs/build/`** — the 9-part build guide (this journey + 8 modules + index).

## Where to pick up

You're implementing **[Module 1](01-package.md)**. The natural path is 1 → 8 in
order; Modules 6 (Herd Immunity) and 8 (cloud agents) can come after a working
1–5 core. Ping me to: verify the `membra` name, dispatch a cloud agent to draft
`tests/`, or rewrite `README.md`/`architecture.md` around the Membra brand.
