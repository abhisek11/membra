"""Sentra SaaS server — marketing site + docs + multitenant dashboard + API.

One process, one port. In production you'd split the control plane (app.sentra.io)
from the data plane (gateway.sentra.io); here they share a server for easy running.

Run:  python3 -m sentra.app      ->  http://localhost:8100
"""
import json
import os
import time
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie

from .engine import Engine, BLOCK, QUARANTINE, REDACT
from .store import Store
from .auth import TenantStore
from . import templates as T
from .docs_page import docs_page

PORT = int(os.environ.get("SENTRA_PORT", "8100"))
UPSTREAM = os.environ.get("SENTRA_UPSTREAM", "http://127.0.0.1:8090")

engine = Engine()
store = Store()
tenants = TenantStore()


def _refusal(model, message):
    return {"id": "sentra-guard", "object": "chat.completion", "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": message},
                         "finish_reason": "content_filter"}]}


def _last_user_message(payload):
    """Return (message_obj, extracted_text) for OpenAI or Anthropic payloads.
    Anthropic message content can be a list of blocks; we join the text blocks.
    """
    for m in reversed(payload.get("messages", [])):
        if m.get("role") == "user":
            c = m.get("content", "")
            if isinstance(c, str):
                return m, c
            if isinstance(c, list):
                text = " ".join(b.get("text", "") for b in c
                                if isinstance(b, dict) and b.get("type") == "text")
                return m, text
    return None, ""


def _apply_redaction(message, safe_text):
    """Write redacted text back, preserving the original content shape."""
    c = message.get("content", "")
    if isinstance(c, str):
        message["content"] = safe_text
    elif isinstance(c, list):
        from .detectors.dlp import scan_dlp, redact
        for b in c:
            if isinstance(b, dict) and b.get("type") == "text":
                b["text"] = redact(b["text"], scan_dlp(b["text"])["findings"])


