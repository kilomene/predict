"""Fit + prove v2.0 (walk-forward, leakage-free).

  python -m predict_agent.fit_v2

Trains on 2023/24 + 2024/25 (big-5), tests on the untouched 2025/26 season:

  1. Per-league Dixon-Coles rho: grid-searched on TRAIN lambdas by log-loss
     of the pure scoreline matrix (rho belongs to the Poisson core).
  2. Calibration: per-league vector scaling (temperature + class bias)
     fitted on TRAIN probabilities from the fitted-rho matrix.
  3. The gate: applied to calibrated TEST probabilities; singles and
     double-chance graded separately, coverage always reported.

Prints the v0.3-style baseline (fixed rho -0.08, uncalibrated, forced argmax)
against the full v2.0 pipeline on the same test matches, and writes
out/v2_params.json for the daily runner.
"""
from __future__ import annotations
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from predict_agent.data.history import download
from predict_agent.ml import RollingState, _date
from predict_agent.models.football import score_matrix, markets_from_matrix
from predict_agent import calibration as cal
from predict_agent import gating

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LEAGUES = ["E0", "SP1", "D1", "I1", "F1"]
NAMES = {"E0": "Premier League", "SP1": "La Liga", "D1": "Bundesliga",
         "I1": "Serie A", "F1": "Ligue 1"}
TRAIN_SEASONS = ["2324", "2425"]
TEST_SEASONS = ["2526"]
RHO_GRID = [-0.18, -0.15, -0.12, -0.10, -0.08, -0.06, -0.04, -0.02, 0.0]
IDX = {"H": 0, "D": 1, "A": 2}

def collect(seasons):
    """Walk-forward rows: (league, lam_h, lam_a, outcome_idx). Lambdas come
    from RollingState (rolling last-8 attack/defence) — the same machinery
    the ML validation used, so numbers are comparable to the v0.3 report."""
    rows = []
    for season in seasons:
        for league in LEAGUES:
            try:
                matches = sorted(download(league, season), key=_date)
            except Exception:
                continue
            state = RollingState()
            for r in matches:
                h, a = r["HomeTeam"], r["AwayTeam"]
                if len(state.hist[h]) >= 3 and len(state.hist[a]) >= 3:
                    feats, _pois = state.features(h, a, _date(r))
                    lam_h, lam_a = feats[12], feats[13]  # FEATURES order: lam_h, lam_a at 12,13
                    res = r.get("FTR") or ("H" if float(r["FTHG"]) > float(r["FTAG"])
                                           else "D" if r["FTHG"] == r["FTAG"] else "A")
                    rows.append((league, lam_h, lam_a, IDX[res]))
                state.update(r)
    return rows

def probs_at_rho(rows, rho_by_league):
    out = []
    for league, lh, la, _y in rows:
        mk = markets_from_matrix(score_matrix(lh, la, rho=rho_by_league[league]))
        out.append((mk["home_win"], mk["draw"], mk["away_win"]))
    return out

def report(tag, probs, outcomes):
    print(f"{tag:<34} acc {cal.accuracy(probs, outcomes):.1%}   "
          f"log-loss {cal.log_loss(probs, outcomes):.4f}   "
          f"ECE {cal.ece(probs, outcomes):.4f}")
    cc = cal.class_calibration(probs, outcomes)
    print(f"{'':<34} draw predicted {cc['D']['predicted']:.1%} vs actual "
          f"{cc['D']['actual']:.1%} (gap {cc['D']['gap']:+.1%})")
    return {"acc": round(cal.accuracy(probs, outcomes), 4),
            "log_loss": round(cal.log_loss(probs, outcomes), 4),
            "ece": round(cal.ece(probs, outcomes), 4), "draw": cc["D"]}

def main():
    print("collecting walk-forward rows...")
    train = collect(TRAIN_SEASONS)
    test = collect(TEST_SEASONS)
    print(f"train {len(train)} matches · test {len(test)} matches\n")

    # ---- 1. per-league rho on train ----
    rho = {}
    for league in LEAGUES:
        rows_l = [r for r in train if r[0] == league]
        ys = [r[3] for r in rows_l]
        best, best_ll = -0.08, None
        for cand in RHO_GRID:
            ll = cal.log_loss(probs_at_rho(rows_l, {league: cand}), ys)
            if best_ll is None or ll < best_ll:
                best, best_ll = cand, ll
        rho[league] = best
        print(f"rho {NAMES[league]:<16} fitted {best:+.2f} (train log-loss {best_ll:.4f})")
    print()

    # ---- 2. baselines on test ----
    y_test = [r[3] for r in test]
    base_probs = probs_at_rho(test, {l: -0.08 for l in LEAGUES})
    print("== TEST 2025/26 (untouched) ==")
    m_base = report("v0.3-style: rho -0.08, raw, argmax", base_probs, y_test)
    rho_probs = probs_at_rho(test, rho)
    m_rho = report("+ fitted per-league rho", rho_probs, y_test)

    # ---- 3. calibration fitted on train, applied to test ----
    train_probs = probs_at_rho(train, rho)
    y_train = [r[3] for r in train]
    calib = {}
    for league in LEAGUES:
        idxs = [i for i, r in enumerate(train) if r[0] == league]
        calib[league] = cal.fit_vector_scaling([train_probs[i] for i in idxs],
                                               [y_train[i] for i in idxs])
    test_cal = [cal.apply_vector_scaling(p, calib[r[0]])
                for p, r in zip(rho_probs, test)]
    m_cal = report("+ calibration (vector scaling)", test_cal, y_test)

    # ---- 4. the gate on calibrated test probs ----
    calls = [gating.decide(p) for p in test_cal]
    outcomes = ["HDA"[y] for y in y_test]
    g = gating.summarise(list(zip(calls, outcomes)))
    print(f"\n== THE GATE on calibrated test probs ==")
    print(f"singles:       {g['singles']} calls ({g['singles_coverage']:.0%} coverage) "
          f"hit rate {g['singles_hit_rate']}")
    print(f"double chance: {g['double_chance']} calls ({g['dc_coverage']:.0%} coverage) "
          f"hit rate {g['dc_hit_rate']}")
    print(f"no pick:       {g['no_pick']} ({g['no_pick_rate']:.0%})")

    params = {"version": "2.0.0", "fitted_on": f"train {TRAIN_SEASONS} big-5",
              "rho": rho, "calibration": calib, "gate": gating.DEFAULTS,
              "test_metrics": {"baseline": m_base, "fitted_rho": m_rho,
                               "calibrated": m_cal, "gate": g}}
    out_path = os.path.join(ROOT, "out", "v2_params.json")
    cal.save_params(params, out_path)
    print(f"\nwrote {out_path}")

if __name__ == "__main__":
    main()
