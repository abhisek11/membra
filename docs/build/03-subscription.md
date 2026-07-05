# Module 3 — Metering + simulated subscription

**Goal:** give every tenant a **plan** (Free / Team / Enterprise), **count**
their inspected calls, and **enforce** the Free-tier quota with a clean `402
Payment Required`. No real money — pure in-app logic you fully control.

---

## 3.1 Concept — metering without a billing provider

A subscription is really two questions:
1. **How much has this tenant used this billing period?** → *metering*
2. **Is that under their plan's limit?** → *enforcement*

You already log every inspected call to the `events` table. So "usage this
month" is just a `COUNT(*)` with a timestamp filter — no separate meter needed.
That's the cheapest correct design; you can graduate to a dedicated `usage`
table later if you need per-endpoint metering.

## 3.2 Define the plans — `src/membra/plans.py`

```python
# src/membra/plans.py
"""Simulated subscription plans. No real billing — limits enforced in-app."""

PLANS = {
    "free":       {"label": "Free",       "limit": 10_000,    "price": 0},
    "team":       {"label": "Team",       "limit": 1_000_000, "price": 99},
    "enterprise": {"label": "Enterprise", "limit": None,      "price": None},  # None = unlimited
}

DEFAULT_PLAN = "free"


def plan_for(tenant) -> dict:
    return PLANS.get((tenant or {}).get("plan", DEFAULT_PLAN), PLANS[DEFAULT_PLAN])


def over_quota(used: int, tenant) -> bool:
    limit = plan_for(tenant)["limit"]
    return limit is not None and used >= limit
```

## 3.3 Add usage counting to `store.py`

Add a `month_usage` method and a `source` column (from Module 2). Edit
`src/membra/store.py`:

```python
    def _init(self):
        with _LOCK, self._conn() as c:
            c.execute(
                """CREATE TABLE IF NOT EXISTS events(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id INTEGER, ts REAL, user TEXT, action TEXT,
                    reasons TEXT, detail TEXT, preview TEXT, source TEXT)""")
            # migrate older DBs that predate these columns
            cols = [r["name"] for r in c.execute("PRAGMA table_info(events)")]
            if "tenant_id" not in cols:
                c.execute("ALTER TABLE events ADD COLUMN tenant_id INTEGER")
            if "source" not in cols:
                c.execute("ALTER TABLE events ADD COLUMN source TEXT")

    def log(self, tenant_id, ts, user, action, reasons, detail, preview, source="gateway"):
        with _LOCK, self._conn() as c:
            c.execute(
                """INSERT INTO events(tenant_id,ts,user,action,reasons,detail,preview,source)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (tenant_id, ts, user, action, json.dumps(reasons),
                 json.dumps(detail), preview[:200], source))

    def month_usage(self, tenant_id, now=None):
        """Count events for this tenant since the start of the current month."""
        import time as _t
        now = now or _t.time()
        lt = _t.localtime(now)
        month_start = _t.mktime((lt.tm_year, lt.tm_mon, 1, 0, 0, 0, 0, 0, -1))
        with _LOCK, self._conn() as c:
            row = c.execute(
                "SELECT COUNT(*) n FROM events WHERE tenant_id=? AND ts>=?",
                (tenant_id, month_start)).fetchone()
        return row["n"]
```

> **Why count events, not calls-before-inspection?** Every inspected call
> produces exactly one event, so the count is the call count. Blocked calls
> still consumed inspection compute, so they *should* count against quota —
> which this design does naturally.

## 3.4 Enforce the quota in the data plane

In `server.py`, add a check right after you resolve the tenant, **before**
running the engine. Factor it into a helper:

```python
from .plans import plan_for, over_quota

def _quota_guard(tenant):
    """Return a 402 JSONResponse if the tenant is over plan, else None."""
    used = store.month_usage(tenant["id"])
    if over_quota(used, tenant):
        p = plan_for(tenant)
        return JSONResponse(
            {"error": "quota_exceeded",
             "message": f"Monthly limit of {p['limit']} calls reached on the {p['label']} plan.",
             "used": used, "limit": p["limit"], "upgrade": "/pricing"},
            status_code=402)
    return None
```

Then in both `data_plane_chat` and `data_plane_agent`, right after the
`_authed_tenant` check:

```python
    blocked = _quota_guard(tenant)
    if blocked:
        return blocked
```

## 3.5 Show usage on the dashboard

Pass usage into the dashboard template. In `server.py`'s `dashboard` route:

```python
    used = store.month_usage(tenant["id"])
    p = plan_for(tenant)
    return T.dashboard(tenant, store.stats(tenant["id"]),
                       store.recent(tenant["id"]), usage=(used, p))
```

Then in `templates.py`'s `dashboard(...)`, accept `usage=None` and render a
meter near the stats:

```python
def dashboard(tenant, stats, events, new_secret=None, usage=None):
    ...
    usage_block = ""
    if usage:
        used, p = usage
        limit = p["limit"]
        pct = 0 if not limit else min(100, round(100 * used / limit))
        cap = f"{used:,} / {limit:,}" if limit else f"{used:,} / ∞"
        bar = (f'<div style="background:#0a1020;border:1px solid var(--line);border-radius:8px;'
               f'height:10px;overflow:hidden;margin-top:6px">'
               f'<div style="width:{pct}%;height:100%;background:var(--cyan)"></div></div>')
        usage_block = (f'<div class="panel"><h3 style="margin-top:0">Usage · {p["label"]} plan</h3>'
                       f'<p class="muted">{cap} calls this month</p>{bar}'
                       f'<p class="muted" style="font-size:13px;margin-top:10px">'
                       f'<a href="/pricing">Upgrade →</a></p></div>')
    # ...insert {usage_block} into the dashgrid, e.g. above the threat feed panel
```

## 3.6 Test the paywall

Temporarily set a tiny limit to see enforcement without making 10k calls:

```python
# in plans.py, TEMPORARILY:
"free": {"label": "Free", "limit": 3, "price": 0},
```

```bash
membra serve &
# make 4 calls with your creds; the 4th returns HTTP 402:
for i in 1 2 3 4; do
  curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8100/v1/chat/completions \
    -H "X-Membra-Client-Id: $ID" -H "X-Membra-Client-Secret: $SECRET" \
    -H "content-type: application/json" \
    -d '{"model":"gpt-4o","messages":[{"role":"user","content":"hi"}]}'
done
# → 200 200 200 402
```

Restore `limit` to `10_000` afterward.

---

## ✅ Done when

- Dashboard shows a usage meter for the tenant's plan.
- The 4th call (with a temp limit of 3) returns **HTTP 402** with an upgrade hint.

You now have a working, self-contained subscription system. Upgrading a tenant
is just `UPDATE tenants SET plan='team'` — which is exactly the one line a real
Stripe webhook would run in Module 7's optional billing extension.

**Next → [Module 4: Gateway + SDK → one tenant](04-integrations.md)**
