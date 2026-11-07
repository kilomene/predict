"""Form, attack/defence strength, and team-stat rates.

All rates are per-match (football) unless stated. Weighted form gives
recent matches more weight — a team's last match matters more than one 10 ago.
"""
from __future__ import annotations

def weighted_form(results: list[float], decay: float = 0.85) -> float:
    """results: points (3/1/0) or any per-match metric, oldest first."""
    if not results:
        return 0.0
    w = [decay ** (len(results) - 1 - i) for i in range(len(results))]
    return sum(r * wi for r, wi in zip(results, w)) / sum(w)

def attack_defence_strength(team_for: float, team_against: float,
                            league_avg: float) -> tuple[float, float]:
    """Classic Maher/Poisson strengths relative to league average."""
    return team_for / league_avg, team_against / league_avg

def expected_goals(home_attack: float, away_defence: float,
                   away_attack: float, home_defence: float,
                   league_avg: float, home_adv_factor: float = 1.15) -> tuple[float, float]:
    lam_home = home_attack * away_defence * league_avg * home_adv_factor
    lam_away = away_attack * home_defence * league_avg / home_adv_factor
    return round(lam_home, 3), round(lam_away, 3)

def injury_adjustment(lam: float, missing_xg_share: float) -> float:
    """Reduce a team's expected output by the xG share of confirmed absentees.
    missing_xg_share: sum of absent players' xG+xA share of team total, 0..1.
    This is where lineup/injury news (Sofascore, Transfermarkt, pressers) enters."""
    return lam * max(0.3, 1.0 - missing_xg_share)
