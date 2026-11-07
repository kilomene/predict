# Predict — Multi-Sport Prediction Agent

> A data-driven prediction agent for **football (soccer), basketball, tennis and volleyball**.
> Not a tipster. A probability machine: it ingests real fixtures, results, form and market odds,
> runs statistical models, and only flags a bet when the model finds **value** against the bookmaker.

**Honest starting point:** a language model guessing from memory is barely better than a coin
flip on match winners. Bookmakers are very good. What moves the needle is data + maths +
backtesting + discipline — which is exactly what this repo builds.

Published accuracy in the literature for football 1X2 (win/draw/win):

| Model | Typical accuracy |
|---|---|
| Guessing / favourites only | ~45–50% |
| Poisson only | ~53.2% |
| Poisson + Elo | ~55.7% |
| Poisson + Elo + xG + ML ensemble | ~58–60% (best published range) |

No model guarantees profit. Profit comes from **calibrated probabilities + value vs. odds +
bankroll discipline**, measured over hundreds of bets — never from one "sure" pick.

---

## What it does

1. **Ingests** fixtures, results and odds from free, legal sources (see `docs/SOURCES.md`)
2. **Builds features**: Elo ratings, attack/defence strength, recent form, home advantage, rest, head-to-head
3. **Predicts** with a sport-specific model:
   - Football: Dixon–Coles / Poisson goal matrix + Elo blend → 1X2, Over/Under 2.5, BTTS, correct-score grid
   - Basketball: Elo + pace-adjusted points model (Normal) → winner, spread, totals
   - Tennis: surface-specific Elo + serve/return ratings → match winner, set betting
   - Volleyball: Elo + set/rally model → match winner, set handicap, totals
4. **Finds value**: compares model probability to bookmaker implied probability,
   computes edge and fractional Kelly stake
5. **Backtests** itself against historical closing odds (football-data.co.uk) and reports
   Brier score, log loss, accuracy and ROI — so claims are measured, not vibes

**Full markets, not just winners:** correct-score grid, anytime/first scorer probabilities,
2+ goals, assists, goal-or-assist, player shots & shots-on-target, team shots, corners,
fouls, cards (referee-adjusted), offsides, clean sheets, BTTS, totals — plus basketball
player points/rebounds/assists, tennis aces, and volleyball kills/blocks/aces.
See `docs/MODELS.md` and `docs/BACKTEST_RESULTS.md` for the measured record:
**57.9% 1X2 accuracy and 11.6% correct-score top-1 on a real 190-match Premier League
backtest — and a losing ROI against Bet365 closing odds, published on purpose.**

## Live scores & bookmakers — linked, not scraped against ToS

This repo **links** to the places you named and uses their official / permitted data routes
where they exist. Sites with no public API get deep links + odds-comparison mapping, not
ToS-breaking bots:

**Live scores:** [LiveScore](https://www.livescore.com) · [Flashscore](https://www.flashscore.com) ·
[Sofascore](https://www.sofascore.com) · [FotMob](https://www.fotmob.com) ·
[BBC Sport](https://www.bbc.com/sport) · [ESPN](https://www.espn.com)

**Bookmakers / odds:** [SportyBet](https://www.sportybet.com) · [Bet9ja](https://www.bet9ja.com) ·
[1xBet](https://1xbet.com) · [Football.com](https://www.football.com) ·
[bet365](https://www.bet365.com) · [Pinnacle](https://www.pinnacle.com) (sharp benchmark odds)

Full catalogue with API status, free tiers and usage notes: [`config/sources.yaml`](config/sources.yaml)
and [`docs/SOURCES.md`](docs/SOURCES.md).

## Free data stack ($0)

| Source | Covers | Free tier |
|---|---|---|
| football-data.co.uk | Football history + closing odds (training/backtest gold) | Free CSV, no key |
| football-data.org | Football fixtures/results, 12 top competitions | 10 calls/min, no live on free |
| API-Sports (API-Football / Basketball / Volleyball) | All 4 sports, fixtures, stats, odds, predictions | 100 req/day per API |
| The Odds API | Football, basketball, tennis odds from 40+ bookmakers | 500 credits/month |
| MoviOdds | bet365 pre-match + in-play odds, 24 sports incl. volleyball | Free, no key (beta) |
| ESPN (unofficial) | Live scores, basketball/tennis schedules | Free, no key |

Keys go in `.env` (copy `.env.example`). **The agent runs with no keys at all** in demo /
historical mode using football-data.co.uk CSVs.

## Quick start

```bash
git clone https://github.com/kilomene/predict.git
cd predict
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env   # optional — add any free keys you have
# (or skip the venv and prefix commands with PYTHONPATH=src)

# Predict a football match from team strengths (no key needed)
python -m predict_agent.predict football --home "Arsenal" --away "Chelsea" \
  --home-xg 1.9 --away-xg 1.1 --odds-home 2.10 --odds-draw 3.40 --odds-away 3.20

# Download real historical data + backtest the football model
python -m predict_agent.backtest --league E0 --season 2324

# Today's fixtures + live-score links for all 4 sports
python -m predict_agent.today
```

## Project layout

```
config/sources.yaml        Every source, bookmaker and live-score site, catalogued
src/predict_agent/
  data/                    One client per source (football-data.org, API-Sports, Odds API, MoviOdds, history CSV)
  features/elo.py          Elo engine (per sport, surface-aware for tennis)
  features/form.py         Form, attack/defence strength, home advantage
  models/football.py       Poisson / Dixon-Coles goal matrix
  models/basketball.py     Pace + Normal points model
  models/tennis.py         Surface Elo + serve/return model
  models/volleyball.py     Elo + set model
  models/value.py          Implied probability, edge, Kelly, expected value
  predict.py               CLI: predict a single match in any sport
  today.py                 CLI: today's fixtures + live links
  backtest.py              CLI: backtest vs historical closing odds
docs/                      ARCHITECTURE, SOURCES, MODELS, RESPONSIBLE
tests/                     Model + value-engine tests
```

## Responsible use

Betting involves risk and can be addictive. This software produces **probabilities, not
certainties**, and is for research/education. Never bet money you cannot afford to lose,
never chase losses, and check the laws in your country. See `docs/RESPONSIBLE.md`.
Bookmaker availability and legality vary by country — SportyBet/Bet9ja serve Nigeria,
1xBet's licence varies by jurisdiction; verify locally before using any of them.

## License

MIT
