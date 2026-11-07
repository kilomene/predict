"""Auto player props — Premier League via the official FPL API (free, no key).

The FPL bootstrap feed carries every PL player's season totals: minutes,
goals, assists, expected goals (xG), expected assists (xA), starts, and
penalties_order. From those we build per-90 rates and feed the shared
player_props model — no hand-typed JSON.

Coverage honesty: this feed is Premier League only. Other leagues need
API-Sports (key) or Sofascore wiring — until then their daily sheets carry
team-level markets, and this module returns None so nothing is faked.
Shots per 90 are estimated from xG (league-average ~0.12 xG per shot,
~35% on target) and labelled as estimates wherever they surface.
"""
from __future__ import annotations
import json, os, time
import requests

CACHE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cache")
BOOT_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"

def _bootstrap() -> dict | None:
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "fpl_bootstrap.json")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < 3600:
        try:
            return json.load(open(path))
        except Exception:
            pass
    try:
        r = requests.get(BOOT_URL, timeout=30, headers={"User-Agent": "predict-agent"})
        r.raise_for_status()
        data = r.json()
        json.dump(data, open(path, "w"))
        return data
    except Exception:
        return None

def team_map(boot: dict) -> dict[int, str]:
    return {t["id"]: t["name"] for t in boot.get("teams", [])}

def pl_player_props(home_name: str, away_name: str, lam_home: float, lam_away: float,
                    min_minutes: int = 300, per_team: int = 6) -> dict | None:
    """home_name/away_name: names as in the FPL feed (use daily.match_team to map).
    Returns predict_players() output or None if data is unavailable."""
    from predict_agent.models.player_props import predict_players
    boot = _bootstrap()
    if not boot:
        return None
    teams = team_map(boot)
    inv = {v: k for k, v in teams.items()}
    if home_name not in inv or away_name not in inv:
        return None
    players: list[dict] = []
    for side, tname, tid in (("home", home_name, inv[home_name]),
                             ("away", away_name, inv[away_name])):
        cands = []
        for el in boot.get("elements", []):
            if el["team"] != tid:
                continue
            mins = el.get("minutes", 0)
            if mins < min_minutes:
                continue
            try:
                xg = float(el.get("expected_goals") or 0)
                xa = float(el.get("expected_assists") or 0)
            except ValueError:
                xg = xa = 0.0
            f90 = 90.0 / mins
            xg90, xa90 = xg * f90, xa * f90
            # expected minutes: share of available minutes, capped, starters boosted
            exp_min = min(90.0, max(20.0, mins / max(1, el.get("starts", 1)) if el.get("starts") else 60.0))
            cands.append({
                "name": el.get("web_name", "Unknown"), "team": side,
                "xg_per90": round(xg90, 3), "xa_per90": round(xa90, 3),
                "shots_per90": round(xg90 / 0.12, 2),          # estimate, see docstring
                "sot_per90": round(xg90 / 0.12 * 0.35, 2),     # estimate
                "key_passes_per90": round(xa90 / 0.30, 2),     # ~0.30 xA per key pass, estimate
                "fouls_per90": 1.0, "cards_per90": 0.12,
                "expected_minutes": round(exp_min),
                "penalty_taker": el.get("penalties_order") == 1,
                "_xg90": xg90,
            })
        cands.sort(key=lambda d: -d["_xg90"])
        players.extend(cands[:per_team])
    if not players:
        return None
    for p in players:
        p.pop("_xg90", None)
    out = predict_players(players, lam_home, lam_away)
    out["_source"] = "FPL official API (Premier League); shots/key-passes are xG-derived estimates"
    return out
