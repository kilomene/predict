"""Live in-play engine — re-prices a match from its current state.

Modes:
  match   Manual what-if (testable, no feed needed):
            python -m predict_agent.live_engine match --lam-home 1.9 --lam-away 1.1 \
                --minute 67 --score 1-0 --red-away 1
  once    Snapshot of every currently-live match in the tracked leagues,
          using pre-match strengths from the daily runner.
  check   One monitoring pass over today's ledger: prints ALERT lines for
          big win-probability swings (>=15 pts vs pre-match) and full-time
          verdicts (pick right/wrong). State in out/live_state.json so each
          event is reported once. This is what the 15-minute cron runs.
  watch   Loop `check`-style snapshots in the terminal every N seconds.

Football method: remaining-goals Poisson/Dixon-Coles matrix.
  remaining_lambda = pre-match lambda x remaining-time fraction (of 94')
  adjusted for red cards (x0.60 self / x1.30 opponent, per card),
  score state (trailing team +10%, leading team -8% — documented heuristic),
  and live xG momentum when supplied (observed xG rate vs expected, clamped).
Basketball: remaining-points Normal model. Tennis: exact game-state DP for
the current set + set-race recursion. Volleyball: rally Monte Carlo.
"""
from __future__ import annotations
import argparse, json, math, os, random, re, sys, time
from functools import lru_cache

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from predict_agent.models.football import score_matrix
from predict_agent.models.value import normal_cdf
from predict_agent.models.tennis import _match_prob_from_set

TOTAL_MINUTES = 94.0
RED_SELF, RED_OPP = 0.60, 1.30

# ---------------- FOOTBALL ----------------
def football_live(lam_h: float, lam_a: float, minute: float, score_h: int, score_a: int,
                  red_h: int = 0, red_a: int = 0,
                  xg_h: float | None = None, xg_a: float | None = None) -> dict:
    minute = min(max(minute, 0.0), TOTAL_MINUTES)
    remain_frac = max(0.0, (TOTAL_MINUTES - minute) / TOTAL_MINUTES)
    elapsed_frac = minute / TOTAL_MINUTES
    rem_h, rem_a = lam_h * remain_frac, lam_a * remain_frac
    rem_h *= (RED_SELF ** red_h) * (RED_OPP ** red_a)
    rem_a *= (RED_SELF ** red_a) * (RED_OPP ** red_h)
    if score_h > score_a:
        rem_h *= 0.92; rem_a *= 1.10
    elif score_a > score_h:
        rem_a *= 0.92; rem_h *= 1.10
    if xg_h is not None and xg_a is not None and elapsed_frac > 0.1:
        for side, (xg, lam, ) in enumerate(((xg_h, lam_h), (xg_a, lam_a))):
            exp_so_far = max(lam * elapsed_frac, 0.05)
            factor = min(1.7, max(0.6, 1.0 + 0.35 * (xg / exp_so_far - 1.0)))
            if side == 0:
                rem_h *= factor
            else:
                rem_a *= factor
    m = score_matrix(round(rem_h, 4), round(rem_a, 4), max_goals=8)
    n = len(m)
    home = draw = away = 0.0
    finals: dict[str, float] = {}
    for i in range(n):
        for j in range(n):
            fh, fa = score_h + i, score_a + j
            p = m[i][j]
            finals[f"{fh}-{fa}"] = finals.get(f"{fh}-{fa}", 0.0) + p
            if fh > fa:
                home += p
            elif fh == fa:
                draw += p
            else:
                away += p
    cur_total = score_h + score_a
    def over(line: float) -> float:
        need = int(line) + 1 - cur_total
        if need <= 0:
            return 1.0
        return sum(m[i][j] for i in range(n) for j in range(n) if i + j >= need)
    btts = 1.0
    if score_h == 0 and score_a == 0:
        btts = sum(m[i][j] for i in range(1, n) for j in range(1, n))
    elif score_h == 0:
        btts = sum(m[i][j] for i in range(1, n) for j in range(n))
    elif score_a == 0:
        btts = sum(m[i][j] for i in range(n) for j in range(1, n))
    p_none = m[0][0]
    tot_rem = rem_h + rem_a
    next_home = (1 - p_none) * (rem_h / tot_rem) if tot_rem > 0 else 0.0
    top = sorted(finals.items(), key=lambda kv: -kv[1])[:5]
    return {
        "minute": minute, "score": f"{score_h}-{score_a}",
        "remaining_xg": {"home": round(rem_h, 3), "away": round(rem_a, 3)},
        "home_win": round(home, 4), "draw": round(draw, 4), "away_win": round(away, 4),
        "over_2_5": round(over(2.5), 4), "over_3_5": round(over(3.5), 4),
        "btts_yes": round(btts, 4),
        "next_goal_home": round(next_home, 4),
        "next_goal_away": round((1 - p_none) - next_home, 4),
        "no_more_goals": round(p_none, 4),
        "top_final_scores": [{"score": s, "prob": round(p, 4)} for s, p in top],
    }

