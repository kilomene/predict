"""Basketball — Elo + pace-adjusted Normal points model."""
from __future__ import annotations
import math
from .value import normal_cdf

def predict(home_pts_exp: float, away_pts_exp: float,
            home_sd: float = 12.0, away_sd: float = 12.0,
            elo_home_prob: float | None = None) -> dict:
    diff_mean = home_pts_exp - away_pts_exp
    diff_sd = math.sqrt(home_sd ** 2 + away_sd ** 2)
    p_home = normal_cdf(diff_mean / diff_sd)
    if elo_home_prob is not None:
        p_home = 0.7 * p_home + 0.3 * elo_home_prob
    total = home_pts_exp + away_pts_exp
    total_sd = diff_sd
    def total_over(line: float) -> float:
        return 1 - normal_cdf((line - total) / total_sd)
    return {
        "expected_home_points": round(home_pts_exp, 1),
        "expected_away_points": round(away_pts_exp, 1),
        "expected_total": round(total, 1),
        "expected_margin_home": round(diff_mean, 1),
        "home_win_prob": round(p_home, 4), "away_win_prob": round(1 - p_home, 4),
        "total_over_220_5": round(total_over(220.5), 4),
        "total_over_230_5": round(total_over(230.5), 4),
        "_note": "Totals/spread for any line: total_over uses Normal(total, sd); "
                 "ask the CLI with --total-line / --spread to get exact lines.",
    }

def total_over_prob(total_exp: float, line: float, sd: float = 17.0) -> float:
    return round(1 - normal_cdf((line - total_exp) / sd), 4)

def spread_prob(margin_exp: float, home_spread: float, sd: float = 17.0) -> float:
    """home_spread negative = home favourite (e.g. -5.5). P(home covers)."""
    return round(1 - normal_cdf(((-home_spread) - margin_exp) / sd), 4)
