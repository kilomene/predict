"""Live data clients — free tiers only, graceful without keys.

- MoviOdds: bet365 odds, NO key, all 4 sports (beta, free)
- The Odds API: 500 credits/mo free (key)
- API-Sports: fixtures/stats/odds/predictions, 100/day per sport (key)
- football-data.org: fixtures/results, 10/min free (key)
- ESPN unofficial: live scores, no key
All functions return [] / {} on failure instead of raising — a missing
feed must degrade the prediction's confidence, never crash the agent.
"""
from __future__ import annotations
import os
import requests

TIMEOUT = 20

def _get(url, headers=None, params=None):
    try:
        r = requests.get(url, headers=headers or {}, params=params or {}, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def moviodds(sport: str = "soccer", stats: bool = False):
    """sport: soccer|basketball|tennis|volleyball — bet365 board, no key."""
    url = f"https://moviodds.com/odds?sport={sport}" + ("&stats=1" if stats else "")
    try:
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def the_odds_api(sport_key: str, regions: str = "uk,eu", markets: str = "h2h,totals"):
    key = os.getenv("THE_ODDS_API_KEY")
    if not key:
        return None
    return _get(f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds",
                params={"apiKey": key, "regions": regions, "markets": markets,
                        "oddsFormat": "decimal"})

# The Odds API sport keys (subset)
ODDS_API_KEYS = {
    "football": "soccer_epl",  # override per league, e.g. soccer_spain_la_liga
    "basketball": "basketball_nba",
    "tennis": "tennis_atp_us_open",  # tournament-specific keys
}

def api_sports(sport: str, endpoint: str, params: dict | None = None):
    """sport: football|basketball|volleyball — one account, per-sport hosts."""
    key = os.getenv("API_SPORTS_KEY")
    if not key:
        return None
    host = f"v3.{sport}.api-sports.io" if sport == "football" else f"v1.{sport}.api-sports.io"
    return _get(f"https://{host}/{endpoint}",
                headers={"x-apisports-key": key}, params=params)

def football_data_org(endpoint: str, params: dict | None = None):
    key = os.getenv("FOOTBALL_DATA_ORG_KEY")
    if not key:
        return None
    return _get(f"https://api.football-data.org/v4/{endpoint}",
                headers={"X-Auth-Token": key}, params=params)

def espn_scoreboard(sport_path: str):
    """e.g. 'basketball/nba', 'tennis/atp', 'soccer/eng.1' — free, no key."""
    return _get(f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard")
