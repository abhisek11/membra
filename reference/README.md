# reference/ — the original prototype (archived)

This folder holds the **original working prototype** (built under the old name
"Sentra"). It is kept here as a **reference** while we hand-build the new
**Membra** package from scratch, following the guide in
[`../docs/build/`](../docs/build/README.md).

**Nothing here is imported by the new code.** When a build module says "reuse the
detection core," you copy the relevant file *out* of here into `src/membra/` and
rebrand it — you don't import from `reference/`.

## What's in here
| Path | What it is |
|---|---|
| `sentra/` | the original package: `app.py`, `gateway.py`, `sdk.py`, `engine.py`, `detectors/`, `auth.py`, `store.py`, `templates.py` |
| `demo/` | original demo scripts + `mock_upstream.py` (a fake offline model) |
| `docs/` | original marketing/architecture docs |
| `data/` | the trained ML injection model (`injection_model.json`) |
| `Dockerfile`, `docker-compose.yml`, `run_demo.sh` | original packaging/run scripts |

## Most useful pieces to copy forward
As you build Membra, these are the reusable, brand-neutral cores worth lifting
from `sentra/` (rebrand strings, keep the logic):
- `detectors/` — injection, ml_injection, dlp, anomaly, agent_guard (+ `data/injection_model.json`)
- `engine.py` — the detector orchestration + `Decision`
- `auth.py` — `TenantStore` (tenants, sessions, client_id/secret)
- `store.py` — the SQLite audit log
- `templates.py` — the site/dashboard HTML
