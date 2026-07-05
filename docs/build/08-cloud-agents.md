# Module 8 — Cloud agents for your engineering pipeline

**Goal:** stop doing repetitive engineering work by hand. Set up agents — both
**on-demand** (one per task) and **scheduled** (recurring) — to run tests, build
and validate the package, review diffs, and draft releases.

> This module is about *how to drive agents from Claude Code*. Some of it I can
> run **for you** on request (spinning up a cloud agent is billable, so I'll
> always ask first). The rest you trigger yourself.

---

## 8.1 Concept — two kinds of agents

| Kind | When it runs | Good for | How |
|---|---|---|---|
| **On-demand (background) agent** | You dispatch it now | Bursts: "write tests for the detectors", "audit pyproject", "draft README" | Ask me, or use the SDK/Task tooling |
| **Scheduled agent (routine)** | On a cron/interval | Standing automation: nightly test run, release on tag, weekly dep check | The `/schedule` skill (routines) |

A rule of thumb: **on-demand for creation, scheduled for guarding.** You *make*
things with a burst of parallel agents; you *protect* the repo with a couple of
recurring ones.

## 8.2 A starter pipeline for Membra

Three stages, each an agent with a tight remit:

```
   ①  test-runner ───▶ ②  packaging-validator ───▶ ③  release-drafter
   pytest -q            python -m build             summarize changes,
   report failures      twine check dist/*          propose version bump,
                        verify wheel contents        draft release notes
```

- **① Test-runner** — runs `pytest`, returns a structured pass/fail + the first
  failing traceback. Scheduled on every push (or nightly).
- **② Packaging-validator** — runs `python -m build` + `twine check` + lists the
  wheel contents to catch missing files (e.g. the ML model). Scheduled on tags.
- **③ Release-drafter** — reads the diff since the last tag, proposes the SemVer
  bump, and drafts release notes. On-demand when you're ready to ship.

## 8.3 Prerequisites before automation is worth it

Automation guards code — so you need code and tests first:

1. Finish Modules 1–5 (a running package).
2. Add a minimal `tests/` (great first on-demand agent job):
   ```
   tests/test_engine.py       # injection blocks, DLP redacts, clean allows
   tests/test_plans.py        # over_quota() boundaries
   tests/test_sdk.py          # guard() raises MembraBlocked on injection
   ```
3. Put the repo on **git + GitHub** (agents and CI need a remote).

## 8.4 How to launch each one

**On-demand, right now (ask me):** e.g. *"spin up an agent to write `tests/` for
the detectors and the plan gate."* I'll dispatch a background agent, it works in
isolation, and I relay the result for your review. You can run several in
parallel (tests + README + pyproject audit at once).

**Scheduled routine (you own it):** use the `/schedule` skill in an interactive
session:
```
/schedule create "nightly: run pytest and twine check on membra, summarize failures" --cron "0 2 * * *"
```
It runs in the cloud on that cadence and reports back. Manage them with
`/schedule list` / `/schedule run`.

**CI on tag (from Module 7.8):** the GitHub Actions `release.yml` is itself an
automated agent of sorts — it builds and publishes to PyPI on every `v*` tag
with no secrets stored (Trusted Publishing).

## 8.5 Guardrails for agent-run pipelines

- **Scope each agent narrowly.** "Run tests and report" beats "improve the
  project." Narrow tasks give verifiable output.
- **Keep humans on releases.** Let agents *draft* the version bump and notes;
  you approve the actual `twine upload`. (Or gate CI publish behind a manual
  approval environment.)
- **Everything is reviewable.** Agents propose diffs/PRs; you merge. Never let an
  unattended agent push to `main` or publish without a gate.
- **Cost awareness.** Scheduled agents run whether or not there's work — pick
  sensible cadences (nightly, on-push) rather than every-few-minutes polling.

---

## What I can do for you on request

Just say the word and I'll:
- **Dispatch on-demand agents now** — write `tests/`, draft the `README.md`
  around the Membra positioning, or audit your `pyproject.toml`.
- **Set up the release workflow** — generate `.github/workflows/release.yml` and
  `ci.yml` once you're on GitHub.
- **Help you stand up scheduled routines** — I'll draft the exact `/schedule`
  commands for the test/build/release cadence.

---

## ✅ Done when

You have a green test run, a `twine check` that passes in CI, and at least one
scheduled agent watching the repo — so shipping Membra is a tag, not a chore.

**← Back to the [guide index](README.md)**
