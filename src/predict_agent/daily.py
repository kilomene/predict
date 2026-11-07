"""Daily picks runner — run every morning by cron, or by hand:

  python -m predict_agent.daily [--date 2026-11-07] [--days 3]

For each date in the horizon it:
  1. SETTLES past ledger entries from ESPN finals, updates the persistent
     Elo state (out/state.json) and the running record (out/record.json).
  2. Builds football strengths from the CURRENT season's football-data.co.uk
     CSVs (real xG columns included where published) + Elo.
  3. Runs the full model per fixture: 1X2 (blended with the ML ensemble
     when out/ml_model.pkl exists), correct scores, totals, BTTS, match
     stats (shots, shots on target, corners, fouls, cards), and — for the
     Premier League — auto player props from the official FPL API.
  4. Flags value vs bet365 Full Time Result odds (MoviOdds, sanity-gated).
  5. Writes out/picks-<date>.md / .json and appends to out/ledger.json.

Honesty rules: unmatched teams are skipped with the reason printed;
confidence labels reflect the data behind each number; basketball/tennis
Elo warms up from settled results and says so until then.
"""
from __future__ import annotations
import argparse, json, os, re, sys, unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import requests

from predict_agent.data.history import download, team_averages
from predict_agent.features.elo import EloTable, expected_score
from predict_agent.models import football, basketball, tennis, volleyball
from predict_agent.models.value import assess
from predict_agent.data.links import links_for

TZ = ZoneInfo("America/Chicago")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "out")
SEASON = "2627"  # 2026/27 — update each August

FOOTBALL_LEAGUES = {
    "E0": ("soccer/eng.1", "Premier League"),
    "SP1": ("soccer/esp.1", "La Liga"),
    "D1": ("soccer/ger.1", "Bundesliga"),
    "I1": ("soccer/ita.1", "Serie A"),
    "F1": ("soccer/fra.1", "Ligue 1"),
}
ESPN_EXTRA = {
    "basketball": ["basketball/nba", "basketball/wnba"],
    "tennis": ["tennis/atp", "tennis/wta"],
}
ALIASES = {
    "manchester united": "Man United", "manchester city": "Man City",
    "newcastle united": "Newcastle", "tottenham hotspur": "Tottenham",
    "tottenham": "Spurs", "wolverhampton wanderers": "Wolves",
    "west ham united": "West Ham", "nottingham forest": "Nottm Forest",
    "brighton & hove albion": "Brighton", "brighton and hove albion": "Brighton",
    "leeds united": "Leeds", "sheffield united": "Sheffield United",
    "ipswich town": "Ipswich", "leicester city": "Leicester",
    "athletic club": "Ath Bilbao", "athletic bilbao": "Ath Bilbao",
    "atlético de madrid": "Ath Madrid", "atletico madrid": "Ath Madrid",
    "real betis": "Betis", "real sociedad": "Sociedad", "celta vigo": "Celta",
    "rayo vallecano": "Vallecano", "deportivo alavés": "Alaves",
    "deportivo alaves": "Alaves", "espanyol": "Espanol",
    "deportivo": "La Coruna", "deportivo la coruña": "La Coruna",
    "deportivo la coruna": "La Coruna", "rcd espanyol": "Espanol",
    "borussia dortmund": "Dortmund", "borussia mönchengladbach": "M'gladbach",
    "borussia monchengladbach": "M'gladbach", "bayer leverkusen": "Leverkusen",
    "bayern munich": "Bayern Munich", "bayern münchen": "Bayern Munich",
    "rb leipzig": "RB Leipzig", "vfb stuttgart": "Stuttgart",
    "vfl wolfsburg": "Wolfsburg", "eintracht frankfurt": "Ein Frankfurt",
    "sc freiburg": "Freiburg", "tsg hoffenheim": "Hoffenheim",
    "1. fc köln": "FC Koln", "1 fc koln": "FC Koln",
    "inter": "Inter", "internazionale": "Inter", "ac milan": "Milan",
    "as roma": "Roma", "ssc napoli": "Napoli", "juventus": "Juventus",
    "ss lazio": "Lazio", "atalanta": "Atalanta", "acf fiorentina": "Fiorentina",
    "paris saint-germain": "Paris SG", "paris sg": "Paris SG",
    "olympique de marseille": "Marseille", "olympique lyonnais": "Lyon",
    "as monaco": "Monaco", "lille osc": "Lille", "ogc nice": "Nice",
    "stade rennais": "Rennes", "rc lens": "Lens",
}

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = s.lower().replace("&", "and")
    s = re.sub(r"\b(fc|afc|cf|sc|ac|as|ss|ssc|ud|cd|rc|ogc|vfl|vfb|tsg|rb|1)\b", "", s)
    return re.sub(r"[^a-z0-9 ]", "", s).strip()

