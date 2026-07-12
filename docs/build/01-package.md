# Module 1 — Package skeleton

**Goal:** turn a folder of scripts into a real, installable Python package named
`membra`, with a working `membra` command. Everything else bolts onto this.

---

## 1.1 Concept — two names, don't confuse them

- **Import name** = what you write in code → `import membra`. It's the folder name.
- **Distribution name** = what you `pip install` → lives on PyPI.

They *can* differ. If `membra` on PyPI is taken, set the distribution name to
`membra-ai` but keep the folder (import) as `membra`. Verify now:

```bash
pip index versions membra      # "No matching distribution" ≈ available
```

## 1.2 Concept — "src layout" and why

The pro convention is to put your package under `src/`:

```
Membra/
├── pyproject.toml         ← the single manifest (replaces setup.py + requirements.txt)
├── README.md
├── LICENSE
├── data/                  ← runtime data (DB, ML model) — stays at repo root
├── src/
│   └── membra/            ← your package
│       ├── __init__.py
│       ├── cli.py         ← NEW: the `membra` command
│       ├── engine.py      ← reuse from prototype
│       ├── detectors/     ← reuse
│       └── ...
├── demo/
└── tests/
```

**Why src?** Your tests then import the *installed* package, not the loose
folder beside them — so "works on my machine, breaks once installed" bugs show
up immediately. It's the single most valuable packaging habit.

**Do it** — create the fresh package folder. The old prototype now lives in
[`reference/`](../../reference/README.md); we build `src/membra/` from scratch
and **copy the reusable detection core forward** as each module needs it
(rebranding strings, keeping the logic):

```bash
mkdir -p src/membra
# copy the brand-neutral cores you'll reuse (rebrand them as you go):
cp -r reference/sentra/detectors      src/membra/detectors
cp reference/sentra/engine.py         src/membra/engine.py
cp reference/sentra/auth.py           src/membra/auth.py
cp reference/sentra/store.py          src/membra/store.py
cp reference/sentra/templates.py      src/membra/templates.py
cp reference/sentra/docs_page.py      src/membra/docs_page.py
# the trained ML model the detectors need:
mkdir -p src/membra/data
cp reference/data/injection_model.json src/membra/data/injection_model.json
```

> You'll rewrite `app.py`/`gateway.py`/`sdk.py` fresh (Modules 2 & 4) — those are
> the parts that change most for Membra, so we don't copy them. The detectors,
> engine, auth, and store are reused almost as-is.

**One fix after copying:** the model now lives *inside* the package
(`src/membra/data/`), so update the path in
`src/membra/detectors/ml_injection.py`:

```python
# was: os.path.join(os.path.dirname(__file__), "..", "..", "data", "injection_model.json")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "injection_model.json")
```
(One less `".."` — from `detectors/` up to `membra/`, then into `data/`.)

Now create `src/membra/__init__.py`:

```python
# src/membra/__init__.py
"""Membra — a security immune system for the AI era."""
__version__ = "0.1.0"
```

## 1.3 The manifest — `pyproject.toml`

Create it at the repo root. **Read the comments — that's the lesson.**

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]              # a modern, zero-config build backend
build-backend = "hatchling.build"

[project]
name = "membra"                        # distribution name (→ "membra-ai" if taken)
version = "0.1.0"
description = "Open-source immune system for AI agents — injection defense, AI-DLP, agent guardrails."
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [{ name = "Abhisek", email = "abhisekrock94@gmail.com" }]
keywords = ["llm-security", "prompt-injection", "ai-dlp", "agent-security", "guardrails"]
classifiers = [
  "Development Status :: 3 - Alpha",
  "License :: OSI Approved :: MIT License",
  "Programming Language :: Python :: 3",
  "Topic :: Security",
]

# Base install = the lightweight SDK. Zero deps → anyone can `guard()` a client
# without pulling a web framework.
dependencies = []

[project.optional-dependencies]
# `pip install membra[server]` adds the web stack ONLY when you want the server.
server = ["fastapi>=0.110", "uvicorn[standard]>=0.29"]
dev = ["build", "twine", "pytest", "httpx"]

[project.scripts]
# THIS line creates the `membra` terminal command → calls main() in cli.py
membra = "membra.cli:main"

[project.urls]
Homepage = "https://github.com/abhisek/membra"
Documentation = "https://github.com/abhisek/membra#readme"

[tool.hatch.build.targets.wheel]
packages = ["src/membra"]              # tell hatchling the package is under src/
```

**The two ideas that matter most here:**

1. **`dependencies = []` + `optional-dependencies.server`.** This is how one
   package is *both* a thin SDK and a full server. SDK users get zero deps;
   server users run `pip install membra[server]`. This split is worth
   internalizing — it's how mature projects (e.g. `uvicorn[standard]`) work.
2. **`[project.scripts]`** turns `membra = "membra.cli:main"` into a real
   command on your `PATH`. No `setup.py console_scripts` boilerplate needed.

## 1.4 The CLI entry point — `src/membra/cli.py`

Start minimal; `serve` and `demo` become real in Modules 2 and 5.

```python
# src/membra/cli.py
"""The `membra` command-line entry point."""
import argparse
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(prog="membra", description="Membra — AI security immune system")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version", help="print the installed version")
    p_serve = sub.add_parser("serve", help="run the dashboard + API")
    p_serve.add_argument("--port", type=int, default=8100)
    sub.add_parser("demo", help="run the hello-world simulation")

    args = parser.parse_args(argv)

    if args.command == "version":
        from membra import __version__
        print(f"membra {__version__}")
    elif args.command == "serve":
        print("serve: implemented in Module 2")     # placeholder
    elif args.command == "demo":
        print("demo: implemented in Module 5")       # placeholder
    else:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## 1.5 The `LICENSE` (open source needs one)

Without a license, legally nobody can use your code. MIT is the standard
permissive pick. Create `LICENSE`:

```
MIT License

Copyright (c) 2026 Abhisek

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 1.6 Install editable and verify

`-e` = *editable*: pip links to your source, so edits take effect with no
reinstall.

```bash
pip install -e ".[server,dev]"
```

Verify all three signals:

```bash
python -c "import membra; print(membra.__version__)"   # → 0.1.0
membra version                                         # → membra 0.1.0
membra                                                 # → prints help
```

---

## ✅ Done when

`membra version` prints `membra 0.1.0` from a fresh terminal. That proves your
package is installed, importable, and has a live CLI.

**The mental model you now own:** a package is four things — a **build backend**
(hatchling), a **manifest** (`pyproject.toml`), an **import package**
(`src/membra`), and an **entry point** (`membra`). Every later module just adds
files into this skeleton.

**Next → [Module 2: FastAPI unification](02-server.md)**
