"""Inbound defense: prompt-injection & jailbreak detection.

MVP uses weighted signal patterns and returns a 0..1 risk score. This is the
seam where you later plug a small classifier / embedding-similarity model
(see roadmap in README) without changing the engine interface.
"""
import re

# (regex, signal_name, weight)
_SIGNALS = [
    (r"ignore (all |the |your )?(previous|prior|above)\s+(instructions|prompt|rules)", "instruction_override", 0.6),
    (r"disregard (the |your |all )?(system prompt|rules|guidelines|instructions)", "instruction_override", 0.6),
    (r"you are now (in )?(developer|dan|jailbreak|god|sudo|root)\s*mode", "role_hijack", 0.6),
    (r"pretend (you are|to be)|act as (an? )?(unrestricted|uncensored|evil)", "role_hijack", 0.5),
    (r"reveal (your )?(system prompt|initial prompt|instructions|the prompt)", "prompt_extraction", 0.5),
    (r"repeat (everything|the text|all text) (above|before)", "prompt_extraction", 0.4),
    (r"print (your )?(system|initial) (prompt|message)", "prompt_extraction", 0.5),
    (r"do anything now|no (restrictions|limitations|filters|rules)", "guardrail_removal", 0.5),
    (r"\bbase64\b.*(decode|execute)|decode the following", "obfuscation", 0.3),
    (r"</?(system|assistant|user)>|\[INST\]|<\|im_start\|>", "delimiter_injection", 0.5),
]

_COMPILED = [(re.compile(p, re.I), name, w) for p, name, w in _SIGNALS]


def scan_injection(text: str) -> dict:
    """Return {'score': float, 'signals': [...]} for inbound text."""
    signals, score = [], 0.0
    for rx, name, weight in _COMPILED:
        if rx.search(text or ""):
            signals.append(name)
            score += weight
    # combine so multiple weak signals still escalate, capped at 1.0
    score = 1.0 - (1.0 - min(score, 0.99))  # keep linear-ish but bounded
    return {"score": round(min(score, 1.0), 3), "signals": sorted(set(signals))}
