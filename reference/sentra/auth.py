"""Multitenancy + auth for the Sentra SaaS.

Each signup creates a TENANT with:
  - login credentials (email + salted PBKDF2 password hash)  -> for the dashboard
  - an API credential pair (client_id + client_secret)        -> for the SDK/gateway

The client_secret is shown ONCE at creation (and on regenerate); we only store
its hash. Dashboard sessions are cookie tokens stored server-side.
"""
import sqlite3
import hashlib
import hmac
import secrets
import time
import threading
import os

_LOCK = threading.Lock()


def _hash_pw(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def _hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


class TenantStore:
    def __init__(self, path: str = "data/sentra.db"):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.path = path
        self._init()

    def _conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def _init(self):
        with _LOCK, self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS tenants(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org TEXT, email TEXT UNIQUE, salt TEXT, pw_hash TEXT,
                client_id TEXT UNIQUE, secret_hash TEXT,
                plan TEXT DEFAULT 'free', created REAL)""")
            c.execute("""CREATE TABLE IF NOT EXISTS sessions(
                token TEXT PRIMARY KEY, tenant_id INTEGER, created REAL)""")

    # ---- signup / login -------------------------------------------------
    def signup(self, org: str, email: str, password: str):
        salt = secrets.token_hex(16)
        client_id = "sentra_ci_" + secrets.token_hex(12)
        client_secret = "sentra_sk_" + secrets.token_urlsafe(32)
        with _LOCK, self._conn() as c:
            exists = c.execute("SELECT 1 FROM tenants WHERE email=?", (email,)).fetchone()
            if exists:
                raise ValueError("An account with that email already exists.")
            cur = c.execute(
                """INSERT INTO tenants(org,email,salt,pw_hash,client_id,secret_hash,created)
                   VALUES(?,?,?,?,?,?,?)""",
                (org, email, salt, _hash_pw(password, salt), client_id,
                 _hash_secret(client_secret), time.time()))
            tenant_id = cur.lastrowid
        # client_secret returned ONCE, never stored in plaintext
        return {"tenant_id": tenant_id, "client_id": client_id,
                "client_secret": client_secret}

    def login(self, email: str, password: str):
        with _LOCK, self._conn() as c:
            row = c.execute("SELECT * FROM tenants WHERE email=?", (email,)).fetchone()
            if not row:
                return None
            if not hmac.compare_digest(row["pw_hash"], _hash_pw(password, row["salt"])):
                return None
            token = secrets.token_urlsafe(24)
            c.execute("INSERT INTO sessions(token,tenant_id,created) VALUES(?,?,?)",
                      (token, row["id"], time.time()))
        return token

    def logout(self, token):
        with _LOCK, self._conn() as c:
            c.execute("DELETE FROM sessions WHERE token=?", (token,))

    def session_tenant(self, token):
        if not token:
            return None
        with _LOCK, self._conn() as c:
            row = c.execute(
                """SELECT t.* FROM sessions s JOIN tenants t ON t.id=s.tenant_id
                   WHERE s.token=?""", (token,)).fetchone()
        return dict(row) if row else None

    # ---- API credential verification (used by the gateway) --------------
    def verify_client(self, client_id: str, client_secret: str):
        if not client_id or not client_secret:
            return None
        with _LOCK, self._conn() as c:
            row = c.execute("SELECT * FROM tenants WHERE client_id=?", (client_id,)).fetchone()
        if not row:
            return None
        if not hmac.compare_digest(row["secret_hash"], _hash_secret(client_secret)):
            return None
        return dict(row)

    def regenerate_secret(self, tenant_id: int):
        client_secret = "sentra_sk_" + secrets.token_urlsafe(32)
        with _LOCK, self._conn() as c:
            c.execute("UPDATE tenants SET secret_hash=? WHERE id=?",
                      (_hash_secret(client_secret), tenant_id))
        return client_secret

    def get(self, tenant_id):
        with _LOCK, self._conn() as c:
            row = c.execute("SELECT * FROM tenants WHERE id=?", (tenant_id,)).fetchone()
        return dict(row) if row else None
