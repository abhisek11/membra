"""Sentra Gateway — an OpenAI/Anthropic-compatible inline proxy.

THE INTEGRATION STORY
=====================
An organization installs Sentra ONCE and changes ONE line in their app: the
`base_url` their AI client points at. Every call to OpenAI / Anthropic (Claude)
/ Azure then transparently flows through Sentra and gets inspected.

    # before
    client = OpenAI(base_url="https://api.openai.com/v1")
    # after  (that's the whole integration)
    client = OpenAI(base_url="http://sentra.internal:8100/v1")

No app rewrite. Works for any tool that speaks the OpenAI chat protocol —
custom apps, LangChain, LlamaIndex, internal copilots, IDE assistants, etc.

Endpoints:
    POST /v1/chat/completions   -> inspect, then forward to UPSTREAM
    GET  /                      -> live dashboard
    GET  /events                -> JSON threat feed
"""
import json
import time
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .engine import Engine, BLOCK, QUARANTINE, REDACT
from .store import Store
from .dashboard import DASHBOARD_HTML

UPSTREAM = os.environ.get("SENTRA_UPSTREAM", "http://127.0.0.1:8090")
PORT = int(os.environ.get("SENTRA_PORT", "8100"))

engine = Engine()
store = Store()


def _refusal_response(model, message):
    """An OpenAI-shaped response so the caller's app never breaks."""
    return {
        "id": "sentra-guard",
        "object": "chat.completion",
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": message},
            "finish_reason": "content_filter",
        }],
        "sentra": {"action": "blocked"},
    }


def _forward_upstream(path, body_bytes, headers):
    req = urllib.request.Request(UPSTREAM + path, data=body_bytes, method="POST")
    for k in ("authorization", "content-type"):
        if k in headers:
            req.add_header(k, headers[k])
    req.add_header("content-type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet default logging
        pass

    def _send(self, code, obj, extra_headers=None):
        data = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            data = DASHBOARD_HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path.startswith("/events"):
            self._send(200, {"events": store.recent(), "stats": store.stats()})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        known = ("/v1/chat/completions", "/v1/agent/authorize")
        if not any(self.path.startswith(p) for p in known):
            self._send(404, {"error": "unsupported endpoint"})
            return

        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid json"})
            return

        # ---- agent action authorization (the T-cell layer) ----
        if self.path.startswith("/v1/agent/authorize"):
            user = self.headers.get("X-Sentra-User", "agent")
            tool = payload.get("tool", "")
            args = payload.get("args", {})
            d = engine.authorize_action(user, tool, args)
            gd = d.detail.get("agent_guard", {})
            store.log(time.time(), user, d.action, d.reasons, d.detail, f"{tool} {args}")
            self._send(200, {"decision": gd.get("action"), "tier": gd.get("tier"),
                             "reasons": d.reasons, "tool": tool},
                       {"X-Sentra-Action": d.action})
            return

        model = payload.get("model", "unknown")
        # identify the user: header wins, else API-key tail, else 'anonymous'
        user = (self.headers.get("X-Sentra-User")
                or (self.headers.get("Authorization", "")[-6:] or "anonymous"))
        messages = payload.get("messages", [])
        last_user = next((m for m in reversed(messages) if m.get("role") == "user"), None)
        text = (last_user or {}).get("content", "") if last_user else ""

        decision = engine.inspect(user, text)
        store.log(time.time(), user, decision.action, decision.reasons,
                  decision.detail, text)

        hdr = {"X-Sentra-Action": decision.action,
               "X-Sentra-Reasons": "; ".join(decision.reasons)}

        # blocked / quarantined -> never reach the model
        if decision.action in (BLOCK, QUARANTINE):
            msg = ("⚠️ This request was blocked by Sentra AI security "
                   f"({'; '.join(decision.reasons)}). If this is a mistake, "
                   "contact your security team.")
            self._send(200, _refusal_response(model, msg), hdr)
            return

        # redact -> rewrite the outgoing message, then forward
        if decision.action == REDACT and last_user is not None:
            last_user["content"] = decision.safe_text
            raw = json.dumps(payload).encode()

        try:
            upstream_bytes = _forward_upstream(self.path, raw, self.headers)
        except Exception as e:  # upstream unreachable
            self._send(502, {"error": f"upstream error: {e}"}, hdr)
            return

        self._send(200, upstream_bytes, hdr)


def serve():
    print(f"Sentra Gateway listening on http://127.0.0.1:{PORT}")
    print(f"  -> forwarding clean traffic to UPSTREAM = {UPSTREAM}")
    print(f"  -> dashboard at http://127.0.0.1:{PORT}/")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    serve()
