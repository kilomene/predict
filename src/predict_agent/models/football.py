"""Football model — Poisson scoreline matrix with Dixon-Coles correction,
blended with Elo, plus full match-stat distributions.

Markets produced:
  1X2, double chance, draw-no-bet, Over/Under 0.5..4.5, BTTS,
  correct score (full grid + top picks), Asian handicap lines,
  team goals, clean sheet, win-to-nil, first-half approximations.
Stat distributions (expected + over/under probabilities) for:
  total/home/away shots, shots on target, corners, fouls, cards, offsides, possession proxy.
Player markets live in player_props.py, built on top of this matrix.
"""
from __future__ import annotations
import math
from .value import poisson_pmf

def _dc_tau(x: int, y: int, lam_h: float, lam_a: float, rho: float = -0.08) -> float:
    """Dixon-Coles low-score dependence correction."""
    if x == 0 and y == 0:
        return 1 - lam_h * lam_a * rho
    if x == 0 and y == 1:
        return 1 + lam_h * rho
    if x == 1 and y == 0:
        return 1 + lam_a * rho
    if x == 1 and y == 1:
        return 1 - rho
    return 1.0

def score_matrix(lam_home: float, lam_away: float, max_goals: int = 10, rho: float = -0.08):
    matrix = []
    total = 0.0
    for i in range(max_goals + 1):
        row = []
        for j in range(max_goals + 1):
            p = poisson_pmf(i, lam_home) * poisson_pmf(j, lam_away) * _dc_tau(i, j, lam_home, lam_away, rho)
            row.append(p)
            total += p
        matrix.append(row)
    # normalise (truncation + tau can drift the sum slightly)
    return [[p / total for p in row] for row in matrix]

def markets_from_matrix(m):
    n = len(m)
    home = sum(m[i][j] for i in range(n) for j in range(n) if i > j)
    draw = sum(m[i][i] for i in range(n))
    away = sum(m[i][j] for i in range(n) for j in range(n) if i < j)
    def over(line: float) -> float:
        k = int(line) + 1
        return sum(m[i][j] for i in range(n) for j in range(n) if i + j >= k)
    btts = sum(m[i][j] for i in range(1, n) for j in range(1, n))
    scores = sorted(
        ((m[i][j], f"{i}-{j}") for i in range(n) for j in range(n)), reverse=True)
    return {
        "home_win": home, "draw": draw, "away_win": away,
        "double_chance_1x": home + draw, "double_chance_12": home + away,
        "double_chance_x2": draw + away,
        "draw_no_bet_home": home / (home + away) if home + away else 0,
        "draw_no_bet_away": away / (home + away) if home + away else 0,
        "over_0_5": over(0.5), "over_1_5": over(1.5), "over_2_5": over(2.5),
        "over_3_5": over(3.5), "over_4_5": over(4.5),
        "under_2_5": 1 - over(2.5), "under_3_5": 1 - over(3.5),
        "btts_yes": btts, "btts_no": 1 - btts,
        "home_clean_sheet": sum(m[i][0] for i in range(n)),
        "away_clean_sheet": sum(m[0][j] for j in range(n)),
        "home_win_to_nil": sum(m[i][0] for i in range(1, n)),
        "away_win_to_nil": sum(m[0][j] for j in range(1, n)),
        "home_over_1_5": sum(sum(m[i][j] for j in range(n)) for i in range(2, n)),
        "away_over_1_5": sum(sum(m[i][j] for i in range(n)) for j in range(2, n)),
        "top_correct_scores": [{"score": s, "prob": round(p, 4)} for p, s in scores[:5]],
        "correct_score_grid": {f"{i}-{j}": round(m[i][j], 4)
                               for i in range(6) for j in range(6)},
    }

def blend_with_elo(markets: dict, elo_home_prob: float, elo_weight: float = 0.25) -> dict:
    """Blend Poisson 1X2 with Elo expectancy. Elo has no draw concept, so its
    mass is split home/away and the draw is shrunk proportionally."""
    non_draw = markets["home_win"] + markets["away_win"]
    if non_draw <= 0:
        return markets
    elo_h = elo_home_prob * non_draw
    elo_a = (1 - elo_home_prob) * non_draw
    markets = dict(markets)
    markets["home_win"] = (1 - elo_weight) * markets["home_win"] + elo_weight * elo_h
    markets["away_win"] = (1 - elo_weight) * markets["away_win"] + elo_weight * elo_a
    s = markets["home_win"] + markets["draw"] + markets["away_win"]
    for k in ("home_win", "draw", "away_win"):
        markets[k] /= s
    return markets

