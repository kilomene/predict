"""Deep links — live scores and bookmakers. Link, don't scrape against ToS."""
from __future__ import annotations
import urllib.parse

LIVE_SCORES = {
    "livescore": "https://www.livescore.com/en/search/?q={q}",
    "flashscore": "https://www.flashscore.com/search/?q={q}",
    "sofascore": "https://www.sofascore.com/search/all?q={q}",
    "fotmob": "https://www.fotmob.com/search?q={q}",
    "espn": "https://www.espn.com/search/_/q/{q}",
    "bbc_sport": "https://www.bbc.co.uk/search?q={q}+football",
}
BOOKMAKERS = {
    "sportybet": "https://www.sportybet.com/ng/sport/football/search?keyword={q}",
    "bet9ja": "https://www.bet9ja.com/search?q={q}",
    "1xbet": "https://1xbet.com/en/search?q={q}",
    "football_com": "https://www.football.com/en/search?q={q}",
    "bet365": "https://www.bet365.com/#/AS/B1/",
    "pinnacle": "https://www.pinnacle.com/en/search/{q}",
}
STATS_SOURCES = {
    "fbref": "https://fbref.com/en/search/search.fcgi?search={q}",
    "understat": "https://understat.com/",
    "whoscored": "https://www.whoscored.com/Search?q={q}",
    "transfermarkt_injuries": "https://www.transfermarkt.com/suche/ergebnisliste?query={q}",
    "clubelo": "http://clubelo.com/",
    "forebet": "https://www.forebet.com/en/football-tips-and-predictions-for-today",
    "footystats": "https://footystats.org/",
    "statsbomb_open_data": "https://github.com/statsbomb/open-data",
}

def links_for(home: str, away: str) -> dict:
    q = urllib.parse.quote(f"{home} {away}")
    return {
        "live_scores": {k: v.format(q=q) for k, v in LIVE_SCORES.items()},
        "bookmakers": {k: v.format(q=q) for k, v in BOOKMAKERS.items()},
        "stats": {k: v.format(q=q) for k, v in STATS_SOURCES.items()},
    }
