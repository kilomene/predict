import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from predict_agent.daily import norm, match_team

def test_norm_and_match():
    known = {"Man United": {}, "Brighton": {}, "Bayern Munich": {}, "Paris SG": {}}
    assert match_team("Manchester United", known) == "Man United"
    assert match_team("Brighton & Hove Albion", known) == "Brighton"
    assert match_team("Bayern Munich", known) == "Bayern Munich"
    assert match_team("Paris Saint-Germain", known) == "Paris SG"
    assert match_team("Unknown FC", known) is None
    assert norm("Atlético de Madrid") == "atletico de madrid"

if __name__ == "__main__":
    test_norm_and_match()
    print("PASS test_daily")