# ---------------- BASKETBALL ----------------
def basketball_live(exp_h: float, exp_a: float, elapsed_min: float,
                    pts_h: int, pts_a: int, total_min: float = 48.0) -> dict:
    frac = max(0.0, (total_min - elapsed_min) / total_min)
    rem_mean_h, rem_mean_a = exp_h * frac, exp_a * frac
    sd = 12.0 * math.sqrt(frac) if frac > 0 else 0.01
    diff_mean = (pts_h - pts_a) + (rem_mean_h - rem_mean_a)
    diff_sd = math.sqrt(2) * sd
    p_home = normal_cdf(diff_mean / diff_sd)
    total_mean = pts_h + pts_a + rem_mean_h + rem_mean_a
    return {"home_win": round(p_home, 4), "away_win": round(1 - p_home, 4),
            "expected_final": {"home": round(pts_h + rem_mean_h, 1),
                               "away": round(pts_a + rem_mean_a, 1)},
            "expected_total": round(total_mean, 1)}

# ---------------- TENNIS (exact DP) ----------------
@lru_cache(maxsize=None)
def _set_prob_from_games(g: float, a: int, b: int) -> float:
    """P(A wins set) from game score a-b, per-game win prob g, tiebreak at 6-6."""
    if a >= 6 and a - b >= 2:
        return 1.0
    if b >= 6 and b - a >= 2:
        return 0.0
    if a == 6 and b == 6:
        return g  # tiebreak proxy: game prob as tiebreak prob
    if a == 7:
        return 1.0
    if b == 7:
        return 0.0
    return g * _set_prob_from_games(g, a + 1, b) + (1 - g) * _set_prob_from_games(g, a, b + 1)

def _game_prob_from_set_prob(p_set: float) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if _set_prob_from_games(mid, 0, 0) < p_set:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

def _match_prob_from_sets(p_set: float, sets_a: int, sets_b: int, best_of: int) -> float:
    need = best_of // 2 + 1
    if sets_a >= need:
        return 1.0
    if sets_b >= need:
        return 0.0
    return (p_set * _match_prob_from_sets(p_set, sets_a + 1, sets_b, best_of)
            + (1 - p_set) * _match_prob_from_sets(p_set, sets_a, sets_b + 1, best_of))

def tennis_live(p_set_a: float, sets_a: int, sets_b: int,
                games_a: int, games_b: int, best_of: int = 3) -> dict:
    g = _game_prob_from_set_prob(p_set_a)
    cur_set = _set_prob_from_games(g, games_a, games_b)
    p_match = (cur_set * _match_prob_from_sets(p_set_a, sets_a + 1, sets_b, best_of)
               + (1 - cur_set) * _match_prob_from_sets(p_set_a, sets_a, sets_b + 1, best_of))
    if sets_a >= best_of // 2 + 1:
        p_match = 1.0
    if sets_b >= best_of // 2 + 1:
        p_match = 0.0
    return {"player_a_win": round(p_match, 4), "player_b_win": round(1 - p_match, 4),
            "current_set_a": round(cur_set, 4), "game_prob_a": round(g, 4)}

