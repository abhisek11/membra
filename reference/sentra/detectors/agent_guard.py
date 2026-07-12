"""Agent guardrails ("T-cell" layer) — gate autonomous-agent tool actions.

An AI agent proposes an action (tool + args) BEFORE executing it. Sentra assigns
a risk tier and returns allow / approve (human-in-the-loop) / deny, based on:
  1. the tool's category (read-only vs destructive vs exfiltrating)
  2. dangerous argument patterns (rm -rf, DROP TABLE, curl|sh, secret egress)
  3. destination allow-listing for outbound calls
"""
import re
from .dlp import scan_dlp

ALLOW = "allow"
APPROVE = "approve"    # requires human approval
DENY = "deny"

# Tool categories -> base risk
_READ_ONLY = {"read_file", "list_dir", "search", "http_get", "db_read", "get_weather"}
_WRITE = {"write_file", "db_write", "send_email", "create_ticket", "post_message"}
_DANGEROUS = {"shell_exec", "run_command", "file_delete", "db_admin",
              "http_post", "transfer_funds", "make_payment", "deploy",
              "delete_resource", "grant_access", "read_secret"}

# Dangerous argument signatures (regex, label)
_ARG_SIGNALS = [
    (r"\brm\s+-rf\b|\bmkfs\b|\bdd\s+if=", "destructive_shell"),
    (r"\bsudo\b|\bchmod\s+777\b", "privilege_escalation"),
    (r"curl[^\n]*\|\s*(sh|bash)|wget[^\n]*\|\s*(sh|bash)", "remote_code_exec"),
    (r"\bDROP\s+TABLE\b|\bTRUNCATE\b|DELETE\s+FROM\s+\w+\s*(;|$)", "destructive_sql"),
    (r":\s*\(\s*\)\s*\{.*\};:", "fork_bomb"),
    (r"/etc/passwd|/etc/shadow|~/.ssh|id_rsa", "sensitive_path"),
]
_ARG_SIGNALS_C = [(re.compile(p, re.I), n) for p, n in _ARG_SIGNALS]


class AgentGuard:
    def __init__(self, allowed_domains=None, allow_write=True):
        # outbound POST/GET destinations you trust
        self.allowed_domains = set(allowed_domains or ["api.internal", "localhost"])
        self.allow_write = allow_write

    def _domain(self, args):
        url = str(args.get("url", "")) if isinstance(args, dict) else ""
        m = re.search(r"https?://([^/\s:]+)", url)
        return m.group(1) if m else None

    def assess(self, tool: str, args: dict) -> dict:
        reasons = []
        argstr = " ".join(f"{k}={v}" for k, v in (args or {}).items()) if isinstance(args, dict) else str(args)

        # 1) dangerous argument content -> hard deny
        for rx, label in _ARG_SIGNALS_C:
            if rx.search(argstr):
                reasons.append(label)
        if reasons:
            return {"action": DENY, "tier": "critical", "reasons": reasons, "tool": tool}

        # 2) data exfiltration: sensitive data in an outbound call
        if tool in ("http_post", "send_email", "post_message"):
            dlp = scan_dlp(argstr)
            if dlp["findings"]:
                kinds = sorted({f["type"] for f in dlp["findings"]})
                return {"action": APPROVE, "tier": "high",
                        "reasons": [f"data_egress({','.join(kinds)})"], "tool": tool}
            dom = self._domain(args)
            if dom and dom not in self.allowed_domains:
                return {"action": APPROVE, "tier": "high",
                        "reasons": [f"external_destination({dom})"], "tool": tool}

        # 3) category-based tiers
        if tool in _READ_ONLY:
            return {"action": ALLOW, "tier": "low", "reasons": ["read_only"], "tool": tool}
        if tool in _WRITE:
            act = ALLOW if self.allow_write else APPROVE
            return {"action": act, "tier": "medium", "reasons": ["write_action"], "tool": tool}
        if tool in _DANGEROUS:
            return {"action": APPROVE, "tier": "high",
                    "reasons": ["dangerous_tool"], "tool": tool}

        # 4) unknown tool -> default to human approval (fail safe)
        return {"action": APPROVE, "tier": "unknown", "reasons": ["unrecognized_tool"], "tool": tool}