def match_team(name: str, known: dict) -> str | None:
    if name in known:
        return name
    low = name.lower()
    if low in ALIASES:
        target = ALIASES[low]
        if target in known:
            return target
        for k in known:
            if norm(k) == norm(target):
                return k
    n = norm(name)
    for k in known:
        if norm(k) == n:
            return k
    for k in known:
        nk = norm(k)
        if nk and (nk in n or n in nk) and min(len(nk), len(n)) >= 4:
            return k
    return None

def espn_events(path: str, yyyymmdd: str) -> list[dict]:
    try:
        r = requests.get(
            f"https://site.api.espn.com/apis/site/v2/sports/{path}/scoreboard",
            params={"dates": yyyymmdd}, timeout=25)
        return r.json().get("events", [])
    except Exception:
        return []

def espn_fixture(ev: dict) -> dict | None:
    try:
        comp = ev["competitions"][0]
        cs = {c["homeAway"]: c for c in comp["competitors"]}
        state = ev.get("status", {}).get("type", {}).get("state", "pre")
        out = {"home": cs["home"]["team"]["displayName"],
               "away": cs["away"]["team"]["displayName"],
               "kickoff_utc": ev.get("date"), "state": state}
        if state == "post":
            out["home_score"] = int(cs["home"].get("score") or 0)
            out["away_score"] = int(cs["away"].get("score") or 0)
        return out
    except Exception:
        return None

def _load(path, default):
    try:
        return json.load(open(path))
    except Exception:
        return default

def _save(path, obj):
    os.makedirs(OUT, exist_ok=True)
    tmp = path + ".tmp"
    json.dump(obj, open(tmp, "w"), indent=1)
    os.replace(tmp, path)

def settle(state: dict, ledger: list, record: dict, today) -> None:
    for entry in ledger:
        if entry.get("settled") or entry["date"] >= today.isoformat():
            continue
        sport = entry["sport"]
        paths = ([v[0] for v in FOOTBALL_LEAGUES.values()] if sport == "football"
                 else ESPN_EXTRA.get(sport, []))
        final = None
        for p in paths:
            for ev in espn_events(p, entry["date"].replace("-", "")):
                fx = espn_fixture(ev)
                if fx and fx["state"] == "post" and \
                        norm(fx["home"]) == norm(entry["home"]) and norm(fx["away"]) == norm(entry["away"]):
                    final = fx
                    break
            if final:
                break
        if not final:
            continue
        hs, as_ = final["home_score"], final["away_score"]
        entry["settled"] = True
        entry["actual"] = f"{hs}-{as_}"
        tab = state.setdefault(sport, {})
        rh = tab.get(entry["home"], 1500.0)
        ra = tab.get(entry["away"], 1500.0)
        exp_h = expected_score(rh, ra, 65 if sport == "football" else 0)
        actual = 0.5 if hs == as_ else (1.0 if hs > as_ else 0.0)
        if sport in ("tennis", "volleyball"):
            actual = 1.0 if hs > as_ else 0.0
        delta = 20 * (actual - exp_h)
        tab[entry["home"]] = round(rh + delta, 1)
        tab[entry["away"]] = round(ra - delta, 1)
        pred = entry.get("pick")
        if pred:
            hit = (pred == "H" and hs > as_) or (pred == "D" and hs == as_) or (pred == "A" and hs < as_)
            entry["hit"] = bool(hit)
            rec = record.setdefault(sport, {"settled": 0, "hits": 0})
            rec["settled"] += 1
            rec["hits"] += 1 if hit else 0

def football_strengths(code: str):
    rows = download(code, SEASON)
    avgs = team_averages(rows)
    elo = EloTable("football")
    for r in rows:
        elo.update(r["HomeTeam"], r["AwayTeam"], home_won=r["FTR"] == "H", draw=r["FTR"] == "D")
    xg = {}
    from collections import defaultdict
    agg = defaultdict(lambda: [0.0, 0.0, 0])
    for r in rows:
        try:
            hx, ax = float(r.get("HxG") or 0), float(r.get("AxG") or 0)
        except ValueError:
            continue
        if hx or ax:
            agg[r["HomeTeam"]][0] += hx; agg[r["HomeTeam"]][1] += ax; agg[r["HomeTeam"]][2] += 1
            agg[r["AwayTeam"]][0] += ax; agg[r["AwayTeam"]][1] += hx; agg[r["AwayTeam"]][2] += 1
    for t, (xf, xa, g) in agg.items():
        if g:
            xg[t] = {"xg_for": xf / g, "xg_against": xa / g, "games": g}
    return avgs, xg, elo, rows

