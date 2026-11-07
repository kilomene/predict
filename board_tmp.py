"""One-off full live board: every football match in today's ledger vs our prediction."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from datetime import datetime
from zoneinfo import ZoneInfo
from predict_agent.live_engine import _espn_live_events, _parse_event, football_live, _load
from predict_agent.daily import OUT, FOOTBALL_LEAGUES, football_strengths, football_prediction, norm

today = datetime.now(ZoneInfo("America/Chicago")).date().isoformat()
ledger = _load(os.path.join(OUT, "ledger.json"), [])
entries = [e for e in ledger if e["sport"] == "football" and e["date"] == today]

# index ESPN events by normalized pairing
events = {}
for code, (path, _disp) in FOOTBALL_LEAGUES.items():
    for ev in _espn_live_events(path, today.replace("-", "")):
        fx = _parse_event(ev)
        if fx:
            events[(norm(fx["home"]), norm(fx["away"]))] = (code, fx)

strengths = {}
rows = []
for e in entries:
    got = events.get((norm(e["home"]), norm(e["away"])))
    pick = e["pick"]
    pre = e["probs"][pick]
    if not got:
        rows.append(f"?? {e['home']} vs {e['away']} — no live feed matched (pick {pick} {pre:.0%})")
        continue
    code, fx = got
    label = {"H": e["home"], "D": "Draw", "A": e["away"]}[pick]
    if fx["state"] == "pre":
        rows.append(f"NOT STARTED {e['home']} vs {e['away']} — our pick: {label} ({pre:.0%})")
    elif fx["state"] == "post":
        hs, as_ = fx["home_score"], fx["away_score"]
        actual = "H" if hs > as_ else "D" if hs == as_ else "A"
        ok = actual == pick
        cs = " · CORRECT SCORE HIT" if e.get("top_score", {}).get("score") == f"{hs}-{as_}" else ""
        rows.append(f"FT {e['home']} {hs}-{as_} {e['away']} — pick {label} ({pre:.0%}) -> "
                    f"{'CORRECT' if ok else 'WRONG'}{cs}")
    else:
        hs, as_ = fx["home_score"], fx["away_score"]
        now_outcome = "H" if hs > as_ else "D" if hs == as_ else "A"
        live_txt = ""
        try:
            if code not in strengths:
                strengths[code] = football_strengths(code)
            avgs, xg, elo, _r = strengths[code]
            gotp, _err = football_prediction(fx["home"], fx["away"], avgs, xg, elo)
            if gotp:
                pred, _c, _h, _a = gotp
                live = football_live(pred["lambda_home"], pred["lambda_away"],
                                     fx["minute"] or 1, hs, as_)
                lp = {"H": live["home_win"], "D": live["draw"], "A": live["away_win"]}[pick]
                live_txt = f" · pick now {lp:.0%} (was {pre:.0%}) · likeliest final {live['top_final_scores'][0]['score']}"
        except Exception as ex:
            live_txt = f" · (live prob n/a: {ex})"
        if now_outcome == pick:
            tag = "ON TRACK"
        elif now_outcome == "D":
            tag = "LEVEL - still open"
        else:
            tag = "AGAINST US (for now)"
        rows.append(f"LIVE {fx['minute']}' {e['home']} {hs}-{as_} {e['away']} — pick {label} -> {tag}{live_txt}")

print(f"BOARD for {today}: {len(entries)} football matches in ledger")
for r in rows:
    print(r)
