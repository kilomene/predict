"""NBA possessions model (v2.0 phase 2) — replaces the v0.3 dummy.

v0.3 fed basketball.predict() `110 ± Elo/25` for every team, so every game
read "Home 54%, total 220". This module builds REAL ratings from the free
ESPN API (the same source the fixtures come from, no key):

  possessions/game (pace)  = FGA + 0.44*FTA - ORB + TOV      (standard estimate)
  offensive rating (ORtg)  = points per 100 possessions
  defensive rating (DRtg)  = points allowed per 100 possessions
                             (standings avgPointsAgainst over the team's own
                              possession estimate — possessions are ~equal for
                              both teams in a game, documented approximation)

Expected points for a matchup (the classic possessions formula):

  game_possessions = pace_h * pace_a / league_pace
  pts_h = game_possessions * (ORtg_h * DRtg_a / league_ORtg) / 100 + 1.25
  pts_a = game_possessions * (ORtg_a * DRtg_h / league_ORtg) / 100 - 1.25

(±1.25 = home-court, a net 2.5-point swing.) Output feeds the existing
Normal spread/total machinery in basketball.predict().
"""
from __future__ import annotations
import requests

BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
BASE_V2 = "https://site.api.espn.com/apis/v2/sports/basketball/nba"

def _get(url, timeout=25):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()

def _stat_map(team_stats_json) -> dict:
    out = {}
    cats = (team_stats_json.get("results", {}).get("stats", {})
            .get("categories", []))
    for c in cats:
        for s in c.get("stats", []):
            try:
                out[s["name"]] = float(s.get("value") or s.get("displayValue") or 0)
            except (TypeError, ValueError):
                continue
    return out

def _standings_points_against() -> dict:
    """displayName -> avgPointsAgainst, gathered from every conference."""
    j = _get(f"{BASE_V2}/standings")
    found = {}
    def walk(o):
        if isinstance(o, dict):
            for e in o.get("entries", []) or []:
                try:
                    name = e["team"]["displayName"]
                    for s in e.get("stats", []):
                        if s.get("name") == "avgPointsAgainst":
                            found[name] = float(s.get("value") or s.get("displayValue"))
                except Exception:
                    continue
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(j)
    return found

def build_ratings() -> dict | None:
    """{team displayName: {pace, ortg, drtg}} + league averages under '_league'.
    None on any failure — callers fall back and SAY so."""
    try:
        teams_j = _get(f"{BASE}/teams")
        teams = teams_j["sports"][0]["leagues"][0]["teams"]
        against = _standings_points_against()
        ratings = {}
        for t in teams:
            team = t["team"]
            name, tid = team["displayName"], team["id"]
            sm = _stat_map(_get(f"{BASE}/teams/{tid}/statistics"))
            fga = sm.get("avgFieldGoalsAttempted", 0)
            fta = sm.get("avgFreeThrowsAttempted", 0)
            orb = sm.get("avgOffensiveRebounds", 0)
            tov = sm.get("avgTurnovers", 0)
            pts = sm.get("avgPoints", 0)
            pa = against.get(name, 0)
            poss = fga + 0.44 * fta - orb + tov
            if poss <= 0 or pts <= 0 or pa <= 0:
                continue
            ratings[name] = {"pace": round(poss, 2),
                             "ortg": round(pts / poss * 100, 2),
                             "drtg": round(pa / poss * 100, 2)}
        if len(ratings) < 20:
            return None
        n = len(ratings)
        ratings["_league"] = {
            "pace": sum(v["pace"] for v in ratings.values() if isinstance(v, dict)) / n,
            "ortg": sum(v["ortg"] for v in ratings.values() if isinstance(v, dict)) / n,
        }
        return ratings
    except Exception:
        return None

def expected_points(home: str, away: str, ratings: dict):
    """(expected_home_pts, expected_away_pts) or None if a team is missing."""
    h, a = ratings.get(home), ratings.get(away)
    lg = ratings.get("_league")
    if not h or not a or not lg:
        return None
    poss = h["pace"] * a["pace"] / lg["pace"]
    pts_h = poss * (h["ortg"] * a["drtg"] / lg["ortg"]) / 100 + 1.25
    pts_a = poss * (a["ortg"] * h["drtg"] / lg["ortg"]) / 100 - 1.25
    return round(pts_h, 1), round(pts_a, 1)
