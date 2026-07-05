# Integration Guide

Sentra speaks the standard OpenAI and Anthropic chat protocols, so most tools
integrate with a one-line change.

## Option A — Transparent Gateway (recommended, zero code change)

Point your existing client's `base_url` at Sentra and add your credential headers.

### OpenAI SDK
```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="http://localhost:8100/v1",          # your Sentra host
    api_key=os.environ["OPENAI_API_KEY"],          # forwarded to the real provider
    default_headers={
        "X-Sentra-Client-Id": os.environ["SENTRA_CLIENT_ID"],
        "X-Sentra-Client-Secret": os.environ["SENTRA_CLIENT_SECRET"],
    },
)
client.chat.completions.create(model="gpt-4o",
    messages=[{"role": "user", "content": "..."}])
```
Set on the Sentra host: `SENTRA_UPSTREAM=https://api.openai.com`.

### Anthropic / Claude
Sentra also guards `/v1/messages`. Point the Anthropic SDK's base URL at Sentra
and set `SENTRA_UPSTREAM=https://api.anthropic.com`. Content blocks are inspected
and redacted per text block.

### Works with anything OpenAI-compatible
LangChain, LlamaIndex, internal copilots, IDE assistants, LiteLLM — all just need
the base URL + headers.

## Option B — SDK Wrapper (in-process)

```python
from openai import OpenAI
from sentra.sdk import guard, SentraBlocked

client = guard(OpenAI())            # the entire integration
try:
    client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "..."}],
        user="alice@acme.com")
except SentraBlocked as e:
    ...  # request refused before leaving the process
```

## Choosing a path
| | Gateway | SDK wrapper |
|---|---|---|
| Code change | base URL only | wrap the client |
| Covers non-Python apps | ✅ | ❌ |
| Central policy & audit | ✅ | per-process |
| Lowest latency | network hop | in-process |

Most orgs run the **gateway** for org-wide coverage and audit, and optionally the
**SDK** in critical services for defense-in-depth.
