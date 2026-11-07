"""CLI — predict a single match in any sport, with full markets + value.

Examples:
  python -m predict_agent.predict football --home Arsenal --away Chelsea \
      --home-xg 1.9 --away-xg 1.1 --odds-home 2.10 --odds-draw 3.40 --odds-away 3.20

  # Full football prediction: team stats + players from a JSON file
  python -m predict_agent.predict football --home Arsenal --away Chelsea \
      --home-xg 1.9 --away-xg 1.1 --full examples/full_prediction.json

  python -m predict_agent.predict basketball --home "LA Lakers" --away "Boston Celtics" \
      --home-pts 112 --away-pts 108
  python -m predict_agent.predict tennis --home Alcaraz --away Sinner \
      --elo-home 2150 --elo-away 2100 --surface hard
  python -m predict_agent.predict volleyball --home Brazil --away Italy \
      --elo-home 1650 --elo-away 1580
"""
from __future__ import annotations
import argparse, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from predict_agent.models import football, basketball, tennis, volleyball, player_props
from predict_agent.models.value import assess
from predict_agent.data.links import links_for

def main():
    ap = argparse.ArgumentParser(prog="predict")
    ap.add_argument("sport", choices=["football", "basketball", "tennis", "volleyball"])
    ap.add_argument("--home", required=True)
    ap.add_argument("--away", required=True)
    ap.add_argument("--home-xg", type=float, default=1.45)
    ap.add_argument("--away-xg", type=float, default=1.15)
    ap.add_argument("--home-pts", type=float, default=110.0)
    ap.add_argument("--away-pts", type=float, default=106.0)
    ap.add_argument("--elo-home", type=float, default=1500)
    ap.add_argument("--elo-away", type=float, default=1500)
    ap.add_argument("--surface", default="hard", choices=["hard", "clay", "grass"])
    ap.add_argument("--odds-home", type=float)
    ap.add_argument("--odds-draw", type=float)
    ap.add_argument("--odds-away", type=float)
    ap.add_argument("--full", help="JSON file with team_stats, referee and players for a full football prediction")
    args = ap.parse_args()

    out: dict = {"match": f"{args.home} vs {args.away}", "sport": args.sport}

    if args.sport == "football":
        full = {}
        if args.full:
            full = json.load(open(args.full))
        out["prediction"] = football.predict(
            args.home_xg, args.away_xg,
            home_stats=full.get("home_stats"), away_stats=full.get("away_stats"),
            referee=full.get("referee"))
        if full.get("players"):
            out["player_props"] = player_props.predict_players(
                full["players"], args.home_xg, args.away_xg)
        if args.odds_home and args.odds_draw and args.odds_away:
            mk = out["prediction"]["markets"]
            out["value"] = {
                "home": assess(mk["home_win"], args.odds_home),
                "draw": assess(mk["draw"], args.odds_draw),
                "away": assess(mk["away_win"], args.odds_away),
            }
    elif args.sport == "basketball":
        out["prediction"] = basketball.predict(args.home_pts, args.away_pts)
        if args.odds_home and args.odds_away:
            out["value"] = {
                "home": assess(out["prediction"]["home_win_prob"], args.odds_home),
                "away": assess(out["prediction"]["away_win_prob"], args.odds_away)}
    elif args.sport == "tennis":
        out["prediction"] = tennis.match_prob(args.elo_home, args.elo_away)
        if args.odds_home and args.odds_away:
            out["value"] = {
                "home": assess(out["prediction"]["player_a_win_prob"], args.odds_home),
                "away": assess(out["prediction"]["player_b_win_prob"], args.odds_away)}
    elif args.sport == "volleyball":
        out["prediction"] = volleyball.predict(args.elo_home, args.elo_away)
        if args.odds_home and args.odds_away:
            out["value"] = {
                "home": assess(out["prediction"]["home_win_prob"], args.odds_home),
                "away": assess(out["prediction"]["away_win_prob"], args.odds_away)}

    out["links"] = links_for(args.home, args.away)
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
