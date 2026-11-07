# The Market Handbook

## Every football market on football.com — decoded, settled, and mapped to the plays we actually make

*Compiled 2026-11-07 by Phoenix (Predict agent) from a full end-to-end study: both official
manuals read completely (football.com "How to Play — Football" and the SportyBet Nigeria
football manual — the same document family, near word-for-word), plus a live market catalogue
of Arsenal vs Hull City (Premier League, in-play) and a pre-match catalogue of Parma vs Bologna
(Serie A). The source manuals are archived in `docs/manuals/`. This handbook is written in our
own words from that study; where the manuals are silent, it says so.*

---

## 1. The five laws everything else obeys

1. **Regular time is the default universe.** Unless a market says otherwise, it is settled on
   the 90 minutes plus injury time. Extra time and penalty shootouts do not count.
2. **Goal time = when the ball crosses the line**, as announced by TV (else the match clock) —
   not when the shot was taken. Corner time = when the kick is taken. Booking time = when the
   card is shown. Offside/penalty time = when the referee decides.
3. **Statistics settle on Opta data** — shots, shots on target, fouls, offsides, tackles,
   saves, woodwork. Opta's definitions can differ from a league's own.
4. **Dead markets die.** If a match is interrupted and not finished within 48 hours of the
   original kickoff, undecided bets are void. Bets taken at a wrong displayed score, a wrong
   match clock (off by more than 5 minutes), or on an event that had already happened can be
   voided by the bookmaker.
5. **Pre-match and live are two different shops.** Whole market families exist on one side
   only (see §12). Anything involving minutes is a live-only product.

## 2. How to read a market name — the two numbers

Every time-based market carries **two different numbers doing two different jobs**:

- The **window** — in the market's *title*: `from 1 to 15`, `from 46 to 60`. This is minutes.
- The **line** — on the *selection*: `0.5`, `2.5`. In a goals market this counts **goals**, never minutes.

Read in full, "Under 0.5" inside a market titled `15 minutes - Over/Under from 1 to 15` means
*under 0.5 goals in minutes 1–15* — i.e. no goal in the first fifteen minutes. Confusing the
window with the line is the single most expensive reading error on this site; this handbook
exists because of it.

## 3. The early no-goal family — the owner's core plays

**The play:** neither team scores inside the opening window. Three windows matter: 5, 10, 15
minutes. Each has **two equivalent doors** on football.com, both **live-only** — they appear
at kickoff and the opening window vanishes the moment it ends.

| Play | Door A — interval 1st-goal market | Selection | Door B — interval totals market | Selection |
|---|---|---|---|---|
| No goal in first 5 min | `5 minutes - 1st goal from 1 to 5` | **None** | `5 minutes - Over/Under from 1 to 5` | **Under 0.5** |
| No goal in first 10 min | `10 minutes - 1st goal from 1 to 10` | **None** | `10 minutes - Over/Under from 1 to 10` | **Under 0.5** |
| No goal in first 15 min | `15 minutes - 1st goal from 1 to 15` | **None** | `15 minutes - Over/Under from 1 to 15` | **Under 0.5** |

How each door works:

- **Door A ("…minutes - 1st goal from a to b")** offers Home / **None** / Away: which team
  scores the first goal *inside that window* — or nobody (**None**). The manual's one-line
  definition covers the Nth-goal interval family ("predict which team will score the Nth goal
  within a time interval"); the None option itself is never defined in either manual — its
  meaning is fixed by the market's structure, and it is confirmed by live prices (the None
  price in a window matches the Under 0.5 price for the same window, e.g. both 1.27 for
  minutes 41–50 on Arsenal vs Hull).
- **Door B ("…minutes - Over/Under from a to b")** is the same bet in totals language: the
  manual defines it as the total goals inside a 5/10/15-minute interval measured against a
  line, and the 0.5 line can only mean zero goals (see §4). In the observed live pages, 0.5
  was the only line offered in these interval totals.
- A near neighbour that is **not** the same bet: `…minutes - 1X2 from a to b` → **Draw**.
  A level window includes 1–1 inside the window; the owner's play loses on any goal. Use
  Doors A/B for the pure play.

