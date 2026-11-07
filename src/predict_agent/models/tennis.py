"""Tennis — surface Elo + set simulation, calibrated by construction.

Elo expectancy IS a match-win probability. Using it directly as a per-game
probability would square the edge and inflate favourites (a bug we caught
in testing: 50 Elo points showed 77% instead of ~57%). Instead we invert
the best-of-N set formula to get the per-set probability that reproduces
the Elo match probability, then simulate sets from it. Match, set and
set-score outputs are therefore consistent with each other and with Elo.
"""
from __future__ import annotations
import random
from ..features.elo import expected_score

def _match_prob_from_set(s: float, best_of: int) -> float:
    need = best_of // 2 + 1
    # P(win match) for best-of-3: s^2 + 2 s^2 (1-s); best-of-5: s^3 + 3 s^3(1-s) + 6 s^3(1-s)^2
    if need == 2:
        return s * s + 2 * s * s * (1 - s)
    return s**3 + 3 * s**3 * (1 - s) + 6 * s**3 * (1 - s) ** 2

def _invert_set_prob(match_p: float, best_of: int) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if _match_prob_from_set(mid, best_of) < match_p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

def match_prob(elo_a: float, elo_b: float, surface_elo_a: float | None = None,
               surface_elo_b: float | None = None, best_of: int = 3) -> dict:
    if surface_elo_a is not None and surface_elo_b is not None:
        p_match = 0.5 * expected_score(elo_a, elo_b) + 0.5 * expected_score(surface_elo_a, surface_elo_b)
    else:
        p_match = expected_score(elo_a, elo_b)
    s = _invert_set_prob(p_match, best_of)
    rng = random.Random(42)
    need = best_of // 2 + 1
    trials = 4000
    wins = 0
    total_sets = 0
    score_counts: dict[str, int] = {}
    for _ in range(trials):
        sa = sb = 0
        while sa < need and sb < need:
            if rng.random() < s:
                sa += 1
            else:
                sb += 1
        total_sets += sa + sb
        score_counts[f"{sa}-{sb}"] = score_counts.get(f"{sa}-{sb}", 0) + 1
        if sa > sb:
            wins += 1
    return {
        "player_a_win_prob": round(p_match, 4),
        "player_b_win_prob": round(1 - p_match, 4),
        "player_a_set_prob": round(s, 4),
        "expected_sets": round(total_sets / trials, 2),
        "set_score_probs": {k: round(v / trials, 4) for k, v in sorted(score_counts.items())},
        "simulated_match_prob_check": round(wins / trials, 4),
    }