# ---------------- VOLLEYBALL (Monte Carlo) ----------------
def volleyball_live(p_set_home: float, sets_h: int, sets_a: int,
                    pts_h: int, pts_a: int, trials: int = 4000) -> dict:
    rally = 0.5 + (p_set_home - 0.5) * 0.28  # documented approximation
    rng = random.Random(11)
    def play_set(ph: int, pa: int, target: int) -> bool:
        h, a = ph, pa
        while True:
            if rng.random() < rally:
                h += 1
            else:
                a += 1
            if (h >= target or a >= target) and abs(h - a) >= 2:
                return h > a
    wins = 0
    for _ in range(trials):
        sh, sa = sets_h, sets_a
        first = True
        while sh < 3 and sa < 3:
            target = 15 if sh + sa == 4 else 25
            won = play_set(pts_h if first else 0, pts_a if first else 0, target)
            first = False
            if won:
                sh += 1
            else:
                sa += 1
        if sh == 3:
            wins += 1
    return {"home_win": round(wins / trials, 4), "away_win": round(1 - wins / trials, 4),
            "rally_prob_home": round(rally, 4)}

# ---------------- FEED + MONITORING ----------------
def _espn_live_events(path: str, yyyymmdd: str) -> list[dict]:
    import requests
    try:
        r = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/{path}/scoreboard",
                         params={"dates": yyyymmdd}, timeout=25)
        return r.json().get("events", [])
    except Exception:
        return []

def _parse_event(ev: dict) -> dict | None:
    try:
        comp = ev["competitions"][0]
        cs = {c["homeAway"]: c for c in comp["competitors"]}
        st = ev.get("status", {})
        state = st.get("type", {}).get("state", "pre")
        clock = st.get("displayClock", "") or ""
        mnt = re.match(r"(\d+)", clock)
        out = {"home": cs["home"]["team"]["displayName"],
               "away": cs["away"]["team"]["displayName"],
               "state": state,
               "minute": int(mnt.group(1)) if mnt else None,
               "home_score": int(cs["home"].get("score") or 0),
               "away_score": int(cs["away"].get("score") or 0)}
        return out
    except Exception:
        return None

def _load(p, d):
    try:
        return json.load(open(p))
    except Exception:
        return d