**Operating facts (verified live):**

- The windows **roll**. Only the current block is listed: at half-time of Arsenal vs Hull the
  15-minute 1X2 showed `from 46 to 60`, the 5-minute showed `from 46 to 50`, and the 10-minute
  1st-goal showed `from 41 to 50`. At kickoff they read `from 1 to 5 / 1 to 10 / 1 to 15`.
- The 10-minute 1X2 is a different animal: one market named **`1X2 - Intervals of 10 Minutes`**
  whose row is *cumulative* ("1 to 50 Minutes", then "1 to 60 Minutes") — the 1X2 of the whole
  score from minute 1 to the next 10-minute boundary. It is not a set of slices.
- There are also cumulative totals, live only: **`Total Goals Over/Under from 1 to X minute`**
  (X = 50, 55, … 85 in repeated groups; the first group was verified as the 0.5 line —
  "no goal at all by minute X" is Under 0.5 there).
- **League/feed dependence:** minute markets are not universal. A live Botola Pro match
  observed the same day (Kawkab vs Wydad) had an empty Minutes tab and no interval markets
  at all. Always confirm the family exists on the specific match before planning a play.
- Pre-match, the Minutes tab holds exactly **two** markets: the first-goal interval markets
  of §5. Nothing else. Any plan that needs a window market is a live-betting plan.

**Measured base rates (our research, for calibration):** across big-league football, roughly
93% of matches are goalless at 5′, ~81% at 10′, ~69–71% at 15′ — before adjusting for the two
teams' expected goals. The Predict engine prices each match individually
(`src/predict_agent/early_goals.py`: P(no goal by t) = exp(−λ_match × F(t)) with the empirical
goal-timing curve F(5)=0.032, F(10)=0.072, F(15)=0.128).

## 4. Over/Under — the lines, settled

The manual's definition, paraphrased: *predict whether the total goals in regular time finish
over or under a given line.* Lines come in three kinds, and the kind decides the settlement:

| Line kind | Examples | Possible settlements |
|---|---|---|
| Half lines | 0.5, 1.5, 2.5, 3.5 | Win or lose only — no refunds |
| Whole lines | 1, 2, 3 | Win, lose, or **void** (stake back) if the total lands exactly on the line |
| Quarter lines | 0.75, 1.25, 2.25, 2.75 | The stake splits across the two neighbouring lines: win, lose, half-win, or half-lose |

**The manual's Over/Under settlement table — in full.** Every line the book offers, every
total-goals outcome, both sides. (Regular time totals; the same grid settles any scoped
version — team, half, interval — inside its own scope.)

| Line | Total goals | Over settles | Under settles |
|---|---|---|---|
| 0.5 | 0 | Lose | **Win** |
| 0.5 | 1+ | **Win** | Lose |
| 0.75 | 0 | Lose | **Win** |
| 0.75 | 1 | Half win | Half lose |
| 0.75 | 2+ | **Win** | Lose |
| 1.0 | 0 | Lose | **Win** |
| 1.0 | 1 | Void | Void |
| 1.0 | 2+ | **Win** | Lose |
| 1.25 | 0 | Lose | **Win** |
| 1.25 | 1 | Half lose | Half win |
| 1.25 | 2+ | **Win** | Lose |
| 1.5 | 0–1 | Lose | **Win** |
| 1.5 | 2+ | **Win** | Lose |
| 1.75 | 0–1 | Lose | **Win** |
| 1.75 | 2 | Half win | Half lose |
| 1.75 | 3+ | **Win** | Lose |
| 2.0 | 0–1 | Lose | **Win** |
| 2.0 | 2 | Void | Void |
| 2.0 | 3+ | **Win** | Lose |
| 2.25 | 0–1 | Lose | **Win** |
| 2.25 | 2 | Half lose | Half win |
| 2.25 | 3+ | **Win** | Lose |
| 2.5 | 0–2 | Lose | **Win** |
| 2.5 | 3+ | **Win** | Lose |
| 2.75 | 0–2 | Lose | **Win** |
| 2.75 | 3 | Half win | Half lose |
| 2.75 | 4+ | **Win** | Lose |
| 3.0 | 0–2 | Lose | **Win** |
| 3.0 | 3 | Void | Void |
| 3.0 | 4+ | **Win** | Lose |

