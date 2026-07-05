# Module 4 — Gateway + SDK → one tenant

**Goal:** make both integration paths authenticate with the **same
`client_id`/`client_secret`** and land in the **same dashboard**. The gateway
already does (Module 2). Here you upgrade the **SDK** so its in-process
inspections also report to the tenant's dashboard — and add two "make-it-easy"
helpers.

---

## 4.1 Concept — three doors, one tenant

```
                       X-Membra-Client-Id / Secret
   ┌─ Gateway ───▶ POST /v1/chat/completions ──┐
   │  (base_url swap)                           │
   │                                            ├─▶  same tenant_id
   ├─ SDK ───────▶ inspect locally, then         │    same dashboard
   │  guard(client)  POST /v1/events (report) ──┘    same usage meter
   │
   └─ Agent ─────▶ POST /v1/agent/authorize ─────▶  (also same tenant)
```

The **credentials are the tenant identity.** Anything that presents them writes
into that tenant's audit log. The gateway forwards the *whole call*; the SDK
inspects *locally* (so it can block before the request ever leaves your process)
and then **reports the event** so you still see it in the dashboard.

## 4.2 Add an ingest endpoint — `/v1/events`

The SDK needs somewhere to POST its local decisions. Add to `server.py`:

```python
@app.post("/v1/events")
async def ingest_event(request: Request):
    tenant = _authed_tenant(request)
    if not tenant:
        return JSONResponse({"error": "invalid or missing client credentials"}, 401)
    e = json.loads(await request.body() or b"{}")
    store.log(tenant["id"], time.time(),
              e.get("user", "sdk-user"), e.get("action", "allow"),
              e.get("reasons", []), e.get("detail", {}),
              e.get("preview", ""), source="sdk")
    return {"ok": True}
```

Now the SDK can tag its events `source="sdk"` and they'll appear alongside
gateway traffic.

## 4.3 Rewrite `src/membra/sdk.py`

Two public helpers: `guard()` (in-process inspection + reporting) and
`gateway_client()` (a configured pass-through client). Both read credentials
from arguments or environment.

