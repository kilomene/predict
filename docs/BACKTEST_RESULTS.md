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

## ML ensemble validation (2025/26, all big-5 leagues, 1,607 matches)

Rolling leakage-free features; trained on 2021/22–2024/25 (6,570 matches):

| Model | 1X2 accuracy | Log-loss |
|---|---|---|
| Poisson/Dixon-Coles (rolling) | 48.1% | 1.0505 |
| ML (GBM + LogReg) | 50.1% | 1.0177 |
| Ensemble (stacked) | 50.2% | 1.0169 |

Note this population (all five leagues, rolling early-season states) is
harder than the Premier League second-half test above (57.9%). The ML
blend weight chosen by validation log-loss was 0.85; the daily runner caps
it at 0.50 against its stronger xG-aggregate model, conservatively.

## v2.0 core — walk-forward (train 2023/24+2024/25, test 2025/26, big-5, 1,607 matches)

Reproduce: `PYTHONPATH=src python -m predict_agent.fit_v2`
Pipeline compared on identical test matches (rolling Poisson core):

| Stage | Accuracy | Log-loss | ECE | Draw pred vs actual |
|---|---|---|---|---|
| v0.3-style (rho −0.08 fixed, raw) | 47.9% | 1.1109 | 0.0946 | 24.5% vs 25.9% |
| + per-league fitted rho | 48.2% | 1.1094 | 0.0992 | 23.2% vs 25.9% |
| + vector-scaling calibration | **49.3%** | **1.0407** | **0.0264** | **25.7% vs 25.9%** |

Findings, honestly:
- Fitted rho came out ≈ 0.00 (E0, I1, F1) and −0.02 (SP1, D1): the textbook
  −0.08 is wrong for modern big-5 rolling lambdas, and rho alone does NOT fix
  draw calibration (gap widened to −2.7 pts before calibration).
- Calibration is the big lever: log-loss −0.069, ECE 0.095 → 0.026 (target
  ≤ 0.05 met), draw gap −0.2 pts (target ±1.5 met).
- The gate (thresholds swept on train, judged on test): at single_min 0.53,
  singles hit 63.2% at 23% coverage; double-chance 77.6% at its band.
  The pre-registered target "≥62% singles at ≥30% coverage" was NOT met by
  the core-only pipeline (59.9% at 33% coverage) — recorded as a miss, to be
  re-tested after phase-2 sharpening (pi-ratings, xG-EWMA, calibrated ML stack).
- This harness's baseline is the rolling Poisson CORE (no Elo blend / ML),
  weaker than the full v0.3 stack's 50.2% — comparisons above are core-vs-core.

## v2.0 phase 2 — pi-ratings and xG-EWMA (walk-forward)

Pi-ratings head vs result-only Elo head (same matches, league totals rolling):

| Season | Pi head acc / log-loss | Elo head acc / log-loss |
|---|---|---|
| 2024/25 (n=1,652) | 50.3% / 1.0189 | 48.9% / 1.0301 |
| 2025/26 (n=1,652) | 49.8% / 1.0326 | 47.9% / 1.0341 |

xG-EWMA lambdas vs goals-rolling lambdas (2025/26, warmed on 2024/25, n=1,714):

| Lambda source | Accuracy | Log-loss |
|---|---|---|
| goals-rolling (current core) | 48.4% | 1.0865 |
| xG-EWMA alone | 47.8% | 1.0546 |
| 50/50 blend | **48.7%** | 1.0559 |

xG improves probability quality materially (log-loss −0.032 alone) but not
argmax by itself; the blend improves both. Pi-ratings and the xG blend are
built and measured; folding them into the ML retrain is the next step.

Basketball: the possessions model (pace/ORtg/DRtg from ESPN team stats +
standings) is live-verified against the real API (30 teams, sensible
ratings, matchup totals vary — e.g. Hawks–Celtics 225.8 vs the old dummy's
flat 220). Backtest target ≥64% winner accuracy grades itself from the
daily ledger as results settle.