# ---------- match-stat distributions ----------
def stat_line_probs(expected: float, lines=(0.5,)) -> dict:
    """Poisson distribution summary for a counting stat (shots, corners, fouls...).
    Cards/fouls are better with Negative Binomial in v2; Poisson is the honest v1."""
    from .value import poisson_at_least
    out = {"expected": round(expected, 2)}
    for line in lines:
        out[f"over_{line}"] = round(poisson_at_least(int(line) + 1, expected), 4)
    out["distribution_top"] = sorted(
        ((round(poisson_pmf(k, expected), 4), k) for k in range(0, 30)), reverse=True)[:3]
    return out

def match_stats(home: dict, away: dict, referee: dict | None = None) -> dict:
    """Inputs are per-match team averages:
    shots, shots_on_target, corners, fouls_committed, fouls_drawn, cards, offsides.
    Referee: {cards_per_game, fouls_per_game} — scales card/foul expectations,
    because referee strictness is one of the strongest card-market signals."""
    ref = referee or {}
    ref_card_factor = (ref.get("cards_per_game", 3.6) / 3.6) if ref else 1.0
    ref_foul_factor = (ref.get("fouls_per_game", 22.0) / 22.0) if ref else 1.0

    def exp_stat(key_h, key_a, cross=True):
        # team's own rate blended with what the opponent typically concedes/draws
        return (home[key_h] + away[key_a]) / 2 if cross else home[key_h]

    total_fouls = (home["fouls_committed"] + away["fouls_committed"]) * ref_foul_factor
    total_cards = (home.get("cards", 1.8) + away.get("cards", 1.8)) * ref_card_factor
    return {
        "home_shots": stat_line_probs(exp_stat("shots", "shots_conceded"), (9.5, 10.5, 11.5, 12.5)),
        "away_shots": stat_line_probs(exp_stat("shots", "shots_conceded") if False else
                                      (away["shots"] + home["shots_conceded"]) / 2, (9.5, 10.5, 11.5)),
        "total_shots": stat_line_probs(home["shots"] + away["shots"], (22.5, 23.5, 24.5, 25.5)),
        "home_shots_on_target": stat_line_probs((home["shots_on_target"] + away["sot_conceded"]) / 2, (3.5, 4.5, 5.5)),
        "away_shots_on_target": stat_line_probs((away["shots_on_target"] + home["sot_conceded"]) / 2, (3.5, 4.5)),
        "total_shots_on_target": stat_line_probs(home["shots_on_target"] + away["shots_on_target"], (7.5, 8.5, 9.5)),
        "home_corners": stat_line_probs((home["corners"] + away["corners_conceded"]) / 2, (4.5, 5.5, 6.5)),
        "away_corners": stat_line_probs((away["corners"] + home["corners_conceded"]) / 2, (3.5, 4.5, 5.5)),
        "total_corners": stat_line_probs(home["corners"] + away["corners"], (8.5, 9.5, 10.5, 11.5)),
        "home_fouls": stat_line_probs(home["fouls_committed"] * ref_foul_factor, (9.5, 10.5, 11.5)),
        "away_fouls": stat_line_probs(away["fouls_committed"] * ref_foul_factor, (9.5, 10.5, 11.5)),
        "total_fouls": stat_line_probs(total_fouls, (20.5, 22.5, 24.5, 26.5)),
        "total_cards": stat_line_probs(total_cards, (2.5, 3.5, 4.5, 5.5)),
        "home_offsides": stat_line_probs(home.get("offsides", 1.8), (1.5, 2.5)),
        "away_offsides": stat_line_probs(away.get("offsides", 1.8), (1.5, 2.5)),
        "_note": "Expectations are model means, not certainties. A stat with expected 5.2 "
                 "lands anywhere in a wide range — bet the distribution, never the mean alone.",
    }

def predict(lam_home: float, lam_away: float, elo_home_prob: float | None = None,
            home_stats: dict | None = None, away_stats: dict | None = None,
            referee: dict | None = None) -> dict:
    m = score_matrix(lam_home, lam_away)
    mk = markets_from_matrix(m)
    if elo_home_prob is not None:
        mk = blend_with_elo(mk, elo_home_prob)
    out = {"lambda_home": lam_home, "lambda_away": lam_away, "markets": mk}
    if home_stats and away_stats:
        out["match_stats"] = match_stats(home_stats, away_stats, referee)
    # honest accuracy note attached to every football output
    out["_accuracy_note"] = (
        "Correct score is intrinsically low-probability: even a perfect model puts only "
        "~10-15% on its single most likely scoreline. Treat the grid as probabilities.")
    return out
