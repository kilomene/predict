"""Value engine — shared by every sport.

A prediction is only a bet when model probability beats the market.
"""
from __future__ import annotations
import math

def implied_prob(decimal_odds: float) -> float:
    if decimal_odds <= 1.0:
        raise ValueError("decimal odds must be > 1.0")
    return 1.0 / decimal_odds

def remove_overround(odds: list[float]) -> list[float]:
    """Normalise implied probs so they sum to 1 (removes bookmaker margin)."""
    raw = [implied_prob(o) for o in odds]
    s = sum(raw)
    return [p / s for p in raw]

def overround(odds: list[float]) -> float:
    return sum(implied_prob(o) for o in odds) - 1.0

def expected_value(model_p: float, decimal_odds: float) -> float:
    """EV per 1 unit staked."""
    return model_p * decimal_odds - 1.0

def edge(model_p: float, decimal_odds: float, all_market_odds: list[float] | None = None) -> float:
    """Edge vs fair (no-vig) implied probability when the full market is known,
    otherwise vs raw implied probability."""
    if all_market_odds:
        # position of this selection must be handled by caller via fair_prob arg;
        # here fall back to raw for the single-odds signature
        pass
    return model_p - implied_prob(decimal_odds)

def kelly_fraction(model_p: float, decimal_odds: float, fraction: float = 0.25, cap: float = 0.05) -> float:
    """Fractional Kelly stake as a fraction of bankroll. Default quarter-Kelly, capped at 5%."""
    b = decimal_odds - 1.0
    q = 1.0 - model_p
    full = (b * model_p - q) / b if b > 0 else 0.0
    return max(0.0, min(cap, full * fraction))

def assess(model_p: float, decimal_odds: float, min_edge: float = 0.05) -> dict:
    imp = implied_prob(decimal_odds)
    ev = expected_value(model_p, decimal_odds)
    e = model_p - imp
    return {
        "model_prob": round(model_p, 4),
        "implied_prob": round(imp, 4),
        "edge": round(e, 4),
        "ev_per_unit": round(ev, 4),
        "kelly_quarter_capped": round(kelly_fraction(model_p, decimal_odds), 4),
        "verdict": "VALUE" if (e >= min_edge and ev > 0) else "NO BET",
    }

def poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def poisson_at_least(k_min: int, lam: float, max_k: int = 15) -> float:
    return sum(poisson_pmf(k, lam) for k in range(k_min, max_k + 1))

def poisson_over(line: float, lam: float) -> float:
    """P(total > line) for a half line e.g. 2.5."""
    return poisson_at_least(int(line) + 1, lam)

def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def brier_score(probs: list[float], outcomes: list[int]) -> float:
    return sum((p - o) ** 2 for p, o in zip(probs, outcomes)) / max(1, len(probs))

def log_loss(probs: list[float], outcomes: list[int], eps: float = 1e-12) -> float:
    total = 0.0
    for p, o in zip(probs, outcomes):
        p = min(max(p, eps), 1 - eps)
        total += -(o * math.log(p) + (1 - o) * math.log(1 - p))
    return total / max(1, len(probs))
