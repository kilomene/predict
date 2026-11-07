# The Market Handbook

## Every football market on football.com — decoded, settled, and mapped to the plays we actually make

*Compiled 2026-11-07 by Phoenix (Predict agent) from a full end-to-end study: both official
manuals read completely (football.com "How to Play — Football" and the SportyBet Nigeria
football manual — the same document family, near word-for-word), plus a live market catalogue
of Arsenal vs Hull City (Premier League, in-play) and a pre-match catalogue of Parma vs Bologna
(Serie A). The source manuals are archived in `docs/manuals/`. This handbook is written in our
own words from that study; where the manuals are silent, it says so. Coverage is A–Z: §16
indexes **every market heading in both manuals** (268 headings, machine-checked against the
manual texts), and the manuals' own settlement tables are carried in full in §4 and §6.*

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
- **Injury time at interval boundaries (manual, Interval Markets):** for the intervals that
  run into a half's end — 41–45, 31–40, 31–45 — events (goals, corners) scored in added
  injury/stoppage time **count inside that interval**. Interval timing always follows the
  event definitions of Law 2: goals by ball-crossing time, corners by taken time, bookings
  by card-shown time, offsides and penalties by the referee's decision (VAR included).
  A penalty **awarded but not taken** is not considered.
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
- **Next Scoring Type:** the *kind* of the next goal. The manual defines each type exactly,
  and two of the definitions surprise:

| Scoring type | The manual's test |
|---|---|
| Free kick | Scored **directly** from a free kick **or a corner**; a deflected shot still counts if the taker is awarded the goal |
| Penalty | Scored **directly** from the penalty — a goal from the **rebound of a missed penalty does not count** |
| Own goal | The goal is declared an own goal |
| Header | The scorer's **last touch** is with the head |
| Shot | Any other body part, where none of the above apply |
| No Goal | No further goal is scored |

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

All player markets settle on **Opta** definitions. The manuals spell out exactly what each
statistic counts — this is the ground truth every player line settles on:

| Statistic | Counts | Does **not** count |
|---|---|---|
| **Player Total Shots** | Any clear attempt to score: on target, off target, blocked (by anyone), off the woodwork; any legal body part | Set-piece attempts with no clear scoring intent that don't directly produce a goal (e.g. a crossed corner); cross-cum-shots / flick-ons with no clear intent |
| **Player Total Shots On Goal** | Attempts that score (whatever the intent); clear attempts that would have gone in but for a goalkeeper save or a **last-man** stop; woodwork shots that go straight in | Blocked shots by anyone other than the last man; woodwork shots that stay out; no-intent set pieces / crosses as above |
| **Player Total Passes** | Attempted passes (completed or not) with clear intention to find a teammate, incl. short-played goal kicks, free kicks and corners | Crosses, throw-ins, goalkeeper throws |
| **Player Tackles** | Ground challenges where the player connects with the ball and takes it from a player clearly in possession — whatever the outcome (possession won, ball out, ball to an opponent) | Missed/failed tackle attempts, aerial duels, fouls, interceptions |
| **Player Assists** | The final contribution (pass, shot, any touch) that leads directly to the receiving teammate's goal | Deflected contributions the recipient was unlikely to reach without the deflection; assists on own goals, penalties, direct corners, direct free kicks. **Pre-assists never count** (MLS rule stated in the manual: the pass before the assist is not an official assist and is ignored) |
| **Player Saves** | Every goalkeeper interception of a shot on goal | — |
| **Player Goals** | Goals in the opposition net | An off-target attempt deflected in off an opponent (an own goal) |

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

## 15. Cup markets — overtime and penalty shootouts

Everything in §§1–14 settles on regular time. Knockout football adds two more universes, and
the manuals give each its own full market set. These exist only in matches that allow them
(cups); none of them touch a regular-time bet.

**Qualification markets:**

| Market | Meaning |
|---|---|
| **To Qualify** | Which team advances to the next round — by whatever method the tie produces |
| **Will There Be Overtime** | Whether extra time is played at all |
| **Winning Method** | The winning team **and** how they win it; in a multi-leg tie the combined result of all legs is used |
| **Overtime & Goal** | Yes = there is overtime **and** a goal in it; No = no overtime, or overtime without a goal |

**Overtime markets** (settled only on the extra-time period itself):

| Market | Meaning |
|---|---|
| Overtime – 1X2 | Winner of the overtime period |
| Overtime – Handicap | Overtime result with the handicap applied |
| Overtime – Over/Under | Total overtime goals vs a line (settles on the §4 grid) |
| Overtime – Nth Goal | Which team scores the Nth overtime goal |
| Overtime – Correct Score | Exact overtime score |
| Overtime – Which Team Will Win the Rest | From the moment of betting, only later overtime goals count |
| Overtime 1st Half – 1X2 / Overtime 1st Half – Handicap / Overtime 1st Half – Correct Score | The same three ideas scoped to the first half of overtime |

