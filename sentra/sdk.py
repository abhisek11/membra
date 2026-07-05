"""SDK integration path — for teams that prefer wrapping the client in code
instead of (or in addition to) the transparent gateway.

    from openai import OpenAI
    from sentra.sdk import guard

    client = guard(OpenAI())          # <- the whole integration
    client.chat.completions.create(model="gpt-4o", messages=[...])

`guard()` intercepts each call, runs the SAME engine the gateway uses, and
blocks/redacts before the request ever leaves the process. Shown here with a
duck-typed client so it runs without the openai package installed.
"""
from .engine import Engine, BLOCK, QUARANTINE, REDACT

_engine = Engine()


class _GuardedCompletions:
    def __init__(self, inner):
        self._inner = inner

    def create(self, *, model, messages, user="anonymous", **kw):
        last = next((m for m in reversed(messages) if m.get("role") == "user"), None)
        text = (last or {}).get("content", "")
        decision = _engine.inspect(user, text)

        if decision.action in (BLOCK, QUARANTINE):
            raise SentraBlocked(decision.reasons)
        if decision.action == REDACT and last is not None:
            last["content"] = decision.safe_text  # redact before it leaves

        return self._inner.chat.completions.create(model=model, messages=messages, **kw)


class SentraBlocked(Exception):
    def __init__(self, reasons):
        self.reasons = reasons
        super().__init__(f"Blocked by Sentra: {', '.join(reasons)}")


class _Chat:
    def __init__(self, inner):
        self.completions = _GuardedCompletions(inner)


class GuardedClient:
    def __init__(self, inner):
        self._inner = inner
        self.chat = _Chat(inner)

    def __getattr__(self, name):        # passthrough for everything else
        return getattr(self._inner, name)


def guard(client):
    """Wrap any OpenAI-style client so all chat calls are inspected."""
    return GuardedClient(client)
