# Architecture

```
 SOURCES                    FEATURES                 MODELS                  OUTPUT
 ───────                    ────────                 ──────                  ──────
 football-data.co.uk ──┐
 football-data.org   ──┤    Elo (per sport)      ┌─ Football: Poisson/DC ─┐
 API-Sports          ──┼──► Form (weighted)      ├─ Basketball: pace/Normal┤─► Probabilities
 The Odds API        ──┤    Attack / Defence     ├─ Tennis: surface Elo   ├─► Value vs odds
 MoviOdds (bet365)   ──┤    Home advantage       └─ Volleyball: set model ┘─► Edge + Kelly
 ESPN live           ──┘    Rest / H2H                                        │
 LiveScore etc. (links)                                                       ▼
                                                              Backtest loop (Brier / log loss / ROI)
                                                              feeds calibration back into the models
```

## Principles

1. **Probabilities, not picks.** Every output is a calibrated probability distribution.
2. **The market is the opponent.** A prediction is only actionable when the model's
   probability beats the bookmaker's implied probability by a margin that survives
   the bookmaker's overround. See `models/value.py`.
3. **Backtest before you believe.** No model ships a claim it hasn't measured against
   historical closing odds. Closing odds (especially Pinnacle) are the hardest benchmark.
4. **$0 by default.** Every source above has a free tier. The agent degrades gracefully:
   with zero keys it trains/backtests on football-data.co.uk history and predicts from
   user-supplied team strengths; keys unlock live fixtures and odds.
5. **Link, don't violate.** Bookmakers and live-score sites without public APIs are
   linked and used for manual odds comparison. No ToS-breaking scraping bots.

## Daily loop (intended running agent)

1. Morning: pull today's fixtures (API-Sports / football-data.org / ESPN)
2. Pull odds (The Odds API + MoviOdds), map best price across linked bookmakers
3. Run each sport's model, compute value flags (edge ≥ 5% by default)
4. Publish a picks sheet: match, market, model %, implied %, edge, fractional-Kelly stake
5. After full-time: settle picks, log Brier/log-loss, update Elo + form tables
6. Weekly: recalibration report — if calibration drifts, refit before trusting new picks