Read the owner's core play off this grid: line **0.5**, total **0** → Under wins. Under 0.5 on a
full match is a bet on 0–0; Under 0.5 inside a `from 1 to 15` window is the no-goal play of §3.

The same line logic applies inside any scope the market names: full match, one team
(Home/Away Team Over/Under), one half, or one interval window (§3, Door B). Scope is always in
the market title; the line is always the count.

## 5. The two "None"s — and the first-goal timing markets

The word **None** appears as a selection in two unrelated places, and confusing them is
expensive:

| Where you see "None" | What it means | Settles |
|---|---|---|
| Interval 1st-goal markets — `…minutes - 1st goal from a to b` (Home / None / Away) | **No goal inside that window** | When the window ends |
| `When will the 1st goal be scored (15 min interval)` / `(10 min interval)` — options 1-15, 16-30, …, 76-90, None | **No goal in the entire match** (0–0 full time) | Full time |

`When will the 1st goal be scored` is the **only** early-timing market sold **pre-match**
(Minutes tab). Its options are windows in which a goal *is* scored — the opposite direction
from the owner's play — plus None for a goalless match. Live, the elapsed windows show as
locked while the rest keep pricing. Observed pre-match (Parma vs Bologna): 15-min version —
1-15 @3.40, 16-30 @4.20, 31-45 @5.10, 46-60 @8.40, 61-75 @12.00, 76-90 @14.00, None @9.70;
10-min version — 1-10 @4.90 stepping to 81-90 @19.50, None @9.60.

Neither manual defines this market family beyond a single line for the 10-minute Nth-goal
version ("predict at which time interval (10 mins) the Nth goal will be scored"), and neither
manual contains the word "None" at all. The meanings above are fixed by market structure and
were verified against live pricing behaviour (the whole-match None shortened from 32.00
pre-match to ~6.50 at half-time of a 0–0 match — exactly how a 0–0-full-time price behaves).

Related goal-timing markets:

- **1st Goal** (Main tab): Home / None / Away — which side scores the match's first goal, or
  nobody. The manual has no heading for this market; the site's separate **Next Goal** rule
  states that if the named goal is never scored, those bets are void — a different treatment
  from a None selection, so do not blend the two in your head.
- **Next Goal / Last Goal:** which team scores the Nth / the last goal of the match.
- **Next Scoring Type:** the *kind* of the next goal — free kick, penalty, header, own goal,
  other, or No Goal.

## 6. The core result markets

| Market | Meaning | Settlement notes |
|---|---|---|
| **1X2** | Home win / Draw / Away win in regular time | The base market. Variants below change *when* it settles |
| **1X2 — 1UP** | Your team is paid as a winner the moment it leads by 1 goal | Once settled, the final score is irrelevant. Draw selections settle like normal 1X2 |
| **1X2 — 2UP** | Paid as a winner the moment your team leads by 2 goals | Same early-settlement logic; still paid if the match is later abandoned with the 2-goal lead |
| **1X2 — NeverDown** | Your team must win **without ever trailing** | Going behind at any point loses the bet, even in a comeback win. football.com also sells team versions (Home/Away 1UP, 2UP, 3UP) and Double Chance 1UP |
| **DrawSave** (football.com) | The **Draw** selection wins if the score is level at the 90th minute — and still wins on any full-time draw | Singles and multiples only; if your team led by 1+ the draw option stays "live" only until the 60th minute per the manual text |
| **Double Chance** | 1X (home or draw), 12 (either team wins), X2 (draw or away) | Two of the three outcomes in one selection |
| **Draw No Bet** | Pick the winner; a draw voids the bet | Stake refunded on a draw |
| **Home No Bet / Away No Bet** | Pick the result; if the named side wins, the bet voids | Mirror-image insurance markets |
| **European Handicap (3-way)** | A goal start (+/−) is added to a team's score, then 1X2 is settled on the adjusted score | Three outcomes, no refunds; the handicap is part of the score |
| **Asian Handicap** | Handicap with split lines (0, ±0.25, ±0.5, ±0.75, ±1…) | Draws can refund (line 0), half-refund (quarter lines). E.g. −0.25: win by 1+ = full win, draw = half stake back, lose = full loss |
| **Correct Score** | The exact full-time score | Usually a 8–16% shot even for the likeliest line — price accordingly |
| **Half Time / Full Time** | The result at half-time **and** at full-time, as one selection (e.g. Draw/Home) | Only the HT/FT *Correct Score* variant exists pre-match on football.com; there is no plain HT/FT 1X2 there |
| **GG/NG (Both Teams To Score)** | Yes = both teams score at least once; No = at least one team fails to score | Also GG/NG 2+ (both score 2+), and 1st-half versions |
| **Exact Goals** | The exact total number of goals (0, 1, 2, 3, 4, 5+) | Live Main tab on football.com; also per-team and per-half |
| **Odd/Even** | Total goals odd or even — **zero goals counts as even** | Per match, per team, per half |
| **Goal Range / Goal Bounds** | Total goals fall inside a chosen band (e.g. 1–2, 2–4, 0–3) | "Excluded Number of Goals" is the inverse idea: total minus a chosen number |
| **Winning Margin** | The exact goal difference between the teams | Sign matters: home by 2 ≠ away by 2 |
| **Teams to Score / Clean Sheet** | Which teams score; which teams keep a clean sheet | Team-level building blocks used by many combos |
| **Win to Nil** | A team wins **and** concedes nothing | Manual spelling: "Win to Nill" |

