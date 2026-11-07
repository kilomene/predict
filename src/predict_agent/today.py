"""Today's fixtures + live links for all 4 sports.
With keys: pulls API-Sports / football-data.org / ESPN.
Without keys: prints the live-score hubs to check, and the MoviOdds boards.
  python -m predict_agent.today
"""
from __future__ import annotations
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from predict_agent.data import live

HUBS = {
    "football": "https://www.livescore.com/en/football/",
    "basketball": "https://www.livescore.com/en/basketball/",
    "tennis": "https://www.livescore.com/en/tennis/",
    "volleyball": "https://www.livescore.com/en/volleyball/",
    "flashscore_all": "https://www.flashscore.com/",
    "sofascore_all": "https://www.sofascore.com/",
}

def main():
    out = {"live_score_hubs": HUBS, "bookmakers": {
        "sportybet": "https://www.sportybet.com",
        "bet9ja": "https://www.bet9ja.com",
        "1xbet": "https://1xbet.com",
        "football_com": "https://www.football.com",
    }}
    for sport in ("soccer", "basketball", "tennis", "volleyball"):
        board = live.moviodds(sport)
        if board:
            out[f"moviodds_{sport}"] = board if not isinstance(board, dict) else \
                {k: board[k] for k in list(board)[:3]} if len(str(board)) > 4000 else board
        else:
            out[f"moviodds_{sport}"] = "unavailable right now — check the live hubs above"
    print(json.dumps(out, indent=2, default=str)[:12000])

if __name__ == "__main__":
    main()
