"""SQLite audit log — every inspected AI interaction, scoped per TENANT."""
import sqlite3
import json
import threading
import os

_LOCK = threading.Lock()


class Store:
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
            c.execute(
                """CREATE TABLE IF NOT EXISTS events(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id INTEGER, ts REAL, user TEXT, action TEXT,
                    reasons TEXT, detail TEXT, preview TEXT)""")
            # migrate older single-tenant DBs
            cols = [r["name"] for r in c.execute("PRAGMA table_info(events)")]
            if "tenant_id" not in cols:
                c.execute("ALTER TABLE events ADD COLUMN tenant_id INTEGER")

    def log(self, tenant_id, ts, user, action, reasons, detail, preview):
        with _LOCK, self._conn() as c:
            c.execute(
                """INSERT INTO events(tenant_id,ts,user,action,reasons,detail,preview)
                   VALUES(?,?,?,?,?,?,?)""",
                (tenant_id, ts, user, action, json.dumps(reasons),
                 json.dumps(detail), preview[:200]))

    def recent(self, tenant_id, limit=100):
        with _LOCK, self._conn() as c:
            rows = c.execute(
                "SELECT * FROM events WHERE tenant_id=? ORDER BY id DESC LIMIT ?",
                (tenant_id, limit)).fetchall()
        return [dict(r) for r in rows]

    def stats(self, tenant_id):
        with _LOCK, self._conn() as c:
            rows = c.execute(
                "SELECT action, COUNT(*) n FROM events WHERE tenant_id=? GROUP BY action",
                (tenant_id,)).fetchall()
        return {r["action"]: r["n"] for r in rows}