**Penalty shootout markets** (settled only on the shootout):

| Market | Meaning |
|---|---|
| Penalty Shootout – Winner | Which team wins the shootout |
| Penalty Shootout – Winner & Over/Under | Shootout winner **and** total shootout goals vs a line |
| Penalty Shootout – Winning Margin | By how many goals the shootout is won |
| Penalty Shootout – Over/Under | Total shootout goals vs a line |
| Penalty Shootout – Exact Goals | Exact total of shootout goals |
| Penalty Shootout – Odd/Even | Total shootout goals odd or even |
| Penalty Shootout – Nth Penalty Scored | Whether the Nth penalty is scored |
| Penalty Shootout – Nth Goal | Which team scores the Nth shootout goal |
| Penalty Shootout – Home Over/Under / Penalty Shootout – Away Over/Under | One team's shootout goals vs a line |
| Penalty Shootout – Home Odd/Even / Penalty Shootout – Away Odd/Even | One team's shootout goals odd or even (no goals = even) |
| Penalty Shootout – Correct Score | Exact shootout score |
| Nth Penalty Scored (match market) | Whether the Nth in-match penalty is scored — a different market from the shootout version above |

## 16. The A–Z index — every market in the manuals

Every market heading carried in the two manuals (SportyBet Nigeria + football.com — the same
document family), grouped by family, one line each. If a market exists in the book, it is
here; the sections above give the deep settlement rules for the families that have them.
Pattern variants (Home/Away, 1st/2nd half, interval versions) are named in full.

### Result markets

| Market | You are predicting |
|---|---|
| 1X2 | Home / Draw / Away in regular time |
| 1X2 – 1UP / 2UP | Your team paid as winner the moment it leads by 1 / by 2 (see §6); team versions: Home team 1UP, Home team 2UP, Home team 3UP, Away team 1UP, Away team 2UP, Away team 3UP, Any team 3UP |
| 1X2 – Never Down | Your team wins without ever trailing (see §6) |
| Double Chance | Two of the three results in one pick: 1X, 12, X2 |
| Double Chance 1UP | Double Chance paid early the moment your team leads at any point; otherwise settles as a normal Double Chance |
| Draw No Bet | Match winner; a draw voids |
| Home No Bet | Match result; a home win voids |
| Away No Bet | Match result; an away win voids |
| Handicap (European, 3-way) | Winner after the bracketed goal start is added to a team's score |
| Asian Handicap | Winner against a split-capable handicap (full table in §6) |
| Half Time/Full Time | The result at half-time **and** at full-time, one selection |
| Half Time/Full Time Correct Score | The correct score at half-time **and** at full-time |
| Rest Match Winner | The result from the moment of betting — the score restarts 0–0 |
| To Qualify | Which team advances (see §15) |
| Winning Method | Winning team and method (see §15) |
| Winning Margin | The exact goal difference of the win |
| Nth Goal & 1X2 | Which team scores the Nth goal **and** who wins the match |

### Goal totals

| Market | You are predicting |
|---|---|
| Over/Under | Total goals vs a line (full settlement table in §4) |
| Home Team Over/Under / Away Team Over/Under | One team's total goals vs a line |
| Exact Goals | The exact total goals (0, 1, 2, 3, 4, 5+) |
| Home Team Exact Goals / Away Team Exact Goals | One team's exact total |
| Multigoals | How many goals will be scored, in the book's bands |
| Home Multigoals / Away Multigoals | One team's goal band |
| Multiscores | The final score, chosen from grouped scorelines |
| Goal Range | Total goals inside a chosen range |
| Goal bounds / Goal bounds - Home / Goal bounds - Away / Goal bounds - 1st Half | Total goals of the named scope fall inside a set goal range |
| Excluded goals / Excluded goals - Home / Excluded goals - Away / Excluded goals - 1st Half | A bet **against** a specific number of goals — that exact total must not happen |
| Odd/Even | Total goals odd or even; no goals counts as even |
| Home Team Odd/Even / Away Team Odd/Even | One team's goals odd or even (0 = even) |
| Both Halves Over x.5 | Goals in **each** half finish over the given line |
| Both Halves Under x.5 | Goals in **each** half finish under the given line |

### Scoring, teams and clean sheets

