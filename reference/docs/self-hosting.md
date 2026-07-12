# Self-Hosting

Sentra's core is pure Python standard library — no dependencies.

## Bare metal / VM
```bash
python3 -m sentra.detectors.ml_injection   # train model once (creates data/injection_model.json)
export SENTRA_UPSTREAM=https://api.openai.com
python3 -m sentra.app                        # http://localhost:8100
```

Environment variables:
| Var | Default | Purpose |
|---|---|---|
| `SENTRA_PORT` | `8100` | Listen port |
| `SENTRA_UPSTREAM` | `http://127.0.0.1:8090` | Real LLM provider base URL |

State lives in `data/sentra.db` (SQLite) — back it up to persist tenants & audit log.

## Docker
```bash
docker build -t sentra .
docker run -p 8100:8100 -e SENTRA_UPSTREAM=https://api.openai.com \
  -v sentra-data:/app/data sentra
```
(If you hit a Docker socket permission error, run with `sudo` or add your user to
the `docker` group: `sudo usermod -aG docker $USER` then re-login.)

## Docker Compose (with mock model for a self-contained demo)
```bash
docker compose up --build       # Sentra on :8100, mock model on :8090
```

## Production hardening checklist
- Terminate TLS in front (nginx / Caddy / cloud LB).
- Split control plane (dashboard) and data plane (gateway) onto separate hosts.
- Put the data plane behind your VPC; only expose the dashboard to admins.
- Rotate client secrets from the dashboard; store them in a secrets manager.
- Ship `events` to your SIEM for alerting.
- Add rate limits / WAF at the edge.

## Scaling notes (roadmap)
- Swap SQLite for Postgres for multi-instance deployments.
- Move sessions to Redis; run the app stateless behind a load balancer.
- Cache the ML model in memory (already loaded once per process).
