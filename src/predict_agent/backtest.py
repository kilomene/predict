"""Backtest the football model against real historical closing odds.

Trains team averages + Elo on the FIRST half of a season, predicts the
second half, and reports accuracy, Brier, log loss — plus ROI of the
value rule (edge >= 5%) at Bet365 closing odds, flat stakes.
This is the honesty engine: if it doesn't beat closing odds in backtest,
we say so and do not recommend betting the model live.

  python -m predict_agent.backtest --league E0 --season 2324
"""
from __future__ import annotations
import argparse, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from predict_agent.data.history import download, team_averages
from predict_agent.features.elo import EloTable
from predict_agent.models import football
from predict_agent.models.value import brier_score, log_loss, assess

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", default="E0")
    ap.add_argument("--season", default="2324")
    args = ap.parse_args()

    rows = download(args.league, args.season)
    half = len(rows) // 2
    train, test = rows[:half], rows[half:]
    avgs = team_averages(train)
    league_avg = sum(v["goals_for"] for v in avgs.values()) / max(1, len(avgs)) or 1.4

    elo = EloTable("football")
    for r in train:
        elo.update(r["HomeTeam"], r["AwayTeam"],
                   home_won=r["FTR"] == "H", draw=r["FTR"] == "D")

    probs, outcomes, correct = [], [], 0
    bets = wins = 0
    pnl = 0.0
    correct_scores_hit = 0
    for r in test:
        h, a = r["HomeTeam"], r["AwayTeam"]
        if h not in avgs or a not in avgs:
            continue
        lam_h = (avgs[h]["goals_for"] / league_avg) * (avgs[a]["goals_against"] / league_avg) * league_avg * 1.15
        lam_a = (avgs[a]["goals_for"] / league_avg) * (avgs[h]["goals_against"] / league_avg) * league_avg / 1.15
        mk = football.predict(lam_h, lam_a, elo_home_prob=elo.win_prob(h, a))["markets"]
        pred = max((mk["home_win"], "H"), (mk["draw"], "D"), (mk["away_win"], "A"))[1]
        if pred == r["FTR"]:
            correct += 1
        if mk["top_correct_scores"] and mk["top_correct_scores"][0]["score"] == f"{r['FTHG']}-{r['FTAG']}":
            correct_scores_hit += 1
        for key, code, odds_key in (("home_win", "H", "B365H"), ("draw", "D", "B365D"), ("away_win", "A", "B365A")):
            probs.append(mk[key])
            outcomes.append(1 if r["FTR"] == code else 0)
            try:
                odds = float(r.get(odds_key) or 0)
            except ValueError:
                odds = 0
            if odds > 1:
                v = assess(mk[key], odds)
                if v["verdict"] == "VALUE":
                    bets += 1
                    if r["FTR"] == code:
                        wins += 1
                        pnl += odds - 1
                    else:
                        pnl -= 1
        elo.update(h, a, home_won=r["FTR"] == "H", draw=r["FTR"] == "D")

    n = max(1, sum(1 for r in test if r["HomeTeam"] in avgs and r["AwayTeam"] in avgs))
    print(f"League {args.league} season {args.season}: {len(rows)} matches, tested on {n}")
    print(f"1X2 accuracy:        {correct / n:.1%}")
    print(f"Correct-score top-1: {correct_scores_hit / n:.1%}  (random/top-pick baseline is ~8-12% — low by nature)")
    print(f"Brier score:         {brier_score(probs, outcomes):.4f}  (lower is better; 0.667 = coin flip on 3-way split)")
    print(f"Log loss:            {log_loss(probs, outcomes):.4f}")
    print(f"Value bets fired:    {bets}  won: {wins}")
    print(f"Flat-stake P&L:      {pnl:+.1f} units  ROI: {(pnl / bets * 100 if bets else 0):+.1f}%")
    print("Note: beating Bet365 CLOSING odds long-term is the hardest test in the game. "
          "A negative ROI here means: use the model for probabilities, not for betting that book at close.")

if __name__ == "__main__":
    main()