def check(threshold: float = 0.15) -> list[str]:
    """One monitoring pass. Returns human alert lines (possibly empty)."""
    from predict_agent.daily import (OUT, FOOTBALL_LEAGUES, football_strengths,
                                     football_prediction, norm)
    from datetime import datetime
    from zoneinfo import ZoneInfo
    today = datetime.now(ZoneInfo("America/Chicago")).date()
    ledger = _load(os.path.join(OUT, "ledger.json"), [])
    live_state = _load(os.path.join(OUT, "live_state.json"), {})
    alerts: list[str] = []
    strengths: dict = {}
    entries = [e for e in ledger if e["sport"] == "football"
               and e["date"] in (today.isoformat(),
                                  (today.fromordinal(today.toordinal() - 1)).isoformat())]
    for code, (path, display) in FOOTBALL_LEAGUES.items():
        for ymd in {e["date"].replace("-", "") for e in entries}:
            for ev in _espn_live_events(path, ymd):
                fx = _parse_event(ev)
                if not fx:
                    continue
                match = next((e for e in entries
                              if norm(e["home"]) == norm(fx["home"])
                              and norm(e["away"]) == norm(fx["away"])), None)
                if not match:
                    continue
                key = f"{match['date']}|{match['home']}|{match['away']}"
                if fx["state"] == "post" and not live_state.get(key, {}).get("ft_reported"):
                    hs, as_ = fx["home_score"], fx["away_score"]
                    actual = "H" if hs > as_ else "D" if hs == as_ else "A"
                    verdict = "PICK CORRECT" if actual == match["pick"] else "pick wrong"
                    top_hit = match.get("top_score", {}).get("score") == f"{hs}-{as_}"
                    alerts.append(
                        f"FULL TIME {match['home']} {hs}-{as_} {match['away']} — "
                        f"our pick was {match['pick']} ({verdict})"
                        + (" · CORRECT SCORE HIT" if top_hit else ""))
                    live_state[key] = {**live_state.get(key, {}), "ft_reported": True}
                elif fx["state"] == "in" and fx["minute"] is not None:
                    if code not in strengths:
                        try:
                            strengths[code] = football_strengths(code)
                        except Exception:
                            continue
                    avgs, xg, elo = strengths[code]
                    got, _err = football_prediction(fx["home"], fx["away"], avgs, xg, elo)
                    if not got:
                        continue
                    pred, _conf, _h, _a = got
                    live = football_live(pred["lambda_home"], pred["lambda_away"],
                                         fx["minute"], fx["home_score"], fx["away_score"])
                    prev = live_state.get(key, {})
                    pre_home = match["probs"]["H"]
                    swing = live["home_win"] - pre_home
                    last_alert = prev.get("last_alert_prob")
                    if abs(swing) >= threshold and (last_alert is None
                                                    or abs(live["home_win"] - last_alert) >= 0.10):
                        alerts.append(
                            f"LIVE {fx['minute']}' {match['home']} {fx['home_score']}-"
                            f"{fx['away_score']} {match['away']} — home win prob "
                            f"{pre_home:.0%} pre-match → {live['home_win']:.0%} now "
                            f"(draw {live['draw']:.0%}, away {live['away_win']:.0%}, "
                            f"likeliest final {live['top_final_scores'][0]['score']})")
                        prev = {**prev, "last_alert_prob": live["home_win"]}
                    prev = {**prev, "last_live_home_win": live["home_win"],
                            "last_minute": fx["minute"]}
                    live_state[key] = prev
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, "live_state.json.tmp")
    json.dump(live_state, open(tmp, "w"), indent=1)
    os.replace(tmp, os.path.join(OUT, "live_state.json"))
    if alerts:
        with open(os.path.join(OUT, "live_alerts.jsonl"), "a") as f:
            for a in alerts:
                f.write(json.dumps({"alert": a}) + "\n")
    return alerts

def main():
    ap = argparse.ArgumentParser(prog="live_engine")
    sub = ap.add_subparsers(dest="mode", required=True)
    m = sub.add_parser("match")
    m.add_argument("--lam-home", type=float, required=True)
    m.add_argument("--lam-away", type=float, required=True)
    m.add_argument("--minute", type=float, required=True)
    m.add_argument("--score", required=True, help="e.g. 1-0")
    m.add_argument("--red-home", type=int, default=0)
    m.add_argument("--red-away", type=int, default=0)
    m.add_argument("--xg-home", type=float)
    m.add_argument("--xg-away", type=float)
    sub.add_parser("check")
    w = sub.add_parser("watch")
    w.add_argument("--interval", type=int, default=120)
    args = ap.parse_args()
    if args.mode == "match":
        sh, sa = (int(x) for x in args.score.split("-"))
        print(json.dumps(football_live(args.lam_home, args.lam_away, args.minute,
                                       sh, sa, args.red_home, args.red_away,
                                       args.xg_home, args.xg_away), indent=2))
    elif args.mode == "check":
        for a in check():
            print("ALERT:", a)
    elif args.mode == "watch":
        print(f"watching every {args.interval}s — Ctrl+C to stop")
        while True:
            for a in check():
                print("ALERT:", a, flush=True)
            time.sleep(args.interval)

if __name__ == "__main__":
    main()
