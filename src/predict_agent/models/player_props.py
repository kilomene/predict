"""Player props — goalscorer, assists, shots, shots on target, fouls, cards.

Method (the same one serious prop models use):
  player_lambda = team_lambda x player's share of team xG (or xA / shots / fouls)
  adjusted for expected minutes, penalty-taker status, and confirmed lineup.
  Then Poisson (goals/shots) or Bernoulli chains give:
    P(anytime scorer), P(first scorer approx), P(2+ goals), P(assist),
    P(over X shots), P(over X shots on target), P(card), P(over X fouls).

Inputs per player (per 90, from FBref / Understat / Sofascore / API-Football):
  name, team ('home'|'away'), xg_per90, xa_per90, shots_per90, sot_per90,
  key_passes_per90, fouls_per90, cards_per90, expected_minutes (default 90),
  penalty_taker (bool), set_piece_taker (bool)
"""
from __future__ import annotations
from .value import poisson_pmf, poisson_at_least

def _scale(per90: float, minutes: float) -> float:
    return per90 * (minutes / 90.0)

def player_prediction(p: dict, team_lambda: float) -> dict:
    mins = p.get("expected_minutes", 90)
    f = mins / 90.0
    # Player goal expectation: blend direct xG/90 with share-of-team method
    xg90 = p.get("xg_per90", 0.0)
    share = p.get("xg_share", None)
    lam_goal = xg90 * f
    if share is not None:
        lam_goal = 0.5 * lam_goal + 0.5 * (team_lambda * share)
    if p.get("penalty_taker"):
        # penalty duty adds roughly the team's penalty rate x conversion
        lam_goal += 0.12 * f
    lam_goal = max(lam_goal, 0.0)

    lam_assist = _scale(p.get("xa_per90", 0.0), mins)
    lam_shots = _scale(p.get("shots_per90", 0.0), mins)
    lam_sot = _scale(p.get("sot_per90", 0.0), mins)
    lam_fouls = _scale(p.get("fouls_per90", 0.0), mins)
    card_p = min(0.85, p.get("cards_per90", 0.0) * f * 1.0 + max(0.0, lam_fouls - 2.0) * 0.03)

    return {
        "player": p["name"], "team": p.get("team"),
        "expected_minutes": mins,
        "expected_goals": round(lam_goal, 3),
        "anytime_scorer_prob": round(1 - poisson_pmf(0, lam_goal), 4),
        "two_plus_goals_prob": round(poisson_at_least(2, lam_goal), 4),
        "brace_or_better_note": "P(2+) above; hat-trick is P(3+)",
        "hat_trick_prob": round(poisson_at_least(3, lam_goal), 4),
        "expected_assists": round(lam_assist, 3),
        "anytime_assist_prob": round(1 - poisson_pmf(0, lam_assist), 4),
        "goal_or_assist_prob": round(1 - poisson_pmf(0, lam_goal + lam_assist), 4),
        "expected_shots": round(lam_shots, 2),
        "shots_over_1_5": round(poisson_at_least(2, lam_shots), 4),
        "shots_over_2_5": round(poisson_at_least(3, lam_shots), 4),
        "expected_shots_on_target": round(lam_sot, 2),
        "sot_over_0_5": round(1 - poisson_pmf(0, lam_sot), 4),
        "sot_over_1_5": round(poisson_at_least(2, lam_sot), 4),
        "expected_fouls": round(lam_fouls, 2),
        "fouls_over_1_5": round(poisson_at_least(2, lam_fouls), 4),
        "card_prob": round(card_p, 4),
        "key_passes_expected": round(_scale(p.get("key_passes_per90", 0.0), mins), 2),
    }

def predict_players(players: list[dict], lam_home: float, lam_away: float) -> dict:
    out = [player_prediction(p, lam_home if p.get("team") == "home" else lam_away)
           for p in players]
    out.sort(key=lambda d: d["anytime_scorer_prob"], reverse=True)
    return {
        "most_likely_scorers": out[:5],
        "all_players": out,
        "first_scorer_note": (
            "First scorer approx = anytime prob weighted by team's share of total "
            "expected goals and by early-goal tendency; see ranked list. Exact first-scorer "
            "probabilities need minute-by-minute hazard modelling (roadmap)."),
    }

# ---- Other sports' player props (same share/rate method) ----
def basketball_player(p: dict) -> dict:
    """p: name, minutes, pts_per_min, reb_per_min, ast_per_min, threes_per_min, usage note."""
    m = p.get("minutes", 32)
    lam_pts = p.get("pts_per_min", 0.6) * m
    lam_ast = p.get("ast_per_min", 0.18) * m
    lam_reb = p.get("reb_per_min", 0.22) * m
    lam_3 = p.get("threes_per_min", 0.08) * m
    from .value import poisson_at_least as al
    return {"player": p["name"], "expected_points": round(lam_pts, 1),
            "points_over_19_5_note": "use lines param in full engine",
            "expected_assists": round(lam_ast, 1), "expected_rebounds": round(lam_reb, 1),
            "expected_threes": round(lam_3, 1),
            "pra_expected": round(lam_pts + lam_ast + lam_reb, 1)}

def tennis_player(p: dict, sets_expected: float = 2.6) -> dict:
    """p: name, aces_per_set, df_per_set, break_pct."""
    return {"player": p["name"],
            "expected_aces": round(p.get("aces_per_set", 0.4) * sets_expected, 1),
            "expected_double_faults": round(p.get("df_per_set", 0.3) * sets_expected, 1),
            "break_prob_per_return_game": p.get("break_pct", 0.22)}

def volleyball_player(p: dict, sets_expected: float = 3.8) -> dict:
    """p: name, kills_per_set, blocks_per_set, aces_per_set."""
    return {"player": p["name"],
            "expected_kills": round(p.get("kills_per_set", 3.0) * sets_expected, 1),
            "expected_blocks": round(p.get("blocks_per_set", 0.5) * sets_expected, 1),
            "expected_aces": round(p.get("aces_per_set", 0.3) * sets_expected, 1)}
