"""Pi-ratings (Constantinou & Fenton 2013) — v2.0 phase 2.

Why: plain Elo learns only H/D/A and throws away the scoreline. Pi-ratings
learn from goal difference, damp large margins (a 5-0 teaches less than five
1-0s), and keep SEPARATE home and away ratings per team. Published head-to-head
on the same data: RPS 0.1991 (pi) vs 0.2042 (Elo) vs 0.1914 (Dixon-Coles) —
pi closes ~40% of the Elo->DC gap at a fraction of the cost, and its real
job here is as a FEATURE for the ML stack and a standalone probability head.

Formulation (published transform, constants exposed for tuning):
  diff         = R_home(home rating) - R_away(away rating)
  expected GD  = 3 * (10^(diff/3) - 1) / (10^(diff/3) + 1)     (in [-3, 3])
  error        = actual GD - expected GD
  damped error = sign(e) * 3 * log10(1 + |e|)                  (the pi damping)
  update       = learning_rate * damped error, applied to the venue ratings
                 (home team's home rating up, away team's away rating down)

Probability head: expected GD + league total-goals expectation give
lambda_home/lambda_away, read off the Dixon-Coles scoreline matrix — so the
head can never contradict the goals model it feeds.
"""
from __future__ import annotations
import math
from ..models.football import score_matrix, markets_from_matrix

class PiRatings:
    def __init__(self, learning_rate: float = 0.10, gd_scale: float = 3.0):
        self.lr = learning_rate
        self.gd_scale = gd_scale
        self.home: dict[str, float] = {}
        self.away: dict[str, float] = {}

    def get_home(self, team: str) -> float:
        return self.home.get(team, 0.0)

    def get_away(self, team: str) -> float:
        return self.away.get(team, 0.0)

    def diff(self, home_team: str, away_team: str) -> float:
        return self.get_home(home_team) - self.get_away(away_team)

    def expected_gd(self, home_team: str, away_team: str) -> float:
        d = self.diff(home_team, away_team)
        t = 10 ** (d / 3.0)
        return self.gd_scale * (t - 1) / (t + 1)

    def _damped(self, e: float) -> float:
        return math.copysign(3.0 * math.log10(1.0 + abs(e)), e) if e else 0.0

    def update(self, home_team: str, away_team: str, home_goals: int, away_goals: int) -> None:
        gd = home_goals - away_goals
        err = gd - self.expected_gd(home_team, away_team)
        step = self.lr * self._damped(err)
        self.home[home_team] = self.get_home(home_team) + step
        self.away[away_team] = self.get_away(away_team) - step

    def probs(self, home_team: str, away_team: str, league_total: float = 2.6,
              rho: float = -0.08):
        """1X2 head: split the league total by expected GD, read the matrix."""
        gd = self.expected_gd(home_team, away_team)
        lam_h = min(max((league_total + gd) / 2.0, 0.15), 4.2)
        lam_a = min(max((league_total - gd) / 2.0, 0.15), 4.2)
        mk = markets_from_matrix(score_matrix(lam_h, lam_a, rho=rho))
        return (mk["home_win"], mk["draw"], mk["away_win"])

    def features(self, home_team: str, away_team: str) -> dict:
        return {"pi_diff": round(self.diff(home_team, away_team), 4),
                "pi_home": round(self.get_home(home_team), 4),
                "pi_away": round(self.get_away(away_team), 4),
                "pi_expected_gd": round(self.expected_gd(home_team, away_team), 4)}
