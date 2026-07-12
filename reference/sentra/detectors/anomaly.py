"""Behavioral immune memory: learn each user's normal AI-usage fingerprint
and flag statistical deviations (z-score on a rolling window).

Catches account-takeover / insider exfiltration that no keyword filter sees:
individually-benign requests whose *pattern* is abnormal.
"""
import math
import time
from collections import defaultdict, deque


class AnomalyTracker:
    def __init__(self, window: int = 200, min_samples: int = 20, z_threshold: float = 4.0):
        self.window = window
        self.min_samples = min_samples
        self.z_threshold = z_threshold
        # per-user rolling samples of feature vectors
        self._msg_len = defaultdict(lambda: deque(maxlen=window))
        self._rate = defaultdict(lambda: deque(maxlen=window))  # timestamps

    @staticmethod
    def _z(value, samples):
        if len(samples) < 2:
            return 0.0
        mean = sum(samples) / len(samples)
        var = sum((x - mean) ** 2 for x in samples) / len(samples)
        std = math.sqrt(var) or 1e-9
        return (value - mean) / std

    def observe(self, user: str, message: str, now: float | None = None) -> dict:
        now = now if now is not None else time.time()
        length = len(message or "")

        # requests in the last 60s = short-term rate
        recent = self._rate[user]
        recent.append(now)
        rate_60s = sum(1 for t in recent if now - t <= 60)

        len_samples = self._msg_len[user]
        z_len = self._z(length, len_samples)
        # rate baseline: compare current 60s rate to historical 60s rates
        # (approximated by counts already stored; simple + effective for MVP)
        len_samples.append(length)

        warming = len(len_samples) < self.min_samples
        z_rate = 0.0
        # crude rate anomaly: > 20 req/min once we have history
        if not warming and rate_60s > 20:
            z_rate = rate_60s / 5.0

        score = max(abs(z_len), z_rate)
        anomalous = (not warming) and score >= self.z_threshold
        return {
            "score": round(score, 2),
            "anomalous": anomalous,
            "warming_up": warming,
            "rate_60s": rate_60s,
            "reason": self._reason(z_len, z_rate),
        }

    @staticmethod
    def _reason(z_len, z_rate):
        reasons = []
        if abs(z_len) >= 4.0:
            reasons.append("abnormal_message_size")
        if z_rate >= 4.0:
            reasons.append("abnormal_request_rate")
        return reasons