| Market | You are predicting |
|---|---|
| GG/NG | Both teams score (GG) or at least one doesn't (NG) — see §6 |
| 1st/2nd Half GG/NG | GG/NG scoped to the named half |
| Teams to Score | Which team(s) will score: home only, away only, both, neither |
| Home Team Clean Sheet / Away Team Clean Sheet | The named team concedes nothing |
| Home Team to Win to Nill / Away Team to Win to Nill | The named team wins **and** keeps a clean sheet (manual spelling) |
| Win to Nil | A team wins and concedes nothing (see §6) |
| Home Team to Score Both Halves / Away Team to Score Both Halves | The named team scores at least once in each half |
| 1st Goal | Which team scores the match's first goal — or None (see §5) |
| Next Goal | Which team scores the Nth goal |
| Last Goal | Which team scores the match's last goal |
| Next Scoring Type | The kind of the next goal (full definitions in §5) |
| Correct Score | The exact full-time score |

### Goal timing and intervals

| Market | You are predicting |
|---|---|
| When Will the Nth Goal Be Scored (10 min interval) | The 10-minute interval in which the Nth goal lands |
| When will the 1st goal be scored (10 / 15 min interval) | The interval of the first goal — or None = a goalless match (see §5) |
| 5/10/15 minutes – 1X2 from a to b | The result inside that minute window (see §3) |
| 1X2 – Intervals of 10 Minutes | The cumulative 1X2 from minute 1 to each 10-minute boundary (see §3) |
| 5/10/15 minutes – Nth Goal from a to b | Which team scores the Nth goal inside the window (or None) |
| 5/10/15 minutes – Over/Under from a to b | Total goals inside the window vs a line — Under 0.5 = the no-goal play (see §3) |
| Total Goals Over/Under from 1 to X minute | Cumulative goals by minute X vs a line (live only, see §3) |
| 1 minute – Over/Under from a to b | Total goals inside a single named minute vs a line |
| 1 minute – Over/Under Corners from a to b | Corners inside one minute vs a line |
| 1 minute – Over/Under Bookings from a to b | Bookings inside one minute vs a line |
| 1 minute – Over/Under Offsides from a to b | Offsides inside one minute vs a line |
| 1 minute – Over/Under Penalties from a to b | Penalties inside one minute vs a line |

### Halves

| Market | You are predicting |
|---|---|
| 1st Half – 1X2 / 2nd Half – 1X2 | The named half's result, on that half's goals only |
| 1st Half – Double Chance / 2nd Half – Double Chance | Double Chance within the half |
| 1st Half – Draw No Bet / 2nd Half – Draw No Bet | Half winner; a drawn half voids |
| 1st Half – Handicap / 2nd Half – Handicap | Half winner with the bracketed start |
| 1st Half – Over/Under / 2nd Half – Over/Under | Total half goals vs a line |
| 1st Half – Home Team Over/Under / 1st Half – Away Team Over/Under | One team's 1st-half goals vs a line |
| 2nd Half – Home Team Over/Under / 2nd Half – Away Team Over/Under | One team's 2nd-half goals vs a line |
| 1st Half – Exact Goals / 2nd Half – Exact Goals | Exact goals in the half |
| 1st Half – Home Team Exact Goals / 1st Half – Away Team Exact Goals | One team's exact 1st-half goals |
| 1st Half – Correct Score / 2nd Half – Correct Score | Exact score of the half |
| 1st Half – Multigoals / 2nd Half – Multigoals | Goal band of the half |
| 1st half – Odd/Even / 2nd Half – Odd/Even | Half goals odd or even (0 = even) |
| 1st Half – GG/NG / 2nd half – GG/NG | Both teams score inside the half |
| 1st half – Home Team Clean Sheet / 1st half – Away Team Clean Sheet | Clean sheet in the 1st half |
| 2nd Half – Home Team Clean Sheet / 2nd Half – Away Team Clean Sheet | Clean sheet in the 2nd half |
| 1st Half – Which Team Will Win the Rest | The rest of the 1st half from the moment of betting, score restarted |
| 1st Half – Nth Goal / 2nd Half – Nth Goal | Which team scores the Nth goal of the half |
| Home Team to Win Both Halves / Away Team to Win Both Halves | The named team outscores the opponent in **both** halves |
| Home Team to Win Either Half / Away Team to Win Either Half | The named team wins at least one half |
| Highest Scoring Half | Which half produces more goals (1st / 2nd / equal) |
| Home Team Highest Scoring Half / Away Team Highest Scoring Half | The half in which the named team scores most |

### Corners

