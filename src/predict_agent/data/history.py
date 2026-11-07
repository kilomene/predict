"""Historical training data — football-data.co.uk free CSVs.

Each CSV carries results PLUS shots, shots on target, corners, fouls,
cards, referee, and Bet365 + Pinnacle closing odds — i.e. almost every
feature the full model needs, for training and honest backtesting.
League codes: E0 Premier League, E1 Championship, SP1 La Liga,
D1 Bundesliga, I1 Serie A, F1 Ligue 1, N1 Eredivisie, P1 Primeira, etc.
"""
from __future__ import annotations
import csv, io, os
import requests

BASE = "https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"
CACHE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "cache")

def download(league: str = "E0", season: str = "2324", use_cache: bool = True) -> list[dict]:
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{league}_{season}.csv")
    if use_cache and os.path.exists(path):
        text = open(path, encoding="utf-8", errors="ignore").read()
    else:
        r = requests.get(BASE.format(season=season, league=league), timeout=30)
        r.raise_for_status()
        text = r.text
        open(path, "w", encoding="utf-8").write(text)
    rows = list(csv.DictReader(io.StringIO(text)))
    return [r for r in rows if r.get("HomeTeam")]

def team_averages(rows: list[dict]) -> dict:
    """Per-team per-match averages for every stat the CSV carries."""
    from collections import defaultdict
    agg = defaultdict(lambda: defaultdict(float))
    games = defaultdict(int)
    def add(team, stats):
        games[team] += 1
        for k, v in stats.items():
            agg[team][k] += v
    def f(row, key):
        try:
            return float(row.get(key) or 0)
        except ValueError:
            return 0.0
    for r in rows:
        add(r["HomeTeam"], {
            "goals_for": f(r, "FTHG"), "goals_against": f(r, "FTAG"),
            "shots": f(r, "HS"), "shots_conceded": f(r, "AS"),
            "sot": f(r, "HST"), "sot_conceded": f(r, "AST"),
            "corners": f(r, "HC"), "corners_conceded": f(r, "AC"),
            "fouls_committed": f(r, "HF"), "cards": f(r, "HY") + 3 * f(r, "HR"),
            "offsides": 0.0})
        add(r["AwayTeam"], {
            "goals_for": f(r, "FTAG"), "goals_against": f(r, "FTHG"),
            "shots": f(r, "AS"), "shots_conceded": f(r, "HS"),
            "sot": f(r, "AST"), "sot_conceded": f(r, "HST"),
            "corners": f(r, "AC"), "corners_conceded": f(r, "HC"),
            "fouls_committed": f(r, "AF"), "cards": f(r, "AY") + 3 * f(r, "AR"),
            "offsides": 0.0})
    return {t: {k: round(v / games[t], 3) for k, v in s.items()} | {"games": games[t]}
            for t, s in agg.items()}
