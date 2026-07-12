"""Outbound defense: AI-DLP — catch secrets & PII before they leave the org.

Two layers:
  1. Known-format matchers (API keys, tokens, PII) — precise, low false-positive.
  2. Shannon-entropy backstop — catches *unknown* secret formats.
"""
import re
import math

_SECRETS = [
    (r"AKIA[0-9A-Z]{16}", "aws_access_key"),
    (r"sk-[A-Za-z0-9]{20,}", "openai_api_key"),
    (r"sk-ant-[A-Za-z0-9\-]{20,}", "anthropic_api_key"),
    (r"ghp_[A-Za-z0-9]{36}", "github_token"),
    (r"xox[baprs]-[A-Za-z0-9\-]{10,}", "slack_token"),
    (r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", "private_key"),
    (r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}", "jwt"),
]

_PII = [
    (r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "email"),
    (r"\b\d{3}-\d{2}-\d{4}\b", "ssn"),
    (r"\b(?:\d[ -]?){13,16}\b", "credit_card"),
    (r"\b(?:\+?\d{1,3}[ -]?)?(?:\(?\d{3}\)?[ -]?)\d{3}[ -]?\d{4}\b", "phone"),
]

_SECRETS_C = [(re.compile(p), n) for p, n in _SECRETS]
_PII_C = [(re.compile(p), n) for p, n in _PII]


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = {c: s.count(c) for c in set(s)}
    return -sum((n / len(s)) * math.log2(n / len(s)) for n in freq.values())


def _luhn_ok(number: str) -> bool:
    digits = [int(c) for c in re.sub(r"\D", "", number)]
    if not 13 <= len(digits) <= 19:
        return False
    checksum, parity = 0, len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def scan_dlp(text: str) -> dict:
    """Return {'findings': [{'type','value'}], 'score': float}."""
    findings, seen = [], set()

    def add(kind, value):
        if value and value not in seen:
            seen.add(value)
            findings.append({"type": kind, "value": value})

    for rx, name in _SECRETS_C:
        for m in rx.findall(text or ""):
            add(name, m if isinstance(m, str) else m[0])

    for rx, name in _PII_C:
        for m in rx.findall(text or ""):
            val = m if isinstance(m, str) else m[0]
            if name == "credit_card" and not _luhn_ok(val):
                continue
            add(name, val.strip())

    # entropy backstop for unknown secret formats
    for token in re.findall(r"[A-Za-z0-9_\-]{24,}", text or ""):
        if token not in seen and _entropy(token) > 4.0:
            add("high_entropy_secret", token)

    score = min(1.0, 0.34 * len(findings))
    return {"findings": findings, "score": round(score, 3)}


def redact(text: str, findings) -> str:
    for f in findings:
        text = text.replace(f["value"], f"[REDACTED:{f['type']}]")
    return text
