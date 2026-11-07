"""Volleyball — Elo-calibrated set model (first to 3 sets).

Same calibration discipline as tennis: Elo expectancy is the match
probability; we invert the best-of-5 set formula for the per-set prob
and simulate sets, so set-score outputs agree with the headline prob.
(A rally-level simulation is the roadmap refinement when rally data exists.)
"""
from __future__ import annotations
import random
from ..features.elo import expected_score
from .tennis import _invert_set_prob

def predict(elo_home: float, elo_away: float, home_adv: float = 40) -> dict:
    p_match = expected_score(elo_home, elo_away, home_adv)
    s = _invert_set_prob(p_match, best_of=5)
    rng = random.Random(7)
    trials = 4000
    home_wins = 0
    set_counts: dict[str, int] = {}
    total_sets = 0
    for _ in range(trials):
        sa = sb = 0
        while sa < 3 and sb < 3:
            if rng.random() < s:
                sa += 1
            else:
                sb += 1
        total_sets += sa + sb
        key = f"{sa}-{sb}"
        set_counts[key] = set_counts.get(key, 0) + 1
        if sa == 3:
            home_wins += 1
    return {
        "home_win_prob": round(p_match, 4),
        "away_win_prob": round(1 - p_match, 4),
        "home_set_prob": round(s, 4),
        "simulated_match_prob_check": round(home_wins / trials, 4),
        "expected_sets": round(total_sets / trials, 2),
        "set_score_probs": {k: round(v / trials, 4) for k, v in sorted(set_counts.items())},
        "over_3_5_sets": round(sum(v for k, v in set_counts.items()
                                   if int(k[0]) + int(k[2]) >= 4) / trials, 4),
        "over_4_5_sets": round((set_counts.get("3-2", 0) + set_counts.get("2-3", 0)) / trials, 4),
    }
