"""ML prompt-injection classifier — logistic regression on hashed n-gram features.

Pure standard library. Uses a STABLE hash (zlib.crc32) so a trained model file
loads identically across processes (Python's built-in hash() is randomized).

  featurize(text) -> sparse dict {bucket: value}
  train / evaluate live in this module (run: python3 -m sentra.detectors.ml_injection)
  scan_injection_ml(text) -> {'score', 'label'} using the saved model
"""
import json
import math
import os
import re
import zlib

DIM = 2048
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "injection_model.json")
_TOKEN = re.compile(r"[a-z0-9<>/\[\]|]+")


def _bucket(token: str) -> int:
    return zlib.crc32(token.encode()) % DIM


def featurize(text: str) -> dict:
    """Char 3-grams + word unigrams, hashed into DIM buckets, L2-normalized."""
    t = (text or "").lower()
    vec = {}
    # word unigrams
    for w in _TOKEN.findall(t):
        b = _bucket("w:" + w)
        vec[b] = vec.get(b, 0.0) + 1.0
    # char 3-grams (captures obfuscation / paraphrase)
    squashed = re.sub(r"\s+", " ", t)
    for i in range(len(squashed) - 2):
        b = _bucket("c:" + squashed[i:i + 3])
        vec[b] = vec.get(b, 0.0) + 1.0
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {k: v / norm for k, v in vec.items()}


def _sigmoid(z):
    if z < -60:
        return 0.0
    if z > 60:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))


def _predict(w, b, x):
    return _sigmoid(sum(w[i] * v for i, v in x.items()) + b)


def train(data, epochs=40, lr=0.5, l2=1e-4):
    w = [0.0] * DIM
    b = 0.0
    import random
    random.seed(7)
    xs = [(featurize(t), y) for t, y in data]
    for _ in range(epochs):
        random.shuffle(xs)
        for x, y in xs:
            p = _predict(w, b, x)
            g = p - y
            for i, v in x.items():
                w[i] -= lr * (g * v + l2 * w[i])
            b -= lr * g
    return w, b


def evaluate(w, b, data, thr=0.5):
    tp = fp = tn = fn = 0
    for t, y in data:
        p = 1 if _predict(w, b, featurize(t)) >= thr else 0
        if p and y:
            tp += 1
        elif p and not y:
            fp += 1
        elif not p and not y:
            tn += 1
        else:
            fn += 1
    acc = (tp + tn) / max(1, len(data))
    prec = tp / max(1, tp + fp)
    rec = tp / max(1, tp + fn)
    f1 = 2 * prec * rec / max(1e-9, prec + rec)
    return {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1,
            "tp": tp, "fp": fp, "tn": tn, "fn": fn}


def save(w, b, path=MODEL_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"dim": DIM, "w": w, "b": b}, f)


_MODEL = None


def _load():
    global _MODEL
    if _MODEL is None and os.path.exists(MODEL_PATH):
        with open(MODEL_PATH) as f:
            _MODEL = json.load(f)
    return _MODEL


def scan_injection_ml(text: str) -> dict:
    m = _load()
    if not m:
        return {"score": 0.0, "label": False, "trained": False}
    p = _predict(m["w"], m["b"], featurize(text))
    return {"score": round(p, 3), "label": p >= 0.5, "trained": True}


if __name__ == "__main__":
    from ._corpus import build
    data = build()
    split = int(len(data) * 0.8)
    train_set, test_set = data[:split], data[split:]
    print(f"corpus: {len(data)}  (train {len(train_set)} / test {len(test_set)})")
    w, b = train(train_set)
    metrics = evaluate(w, b, test_set)
    save(w, b)
    print("held-out test metrics:")
    for k in ("accuracy", "precision", "recall", "f1"):
        print(f"  {k:10s}: {metrics[k]:.3f}")
    print(f"  confusion  : tp={metrics['tp']} fp={metrics['fp']} "
          f"tn={metrics['tn']} fn={metrics['fn']}")
    print(f"model saved -> {os.path.relpath(MODEL_PATH)}")
