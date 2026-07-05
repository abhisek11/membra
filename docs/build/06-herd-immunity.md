# Module 6 — Herd Immunity (the hero feature)

**Goal:** build the thing that makes Membra *different* — an opt-in network where
one deployment's newly-discovered attack becomes every deployment's vaccine. It
turns your install base into a data moat competitors structurally can't copy.

> This is a **v0** you can ship and iterate. It's designed to be privacy-safe
> (shares signatures, never raw prompts) and fully optional.

---

## 6.1 Concept — what actually gets shared

A real immune system doesn't share cells; it shares *antibodies*. Membra shares
**signatures**, never content:

- When a tenant's engine **blocks** an injection with high confidence, Membra
  derives a **one-way fingerprint** of the *pattern* (not the text) — e.g. a set
  of hashed n-gram buckets, or the SHA-256 of a normalized skeleton.
- That fingerprint (+ a label + a confidence) is the "antibody." It contains no
  recoverable prompt, no PII, no tenant identity.
- Other nodes pull the shared antibody set and add it to their matcher. A brand
  new attack seen once, anywhere, is recognized everywhere.

Two properties make it defensible:
1. **Network effect** — value grows with the number of deployments. Features get
   cloned; a growing shared-threat corpus doesn't.
2. **OSS-only advantage** — closed enterprise vendors can't build this because
   they don't have a broad self-hosted install base contributing signals.

## 6.2 Derive a privacy-safe signature

Reuse the ML featurizer you already have (`detectors/ml_injection.featurize`) —
it hashes text into buckets, which is inherently one-way. Add
`src/membra/immunity.py`:

```python
# src/membra/immunity.py
"""Herd Immunity — share attack SIGNATURES (never content) across deployments."""
import hashlib
from .detectors.ml_injection import featurize


def signature(text: str) -> str:
    """A stable, non-reversible fingerprint of an attack's shape.

    We take the top hashed feature buckets and hash their identities. Two
    paraphrases of the same attack collide; the original text is unrecoverable.
    """
    vec = featurize(text or "")
    top = sorted(vec, key=vec.get, reverse=True)[:24]      # bucket ids only
    skeleton = ",".join(str(b) for b in sorted(top))
    return "ab_" + hashlib.sha256(skeleton.encode()).hexdigest()[:32]


def antibody(text: str, reasons) -> dict:
    return {"sig": signature(text), "labels": list(reasons), "conf": 1.0}
```

## 6.3 Store and match antibodies

Add a tiny table + matcher. In `store.py`:

```python
    def _init(self):
        with _LOCK, self._conn() as c:
            # ... existing events table ...
            c.execute("""CREATE TABLE IF NOT EXISTS antibodies(
                sig TEXT PRIMARY KEY, labels TEXT, conf REAL, seen INTEGER DEFAULT 1, ts REAL)""")

    def add_antibody(self, ab, ts):
        import json as _j
        with _LOCK, self._conn() as c:
            c.execute("""INSERT INTO antibodies(sig,labels,conf,seen,ts) VALUES(?,?,?,1,?)
                         ON CONFLICT(sig) DO UPDATE SET seen=seen+1, ts=?""",
                      (ab["sig"], _j.dumps(ab["labels"]), ab["conf"], ts, ts))

    def has_antibody(self, sig):
        with _LOCK, self._conn() as c:
            return c.execute("SELECT 1 FROM antibodies WHERE sig=?", (sig,)).fetchone() is not None

    def antibodies_since(self, ts=0):
        with _LOCK, self._conn() as c:
            rows = c.execute("SELECT sig,labels,conf FROM antibodies WHERE ts>=?", (ts,)).fetchall()
        return [dict(r) for r in rows]
```

## 6.4 Feed the engine both ways

**Contribute** — when the data plane blocks an injection, register the antibody
(opt-in via an env flag). In `server.py`, inside `data_plane_chat` after a BLOCK:

```python
    if d.action == BLOCK and os.environ.get("MEMBRA_HERD", "").lower() in ("1", "true", "on"):
        from .immunity import antibody
        store.add_antibody(antibody(text, d.reasons), time.time())
```

**Recognize** — check the shared set *before* the ML step so a known attack is
caught instantly and cheaply. In `engine.py`'s `inspect()`, near the top:

```python
    # 0) herd immunity: known attack signature?  (injected matcher, optional)
    if self.immunity_match and self.immunity_match(text):
        return Decision(BLOCK, ["herd_immunity(known_signature)"], safe_text="", detail=detail)
```

Give `Engine.__init__` an optional `immunity_match=None` callable and pass one in
from `server.py`:

```python
engine = Engine()
from .immunity import signature
engine.immunity_match = lambda text: store.has_antibody(signature(text))
```

## 6.5 The network hop (federation) — v0

For a single node you're done: attacks blocked once are recognized forever. To
*share across deployments*, add two endpoints and a periodic pull:

- `GET /v1/herd/pull?since=<ts>` → returns `antibodies_since(ts)` (public, no
  content, safe to expose).
- `POST /v1/herd/push` → accepts a batch of antibodies from a trusted node.

A hosted "hub" node aggregates pushes and serves pulls; self-hosted nodes pull
on a timer. Ship the single-node version first, add federation when you have >1
deployment. **Keep it opt-in** and document exactly what's shared — trust is the
product here.

## 6.6 Verify

```bash
export MEMBRA_HERD=on
membra serve &
# First time: a novel attack is caught by the ML/regex engine and recorded.
curl ... -d '{"messages":[{"role":"user","content":"a brand-new jailbreak phrasing"}]}'
# Restart nothing. Send a PARAPHRASE — it's now blocked by herd_immunity, pre-ML:
curl ... -d '{"messages":[{"role":"user","content":"a slightly reworded jailbreak phrasing"}]}' -i
# → X-Membra-Reasons: herd_immunity(known_signature)
```

---

## ✅ Done when

A paraphrase of a previously-blocked attack is caught with reason
`herd_immunity(known_signature)` — proving the system learned from one instance.
That's the hero, working. Federation (6.5) is your Series-A story; the single
node is your demo today.

**Next → [Module 7: Publish to PyPI](07-publish.md)**
