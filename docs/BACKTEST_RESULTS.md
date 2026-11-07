# Backtest results — measured, not promised

Run it yourself:
```bash
PYTHONPATH=src python3 -m predict_agent.backtest --league E0 --season 2324
```

## Premier League 2023/24 (E0), second half — 190 matches
Trained on the first 190 matches of the season (team averages + Elo),
predicted the remaining 190. Data: football-data.co.uk (results + closing odds).

| Metric | Result | What it means |
|---|---|---|
| 1X2 accuracy | **57.9%** | In the best published range (Poisson+Elo ≈ 55.7%, ensembles ≈ 58–60%) |
| Correct score, top-1 pick | **11.6%** | Normal. The single likeliest scoreline is still unlikely — exact-score betting is a lottery with better maths |
| Brier score | 0.1813 | Well calibrated vs 0.667 coin-flip reference |
| Log loss | 0.5419 | — |
| Value rule (edge ≥ 5%) vs Bet365 **closing** odds | 95 bets, **−25.3% ROI** | **Losing.** Closing odds are the market at its smartest |

## The honest conclusion
This model is a strong **probability engine** and a weak **closing-line betting system** —
which is exactly what the literature predicts. Beating closing odds at Bet365/Pinnacle
long-term is the hardest test in sports betting.

Where an edge can realistically exist:
1. **Earlier prices** — before the market sharpens (opening odds, not closing)
2. **Softer bookmakers** — regional books (SportyBet, Bet9ja, 1xBet, Football.com) often
   price slower than Pinnacle/Bet365; the same model probability can be value there
   and no-value at the sharp book. This is why the repo links them for price comparison.
3. **Props and stats markets** — shots, fouls, cards and player markets are priced
   less efficiently than 1X2, especially with referee and lineup information.

Anyone — human or AI — who promises you routine correct scores, guaranteed
scorers, or "very very accurate everything" is selling you something.
What a serious system gives you: calibrated probabilities, the full distribution
for every market, and a measured record you can audit. That is what this repo does.
