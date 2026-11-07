# Models

## Football — Poisson / Dixon–Coles + Elo
Goals are rare, discrete events and fit Poisson well. From each team's expected goals
(λ_home, λ_away — built from attack strength × opponent defence strength × league average ×
home advantage) we build the full scoreline matrix P(home=i, away=j), apply the Dixon–Coles
low-score correction (0-0, 1-0, 0-1, 1-1 are not independent in real football), then sum the
matrix into 1X2, Over/Under, BTTS and correct-score markets. The Poisson result is blended
with an Elo-derived win expectancy so form/strength momentum is not ignored.

## Basketball — Elo + pace points model
Team points are approximately Normal. Expected points = pace × offensive rating vs.
opponent defensive rating, plus home-court advantage (~3 points in the NBA). Winner,
spread and totals come from the two Normal distributions and their difference distribution.

## Tennis — surface Elo + serve/return
Tennis Elo must be surface-specific (clay/grass/hard ratings differ materially — the
classic FiveThirtyEight approach). Match probability comes from the Elo expectancy,
adjusted by hold/serve percentages where data is available. Set markets are derived
by simulating sets from game-win probability.

## Volleyball — Elo + set model
Rally scoring makes set outcomes well modelled from a per-rally win probability;
match probability is built up set-by-set (first to 3, sets to 25, fifth to 15).
An Elo layer supplies the team-strength prior when rally data is unavailable.

## Value engine (all sports)
- Implied probability = 1 / decimal odds, normalised across the market to remove overround
- Edge = model probability − implied probability
- Expected value per unit = model_p × odds − 1
- Stake = fractional Kelly (default quarter-Kelly, capped) — full Kelly is too volatile
- Default action threshold: edge ≥ 0.05 and EV > 0, else **no bet** — passing is a decision

## Calibration metrics
Brier score, log loss, accuracy by confidence bucket, and ROI vs. closing odds.
A model that says "70%" must win ~70% of the time in that bucket, or it gets refitted.

## Extra markets (full functionality)

### Correct score
Read directly off the Dixon–Coles scoreline grid. The model returns the full
6×6 grid plus top-5. Honest ceiling: the single most likely score usually
carries only ~10–15% — anyone claiming routine exact-score certainty is lying.

### Goalscorer / assists / player props (`models/player_props.py`)
Player λ = blend of (player xG per 90 × minutes factor) and (team λ × player xG share),
plus penalty-taker uplift. Poisson then gives anytime scorer, 2+ goals, hat-trick,
anytime assist (from xA per 90), goal-or-assist, shots over lines (shots/90),
shots-on-target over lines, fouls over lines, and card probability
(cards/90 adjusted by foul rate). Inputs come from FBref/Understat/Sofascore/
API-Football per-90s and confirmed lineups — a player not starting collapses
his λ via expected minutes, which is why lineup news at T-60m matters so much.

### Match stats (`football.match_stats`)
Shots, shots on target, corners, fouls and cards are modelled as Poisson counts
from each team's rate blended with what the opponent concedes/draws.
Cards and fouls are scaled by the appointed referee's cards/fouls per game —
referee strictness is a first-order input, not a footnote. Offsides included.
Outputs are expected values + over/under probabilities per standard line.

### Real-time layer
Pre-match probabilities are the prior. In-play, the same matrices are re-run
with time elapsed, current score, red cards and live xG/shot momentum
(MoviOdds stats=1 / Sofascore live xG) to produce live win probabilities —
the roadmap item `live.py` clients already feed.