### The Asian Handicap settlement table — in full

The manual settles Asian Handicap from a master table: your team's handicap against your
team's actual result. Every line, both directions, transcribed whole — this is the table the
one-line summary in §6 above was compressing. A minus handicap means your team *gives* the
start; plus means it *receives* it.

| Handicap on your team | Your team's result | Bet settles |
|---|---|---|
| 0 | Win | Win |
| 0 | Draw | Void (stake back) |
| 0 | Lose | Lose |
| −0.25 | Win | Win |
| −0.25 | Draw | Half lose |
| −0.25 | Lose | Lose |
| +0.25 | Win | Win |
| +0.25 | Draw | Half win |
| +0.25 | Lose | Lose |
| −0.5 | Win | Win |
| −0.5 | Draw | Lose |
| −0.5 | Lose | Lose |
| +0.5 | Win | Win |
| +0.5 | Draw | Win |
| +0.5 | Lose | Lose |
| −0.75 | Win by 2+ | Win |
| −0.75 | Win by 1 | Half win |
| −0.75 | Draw | Lose |
| −0.75 | Lose | Lose |
| +0.75 | Win | Win |
| +0.75 | Draw | Win |
| +0.75 | Lose by 1 | Half lose |
| +0.75 | Lose by 2+ | Lose |
| −1 | Win by 2+ | Win |
| −1 | Win by 1 | Void |
| −1 | Draw | Lose |
| −1 | Lose | Lose |
| +1 | Win | Win |
| +1 | Draw | Win |
| +1 | Lose by 1 | Void |
| +1 | Lose by 2+ | Lose |
| −1.25 | Win by 2+ | Win |
| −1.25 | Win by 1 | Half lose |
| −1.25 | Draw | Lose |
| −1.25 | Lose | Lose |
| +1.25 | Win | Win |
| +1.25 | Draw | Win |
| +1.25 | Lose by 1 | Half win |
| +1.25 | Lose by 2+ | Lose |
| −1.5 | Win by 2+ | Win |
| −1.5 | Win by 1 | Lose |
| −1.5 | Draw | Lose |
| −1.5 | Lose | Lose |
| +1.5 | Win | Win |
| +1.5 | Draw | Win |
| +1.5 | Lose by 1 | Win |
| +1.5 | Lose by 2+ | Lose |
| −1.75 | Win by 3+ | Win |
| −1.75 | Win by 2 | Half win |
| −1.75 | Win by 1 | Lose |
| −1.75 | Draw | Lose |
| −1.75 | Lose | Lose |
| +1.75 | Win | Win |
| +1.75 | Draw | Win |
| +1.75 | Lose by 1 | Win |
| +1.75 | Lose by 2 | Half lose |
| +1.75 | Lose by 3+ | Lose |
| −2 | Win by 3+ | Win |
| −2 | Win by 2 | Void |
| −2 | Win by 1 | Lose |
| −2 | Draw | Lose |
| −2 | Lose | Lose |
| +2 | Win | Win |
| +2 | Draw | Win |
| +2 | Lose by 1 | Win |
| +2 | Lose by 2 | Void |
| +2 | Lose by 3+ | Lose |