```python
# src/membra/sdk.py
"""Membra SDK — inspect AI calls in-process, and report them to your dashboard.

    from membra.sdk import guard
    client = guard(OpenAI())      # reads MEMBRA_CLIENT_ID / _SECRET / _URL from env
    client.chat.completions.create(model="gpt-4o", messages=[...])
"""
import os
import json
import threading
import urllib.request

from .engine import Engine, BLOCK, QUARANTINE, REDACT

_engine = Engine()


def _env(name, override):
    return override if override is not None else os.environ.get(name)


def _report(url, cid, secret, event):
    """Fire-and-forget: POST the local decision to the dashboard. Best-effort."""
    if not (url and cid and secret):
        return
    def _send():
        try:
            req = urllib.request.Request(
                url.rstrip("/") + "/v1/events",
                data=json.dumps(event).encode(), method="POST")
            req.add_header("content-type", "application/json")
            req.add_header("X-Membra-Client-Id", cid)
            req.add_header("X-Membra-Client-Secret", secret)
            urllib.request.urlopen(req, timeout=5).read()
        except Exception:
            pass  # telemetry must never break the caller's app
    threading.Thread(target=_send, daemon=True).start()


class MembraBlocked(Exception):
    def __init__(self, reasons):
        self.reasons = reasons
        super().__init__(f"Blocked by Membra: {', '.join(reasons)}")


class _GuardedCompletions:
    def __init__(self, inner, cfg):
        self._inner, self._cfg = inner, cfg

    def create(self, *, model, messages, user=None, **kw):
        user = user or self._cfg["user"]
        last = next((m for m in reversed(messages) if m.get("role") == "user"), None)
        text = (last or {}).get("content", "")
        d = _engine.inspect(user, text)

        _report(self._cfg["url"], self._cfg["cid"], self._cfg["secret"],
                {"user": user, "action": d.action, "reasons": d.reasons,
                 "detail": d.detail, "preview": text[:200]})

        if d.action in (BLOCK, QUARANTINE):
            raise MembraBlocked(d.reasons)
        if d.action == REDACT and last is not None:
            last["content"] = d.safe_text
        return self._inner.chat.completions.create(model=model, messages=messages, **kw)


class _Chat:
    def __init__(self, inner, cfg):
        self.completions = _GuardedCompletions(inner, cfg)


class GuardedClient:
    def __init__(self, inner, cfg):
        self._inner = inner
        self.chat = _Chat(inner, cfg)

    def __getattr__(self, name):        # passthrough for everything else
        return getattr(self._inner, name)


def guard(client, client_id=None, client_secret=None, membra_url=None, user="sdk-user"):
    """Wrap an OpenAI-style client so every chat call is inspected and reported."""
    cfg = {"cid": _env("MEMBRA_CLIENT_ID", client_id),
           "secret": _env("MEMBRA_CLIENT_SECRET", client_secret),
           "url": _env("MEMBRA_URL", membra_url) or "http://127.0.0.1:8100",
           "user": user}
    return GuardedClient(client, cfg)


def gateway_client(client_cls, client_id=None, client_secret=None, membra_url=None, **kw):
    """Build an OpenAI-style client pre-pointed at the Membra gateway.

        from openai import OpenAI
        client = gateway_client(OpenAI)   # reads creds + url from env
    """
    url = (_env("MEMBRA_URL", membra_url) or "http://127.0.0.1:8100").rstrip("/")
    return client_cls(
        base_url=url + "/v1",
        default_headers={"X-Membra-Client-Id": _env("MEMBRA_CLIENT_ID", client_id),
                         "X-Membra-Client-Secret": _env("MEMBRA_CLIENT_SECRET", client_secret)},
        **kw)
```

Export them for a clean `from membra import guard`:

```python
# src/membra/__init__.py  (add at the bottom)
from .sdk import guard, gateway_client, MembraBlocked   # noqa: E402,F401
```

> **Watch the import cost:** `sdk.py` imports `engine` → `detectors`, which are
> pure-stdlib. It does **not** import FastAPI. That's what keeps the base
> `pip install membra` lightweight — a rule to preserve as the package grows.

## 4.4 Make it easy — the two-line usage

Set credentials once in the environment:

```bash
export MEMBRA_CLIENT_ID=membra_ci_...
export MEMBRA_CLIENT_SECRET=membra_sk_...
export MEMBRA_URL=http://127.0.0.1:8100
```

**Path A — Gateway (zero app logic, server-side inspection):**
```python
from openai import OpenAI
from membra import gateway_client
client = gateway_client(OpenAI)
client.chat.completions.create(model="gpt-4o", messages=[{"role":"user","content":"hi"}])
```

**Path B — SDK (in-process, blocks before egress, reports to dashboard):**
```python
from openai import OpenAI
from membra import guard
client = guard(OpenAI())
client.chat.completions.create(model="gpt-4o", messages=[{"role":"user","content":"hi"}])
```

Both show up in the **same** dashboard, under the **same** tenant — gateway
events tagged `gateway`, SDK events tagged `sdk`.

## 4.5 Surface the source in the dashboard

Add a "Source" column so you can *see* the unification. In `templates.py`
`dashboard()`, add a header cell and render `e["source"]`; do the same in the JS
`refresh()` (`e.source`). Small change, big payoff — the demo in Module 5 lights
up all three sources in one feed.

---

## ✅ Done when

With one set of credentials in your env, a **gateway** call and an **SDK** call
both appear in the same dashboard feed — one tagged `gateway`, one tagged `sdk`
— and a blocked prompt via the SDK raises `MembraBlocked` locally *and* still
logs to the dashboard.

**Next → [Module 5: Hello-world demo agent](05-demo.md)**
