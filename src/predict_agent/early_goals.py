"""Early-goal timing model — "will there be a goal in the first N minutes?"

Built from measured data, not bookmaker odds:

  P(no goal by minute t) = exp(-lambda_match * F(t))

where lambda_match is the match's total expected goals (from the xG model)
and F(t) is the empirical cumulative share of all goals scored by minute t.
Goals are NOT uniform across a match — the scoring rate starts low and
rises — so a naive uniform split (t/94) overstates early goals badly.

F values (share of ALL goals), triangulated from three sources:
  * Published: Alberti et al. 2013 (4 leagues) 0-15 share 13.7%;
    Njororai 2014 (Big Five 2013/14) 0-15 share 12.3%, per league 12.0-12.8%;
    StatsUltra (PL 2023/24+2024/25) 0-10 share 7.5%.
  * Our own harvest of ESPN goal minutes, Big Five, Oct 18 - Nov 6 2026
    (135 finished matches, 414 goals): 0-10 share 7.0%, 0-15 share 12.6%;
    directly measured P(no goal by 10) = 81.5%, P(no goal by 15) = 68.9%.
  * Cross-check: Premier League 2016/17-2020/21 census (1,900 matches)
    measured P(no goal by 15) = 70.8%, mean first-goal time 30:57.

Blended curve used here: F(5)=0.032 (interpolated), F(10)=0.072, F(15)=0.128.
Sanity: at an average match (lambda 2.75) the formula gives P(no goal by
10) = 82% and by 15 = 70% — matching the measured base rates above.

Team "fast start / slow start" tendencies are mostly NOT persistent in the
research (a team is involved in only ~13 early goals a season — far too few
to identify a timing trait), so this model deliberately uses match goal
expectancy only, with no team timing fudge factors.
"""
from __future__ import annotations
import math

# minute -> cumulative share of all goals scored by that minute
GOAL_SHARE_CDF = {0: 0.0, 5: 0.032, 10: 0.072, 15: 0.128, 30: 0.27, 45: 0.44,
                  60: 0.62, 75: 0.80, 90: 0.985, 94: 1.0}

def share_by(minute: float) -> float:
    pts = sorted(GOAL_SHARE_CDF.items())
    if minute <= 0:
        return 0.0
    for (m0, f0), (m1, f1) in zip(pts, pts[1:]):
        if m0 <= minute <= m1:
            if m1 == m0:
                return f1
            return f0 + (f1 - f0) * (minute - m0) / (m1 - m0)
    return 1.0

def prob_no_goal_by(lam_home: float, lam_away: float, minute: float) -> float:
    return math.exp(-(lam_home + lam_away) * share_by(minute))

def prob_goal_by(lam_home: float, lam_away: float, minute: float) -> float:
    return 1.0 - prob_no_goal_by(lam_home, lam_away, minute)

def early_report(lam_home: float, lam_away: float) -> dict:
    out = {"lambda_total": round(lam_home + lam_away, 2)}
    for m in (5, 10, 15):
        p_no = prob_no_goal_by(lam_home, lam_away, m)
        out[f"no_goal_by_{m}"] = round(p_no, 4)
        out[f"goal_by_{m}"] = round(1 - p_no, 4)
        out[f"fair_odds_no_goal_by_{m}"] = round(1.0 / p_no, 2) if p_no > 0 else None
    # verdict on the two windows the owner cares about
    p15 = out["no_goal_by_15"]
    out["verdict_15"] = ("STRONG" if p15 >= 0.70 else
                         "LEAN" if p15 >= 0.65 else
                         "WEAK" if p15 >= 0.60 else "AVOID")
    p10 = out["no_goal_by_10"]
    out["verdict_10"] = ("STRONG" if p10 >= 0.80 else
                         "LEAN" if p10 >= 0.76 else
                         "WEAK" if p10 >= 0.72 else "AVOID")
    return out
