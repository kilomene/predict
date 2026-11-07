# Predict v2.0 — Design

*Commissioned 2026-11-07 after the owner graded v0.3's live card and found it
wanting. Research basis: `~/workspace/research_notes/predict-v2-research-20261107/report.md`
(63 sources). This document is the contract the build is measured against.*

## Why v0.3 was not good enough (measured, not vibes)

Nov 7 live card: 8/15 picks correct. Five of the seven misses were draws on
which the system forced a winner pick. Structural causes found in the code:

1. **Forced argmax pick.** The headline pick is always the single most likely
   outcome, even at 36%. Draws are almost never argmax, so the system
   structurally predicts ~0 draws while ~25% of matches are draws.
2. **No calibration layer.** Probabilities were never fitted against reality.
   An uncalibrated "60%" that is really 53% poisons every downstream decision
   (value flags, Kelly stakes, confidence labels).
3. **Hard-coded Dixon–Coles rho = −0.08 for every league**, and season-flat
   lambdas with no time decay in the daily path.
4. **Basketball was a dummy**: `110 ± Elo/25` for every team — every game read
   "Home 54%, total 220". Not a model.
5. **No error-learning loop** beyond Elo/record bookkeeping: patterns of error
   (like draw blindness) were never measured, so they were never fixed.

## Architecture — the honesty release (v2.0 core)

Pipeline per football fixture:

```
rolling/season data → λ (attack × defence × league avg × home adv)
  → Dixon–Coles matrix with PER-LEAGUE FITTED rho
  → 1X2 probabilities → ML ensemble blend (existing, capped)
  → CALIBRATION: per-league vector scaling (temperature + class bias;
    the draw-bias term is the draw correction) fitted on past seasons
  → GATE: decides what kind of call the evidence supports
       SINGLE         top calibrated prob ≥ 0.60
       DOUBLE CHANCE  top two outcomes sum ≥ 0.78 and top ≥ 0.42
       NO PICK        otherwise — "too close to call" is a result, not a failure
  → sheet + ledger (raw argmax pick still recorded and graded separately,
    so the gate can never hide the model's true hit rate)
```

### Modules

- `calibration.py` — vector scaling / temperature / Platt fitting, ECE and
  per-class calibration reporting, JSON params (`out/v2_params.json`).
- `gating.py` — the call policy above + grading for each call type.
- `fit_v2.py` — walk-forward fitting: trains rho + calibration on
  2023/24 + 2024/25 (big-5), tests untouched on 2025/26, prints the full
  v0.3-vs-v2.0 comparison and writes `out/v2_params.json`.
- `football.predict(..., rho=)` — rho is now a parameter, per-league.

### Phase 2 (after core proves itself)

- Pi-ratings as ML features (research: RPS 0.1991 vs Elo 0.2042).
- xG-EWMA ratings from Understat (FBref lost xG in Jan 2026) blended with
  the goals-based Dixon–Coles — the largest single accuracy lever found.
- Basketball possessions model: `(Pace_h × Pace_a / LgPace) ×
  (ORtg × OppDRtg / LgAvg)` from free Basketball-Reference/SportsDataverse
  data into the existing Normal spread/total machinery.
- Live engine v2: fitted minute-intensity curve + score-state effects
  instead of the linear clock and fixed heuristics.

## Pre-registered targets (walk-forward, 2025/26 big-5 test split)

| Metric | v0.3 baseline | v2.0 target |
|---|---|---|
| Pure-model 1X2 accuracy | 48.1–50.2% | ≥ 52% |
| Log-loss | 1.0169–1.0505 | ≤ 0.995 |
| ECE (per league) | 0.08–0.12 (est.) | ≤ 0.05 |
| Draw-rate calibration | unmeasured | within ±1.5 pts per league |
| Gated singles hit rate | n/a (forced picks) | ≥ 62% at ≥ 30% coverage |
| Basketball winner accuracy | ~54% (dummy) | ≥ 64%, non-degenerate totals |

Any component that does not improve its target metric on the untouched test
split is dropped or shrunk and the null result is recorded in
`docs/BACKTEST_RESULTS.md`. No component ships on promise.

## What v2.0 deliberately does NOT do

- No market-consensus blending into the model's own probabilities (two
  independent studies found the optimal weight on the model vs sharp closing
  prices was ~0 — blending would be dressing up the bookmaker's numbers as
  ours). Market prices stay where they belong: in the value engine.
- No paid data, ever (owner's $0 rule). Understat, football-data.co.uk,
  ESPN, FPL, Basketball-Reference — all free routes.
- No guaranteed winners. The gate's NO PICK exists precisely so the system
  stops pretending on matches it cannot separate.