def _forward(path, body_bytes, headers):
    req = urllib.request.Request(UPSTREAM + path, data=body_bytes, method="POST")
    if "authorization" in headers:
        req.add_header("authorization", headers["authorization"])
    req.add_header("content-type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    # ---- helpers -------------------------------------------------------
    def _html(self, body, code=200, cookie=None):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj, code=200, extra=None):
        data = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, to, cookie=None):
        self.send_response(302)
        self.send_header("Location", to)
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()

    def _session(self):
        c = SimpleCookie(self.headers.get("Cookie", ""))
        token = c["sid"].value if "sid" in c else None
        return tenants.session_tenant(token)

    def _form(self):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n).decode()
        return {k: v[0] for k, v in urllib.parse.parse_qs(raw).items()}, raw

    # ---- GET -----------------------------------------------------------
    def do_GET(self):
        path = self.path.split("?")[0]
        tenant = self._session()
        if path == "/":
            return self._html(T.landing(tenant))
        if path == "/products":
            return self._html(T.products(tenant))
        if path == "/pricing":
            return self._html(T.pricing(tenant))
        if path == "/docs":
            return self._html(docs_page(tenant))
        if path == "/login":
            return self._html(T.auth_page("login"))
        if path == "/signup":
            return self._html(T.auth_page("signup"))
        if path == "/logout":
            c = SimpleCookie(self.headers.get("Cookie", ""))
            if "sid" in c:
                tenants.logout(c["sid"].value)
            return self._redirect("/", cookie="sid=; Path=/; Max-Age=0")
        if path == "/dashboard":
            if not tenant:
                return self._redirect("/login")
            return self._html(T.dashboard(tenant, store.stats(tenant["id"]),
                                          store.recent(tenant["id"])))
        if path == "/api/events":
            if not tenant:
                return self._json({"error": "unauthorized"}, 401)
            return self._json({"events": store.recent(tenant["id"]),
                               "stats": store.stats(tenant["id"])})
        return self._html("<div class='wrap'><h2>404</h2></div>", 404)

    # ---- POST ----------------------------------------------------------
    def do_POST(self):
        path = self.path.split("?")[0]

        if path == "/signup":
            form, _ = self._form()
            try:
                creds = tenants.signup(form.get("org", ""), form["email"], form["password"])
            except (KeyError, ValueError) as e:
                return self._html(T.auth_page("signup", str(e) or "Missing fields"))
            token = tenants.login(form["email"], form["password"])
            return self._html(T.signup_success(creds),
                              cookie=f"sid={token}; Path=/; HttpOnly")

        if path == "/login":
            form, _ = self._form()
            token = tenants.login(form.get("email", ""), form.get("password", ""))
            if not token:
                return self._html(T.auth_page("login", "Invalid email or password."))
            return self._redirect("/dashboard", cookie=f"sid={token}; Path=/; HttpOnly")

        if path == "/dashboard/regen":
            tenant = self._session()
            if not tenant:
                return self._redirect("/login")
            new_secret = tenants.regenerate_secret(tenant["id"])
            return self._html(T.dashboard(tenants.get(tenant["id"]),
                                          store.stats(tenant["id"]),
                                          store.recent(tenant["id"]), new_secret=new_secret))

        # ---------- tenant-authenticated API ----------
        if path.startswith("/v1/"):
            return self._api(path)

        return self._json({"error": "not found"}, 404)

    def _api(self, path):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n)
        cid = self.headers.get("X-Sentra-Client-Id")
        csecret = self.headers.get("X-Sentra-Client-Secret")
        tenant = tenants.verify_client(cid, csecret)
        if not tenant:
            return self._json({"error": "invalid or missing client credentials"}, 401)
        tid = tenant["id"]
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return self._json({"error": "invalid json"}, 400)
        user = self.headers.get("X-Sentra-User", "anonymous")

        # agent action authorization
        if path.startswith("/v1/agent/authorize"):
            d = engine.authorize_action(user, payload.get("tool", ""), payload.get("args", {}))
            gd = d.detail.get("agent_guard", {})
            store.log(tid, time.time(), user, d.action, d.reasons, d.detail,
                      f"{payload.get('tool','')} {payload.get('args','')}")
            return self._json({"decision": gd.get("action"), "tier": gd.get("tier"),
                               "reasons": d.reasons, "tool": payload.get("tool", "")},
                              extra={"X-Sentra-Action": d.action})

        # chat: OpenAI (/v1/chat/completions) AND Anthropic/Claude (/v1/messages)
        if path.startswith("/v1/chat/completions") or path.startswith("/v1/messages"):
            model = payload.get("model", "unknown")
            last, text = _last_user_message(payload)
            d = engine.inspect(user, text)
            store.log(tid, time.time(), user, d.action, d.reasons, d.detail, text)
            hdr = {"X-Sentra-Action": d.action, "X-Sentra-Reasons": "; ".join(d.reasons)}
            if d.action in (BLOCK, QUARANTINE):
                msg = (f"⚠️ Blocked by Sentra ({'; '.join(d.reasons)}). "
                       "Contact your security team if this is an error.")
                return self._json(_refusal(model, msg), extra=hdr)
            if d.action == REDACT and last is not None:
                _apply_redaction(last, d.safe_text)   # handles str or content-blocks
                raw = json.dumps(payload).encode()
            try:
                up = _forward(path, raw, self.headers)
            except Exception as e:
                return self._json({"error": f"upstream error: {e}"}, 502, hdr)
            return self._json(up, extra=hdr)

        return self._json({"error": "unsupported endpoint"}, 404)


def serve():
    print(f"◈ Sentra SaaS on http://localhost:{PORT}")
    print(f"   site: /   docs: /docs   signup: /signup   dashboard: /dashboard")
    print(f"   API upstream -> {UPSTREAM}")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()


if __name__ == "__main__":
    serve()
