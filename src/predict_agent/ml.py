"""ML ensemble — the next-level brain for football 1X2.

Trains on rolling, leakage-free features from football-data.co.uk history
(Elo, form, attack/defence, xG form, shots, rest days — every feature is
computed ONLY from matches played before the match being predicted).

Models (averaged): HistGradientBoosting + multinomial Logistic Regression
(scikit-learn; a numpy softmax fallback is used if sklearn is unavailable).
The ML probability is then stacked with the Poisson/Dixon-Coles probability
using a blend weight chosen by validation log-loss — the ensemble must
EARN its place against the statistical model, and the report shows whether
it did.

  python -m predict_agent.ml report   # train on <=2425, validate on 2526
  python -m predict_agent.ml train    # retrain on everything, save model
"""
from __future__ import annotations
import argparse, math, os, pickle, sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from predict_agent.data.history import download
from predict_agent.features.elo import EloTable
from predict_agent.models import football as fb
from predict_agent.models.value import log_loss

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_PATH = os.path.join(ROOT, "out", "ml_model.pkl")
LEAGUES = ["E0", "SP1", "D1", "I1", "F1"]
FEATURES = ["elo_diff", "form_diff", "att_h", "def_h", "att_a", "def_a",
            "xg_att_h", "xg_def_h", "xg_att_a", "xg_def_a",
            "sot_diff", "rest_diff", "lam_h", "lam_a", "pois_h", "pois_d", "pois_a"]

def _f(row, key):
    try:
        return float(row.get(key) or 0)
    except (TypeError, ValueError):
        return 0.0

def _date(row):
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(row.get("Date", ""), fmt)
        except ValueError:
            continue
    return datetime.min

class RollingState:
    """Per-league rolling team state, updated match by match (no leakage)."""
    def __init__(self):
        self.elo = EloTable("football")
        self.hist: dict[str, list[dict]] = defaultdict(list)
        self.last_date: dict[str, datetime] = {}
        self.league_goals = 0.0
        self.league_games = 0

    @property
    def league_avg(self):
        return self.league_goals / self.league_games if self.league_games else 2.6

    def _avg(self, team, key, n=8):
        rows = self.hist[team][-n:]
        if not rows:
            return None
        return sum(r[key] for r in rows) / len(rows)

    def features(self, home: str, away: str, date: datetime):
        la = self.league_avg / 2.0  # per-team average goals
        def avg_or(team, key, default):
            v = self._avg(team, key)
            return v if v is not None else default
        att_h = avg_or(home, "gf", la) / la
        def_h = avg_or(home, "ga", la) / la
        att_a = avg_or(away, "gf", la) / la
        def_a = avg_or(away, "ga", la) / la
        xatt_h = avg_or(home, "xgf", la) / la
        xdef_h = avg_or(home, "xga", la) / la
        xatt_a = avg_or(away, "xgf", la) / la
        xdef_a = avg_or(away, "xga", la) / la
        form_h = avg_or(home, "pts", 1.2)
        form_a = avg_or(away, "pts", 1.2)
        sot_h = avg_or(home, "sot", 4.5)
        sot_a = avg_or(away, "sot", 4.5)
        lam_h = att_h * def_a * la * 1.15
        lam_a = att_a * def_h * la / 1.15
        mk = fb.predict(round(lam_h, 3), round(lam_a, 3),
                        elo_home_prob=self.elo.win_prob(home, away))["markets"]
        rest_h = (date - self.last_date[home]).days if home in self.last_date else 7
        rest_a = (date - self.last_date[away]).days if away in self.last_date else 7
        feats = {
            "elo_diff": self.elo.get(home) - self.elo.get(away),
            "form_diff": form_h - form_a,
            "att_h": att_h, "def_h": def_h, "att_a": att_a, "def_a": def_a,
            "xg_att_h": xatt_h, "xg_def_h": xdef_h, "xg_att_a": xatt_a, "xg_def_a": xdef_a,
            "sot_diff": sot_h - sot_a,
            "rest_diff": max(-14, min(14, rest_h - rest_a)),
            "lam_h": lam_h, "lam_a": lam_a,
            "pois_h": mk["home_win"], "pois_d": mk["draw"], "pois_a": mk["away_win"],
        }
        return [feats[k] for k in FEATURES], (mk["home_win"], mk["draw"], mk["away_win"])

    def update(self, row):
        h, a = row["HomeTeam"], row["AwayTeam"]
        hg, ag = int(_f(row, "FTHG")), int(_f(row, "FTAG"))
        res = row.get("FTR") or ("H" if hg > ag else "D" if hg == ag else "A")
        self.hist[h].append({"gf": hg, "ga": ag, "xgf": _f(row, "HxG") or hg,
                             "xga": _f(row, "AxG") or ag, "sot": _f(row, "HST"),
                             "pts": 3 if res == "H" else 1 if res == "D" else 0})
        self.hist[a].append({"gf": ag, "ga": hg, "xgf": _f(row, "AxG") or ag,
                             "xga": _f(row, "HxG") or hg, "sot": _f(row, "AST"),
                             "pts": 3 if res == "A" else 1 if res == "D" else 0})
        self.last_date[h] = self.last_date[a] = _date(row)
        self.league_goals += hg + ag
        self.league_games += 1
        self.elo.update(h, a, home_won=res == "H", draw=res == "D")