The pattern underneath the table: whole lines can void, half lines never split, and quarter
lines are two half-bets in one — half the stake on the line above, half on the line below
(e.g. −0.75 = half on −0.5, half on −1.0). The same split logic drives the quarter rows of
the Over/Under table in §4.

## 7. Halves

Every core idea repeats per half, and a half is settled **only on goals within that half**
(the second half starts 0–0 for betting purposes):

- 1st Half / 2nd Half versions of: 1X2, Double Chance, Draw No Bet, Handicap, Asian Handicap,
  Over/Under, GG/NG, Correct Score, team totals, exact goals, odd/even, clean sheets.
- **Which Team Will Win the Rest (of the half/match):** from the moment of betting, only goals
  scored after that moment count — the score effectively restarts at 0–0.
- **Highest Scoring Half:** which half produces more goals (1st / 2nd / equal), also per team.
- **Win Both Halves / Win Either Half:** a team must outscore the opponent in both halves, or
  in at least one.

## 8. Corners and bookings

**Corners** settle on corners **taken** — awarded-but-not-taken corners do not count, and a
re-taken corner counts once. Markets: total Corners Over/Under, Corners 1X2 (which team takes
more), per-team totals, Corner Handicap, Corner Range, Nth Corner, Last Corner, Race to X
Corners, odd/even — plus half and 5/10/15-minute interval versions of the same ideas.

**Bookings** counting, from the manual — as a table, the way the book itself counts:

| Card event | Counts as cards | Booking points |
|---|---|---|
| Yellow card | 1 | 10 |
| Red card (straight, or second-yellow red) | 2 | 25 |
| The second yellow itself | Not double-counted | — |
| **Maximum one player can cause** | **3 cards** | **35 points** |

Cards shown after the final whistle, and cards for non-players (bench, manager, substituted
players), do not count; a card shown during the half-time break counts in the second half. Markets: Total
Bookings (cards) Over/Under, Booking Points Over/Under, Bookings 1X2, 1st Booking (Home / None
/ Away), Exact Bookings, Sending Off (per team too), booking handicaps — plus half and interval
versions.

## 9. Player markets

All player markets settle on **Opta** definitions (a "shot on target" includes a goal-line or
woodwork contact per Opta; a shot blocked by another outfield player is not a shot at all, and
so on).

- **Participation rule:** if the player takes any part in the match, the bet stands — starter
  or substitute, however few minutes.
- **No-show rule:** if the player never enters, bets void — **except** a named list that voids
  if the player merely does not **start**: player shots, shots on goal, assists, tackles,
  passes, player-not-to-score, and player head-to-heads.
