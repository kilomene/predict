"""Calibration layer (v2.0) — make the probabilities mean what they say.

A model that says 60% must win ~60% of the time in that bucket, or every
downstream decision built on its numbers (value flags, Kelly stakes,
confidence gates) is arithmetic on fiction. v0.3 shipped with NO calibration
at all; this module is the fix.

Method: vector scaling (Guo et al. 2017, extended) —

    p'_i  ∝  exp( log(p_i) / T  +  b_i )

with one temperature T and a per-class bias b. The draw class bias b_D is
exactly the systematic draw correction: if the raw model chronically
under-states draws, fitting raises b_D until predicted draw mass matches
reality. Fitted by minimising log-loss on held-out historical predictions
(never on the matches being predicted).

Also provided: Platt scaling for binary markets (Over/Under, BTTS),
expected calibration error (ECE), and per-class calibration reports.
"""
from __future__ import annotations
import json, math

CLASSES = ("H", "D", "A")

def _softmax(z):
    m = max(z)
    e = [math.exp(v - m) for v in z]
    s = sum(e)
    return [v / s for v in e]

def apply_vector_scaling(probs, params: dict):
    """probs: (pH, pD, pA). params: {'temperature': T, 'bias': [bH, bD, bA]}"""
    T = float(params.get("temperature", 1.0)) or 1.0
    b = params.get("bias", [0.0, 0.0, 0.0])
    z = [math.log(max(p, 1e-9)) / T + float(b[i]) for i, p in enumerate(probs)]
    return tuple(_softmax(z))

def fit_vector_scaling(probs_list, outcomes, l2: float = 1e-3) -> dict:
    """outcomes: list of class indices 0/1/2. Returns fitted params dict.
    Uses scipy when available; falls back to a simple grid+coordinate search."""
    import numpy as np
    P = np.clip(np.array(probs_list, dtype=float), 1e-9, 1.0)
    Y = np.array(outcomes, dtype=int)
    logP = np.log(P)
    n = len(Y)

    def nll(x):
        T = math.exp(x[0])  # parametrise T in log space, stays positive
        b = np.array(x[1:4])
        z = logP / T + b
        z = z - z.max(axis=1, keepdims=True)
        e = np.exp(z)
        q = e / e.sum(axis=1, keepdims=True)
        return float(-np.log(np.clip(q[np.arange(n), Y], 1e-12, 1.0)).mean()
                     + l2 * float((b ** 2).sum()))

    try:
        from scipy.optimize import minimize
        res = minimize(nll, [0.0, 0.0, 0.0, 0.0], method="Nelder-Mead",
                       options={"maxiter": 4000, "xatol": 1e-4, "fatol": 1e-6})
        x = res.x
    except Exception:
        # coordinate search fallback: coarse-to-fine on (T, bD) with bH=bA=0 baseline
        best, bx = nll([0.0, 0.0, 0.0, 0.0]), [0.0, 0.0, 0.0, 0.0]
        step = 0.4
        while step > 0.01:
            improved = False
            for i in range(4):
                for s in (-step, step):
                    cand = list(bx); cand[i] += s
                    v = nll(cand)
                    if v < best:
                        best, bx, improved = v, cand, True
            if not improved:
                step /= 2
        x = bx
    return {"temperature": round(math.exp(float(x[0])), 4),
            "bias": [round(float(v), 4) for v in x[1:4]]}

def fit_platt(probs, outcomes) -> dict:
    """Binary Platt scaling: p' = sigmoid(a * logit(p) + b)."""
    import numpy as np
    p = np.clip(np.array(probs, dtype=float), 1e-6, 1 - 1e-6)
    y = np.array(outcomes, dtype=float)
    logit = np.log(p / (1 - p))

    def nll(ab):
        a, b = ab
        q = 1.0 / (1.0 + np.exp(-(a * logit + b)))
        return float(-(y * np.log(np.clip(q, 1e-12, 1)) +
                       (1 - y) * np.log(np.clip(1 - q, 1e-12, 1))).mean())
    try:
        from scipy.optimize import minimize
        res = minimize(nll, [1.0, 0.0], method="Nelder-Mead",
                       options={"maxiter": 2000})
        a, b = float(res.x[0]), float(res.x[1])
    except Exception:
        a, b = 1.0, 0.0
    return {"a": round(a, 4), "b": round(b, 4)}

def apply_platt(p: float, params: dict) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    z = params["a"] * math.log(p / (1 - p)) + params["b"]
    return 1.0 / (1.0 + math.exp(-z))

def log_loss(probs_list, outcomes) -> float:
    n = max(1, len(outcomes))
    return -sum(math.log(max(probs_list[i][outcomes[i]], 1e-12))
                for i in range(len(outcomes))) / n

def accuracy(probs_list, outcomes) -> float:
    if not outcomes:
        return 0.0
    return sum(1 for i, y in enumerate(outcomes)
               if max(range(3), key=lambda k: probs_list[i][k]) == y) / len(outcomes)

def ece(probs_list, outcomes, bins: int = 10) -> float:
    """Top-label expected calibration error."""
    if not outcomes:
        return 0.0
    buckets = [[] for _ in range(bins)]
    for p, y in zip(probs_list, outcomes):
        top = max(range(3), key=lambda k: p[k])
        buckets[min(bins - 1, int(p[top] * bins))].append((p[top], 1.0 if top == y else 0.0))
    err, n = 0.0, len(outcomes)
    for b in buckets:
        if b:
            err += len(b) / n * abs(sum(v for _, v in b) / len(b)
                                    - sum(c for c, _ in b) / len(b))
    return err

def class_calibration(probs_list, outcomes) -> dict:
    """Per-class: mean predicted probability vs actual frequency.
    The draw row is the one v0.3 never measured."""
    out = {}
    n = max(1, len(outcomes))
    for k, name in enumerate(CLASSES):
        pred = sum(p[k] for p in probs_list) / n
        actual = sum(1 for y in outcomes if y == k) / n
        out[name] = {"predicted": round(pred, 4), "actual": round(actual, 4),
                     "gap": round(pred - actual, 4)}
    return out

def save_params(params: dict, path: str) -> None:
    with open(path, "w") as f:
        json.dump(params, f, indent=1)

def load_params(path: str) -> dict | None:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None