def build_dataset(seasons: list[str]):
    X, Y, P = [], [], []  # features, label idx (0 H, 1 D, 2 A), poisson probs
    for season in seasons:
        for league in LEAGUES:
            try:
                rows = download(league, season)
            except Exception:
                continue
            rows = sorted(rows, key=_date)
            state = RollingState()
            for row in rows:
                if len(state.hist[row["HomeTeam"]]) >= 3 and len(state.hist[row["AwayTeam"]]) >= 3:
                    feats, pois = state.features(row["HomeTeam"], row["AwayTeam"], _date(row))
                    res = row.get("FTR") or ("H" if _f(row, "FTHG") > _f(row, "FTAG")
                                             else "D" if _f(row, "FTHG") == _f(row, "FTAG") else "A")
                    X.append(feats)
                    Y.append({"H": 0, "D": 1, "A": 2}[res])
                    P.append(pois)
                state.update(row)
    return X, Y, P

def _train_models(X, Y):
    import numpy as np
    X, Y = np.array(X), np.array(Y)
    models = []
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier
        gbm = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06,
                                             max_depth=3, random_state=7)
        gbm.fit(X, Y)
        models.append(gbm)
    except Exception:
        pass
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import make_pipeline
        lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
        lr.fit(X, Y)
        models.append(lr)
    except Exception:
        pass
    if not models:
        models = [_NumpySoftmax().fit(X, Y)]
    return models

class _NumpySoftmax:
    """Fallback multinomial logistic regression in pure numpy."""
    def fit(self, X, Y):
        import numpy as np
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-9
        Xs = (X - self.mu) / self.sd
        Xs = np.c_[Xs, np.ones(len(Xs))]
        W = np.zeros((Xs.shape[1], 3))
        Yh = np.eye(3)[Y]
        for _ in range(300):
            z = Xs @ W
            z -= z.max(1, keepdims=True)
            p = np.exp(z); p /= p.sum(1, keepdims=True)
            W -= 0.05 * (Xs.T @ (p - Yh) / len(Xs) + 0.001 * W)
        self.W = W
        return self
    def predict_proba(self, X):
        import numpy as np
        Xs = (np.array(X) - self.mu) / self.sd
        Xs = np.c_[Xs, np.ones(len(Xs))]
        z = Xs @ self.W
        z -= z.max(1, keepdims=True)
        p = np.exp(z)
        return p / p.sum(1, keepdims=True)

def ml_probs(models, X):
    import numpy as np
    ps = [m.predict_proba(np.array(X)) for m in models]
    return sum(ps) / len(ps)

def _metrics(name, probs, Y):
    import numpy as np
    probs = np.array(probs); Y = np.array(Y)
    acc = (probs.argmax(1) == Y).mean()
    ll = -np.log(np.clip(probs[np.arange(len(Y)), Y], 1e-9, 1.0)).mean()
    print(f"{name:<22} accuracy {acc:.1%}   log-loss {ll:.4f}")
    return acc, ll

def report():
    import numpy as np
    print("Building datasets (rolling features, no leakage)...")
    Xtr, Ytr, _ = build_dataset(["2122", "2223", "2324", "2425"])
    Xva, Yva, Pva = build_dataset(["2526"])
    print(f"train {len(Xtr)} matches · validation {len(Xva)} matches (2025/26, all big-5)")
    models = _train_models(Xtr, Ytr)
    Pm = ml_probs(models, Xva)
    _metrics("Poisson/Dixon-Coles", Pva, Yva)
    _metrics("ML (GBM + LogReg)", Pm, Yva)
    best = (None, 9e9)
    for w in [i / 20 for i in range(21)]:  # weight on ML
        blend = [(1 - w) * np.array(p) + w * m for p, m in zip(Pva, Pm)]
        import numpy as np
        Y = np.array(Yva); B = np.array(blend)
        ll = -np.log(np.clip(B[np.arange(len(Y)), Y], 1e-9, 1.0)).mean()
        if ll < best[1]:
            best = (w, ll)
    w = best[0]
    blend = [(1 - w) * np.array(p) + w * m for p, m in zip(Pva, Pm)]
    _metrics(f"ENSEMBLE (ML w={w:.2f})", blend, Yva)
    print(f"\nChosen ML blend weight: {w:.2f} (by validation log-loss)")
    return w

def train_and_save():
    w = report()
    print("\nRetraining on all seasons incl. 2025/26 + 2026/27 so far...")
    X, Y, _ = build_dataset(["2122", "2223", "2324", "2425", "2526", "2627"])
    models = _train_models(X, Y)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"models": models, "ml_weight": w, "features": FEATURES}, f)
    print(f"saved {MODEL_PATH} ({len(X)} training matches)")

def load_ensemble():
    try:
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["report", "train"])
    args = ap.parse_args()
    if args.cmd == "report":
        report()
    else:
        train_and_save()

if __name__ == "__main__":
    main()
