"""xG-EWMA ratings (v2.0 phase 2) — learn from the chance-creation process,
not just its noisy sample (goals).

Each team's attacking/defensive strength is an exponentially weighted moving
average of its per-match xG for/against (football-data.co.uk publishes HxG/AxG
for the big-5), so recent matches count more and a lucky/unlucky finishing
run does not drag the rating the way raw goals do. Lambdas are then built
exactly like the goals model — attack x defence x league average — which
lets the two be A/B-tested and blended on identical footing.
"""
from __future__ import annotations

class XgEwma:
    def __init__(self, alpha: float = 0.22, prior_games: float = 5.0):
        self.alpha = alpha
        self.prior = prior_games  # shrinkage: ratings start at league average
        self.xgf: dict[str, float] = {}
        self.xga: dict[str, float] = {}
        self.games: dict[str, int] = {}
        self.total_xg = 0.0
        self.matches = 0

    @property
    def league_avg(self) -> float:
        return self.total_xg / self.matches if self.matches else 2.6

    def _shrunk(self, store: dict, team: str) -> float:
        la = self.league_avg / 2.0
        g = self.games.get(team, 0)
        if team not in store:
            return la
        return (store[team] * g + la * self.prior) / (g + self.prior)

    def update(self, home: str, away: str, hxg: float, axg: float) -> None:
        a = self.alpha
        for team, xf, xa in ((home, hxg, axg), (away, axg, hxg)):
            if team in self.xgf:
                self.xgf[team] = (1 - a) * self.xgf[team] + a * xf
                self.xga[team] = (1 - a) * self.xga[team] + a * xa
            else:
                self.xgf[team], self.xga[team] = xf, xa
            self.games[team] = self.games.get(team, 0) + 1
        self.total_xg += hxg + axg
        self.matches += 1

    def lambdas(self, home: str, away: str):
        la = self.league_avg / 2.0
        if la <= 0:
            return None
        lam_h = (self._shrunk(self.xgf, home) / la) * (self._shrunk(self.xga, away) / la) * la * 1.12
        lam_a = (self._shrunk(self.xgf, away) / la) * (self._shrunk(self.xga, home) / la) * la / 1.12
        return (min(max(lam_h, 0.2), 4.0), min(max(lam_a, 0.2), 4.0))
