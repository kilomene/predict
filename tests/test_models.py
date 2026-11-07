import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from predict_agent.models import football, basketball, tennis, volleyball, player_props
from predict_agent.models.value import assess, remove_overround, kelly_fraction, poisson_pmf

def approx(a, b, tol=0.02):
    return abs(a - b) <= tol

def test_football_markets_sum():
    out = football.predict(1.9, 1.1)
    mk = out["markets"]
    assert approx(mk["home_win"] + mk["draw"] + mk["away_win"], 1.0)
    assert mk["home_win"] > mk["away_win"]  # stronger home lambda must favour home
    assert 0 < mk["over_2_5"] < 1 and 0 < mk["btts_yes"] < 1
    assert mk["top_correct_scores"][0]["prob"] < 0.25  # correct score is never "certain"
    grid_total = sum(mk["correct_score_grid"].values())
    assert grid_total <= 1.0

def test_football_stats():
    hs = {"shots": 15, "shots_conceded": 10, "shots_on_target": 5, "sot_conceded": 3,
          "corners": 6, "corners_conceded": 4, "fouls_committed": 11, "cards": 1.8, "offsides": 2}
    as_ = {"shots": 12, "shots_conceded": 13, "shots_on_target": 4, "sot_conceded": 5,
           "corners": 5, "corners_conceded": 6, "fouls_committed": 13, "cards": 2.1, "offsides": 1.5}
    out = football.predict(1.8, 1.0, home_stats=hs, away_stats=as_,
                           referee={"cards_per_game": 5.0, "fouls_per_game": 26})
    ms = out["match_stats"]
    assert ms["total_shots"]["expected"] == 27
    assert ms["total_cards"]["expected"] > 3.9  # strict referee lifts cards

def test_player_props():
    players = [{"name": "Striker", "team": "home", "xg_per90": 0.7, "xa_per90": 0.2,
                "shots_per90": 3.5, "sot_per90": 1.6, "key_passes_per90": 1.0,
                "fouls_per90": 1.2, "cards_per90": 0.15, "expected_minutes": 90,
                "penalty_taker": True}]
    out = player_props.predict_players(players, 2.0, 1.0)
    top = out["most_likely_scorers"][0]
    assert 0.35 < top["anytime_scorer_prob"] < 0.75
    assert top["anytime_assist_prob"] > 0
    assert top["sot_over_0_5"] > top["anytime_scorer_prob"]

def test_value_engine():
    fair = remove_overround([2.0, 3.5, 3.5])
    assert approx(sum(fair), 1.0)
    v = assess(0.60, 2.0)
    assert v["verdict"] == "VALUE" and v["ev_per_unit"] > 0
    v2 = assess(0.40, 2.0)
    assert v2["verdict"] == "NO BET"
    assert 0 <= kelly_fraction(0.6, 2.0) <= 0.05
    assert approx(poisson_pmf(0, 0.0), 1.0)

def test_other_sports():
    b = basketball.predict(112, 105)
    assert approx(b["home_win_prob"] + b["away_win_prob"], 1.0)
    assert b["home_win_prob"] > 0.5
    t = tennis.match_prob(2150, 2000)
    assert t["player_a_win_prob"] > 0.5
    v = volleyball.predict(1650, 1500)
    assert approx(v["home_win_prob"] + v["away_win_prob"], 1.0)
    assert v["home_win_prob"] > 0.5
    assert set(v["set_score_probs"]).issubset({"3-0", "3-1", "3-2", "2-3", "1-3", "0-3"})

if __name__ == "__main__":
    for name, fn in sorted(dict(globals()).items()):
        if name.startswith("test_"):
            fn()
            print(f"PASS {name}")
    print("All tests passed.")
