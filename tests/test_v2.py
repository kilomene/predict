"""v2.0 core tests: calibration must measurably de-bias a rigged model,
and the gate must refuse to force picks on coin-flip matches."""
import random, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from predict_agent import calibration as cal
from predict_agent import gating

def _rigged_dataset(n=3000, seed=7):
    """A model that over-predicts home wins and under-predicts draws:
    true rates H .45 / D .27 / A .28, model says H .58 / D .17 / A .25."""
    rng = random.Random(seed)
    probs, outcomes = [], []
    for _ in range(n):
        u = rng.random()
        y = 0 if u < 0.45 else 1 if u < 0.72 else 2
        base = [(0.58, 0.17, 0.25), (0.50, 0.20, 0.30), (0.52, 0.18, 0.30)][y]
        jitter = tuple(max(0.02, b + rng.uniform(-0.06, 0.06)) for b in base)
        s = sum(jitter)
        probs.append(tuple(v / s for v in jitter))
        outcomes.append(y)
    return probs, outcomes

def test_calibration_reduces_draw_gap_and_logloss():
    probs, outcomes = _rigged_dataset()
    before = cal.class_calibration(probs, outcomes)
    assert before["D"]["gap"] < -0.05, "rigged model must under-predict draws"
    params = cal.fit_vector_scaling(probs, outcomes)
    fixed = [cal.apply_vector_scaling(p, params) for p in probs]
    after = cal.class_calibration(fixed, outcomes)
    assert abs(after["D"]["gap"]) < abs(before["D"]["gap"]) - 0.03
    assert cal.log_loss(fixed, outcomes) < cal.log_loss(probs, outcomes)
    assert cal.ece(fixed, outcomes) <= cal.ece(probs, outcomes) + 1e-9

def test_calibration_identity_on_perfect_params():
    p = (0.5, 0.3, 0.2)
    out = cal.apply_vector_scaling(p, {"temperature": 1.0, "bias": [0, 0, 0]})
    assert all(abs(a - b) < 1e-9 for a, b in zip(out, p))

def test_gate_refuses_coin_flip():
    call = gating.decide((0.38, 0.31, 0.31))
    assert call["type"] == "NO_PICK" and call["selection"] is None

def test_gate_single_and_dc():
    assert gating.decide((0.67, 0.19, 0.14))["type"] == "SINGLE"
    dc = gating.decide((0.46, 0.33, 0.21))
    assert dc["type"] == "DOUBLE_CHANCE" and dc["selection"] == "1X"
    assert gating.grade(dc, "D") is True and gating.grade(dc, "A") is False
    assert gating.grade(gating.decide((0.38, 0.31, 0.31)), "H") is None

def test_gate_summary_reports_coverage():
    calls = [gating.decide(p) for p in [(0.7, 0.2, 0.1), (0.46, 0.33, 0.21), (0.38, 0.31, 0.31)]]
    s = gating.summarise(list(zip(calls, ["H", "D", "A"])))
    assert s["matches"] == 3 and s["singles"] == 1 and s["double_chance"] == 1 and s["no_pick"] == 1
    assert s["singles_hit_rate"] == 1.0


def test_pi_ratings_learn_and_damp():
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from predict_agent.features.pi_ratings import PiRatings
    pi = PiRatings()
    assert pi.expected_gd("A", "B") == 0.0
    for _ in range(10):
        pi.update("A", "B", 2, 0)
    assert pi.get_home("A") > 0 and pi.get_away("B") < 0
    assert pi.expected_gd("A", "B") > 0.5
    p = pi.probs("A", "B")
    assert p[0] > p[2] and abs(sum(p) - 1) < 1e-6
    # damping: a 6-0 must move ratings less than 6x a 1-0 from scratch
    one, six = PiRatings(), PiRatings()
    one.update("A", "B", 1, 0); six.update("A", "B", 6, 0)
    assert 0 < six.get_home("A") < 6 * one.get_home("A")

def test_live_intensity_curve():
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from predict_agent.live_engine import football_live
    # minute 0: intensity ~= pre-match (full lambda remains)
    r0 = football_live(1.9, 1.1, 0, 0, 0)
    assert r0["remaining_xg"]["home"] == 1.9
    # half-time: intensity keeps MORE remaining than the linear clock
    # (goals are back-loaded: 56% of goals still to come at 45')
    ri = football_live(1.9, 1.1, 45, 0, 0, model="intensity")
    rl = football_live(1.9, 1.1, 45, 0, 0, model="linear")
    assert ri["remaining_xg"]["home"] > rl["remaining_xg"]["home"]
    # late game: a 2-0 lead at 89' is safer under intensity (fewer goals left)
    late_i = football_live(1.9, 1.1, 89, 2, 0, model="intensity")
    assert late_i["home_win"] > 0.95
    # monotonic: remaining xG never rises with time
    prev = 99.0
    for mnt in (0, 15, 30, 45, 60, 75, 90):
        r = football_live(1.9, 1.1, mnt, 0, 0)
        assert r["remaining_xg"]["home"] <= prev + 1e-9
        prev = r["remaining_xg"]["home"]


if __name__ == "__main__":
    for name, fn in sorted(dict(globals()).items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
