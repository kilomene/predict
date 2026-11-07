"""Elo engine — generic, with sport presets and tennis surface support."""
from __future__ import annotations

PRESETS = {
    "football": {"k": 20, "home_adv": 65, "base": 1500},
    "basketball": {"k": 20, "home_adv": 100, "base": 1500},  # ~100 Elo ≈ 3.5 pts
    "tennis": {"k": 32, "home_adv": 0, "base": 1500},
    "volleyball": {"k": 24, "home_adv": 40, "base": 1500},
}

def expected_score(rating_a: float, rating_b: float, home_adv: float = 0.0) -> float:
    return 1.0 / (1.0 + 10 ** (-(rating_a + home_adv - rating_b) / 400.0))

class EloTable:
    def __init__(self, sport: str = "football"):
        self.sport = sport
        p = PRESETS[sport]
        self.k, self.home_adv, self.base = p["k"], p["home_adv"], p["base"]
        self.ratings: dict[str, float] = {}
        # tennis: surface ratings keyed "Player|clay" etc.
        self.surface_ratings: dict[str, float] = {}

    def get(self, team: str) -> float:
        return self.ratings.get(team, self.base)

    def get_surface(self, player: str, surface: str) -> float:
        return self.surface_ratings.get(f"{player}|{surface}", self.get(player))

    def update(self, home: str, away: str, home_won: bool, draw: bool = False,
               margin_factor: float = 1.0, surface: str | None = None):
        rh, ra = self.get(home), self.get(away)
        exp_h = expected_score(rh, ra, self.home_adv)
        actual_h = 0.5 if draw else (1.0 if home_won else 0.0)
        delta = self.k * margin_factor * (actual_h - exp_h)
        self.ratings[home] = rh + delta
        self.ratings[away] = ra - delta
        if surface:
            sh, sa = self.get_surface(home, surface), self.get_surface(away, surface)
            exp_s = expected_score(sh, sa, 0)
            ds = self.k * margin_factor * (actual_h - exp_s)
            self.surface_ratings[f"{home}|{surface}"] = sh + ds
            self.surface_ratings[f"{away}|{surface}"] = sa - ds

    def win_prob(self, home: str, away: str) -> float:
        return expected_score(self.get(home), self.get(away), self.home_adv)
