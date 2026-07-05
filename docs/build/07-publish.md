# Module 7 — Publish to PyPI

**Goal:** take your `membra` package from local to `pip install membra`, the
right way — TestPyPI first, then real PyPI, with API tokens and a repeatable
release flow.

---

## 7.1 Concept — what "publishing" actually is

Two artifacts get uploaded to an index (PyPI):
- a **wheel** (`membra-0.1.0-py3-none-any.whl`) — the fast, prebuilt install
- an **sdist** (`membra-0.1.0.tar.gz`) — the source fallback

You **build** them locally with `build`, **check** them with `twine`, then
**upload** with `twine`. PyPI is just a package index; nothing magic.

## 7.2 Pre-flight checklist

Before you ever upload, confirm:

```bash
pip index versions membra          # name still free? (else set name="membra-ai" in pyproject)
```

- [ ] `name` in `pyproject.toml` is available on PyPI
- [ ] `version` is one you've never uploaded (PyPI **rejects re-uploads** of a version — this trips everyone once)
- [ ] `README.md` renders (it becomes your PyPI project page)
- [ ] `LICENSE` present, `license`/`classifiers` set
- [ ] `python -c "import membra"` works from a clean venv

## 7.3 Build the distributions

```bash
pip install --upgrade build twine
python -m build            # writes dist/membra-0.1.0-py3-none-any.whl and .tar.gz
twine check dist/*         # validates metadata + README rendering  → should print PASSED
```

Inspect what actually got packaged (catch missing files early):

```bash
python -m zipfile -l dist/membra-0.1.0-py3-none-any.whl
```
Make sure `membra/` and its submodules are present. If your ML model
(`data/injection_model.json`) must ship *inside* the package, move it under
`src/membra/data/` and reference it via `importlib.resources` — files outside
the package are **not** included in the wheel. (Good v0.2 task.)

## 7.4 Get API tokens

Create accounts and tokens (tokens, never passwords):
- TestPyPI: https://test.pypi.org/manage/account/token/
- PyPI:     https://pypi.org/manage/account/token/

Store them in `~/.pypirc` (chmod 600) so you don't paste them each time:

```ini
# ~/.pypirc
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEI...          # your PyPI token

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEN...          # your TestPyPI token
```

## 7.5 Rehearse on TestPyPI

**Always** dry-run on TestPyPI — it's a throwaway mirror, so mistakes are free.

```bash
twine upload -r testpypi dist/*
```

Then install from it in a *fresh* venv to prove it works end-to-end:

```bash
python -m venv /tmp/t && . /tmp/t/bin/activate
pip install -i https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ "membra[server]"
membra version        # → membra 0.1.0
deactivate
```
(The `--extra-index-url` lets pip pull your real deps, FastAPI etc., from PyPI
while pulling *membra* from TestPyPI.)

## 7.6 Release to real PyPI

```bash
twine upload dist/*         # uploads to PyPI (uses [pypi] from ~/.pypirc)
```

Verify:
```bash
pip install membra
```
Your project is now live at `https://pypi.org/project/membra/`. 🎉

## 7.7 Cutting the next version (the repeatable loop)

Every release, in order:
1. Bump `version` in `pyproject.toml` (e.g. `0.1.1`). **Never reuse a version.**
2. `rm -rf dist/ && python -m build && twine check dist/*`
3. `twine upload dist/*`
4. Tag it: `git tag v0.1.1 && git push --tags` (once you're on git).

Consider adopting SemVer: `MAJOR.MINOR.PATCH` — patch for fixes, minor for
back-compatible features, major for breaking changes.

## 7.8 Automate it later (GitHub Actions)

Once on GitHub, a release workflow publishes on every tag using PyPI's
**Trusted Publishing** (OIDC — no tokens stored in CI):

```yaml
# .github/workflows/release.yml
name: release
on:
  push:
    tags: ["v*"]
permissions:
  id-token: write            # required for trusted publishing
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install build && python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```
Set it up in Module 8 as part of your cloud engineering pipeline.

---

## ✅ Done when

`pip install membra` (from a machine that never saw your source) installs the
package and `membra version` runs. You are open-source and shippable.

**Next → [Module 8: Cloud agents for your engineering pipeline](08-cloud-agents.md)**
