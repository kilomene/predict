import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from predict_agent.live_engine import football_live, basketball_live, tennis_live, volleyball_live
from predict_agent.models import football

def approx(a, b, tol=0.03):
    return abs(a - b) <= tol

def test_football_live():
    pre = football.predict(1.9, 1.1)["markets"]
    live0 = football_live(1.9, 1.1, 0, 0, 0)
    assert approx(live0["home_win"], pre["home_win"], 0.04), (live0["home_win"], pre["home_win"])
    late = football_live(1.9, 1.1, 89, 2, 0)
    assert late["home_win"] > 0.97, late
    red = football_live(1.9, 1.1, 45, 0, 0, red_h=1)
    plain = football_live(1.9, 1.1, 45, 0, 0)
    assert red["home_win"] < plain["home_win"] - 0.05
    assert approx(late["home_win"] + late["draw"] + late["away_win"], 1.0, 0.01)
    assert late["no_more_goals"] > 0.7

def test_other_sports_live():
    b = basketball_live(110, 106, 47, 108, 100)
    assert b["home_win"] > 0.95
    t = tennis_live(0.55, 1, 0, 5, 3)
    assert t["player_a_win"] > 0.75
    t2 = tennis_live(0.55, 2, 0, 0, 0)
    assert t2["player_a_win"] == 1.0
    v = volleyball_live(0.58, 2, 0, 20, 12)
    assert v["home_win"] > 0.9

if __name__ == "__main__":
    test_football_live(); print("PASS test_football_live")
    test_other_sports_live(); print("PASS test_other_sports_live")
