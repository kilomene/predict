# Sources

Catalogue lives in `config/sources.yaml`. Summary:

## Live scores (linked)
LiveScore, Flashscore, Sofascore, FotMob, BBC Sport, ESPN — the agent links every
fixture it predicts to its live page on these sites so you can follow it in-play.
ESPN additionally exposes free unofficial JSON used for live basketball/tennis scores.

## Data & odds APIs (used programmatically, free tiers)
- **football-data.co.uk** — historical football results + Bet365/Pinnacle closing odds as CSV.
  This is the training and backtesting backbone: decades of matches with the market's own prices.
- **football-data.org** — fixtures/results/standings for 12 top competitions, 10 calls/min free.
- **API-Sports** — API-Football, API-Basketball, API-Volleyball under one account,
  100 requests/day each free; fixtures, stats, odds and their own predictions endpoint.
- **The Odds API** — odds from 40+ bookmakers for football, basketball and tennis; 500 free credits/month.
- **MoviOdds** — bet365 odds for 24 sports including volleyball, free with no key (beta),
  REST + WebSocket, with live stats (xG, possession, aces, breaks).
- **Sportmonks / TheSportsDB** — optional extras, free tiers available.

## Bookmakers (linked for betting / price comparison)
SportyBet, Bet9ja ("bet naija"), 1xBet, Football.com, bet365, Pinnacle.
None of these offers a public odds API to normal users, so the honest engineering choice is:
deep links + a best-price comparison table filled from The Odds API / MoviOdds where the
same market is covered, and manual entry for SportyBet/Bet9ja/1xBet-only prices.
Any claim of "scraping all bookmakers live" without an API would be brittle and against
their terms — this repo does not pretend otherwise.
