# ◈ Membra — the open-source immune system for AI agents

> One line to install. It blocks prompt injection and data leaks, guards every
> agent tool call — and because it's a network, every deployment makes all the
> others stronger.

Firewalls and antivirus guard the network and the files. When a company wires
LLMs and autonomous agents into its workflows, it opens a **new attack surface
those tools can't see** — the prompt/response channel and the actions agents
take. **Membra is the inline immune layer that can.**

```python
# talking to OpenAI directly:
client = OpenAI()

# talking THROUGH Membra — the entire change:
client = OpenAI(base_url="https://gateway.membra.ai/v1",
                default_headers={"X-Membra-Client-Id": ID,
                                 "X-Membra-Client-Secret": SECRET})
```

## What it does

| Immune concept | What Membra does |
|---|---|
| 🦠 Antigen detection | Block **prompt injection / jailbreaks** (regex signals + trained ML ensemble) |
| 🩸 Barrier defense | **AI-DLP**: redact secrets & PII before they leave your org |
| 🧠 Immune memory | Learn each user's normal usage; flag **behavioral anomalies** |
| 🛡️ T-cell guardrails | Gate risky **autonomous-agent actions** (allow / approve / deny) |
| 🌐 Herd immunity | An attack seen by **any** deployment vaccinates **every** deployment |

## Why Membra (vs. the crowd)

Three things stacked that no competitor combines:

- **Open-source & dev-first** — `pip install membra`, one line. Bottom-up
  adoption, not a six-month enterprise sale.
- **Agent-native** — guards *tool calls and actions*, not just prompt-in/out.
  That's where 2026's real risk lives.
- **It learns** — per-user behavioral baselines, not the same static regex
  everyone else ships. And **Herd Immunity** is a network-effect moat competitors
  structurally can't copy.

## Status

This repo is being **hand-built, step by step**, from an earlier working
prototype. The complete build guide is in **[`docs/build/`](docs/build/README.md)**:

| Module | Topic |
|---|---|
| [1](docs/build/01-package.md) | Package skeleton (`pip install -e .`, the `membra` CLI) |
| [2](docs/build/02-server.md) | FastAPI app: site + dashboard + `/v1` data plane |
| [3](docs/build/03-subscription.md) | Usage metering + simulated plans |
| [4](docs/build/04-integrations.md) | Gateway + SDK → one tenant, one dashboard |
| [5](docs/build/05-demo.md) | Hello-world demo with the real OpenAI SDK |
| [6](docs/build/06-herd-immunity.md) | Herd Immunity (the hero feature) |
| [7](docs/build/07-publish.md) | Publish to PyPI |
| [8](docs/build/08-cloud-agents.md) | Cloud agents for the engineering pipeline |

The original prototype is archived in **[`reference/`](reference/README.md)** —
kept for reference and to copy the detection core forward as we build.

See **[docs/build/JOURNEY.md](docs/build/JOURNEY.md)** for the full decision log.

## License

MIT — see [LICENSE](LICENSE) (added in Module 1).
