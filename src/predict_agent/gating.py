"""The gate (v2.0) — decide what kind of call the evidence actually supports.

v0.3's failure mode, measured on the 2026-11-07 live card: the headline pick
was always the argmax outcome, even at 36%, so five draws were "predicted"
as home/away wins. A probability distribution is not a pick. This module is
the layer that turns calibrated probabilities into an honest call:

  SINGLE         one outcome is strong enough to stand alone (top >= 0.60)
  DOUBLE_CHANCE  no single outcome is strong, but the top two together are
                 (sum >= 0.78 and top >= 0.42) — the call names both
  NO_PICK        the match is too close to separate; saying so IS the output

The gate never edits the probabilities and never hides the raw argmax pick:
the ledger still records and grades the argmax separately, so the model's
true hit rate stays auditable. Calls are graded as their own record.
"""
from __future__ import annotations

DEFAULTS = {"single_min": 0.53, "dc_sum_min": 0.78, "dc_top_min": 0.42}
# single_min 0.53 chosen from the train-fitted sweep in fit_v2 (2026-11-07):
# test singles hit 63.2% at 23% coverage there, vs 59.9% at 0.50 / 33%.
LABELS = ("H", "D", "A")
NAMES = {"H": "Home", "D": "Draw", "A": "Away"}
DC_NAME = {frozenset("HD"): "1X", frozenset("HA"): "12", frozenset("DA"): "X2"}

def decide(probs, cfg: dict | None = None) -> dict:
    """probs: calibrated (pH, pD, pA). Returns a call dict:
    {type, selection(s), top_prob, probs} — selection is a class label for
    SINGLE, a frozenset-name like '1X' for DOUBLE_CHANCE, None for NO_PICK."""
    cfg = {**DEFAULTS, **(cfg or {})}
    order = sorted(range(3), key=lambda k: -probs[k])
    top, second = order[0], order[1]
    p_top, p_second = probs[top], probs[second]
    if p_top >= cfg["single_min"]:
        return {"type": "SINGLE", "selection": LABELS[top],
                "label": NAMES[LABELS[top]], "top_prob": round(p_top, 4)}
    if p_top >= cfg["dc_top_min"] and p_top + p_second >= cfg["dc_sum_min"]:
        pair = frozenset((LABELS[top], LABELS[second]))
        return {"type": "DOUBLE_CHANCE", "selection": DC_NAME[pair],
                "covers": sorted(pair), "top_prob": round(p_top, 4),
                "label": f"{NAMES[LABELS[top]]} or {NAMES[LABELS[second]]}"}
    return {"type": "NO_PICK", "selection": None, "top_prob": round(p_top, 4),
            "label": "Too close to call"}

def grade(call: dict, outcome: str) -> bool | None:
    """outcome: 'H'/'D'/'A'. NO_PICK grades as None (excluded, but counted
    in coverage — the gate may never grade itself only on easy matches
    without reporting how many it skipped)."""
    if call["type"] == "SINGLE":
        return call["selection"] == outcome
    if call["type"] == "DOUBLE_CHANCE":
        return outcome in call["covers"]
    return None

def summarise(calls_outcomes) -> dict:
    """calls_outcomes: list of (call, outcome). Full gate report card."""
    n = len(calls_outcomes)
    singles = [(c, o) for c, o in calls_outcomes if c["type"] == "SINGLE"]
    dcs = [(c, o) for c, o in calls_outcomes if c["type"] == "DOUBLE_CHANCE"]
    skips = n - len(singles) - len(dcs)
    def rate(rows):
        return round(sum(1 for c, o in rows if grade(c, o)) / len(rows), 4) if rows else None
    return {"matches": n,
            "singles": len(singles), "singles_hit_rate": rate(singles),
            "singles_coverage": round(len(singles) / n, 4) if n else 0.0,
            "double_chance": len(dcs), "dc_hit_rate": rate(dcs),
            "dc_coverage": round(len(dcs) / n, 4) if n else 0.0,
            "no_pick": skips,
            "no_pick_rate": round(skips / n, 4) if n else 0.0}