| Market | You are predicting |
|---|---|
| Corners – 1X2 | Which team takes more corners (corners count when taken — §8) |
| Nth Corner / Last Corner | Which team takes the Nth / the last corner |
| Corner Handicap | Most corners with the bracketed start |
| Corners – Over/Under | Total corners vs a line |
| Home Team Corners – Over/Under / Away Team Corners – Over/Under | One team's corners vs a line |
| Corner Range / Home Team Corner Range / Away Team Corner Range | Corners fall inside a range (match or one team) |
| Odd/Even Corners | Total corners odd or even (0 = even) |
| Race to X Corners | Which team reaches X corners first |
| 1st Half – Corner 1X2 / 1st Half – Nth Corner / 1st Half – Last Corner / 1st Half – Corner Handicap | The corner markets scoped to the 1st half |
| 1st Half Corners – Over/Under / 1st Half – Home Corners Over/Under / 1st Half – Away Corners Over/Under | Corner totals vs lines, 1st half |
| 1st Half – Home Exact Corners / 1st Half – Away Exact Corners | One team's exact 1st-half corners |
| 1st Half – Corner Range / 1st Half – Odd/Even Corners | Range / odd-even of 1st-half corners |
| 1st Half – Race to X Corners | First to X corners inside the 1st half |
| 5/10/15 minutes – Corners 1X2 from a to b | Most corners inside the window |
| 5/10/15 minutes – Xth Corner from a to b | Which team takes the Xth corner inside the window |
| 5/10/15 minutes – Corner Handicap from a to b | Window corner winner with a start |
| 5/10/15 minutes – Corners – Over/Under from a to b | Window corner total vs a line |
| 5/10/15 minutes – Home Corners – Over/Under from a to b / 5/10/15 minutes – Away Corners – Over/Under from a to b | One team's window corners vs a line |
| 5/10/15 minutes – Odd/Even Corners from a to b | Window corners odd or even |

### Bookings

Counting law for the whole family is the table in §8 (yellow 1 card / 10 pts, red 2 / 25,
max 3 / 35 per player).

| Market | You are predicting |
|---|---|
| Booking 1X2 | Which team receives more bookings |
| 1st Booking | Which team is booked first — Home / None / Away |
| Nth Booking | Which team receives the Nth booking |
| Total Bookings | Total bookings (cards) vs a line |
| Total Booking Points | Total booking points vs a line |
| Home Team Total Bookings / Away Team Total Bookings | One team's bookings vs a line |
| Exact Bookings / Home Team Exact Bookings / Away Team Exact Bookings | The exact number of bookings (match or one team) |
| Booking Point Range | Total booking points fall inside a range |
| Sending Off / Home Team Sending Off / Away Team Sending Off | A player is sent off (match, or for the named team) |
| 1st Half – Booking 1X2 / 1st Half – Nth Booking / 1st Half – Total Booking Points / 1st Half – Total Bookings | The booking markets scoped to the 1st half |
| 1st Half – Home Team Total Bookings / 1st Half – Away Team Total Bookings | One team's 1st-half bookings vs a line |
| 1st Half – Exact Bookings / 1st Half – Home Team Exact Bookings / 1st Half – Away Team Exact Bookings | Exact 1st-half bookings (match or one team) |
| 1st Half – Booking Point Range / 1st Half – Sending Off / 1st Half – Home Team Sending Off / 1st Half – Away Team Sending Off | Range and sendings-off, 1st half |
| 5/10/15 minutes – Booking 1X2 from a to b | More bookings inside the window |
| 5/10/15 minutes – Total Bookings from a to b | Window bookings vs a line |
| 5/10/15 minutes – Sending Off from a to b / 5/10/15 minutes – Home Team Sending Off from a to b / 5/10/15 minutes – Away Team Sending Off from a to b | A sending-off inside the window |

### Player markets

Settlement starts from the stat definitions in §9 and the participation / no-start rules
there. Every market below is per named player.