def football_prediction(home_espn: str, away_espn: str, avgs, xg, elo, rho: float = -0.08):
    h = match_team(home_espn, avgs)
    a = match_team(away_espn, avgs)
    if not h or not a:
        return None, f"team not matched to season data ({home_espn} / {away_espn})"
    teams = list(avgs)
    def lg(key, src):
        vals = [src[t][key] for t in teams if t in src]
        return sum(vals) / max(1, len(vals))
    if h in xg and a in xg and xg[h]["games"] >= 3 and xg[a]["games"] >= 3:
        base = lg("xg_for", xg) or 1.35
        lam_h = (xg[h]["xg_for"] / base) * (xg[a]["xg_against"] / base) * base * 1.12
        lam_a = (xg[a]["xg_for"] / base) * (xg[h]["xg_against"] / base) * base / 1.12
        conf = "HIGH (real xG)"
    else:
        base = lg("goals_for", avgs) or 1.35
        lam_h = (avgs[h]["goals_for"] / base) * (avgs[a]["goals_against"] / base) * base * 1.15
        lam_a = (avgs[a]["goals_for"] / base) * (avgs[h]["goals_against"] / base) * base / 1.15
        conf = "MEDIUM (goals-based)"
    lam_h = min(max(lam_h, 0.25), 3.8)
    lam_a = min(max(lam_a, 0.25), 3.8)
    def stats(team):
        v = avgs[team]
        return {"shots": v["shots"], "shots_conceded": v["shots_conceded"],
                "shots_on_target": v["sot"], "sot_conceded": v["sot_conceded"],
                "corners": v["corners"], "corners_conceded": v["corners_conceded"],
                "fouls_committed": v["fouls_committed"], "cards": v["cards"],
                "offsides": v.get("offsides", 1.8)}
    pred = football.predict(round(lam_h, 3), round(lam_a, 3),
                            elo_home_prob=elo.win_prob(h, a),
                            home_stats=stats(h), away_stats=stats(a), rho=rho)
    return (pred, conf, h, a), None

# ---------------- MoviOdds (bet365) Full Time Result odds ----------------
def moviodds_1x2_index(sport: str = "soccer", run_date=None, window_days: int = 2) -> dict:
    """Only group_id 40 ("Full Time Result") is the real 1X2 market — sibling
    groups share the same labels and poisoned run 1. Plus: our leagues only,
    kickoff within the window, implied-sum sanity gate [0.95, 1.30]."""
    index = {}
    try:
        r = requests.get(f"https://moviodds.com/odds?sport={sport}", timeout=180)
        r.raise_for_status()
        board = r.json()
    except Exception:
        return index
    leagues = ("Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1")
    for m in board.get("matches", []):
        if m.get("in_play"):
            continue
        if sport == "soccer" and not any(l in m.get("league", "") for l in leagues):
            continue
        home, away = m.get("home", ""), m.get("away", "")
        if not home or not away:
            continue
        if run_date is not None:
            try:
                ko = datetime.fromisoformat(m.get("kickoff_utc", "").replace("Z", "+00:00"))
                if abs((ko.date() - run_date).days) > window_days:
                    continue
            except Exception:
                continue
        by_label = {}
        for q in m.get("quotes", []):
            if str(q.get("group_id")) != "40":
                continue
            lab = norm(str(q.get("label", "")))
            if lab in ("draw", "the draw"):
                by_label["D"] = q.get("odds_dec")
            elif lab == norm(home):
                by_label["H"] = q.get("odds_dec")
            elif lab == norm(away):
                by_label["A"] = q.get("odds_dec")
        if len(by_label) == 3 and all(by_label.values()):
            implied = sum(1.0 / o for o in by_label.values())
            if 0.95 <= implied <= 1.30:
                index[(norm(home), norm(away))] = (by_label["H"], by_label["D"], by_label["A"])
    return index

