"""The engine: runs all detectors on a request and returns a policy decision.

This is the single entry point used by BOTH integration paths:
  - the inline gateway (sentra/gateway.py)  -> zero code change for the org
  - the SDK wrapper       (sentra/sdk.py)   -> one line change in the org's app
"""
from dataclasses import dataclass, field
from .detectors import scan_injection, scan_dlp, redact, AnomalyTracker
from .detectors.ml_injection import scan_injection_ml
from .detectors.agent_guard import AgentGuard

# Actions, most -> least severe
BLOCK = "block"
QUARANTINE = "quarantine"
REDACT = "redact"
ALLOW = "allow"


@dataclass
class Decision:
    action: str
    reasons: list = field(default_factory=list)
    safe_text: str = ""            # text to actually forward to the model
    detail: dict = field(default_factory=dict)

    @property
    def allowed(self) -> bool:
        return self.action in (ALLOW, REDACT)


class Engine:
    def __init__(self, injection_threshold: float = 0.5):
        self.injection_threshold = injection_threshold
        self.anomaly = AnomalyTracker()
        self.agent_guard = AgentGuard()

    def authorize_action(self, user: str, tool: str, args: dict) -> Decision:
        """Gate an autonomous agent's proposed tool action (the T-cell layer)."""
        a = self.agent_guard.assess(tool, args)
        mapping = {"allow": ALLOW, "approve": QUARANTINE, "deny": BLOCK}
        return Decision(mapping[a["action"]], a["reasons"],
                        safe_text=tool, detail={"agent_guard": a})

    def inspect(self, user: str, text: str) -> Decision:
        reasons, detail = [], {}

        # 1) inbound: injection / jailbreak  (regex signals + ML ensemble)
        inj = scan_injection(text)          # explainable pattern signals
        ml = scan_injection_ml(text)        # generalizes to paraphrases
        risk = max(inj["score"], ml["score"])
        detail["injection"] = {**inj, "ml_score": ml["score"], "risk": round(risk, 3)}
        if risk >= self.injection_threshold:
            why = inj["signals"] or [f"ml_injection({ml['score']})"]
            reasons.append(f"prompt_injection({','.join(why)})")
            return Decision(BLOCK, reasons, safe_text="", detail=detail)

        # 2) behavioral anomaly (immune memory)
        ano = self.anomaly.observe(user, text)
        detail["anomaly"] = ano
        if ano["anomalous"]:
            reasons.append(f"behavioral_anomaly({','.join(ano['reason']) or 'rate'})")
            return Decision(QUARANTINE, reasons, safe_text="", detail=detail)

        # 3) outbound: DLP redaction
        dlp = scan_dlp(text)
        detail["dlp"] = dlp
        if dlp["findings"]:
            safe = redact(text, dlp["findings"])
            reasons.append(f"dlp_redacted({','.join(sorted({f['type'] for f in dlp['findings']}))})")
            return Decision(REDACT, reasons, safe_text=safe, detail=detail)

        return Decision(ALLOW, ["clean"], safe_text=text, detail=detail)