| Market | You are predicting |
|---|---|
| First Goalscorer / Anytime Goalscorer / Last Goalscorer / Nth Goalscorer | The player scores the first / any / last / Nth goal (own goals: §9) |
| First To Score for Their Team | The player scores his team's first goal |
| To Score in First 10 Mins | The player scores inside the first 10 minutes |
| Player To Score In 1st Half / Player To Score In 2nd Half / Player To Score in Both Halves | The player scores in the named half / in each half |
| Player to Score 2+ / To Score or Assist / To Score and Assist | The player's goal-assist combinations |
| To Score a Header / Player To Score a Free-Kick | The goal is scored with a header / from a direct free kick |
| Player To Score with Right Foot / Player To Score with Left Foot | The goal is scored with the named foot |
| Player Score from Outside Box | The goal is scored from outside the area |
| Player Goals / Player Assists | The player scores / assists at all in regular time (lines versions exist as totals) |
| Player Shots / Player Total Shots | The player's total shots vs a line (definition: §9) |
| Player Shots on Target / Player Total Shots On Goal | Shots on target vs a line |
| Player Shots on Target from Outside Box | SoT from outside the box vs a line |
| Player Right Foot Shots on Target / Player Left Foot Shots on Target | SoT with the named foot vs a line |
| Player 1st Half Shots on Target / Player 2nd Half Shots on Target / Player Shots on Target Each Half | SoT in the named half / in each half |
| Player Total Attempted Passes / Player Total Passes / Player Passes | Attempted passes vs a line (definition: §9) |
| Player Tackles / Player Total tackles | Tackles vs a line (definition: §9) |
| Player Fouls | Fouls committed vs a line |
| Player Offsides | Offsides vs a line |
| Player Steals | Steals vs a line |
| Player Saves | Goalkeeper saves vs a line |
| Player To Be Carded / First Player Booked | The player is carded / is the first player carded |
| Player Not to Score | The player does **not** score (voids if he doesn't start — §9) |
| Player H2H | One named player out-performs another on the paired stat (voids if either doesn't start — §9) |
| Posts and Crossbars (player/team) | Shots hitting woodwork — a woodwork shot that goes in counts as a goal, not woodwork |

### Combination markets

The "&" family needs **both** legs; the "or" family needs **either** leg (see §11).

| Market | Legs |
|---|---|
| 1X2 & GG/NG | Result + both teams score |
| 1X2 & Over/Under | Result + total goals vs a line |
| Over/Under & GG/NG | Total goals line + both teams score |
| Double Chance & GG/NG / Double Chance & Over/Under | Double Chance + the named second leg |
| Double Chance & 1st Half GG/NG / Double Chance & 2nd Half GG/NG | Double Chance (match) + GG/NG in the named half |
| 1st Half – Double Chance & GG/NG / 2nd Half – Double Chance & GG/NG | Half Double Chance + half GG/NG |
| 1st Half – 1X2 & GG/NG / 1st Half – 1X2 & Over/Under | 1st-half result + the named second leg |
| 2nd Half – 1X2 & GG/NG / 2nd Half – 1X2 & Over/Under | 2nd-half result + the named second leg |
| Half Time/Full Time & Over/Under | HT/FT + match total vs a line |
| Half Time/Full Time & 1st Half Over/Under | HT/FT + 1st-half total vs a line |
| Half Time/Full Time & Exact Goals | HT/FT + exact match goals |
| Home Team or Over Goals / Home Team or Under Goals | Home win **or** the goals line lands |
| Draw or Over Goals / Draw or Under Goals | Draw **or** the goals line lands |
| Away Team or Over Goals / Away Team or Under Goals | Away win **or** the goals line lands |
| Home Team or GG/NG / Draw or GG/NG / Away Team or GG/NG | The result leg **or** both teams score |
| Home Team or Any Clean Sheet / Draw or Any Clean Sheet / Away Team or Any Clean Sheet | The result leg **or** either team keeps a clean sheet |

### Overtime and penalty shootouts

The full family is tabled in §15: Overtime & Goal, Overtime – 1X2, Overtime – Nth Goal,
Overtime – Over/Under, Overtime – Handicap, Overtime – Correct Score, Overtime – Which Team
Will Win the Rest, Overtime 1st Half – 1X2 / Overtime 1st Half – Handicap / Overtime 1st Half – Correct Score, Will There Be
Overtime, and the twelve Penalty Shootout markets (Winner, Winner & Over/Under, Winning
Margin, Over/Under, Exact Goals, Odd/Even, Nth Penalty Scored, Nth Goal, Home/Away
Over/Under, Home/Away Odd/Even, Correct Score).

### EarlyWin (football.com, pre-match only)

The full family is tabled in §10: 1X2 (1UP), 1X2 (2UP), team 1UP/2UP/3UP, Double Chance (1UP),
DrawSave, Over/Under (GoalRush), Over/Under EarlyGoals (the football.com manual's name for
the early ladder — Over 1.5 needs 1 goal by 10′, Over 2.5 needs 2 by 30′, Over 3.5 needs 3
by 50′), Home/Away Over/Under EarlyGoals, and To Lead by 1 / 2 / 3 Goals at Any Time.

---

*Sources: football.com How to Play — Football & General Settlement pages; SportyBet Nigeria
How to Play — Football & General pages (both archived in `docs/manuals/`); live and pre-match
market catalogues captured 2026-11-07 on football.com/ng. Prices quoted in this handbook are
observations from that day, not standing odds.*