def lookup_odds(index: dict, name_pairs: list[tuple[str, str]]):
    for h, a in name_pairs:
        got = index.get((norm(h), norm(a)))
        if got:
            return got
    return None

# ---------------- per-date generation ----------------
def gen_date(day, ledger, record, state, strengths, odds_index, ensemble, rolling, v2=None):
    ymd = day.strftime("%Y%m%d")
    lines = [f"# Predict — daily picks for {day.isoformat()}", ""]
    picks_json = {"date": day.isoformat(), "generated_tz": "America/Chicago", "fixtures": []}

    lines += ["## Football", ""]
    if odds_index:
        lines.append(f"_bet365 odds via MoviOdds: {len(odds_index)} pre-match fixtures indexed for value checks._")
    else:
        lines.append("_Odds feed unavailable this run — probabilities shown without value flags._")
    lines.append("")

    fpl_names = None
    for code, (path, display) in FOOTBALL_LEAGUES.items():
        events = [espn_fixture(e) for e in espn_events(path, ymd)]
        events = [e for e in events if e and e["state"] == "pre"]
        if not events:
            continue
        if code not in strengths:
            try:
                strengths[code] = football_strengths(code)
            except Exception as ex:
                lines.append(f"_{display}: strength data unavailable ({ex})_")
                continue
        avgs, xg, elo, rows = strengths[code]
        lines.append(f"### {display}")
        for fx in events:
            rho = (v2 or {}).get("rho", {}).get(code, -0.08)
            got, err = football_prediction(fx["home"], fx["away"], avgs, xg, elo, rho=rho)
            if not got:
                lines.append(f"- {fx['home']} vs {fx['away']} — skipped: {err}")
                continue
            pred, conf, h, a = got
            mk = dict(pred["markets"])
            ml_info = None
            if ensemble is not None and code in rolling:
                try:
                    from predict_agent.ml import ml_probs
                    feats, _pois = rolling[code].features(
                        h, a, datetime(day.year, day.month, day.day))
                    pm = ml_probs(ensemble["models"], [feats])[0]
                    w = min(float(ensemble.get("ml_weight", 0.3)), 0.5)
                    blended = [(1 - w) * mk["home_win"] + w * float(pm[0]),
                               (1 - w) * mk["draw"] + w * float(pm[1]),
                               (1 - w) * mk["away_win"] + w * float(pm[2])]
                    s = sum(blended)
                    mk["home_win"], mk["draw"], mk["away_win"] = [b / s for b in blended]
                    ml_info = {"ml_probs": [round(float(x), 4) for x in pm], "ml_weight": w}
                    conf += " + ML ensemble"
                except Exception:
                    ml_info = None
            # v2.0: calibrate the blended 1X2, then let the gate decide the call.
            call = None
            if v2 and code in v2.get("calibration", {}):
                from predict_agent import calibration as _cal, gating as _gate
                raw = (mk["home_win"], mk["draw"], mk["away_win"])
                cprobs = _cal.apply_vector_scaling(raw, v2["calibration"][code])
                mk["home_win"], mk["draw"], mk["away_win"] = cprobs
                mk["probs_raw"] = raw
                call = _gate.decide(cprobs, v2.get("gate"))
                conf += " · v2 calibrated"
            pick = max((mk["home_win"], "H"), (mk["draw"], "D"), (mk["away_win"], "A"))
            tops = ", ".join(f"{t['score']} ({t['prob']:.0%})" for t in mk["top_correct_scores"][:3])
            if call and call["type"] == "SINGLE":
                call_txt = f"call: SINGLE {call['label']} ({call['top_prob']:.0%})"
            elif call and call["type"] == "DOUBLE_CHANCE":
                call_txt = f"call: DOUBLE CHANCE {call['selection']} — {call['label']}"
            elif call:
                call_txt = "call: NO PICK — too close to call"
            else:
                call_txt = (f"pick: {'Home' if pick[1]=='H' else 'Draw' if pick[1]=='D' else 'Away'} "
                            f"({pick[0]:.0%})")
            lines.append(
                f"- **{fx['home']} vs {fx['away']}** — {call_txt} · "
                f"1X2 {mk['home_win']:.0%}/{mk['draw']:.0%}/{mk['away_win']:.0%} · "
                f"scores: {tops} · Over 2.5 {mk['over_2_5']:.0%} · BTTS {mk['btts_yes']:.0%} · "
                f"xG {pred['lambda_home']:.2f}–{pred['lambda_away']:.2f} · conf {conf}")
            ms = pred.get("match_stats") or {}
            if ms:
                lines.append(
                    f"  - Stats: shots {ms['total_shots']['expected']:.0f} "
                    f"(on target {ms['total_shots_on_target']['expected']:.0f}) · "
                    f"corners {ms['total_corners']['expected']:.0f} "
                    f"(over 9.5: {ms['total_corners'].get('over_9.5', 0):.0%}) · "
                    f"fouls {ms['total_fouls']['expected']:.0f} · "
                    f"cards {ms['total_cards']['expected']:.1f} "
                    f"(over 3.5: {ms['total_cards'].get('over_3.5', 0):.0%})")
            if display == "Premier League":
                try:
                    from predict_agent.props_auto import pl_player_props, _bootstrap, team_map
                    if fpl_names is None:
                        boot = _bootstrap()
                        fpl_names = {n: {} for n in team_map(boot).values()} if boot else {}
                    hf = match_team(fx["home"], fpl_names) if fpl_names else None
                    af = match_team(fx["away"], fpl_names) if fpl_names else None
                    if hf and af:
                        props = pl_player_props(hf, af, pred["lambda_home"], pred["lambda_away"])
                        if props:
                            scorers = ", ".join(
                                f"{p['player']} {p['anytime_scorer_prob']:.0%}"
                                for p in props["most_likely_scorers"][:3])
                            best_ast = max(props["all_players"],
                                           key=lambda p: p["anytime_assist_prob"])
                            lines.append(f"  - Scorers: {scorers} · Assist watch: "
                                         f"{best_ast['player']} {best_ast['anytime_assist_prob']:.0%}")
                except Exception:
                    pass
            odds = lookup_odds(odds_index, [(fx["home"], fx["away"]), (h, a)])
            entry = {"date": day.isoformat(), "sport": "football", "league": display,
                     "odds_b365": odds, "home": fx["home"], "away": fx["away"],
                     "pick": pick[1],
                     "probs": {"H": round(mk["home_win"], 4), "D": round(mk["draw"], 4),
                               "A": round(mk["away_win"], 4)},
                     "top_score": mk["top_correct_scores"][0], "settled": False}
            if ml_info:
                entry["ml"] = ml_info
            if call:
                entry["call"] = call
                if "probs_raw" in mk:
                    entry["probs_raw"] = {"H": round(mk["probs_raw"][0], 4),
                                          "D": round(mk["probs_raw"][1], 4),
                                          "A": round(mk["probs_raw"][2], 4)}
            if odds:
                va = {"H": assess(mk["home_win"], odds[0]),
                      "D": assess(mk["draw"], odds[1]),
                      "A": assess(mk["away_win"], odds[2])}
                flags = [f"{k} @{o:.2f} (edge {va[k]['edge']:+.0%})"
                         for k, o in zip("HDA", odds) if va[k]["verdict"] == "VALUE"]
                if flags:
                    lines.append(f"  - **VALUE:** " + " · ".join(flags))
            ledger.append(entry)
            picks_json["fixtures"].append(entry | {"confidence": conf})
        lines.append("")

    for sport, paths in ESPN_EXTRA.items():
        rows_out = []
        for path in paths:
            for e in espn_events(path, ymd):
                fx = espn_fixture(e)
                if fx and fx["state"] == "pre":
                    rows_out.append(fx)
        if not rows_out:
            continue
        lines += [f"## {sport.capitalize()}", ""]
        tab = state.get(sport, {})
        settled_n = record.get(sport, {}).get("settled", 0)
        conf = "MEDIUM (Elo warmed)" if settled_n >= 20 else "LOW (Elo still warming up)"
        for fx in rows_out:
            rh, ra = tab.get(fx["home"], 1500.0), tab.get(fx["away"], 1500.0)
            if sport == "basketball":
                # v2.0: real possessions model (pace/ORtg/DRtg from ESPN team
                # stats) when ratings are available; the old 110±Elo dummy is
                # only a labelled fallback now, never the silent default.
                exp = None
                try:
                    from predict_agent.models import basketball_ratings
                    global _NBA_RATINGS
                    if "_NBA_RATINGS" not in globals():
                        _NBA_RATINGS = basketball_ratings.build_ratings()
                    if _NBA_RATINGS:
                        by_norm = {norm(k): k for k in _NBA_RATINGS if not k.startswith("_")}
                        hk = by_norm.get(norm(fx["home"])); ak = by_norm.get(norm(fx["away"]))
                        if hk and ak:
                            exp = basketball_ratings.expected_points(hk, ak, _NBA_RATINGS)
                except Exception:
                    exp = None
                if exp:
                    p = basketball.predict(exp[0], exp[1],
                                           elo_home_prob=expected_score(rh, ra, 100))
                    conf = "MEDIUM (possessions model: pace/ORtg/DRtg)"
                else:
                    p = basketball.predict(110 + (rh - ra) / 25.0, 110 - (rh - ra) / 25.0,
                                           elo_home_prob=expected_score(rh, ra, 100))
                    conf = "LOW (Elo fallback — ratings unavailable)"
                ph = p["home_win_prob"]
                extra = f" · expected total {p['expected_total']:.0f}"
            else:
                p = tennis.match_prob(rh, ra)
                ph = p["player_a_win_prob"]
                extra = f" · expected sets {p['expected_sets']}"
            pick = "H" if ph >= 0.5 else "A"
            lines.append(f"- **{fx['home']} vs {fx['away']}** — pick: "
                         f"{'Home' if pick=='H' else 'Away'} ({max(ph, 1-ph):.0%}){extra} · conf {conf}")
            entry = {"date": day.isoformat(), "sport": sport, "home": fx["home"],
                     "away": fx["away"], "pick": pick,
                     "probs": {"H": round(ph, 4), "A": round(1 - ph, 4)}, "settled": False}
            ledger.append(entry)
            picks_json["fixtures"].append(entry | {"confidence": conf})
        lines.append("")

    if record:
        lines += ["## Running record (settled by the agent itself)", ""]
        for sport, r in sorted(record.items()):
            if r.get("settled"):
                lines.append(f"- {sport}: {r['hits']}/{r['settled']} picks correct "
                             f"({r['hits'] / r['settled']:.0%})")
        lines.append("")
    lines += ["_Probabilities, not certainties. Correct score top pick is usually a "
              "10–15% shot even for a strong model. Player props: Premier League via "
              "the official FPL API; shots figures are xG-derived estimates._"]
    return lines, picks_json

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (America/Chicago). Default: today")
    ap.add_argument("--days", type=int, default=1, help="horizon: predict this many days forward")
    args = ap.parse_args()
    start = datetime.now(TZ).date() if not args.date else datetime.strptime(args.date, "%Y-%m-%d").date()
    days = [start + timedelta(days=i) for i in range(max(1, args.days))]

    state = _load(os.path.join(OUT, "state.json"), {})
    ledger = _load(os.path.join(OUT, "ledger.json"), [])
    record = _load(os.path.join(OUT, "record.json"), {})
    settle(state, ledger, record, start)
    horizon = {d.isoformat() for d in days}
    ledger = [e for e in ledger if not (e["date"] in horizon and not e.get("settled"))]

    ensemble = None
    rolling: dict = {}
    try:
        from predict_agent.ml import load_ensemble, RollingState, _date
        ensemble = load_ensemble()
        if ensemble is not None:
            for code in FOOTBALL_LEAGUES:
                rows = sorted(download(code, SEASON), key=_date)
                st = RollingState()
                for r in rows:
                    st.update(r)
                rolling[code] = st
    except Exception:
        ensemble = None

    odds_index = moviodds_1x2_index("soccer", run_date=start, window_days=max(2, args.days + 1))
    v2 = None
    try:
        from predict_agent.calibration import load_params
        v2 = load_params(os.path.join(OUT, "v2_params.json"))
    except Exception:
        v2 = None
    strengths: dict = {}
    total = 0
    for day in days:
        lines, picks_json = gen_date(day, ledger, record, state, strengths,
                                     odds_index, ensemble, rolling, v2=v2)
        total += len(picks_json["fixtures"])
        md_path = os.path.join(OUT, f"picks-{day.isoformat()}.md")
        open(md_path, "w").write("\n".join(lines) + "\n")
        _save(os.path.join(OUT, f"picks-{day.isoformat()}.json"), picks_json)
        print(f"{day.isoformat()}: {len(picks_json['fixtures'])} fixtures -> {md_path}")
    _save(os.path.join(OUT, "state.json"), state)
    _save(os.path.join(OUT, "ledger.json"), ledger)
    _save(os.path.join(OUT, "record.json"), record)
    print(f"total fixtures predicted: {total}")
    if days:
        print(open(os.path.join(OUT, f"picks-{days[0].isoformat()}.md")).read())

if __name__ == "__main__":
    main()