- **Goalscorer markets:** First / Anytime / Last goalscorer; to score 2+; score-or-assist;
  score-and-assist; method markets (header, free kick, foot). **Own goals never count** for
  Anytime or score-X markets — but an own goal **does** count as the First Goal for First
  Goalscorer settlement. If a match ends goalless, First Goalscorer player bets lose (the
  market's own "no goal" outcome is the winner).
- **Performance lines:** shots, shots on target (incl. from outside the box, per half, each
  half), passes, tackles, fouls, offsides, to be carded, first player booked.

## 10. Football.com's EarlyWin family (pre-match only)

A whole tab that exists **only before kickoff** on football.com (not in the SportyBet manual):

- **1X2 (1UP) / 1X2 (2UP)** and **Double Chance (1UP)** — as §6.
- **Over/Under (GoalRush):** you bet **Over only**; the bet is paid immediately if the goals
  arrive early on a fixed ladder (per the manual's EarlyGoals definition: Over 1.5 needs 1 goal
  by 10′, Over 2.5 needs 2 by 30′, Over 3.5 needs 3 by 50′). If the early condition fails, the
  selection is **not lost** — it reverts to being a normal Over/Under bet for the full match.
- **Home/Away Over/Under (Early Goals)** and **(GoalRush)** — the same idea scoped to one team.
- **To Lead by 1 / 2 / 3 Goals at Any Time** — the team reaches that lead at any point.

## 11. Combination markets

The site builds two-leg ideas into single selections. The recurring grammar: **"A or B"** wins
if *either* leg lands; **"A & B"** needs *both*.

- **1X2 & Over/Under**, **1X2 & GG/NG**, **Double Chance & Over/Under**, **Double Chance &
  GG/NG**, **Over/Under & GG/NG**, **HT/FT & Over/Under** — the paired markets, both legs must
  land (& versions).
- **Home/Draw/Away Team *or* …** — e.g. "Home Team or Over 2.5", "Draw or GG/NG",
  "Away Team or Any Clean Sheet": wins if the result leg *or* the goals leg lands.

## 12. Live vs pre-match — the map that matters

Observed on the same day: a live Premier League match showing **241 markets** (falling as
windows settle) and a pre-match Serie A match showing **881** (every line variant counted).
Named blocks: ~130 live, ~142 pre-match — but the *families* differ:

| Live only | Pre-match only |
|---|---|
| All rolling interval markets (1X2, 1st goal, Over/Under at 5/10/15 min) | The entire **EarlyWin** tab (1UP/2UP/DrawSave/GoalRush/EarlyGoals) |
| Cumulative totals "from 1 to X minute" | 1st Booking, Exact Bookings |
| Rest of the Match, Win From Behind | Goal in Both Halves, Goal Bounds, Excluded Number of Goals |
| Exact Goals, Odd/Even (match), Home/Away No Bet | Full player-prop depth (assists, passes, tackles, not-to-score…) |
| Fouls markets (Fouls 1X2, Fouls Over/Under, team fouls) | Team posts/crossbars, team offsides, substitution markets |
| 2nd-half market set (grows as the match ages) | 1st-half everything (dies at half-time) |

Both sides share: 1X2 and variants, all Over/Under lines, Double Chance, handicaps, GG/NG,
correct score, team totals, corners and bookings cores, goalscorer markets, and the Minutes
tab's two first-goal interval markets.

## 13. Traps this handbook now guards against

1. **The two Nones** (§5). Always name the market, not just the selection.
2. **Window ≠ line** (§2). Minutes live in titles; 0.5 counts goals.
3. **"It doesn't exist" is a live-vs-pre-match claim.** The early no-goal family is invisible
   until kickoff. No market is declared absent until the live list has been checked.
4. **Padlocks are normal.** Markets suspend briefly around goals, dangerous attacks and
   half-time, and settled windows lock/disappear. A locked market is not a broken site.
5. **The manuals have gaps and typos.** "None" is defined nowhere; the 15-minute first-goal
   market has no manual heading; football.com's manual mis-defines "Draw or GG/NG" (copied
   from the Home Team version) and repeats 1UP text inside its EarlyGoals section. When the
   manual and the market's own structure disagree, structure and observed settlement win.
6. **Feed dependence.** Lower-league matches may carry no minute markets at all (§3). Check
   the specific match, every time.

## 14. Our staking protocol (standing)

1. The model chooses the play by **percentage** — never by the bookmaker's price.
2. Before any stake, the exact **market name + selection + settlement** is stated and matched
   against this handbook (e.g. *15 minutes - 1st goal from 1 to 15 → None; settles at 15:00*).
3. Stakes are singles, at the owner's exact amounts, on football.com only, unless the owner
   rules otherwise for that bet.
4. Every result — right or wrong — is settled into the Predict ledger and graded the next
   morning; the ratings learn from all of it.

---

*Sources: football.com How to Play — Football & General Settlement pages; SportyBet Nigeria
How to Play — Football & General pages (both archived in `docs/manuals/`); live and pre-match
market catalogues captured 2026-11-07 on football.com/ng. Prices quoted in this handbook are
observations from that day, not standing odds.*
