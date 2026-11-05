# Kernstown 1862 (CivilWar1): a Must Attack scenario

`mKernstown1862_CW1.json` is a First Kernstown (23 March 1862) scenario for *Sekigahara 1600: Must Attack!*. It is in the same format the game's Wargame Maker exports. `build_kernstown_ma.py` generates it from this repo's Kernstown map data.

**Status: v3.9, not tested in the game.** v3.9 is a look pass plus one name: new counters (cloth plates with an engraved double rule, numbered brigade bands, OR-attested colours, elite frame and star, gun and rank plates, strengths on cream cartouches; see Counters), Major Hotchkiss's "plate pass" on the board art (hachures over a sepia slope wash, watercolour washes, period lettering, a References panel), and the Danville battery renamed Lanier Danville (Archivist ruling, OR 12/1 p.408). No rule, strength, standby group, terrain or victory value changed. v3.8 and v3.8.1 change only the board art: Major Hotchkiss's engraved-detail pass, then two fixes (marsh tufts only on the game's marsh hex, a clearer Hoge Run). v3.7 is the last change to the rules and data. v3.7 answers playtest 5 (v3.5): Jackson can now withdraw off the south edge (Confederate exit hexes where the Valley Turnpike and the Middle Road leave the board, 1 point per CS exited, in Second Bull Run's format), Sullivan's 39 IL joins the rest of its brigade in standby group 2, and `carryover.py` with `CAMPAIGN_CARRYOVER.md` reads a save's surviving, exited and eliminated strength to seed a next scenario. The CRT, retreat rules, doctrines, terrain types and portraits are unchanged, and winLine 45 and thresholds 5/40/81 do not move. v3.6 folds in three staff reviews of v3.5 (`staff_notes/`): briefing corrections against the Official Records (archivist), counter strengths, names and elite picks from the OR (quartermaster), and a quieter, period-correct board art (Hotchkiss). v3.5 was a polish pass on v3.4: a reachable Union strategic victory, a Middle Road objective at the south end of Sandy Ridge, elite (surprise) brigades on both sides, a finished title cartouche, compass rose, scale bar and Winchester street plan on the board art, and briefing fixes. The CRT, retreat rules, AI doctrines, terrain types and standby groups are as in v3.4 (v3.6 changes none of them). v1 to v3.3 loaded and ran in the game (playtests 1-4). Playtest 4 (v3.3, all 11 turns) lost 11 units, 9 of them to a retreat with nowhere to go. Replaying the four saves showed the main cause: the engine never retreats a unit into a `mountain` hex, and our ridge was mountain. v3.4 writes the ridge as `rough` (same x2 defence and 2 MP), makes forced attacks at poor odds usually stall, and gives Jackson a Steady AI. Both files pass `validate_kernstown_ma.py`. Nothing in v3.4, v3.5 or v3.6 has been played yet.

| File | What it is |
|---|---|
| `mKernstown1862_CW1.json` | The scenario with painted board art (12.9 MB, UTF-8, no BOM) |
| `mKernstown1862_CW1_noart.json` | The same scenario without `boardArt` (6.5 MB). Use it if the art fails to load or does not line up. Everything else matches the main file. |
| `DEV_WISHLIST.md` | What we would like the game to add, written for the developer |
| `build_kernstown_ma.py` | Rebuilds both files from `data/` |
| `board_art.py` | Paints `meta.boardArt` on the Must Attack grid |
| `ma_grid.py` | The Must Attack hex grid: odd-r pointy-top, edges 0=E, 1=SE, 2=SW, 3=W, 4=NW, 5=NE |
| `validate_kernstown_ma.py` | Checks a scenario against the stock scenarios |
| `carryover.py` | v3.7: prints each side's surviving, exited and eliminated strength per unit from a save (see `CAMPAIGN_CARRYOVER.md`) |
| `CAMPAIGN_CARRYOVER.md` | v3.7: how to read a save's Units, Eliminated and Exited lists to seed the next scenario |
| `render_preview.py` | Draws `preview.png` (whole board), `preview_zoom.png` (Sandy Ridge to Kernstown) and `preview_counters.png` (all 29 counters). The previews are assembled from the file. They are not game screenshots, and the hex-name font in them is our guess. |

## Install

We have not confirmed where the game keeps scenario files.

1. Find the folder that holds the stock scenarios (for example `antietam1862.json`), or the folder where the Wargame Maker saves its exports.
2. Copy `mKernstown1862_CW1.json` into that folder. Copy `mKernstown1862_CW1_noart.json` too if you want the fallback.
3. Start the game and load **Kernstown 1862 (CivilWar1)** from the scenario list or the Wargame Maker.
4. If it is not listed, import it from the Wargame Maker, and report what happened.

Do not overwrite `user_kernstown1862.json`. It is the user's own file, and these files have different names.

## What to test first

1. **Retreats onto the ridge.** Sandy Ridge, Pritchard's Hill and the wall are now `rough`. A unit beaten next to the ridge should fall back onto it instead of being destroyed. Count the units lost to a retreat with no open hex; playtest 4 lost 9.
2. **Poor-odds attacks stall.** At 1:3 to 1:1 most rolls should give C. Only a 1 (at 1:3, a 1 or 2) repulses the attacker, and 1:1 on a 6 still drives the defender back.
3. **Jackson's AI (Steady).** Does it hold the wall and Glass Farm instead of pushing a lone brigade north onto the ridge, as the Aggressive AI did with Garnett 5/33 on turn 1 of playtest 4?
4. **Standby triggers.** Save on turn 1 and check that Confederate units carry `StandbyGroup` 1-4 and `StandbyActive` false. Then watch: does Burks come on in the same turn Tyler does (and the other way round)? Does Ashby stay put while Sullivan's 13 IN/5 OH stands within 4 hexes, and move once it leaves? The guns on both ridges should fire but never move unless an enemy comes next to them.
6. **Withdrawal (v3.7).** Move a Confederate unit onto a south-edge exit hex beside the Valley Turnpike (11-13,35) or the Middle Road (0-2,35) and exit it. Report: is there an exit command or does it leave on its own; does `Exited` in the save list it; does the score change by its CS (and in which direction); does the AI Jackson ever exit on its own, and when. See "Withdrawal" under Victory.
5. **Replacements.** Playtest 4 confirmed them: Marye's battery, destroyed by an AE, came back as "Replacements ①" at CS 2, six hexes back, with Marye's counter art. With v3.4's table only a DE at 5:1 or 6:1 can make one, so they will be rare.

The full checklist is at the end of this file.

## The scenario at a glance

- **Board.** 32 x 36 hexes, about 300 m a hex, from beyond Sandy Ridge east to Opequon Creek and from Bartonsville north to Winchester.
- **Turns.** 11 turns of 30 minutes. Turn 1 is 3/23 at 14:00. The Confederates move first (`firstMove: "second"`).
  - Turn 10 (18:30) falls in twilight. Turn 11 (19:00) is a night turn (`night_turns: [11]`), and the game ends after it.
  - We computed the light for Winchester on 23 March 1862 (NOAA formula, local mean time): sunset 18:14, civil dusk 18:41. The briefing rounds these to 6:15 and 6:40.
- **Activation.** Union 5, rising to 7 from turn 5; Confederate 6.
- **AI personality.** `doctrine: {blue: "def", red: "std"}`: Cautious Union, Steady Confederates (v3.4). In playtest 4 the Aggressive (`off`) Jackson pushed Garnett 5/33 alone onto the ridge north of the wall on turn 1, and lost it on turn 2. Historically Jackson's line held the stone wall and struck at what came at it. `std` is the stock word for that: Gettysburg gives it to Meade's Union, holding Cemetery Ridge and counterattacking locally, against Lee's `off`. `line` belongs to Antietam's attacking Union, so it fits less well. Kimball stays Cautious: his units went forward because they were in contact, and Tyler and Sullivan come on through the standby triggers.
- **Replacements** on (`rules.replacement: true`, as Gettysburg).
- **Retreat rules.** `retreat_control` 0, `retreat_distance` 1, `zoc_exit_allowed` false and `full_move_entry_allowed` false. These are the only values any stock file uses. `stacking_limit` is 2.

### Victory

| Hex | VP | Start |
|---|---|---|
| Winchester (25,3) | 30 | Union |
| Pritchard's Hill (13,15) | 20 | Union |
| Kernstown (16,20) | 15 | Union |
| Stone Wall (10,19) | 15 | neutral |
| Middle Road (4,25) | 10 | Confederate (v3.5) |
| Bartonsville (12,32) | 10 | Confederate |

- **Command points.** Glass Farm (8,19), the west end of the wall, is +2 and Grade Junction (18,18), where the Cedar Creek Grade meets the pike, is +2. Both start neutral. (v3.2: Glass Farm was a 5-VP hex and the CP was "Wall" at (9,19); three names in a row ran together.)
- **Margin (editor help).** Objective points held minus the enemy's, plus strength destroyed minus strength lost. So losses now count one point per CS, and CS is doubled.
- **Middle Road (v3.5).** A 10-VP hex where the Middle Road crosses the south end of Sandy Ridge (the ridge core ends at (4,27)). It is a game objective, not a historical claim: it gives the Union a rear target behind Jackson's left that is as far from Kimball's start as Kernstown is from Jackson's. Without it, the Union's in-reach objective swing was 35 VP against Jackson's 85; with it, 55 against 85.
- **winLine 45** (v3.5 and v3.6; 55 before). v3.6's strength changes do not move it: it counts objectives only. That is the score if nothing changes hands: Union 65 minus Confederate 20. The builder asserts this, and the validator fails the file if winLine is not the status quo.
  - Jackson holds the wall until dark: about 30, a Confederate tactical result.
  - Kimball takes the wall and keeps his own ground, as happened historically: about 60, a Union tactical win.
- **Thresholds 5 / 40 / 81** (v3.6; 5 / 40 / 79 in v3.5, 7 / 58 / 116 before). They are 5%, 40% and 80% of the scarcer side's room past the line, where room = every objective held + the whole enemy force destroyed + no losses, measured from winLine. Union room = 100 + 46 − 45 = 101; Confederate room = 100 + 67 + 45 = 212; min 101 (v3.6 strengths: Union 67 CS, Confederate 46).
  - Why not the editor's guidance (5/40/80% of objectives + average CS, which fit the stock files)? That total assumes a line near the middle. Ours is the status quo, which is far toward the Union, so the guidance strategic (116 in v3.4, 125 now) was beyond the Union's best possible margin (79 in v3.4). The validator warned about it; it now fails any unreachable level, and there is none.
  - What each level needs, counting only plausible objectives (Winchester excluded for Jackson): Union strategic = the wall, Middle Road and Bartonsville + 26 CS net (57% of Jackson's force); Confederate strategic = Pritchard's Hill and Kernstown + 11 CS net (16% of Kimball's). Operational: Union wall + Middle Road + Bartonsville (+55), or wall + Middle Road (+35) and 5 CS net; Jackson wall + Kernstown (−45 against the line) with no CS needed.

### Withdrawal (v3.7)

Playtest 5 lost Burks's 21 VA/1 Bn and 42 VA together on a blocked DR (turn 9, (17,20)), Marye's battery alone (turn 10, (16,21)) and Brodhead's cavalry; the owner asked for a way for Jackson to withdraw when the Union is overwhelming, as he did, and to decide afterwards what comes next.

- **Exit hexes** (`hex.exitHex` second = true, plus `boxes[19]` = 1): (11,35), (12,35), (13,35), where the Valley Turnpike leaves the south edge toward Newtown and Strasburg, and (0,35), (1,35), (2,35), where the Middle Road leaves. Only the Confederates may exit. The road hex is the middle one of each three. None carries VP or CP, and none is impassable ((0,35) is rough, the rest plain). The board art marks both with a small arrow and an italic legend one row in, so the exit row itself is clear.
- **Points:** `rules.exit_points_per_cs` {"first": 0, "second": 1}: one point per CS exited, for the Confederates only. `rules.exit_sudden_death_cs` {"first": 0, "second": 0}. Every unit keeps `exitPoints` 0.
- **Why this form and these values (stock evidence).** Second Bull Run is the only stock file that uses exits: `exit_points_per_cs` {"first": 1, "second": 0}, `exit_sudden_death_cs` {"first": 0, "second": 0}, four first-side exit hexes (51,16)-(51,19) on the east edge just south of where the Warrenton Turnpike leaves toward Centreville (Pope's line of retreat), each with `boxes[18]` = 1, and `exitPoints` 0 on every unit. Gettysburg carries both rules keys as 0 and no exit hexes; no other stock file has them. We copy Second Bull Run: dict form, the retreating side only, 1 per CS, sudden death off, exits by the road the army really left on. `boxes[19]` for the second side is inferred from the pairs 10/11 (VP) and 16/17 (CP).
- **Why 1 per CS, not more.** The engine's exact arithmetic is not documented (DEV_WISHLIST 23). Two readings: (A) an exited unit is simply safe (not counted as lost) and its points are added for Jackson; (B) losses are initial CS minus CS on the board, so exiting counts as a loss and the points refund it. Worked cases at 1 per CS (Union holds every objective = 100 before strength):
  - Battered army: Jackson has lost 20 CS and the Union 8; 26 CS left. Destroyed in place: 100 + 46 − 8 = 138, Union strategic. Withdrawn: 86 (A) or 112 (B), Union operational in both. Withdrawing in good order beats dying in place.
  - Full early withdrawal, Union follows and takes everything: 54 (A) or 100 (B), a Union victory in both. Fighting it out at the wall (about 30) is a Confederate win, so an early walk-off does not beat fighting.
  - At 2 per CS, (A) would make a full withdrawal score 8 and the battered case 60, close to a draw, which rewards leaving at once; so 1.
  - Known risk, reading (A) only: if Jackson marches everything off and the Union never advances, the score is about 45 − 46 = −1, a Confederate win. That needs the Union to sit still for 11 turns; test item 6 checks how the engine scores exits, and DEV_WISHLIST 23 asks the developer.
- **Victory numbers do not move.** Exits can only add to the Confederate room (212, or 258 counting every Confederate CS exited under reading A); the Union room (101) stays the smaller, so winLine 45 and thresholds 5/40/81 stand. The builder still checks the briefing against the file.
- **After the battle.** The strength that exits, plus what is still on the board, is what Jackson carries into the next fight: `python3 carryover.py SAVE.json` (see `CAMPAIGN_CARRYOVER.md`).

### Order of battle

v3.3: every strength below is doubled in the file (`CS_SCALE = 2` in the builder), so one point is about 150 men (`scaleMen` 150). The figures below are the pre-scale values; multiply by 2. v3.6 allows halves (x.5), so the file values are whole numbers. A typical battery is CS 2 (4 in the file) and Chew's horse battery CS 1 (2). Guns have MP 3 and range 3, infantry MP 4, cavalry MP 6. HQ counters are CS 1 (2), MP 4. `S#` is the standby group.

**Union, Kimball (Shields' division), side 0.** v3.2: every battery starts stacked with one non-artillery unit.
- Pritchard's Hill: 14 IN/84 PA 3 + Jenks A 1 WV Bty 2.5 (12,16); Kimball's HQ + Robinson L 1 OH Bty (13,16); 8 OH/67 OH 3 + Clark E 4 US Bty 2.5 (13,17). v3.6: Jenks and Clark had the Parrotts that did the day's execution (Daum, OR 12/1 p.359).
- Sullivan: 62 OH 2 + Keeper B 1 WV Bty 1 (18,14) S2/S4 (v3.6: one section only, Daum p.359; Keeper as its commander is not in the OR, provisional); 13 IN/5 OH 3 (18,20) S2; 39 IL 1 (22,6) S2 (v3.7; S3 before) + Huntington H 1 OH Bty (22,6) S3
- Brodhead: 1 MI Cav 1 (6,12), WV/OH/MD/PA Cav 1.5 (18,21) (v3.6: was "OH/MD Cav" 1; the engaged non-Michigan companies included the PA squadron and six companies of the 1st (W.) Va Cav, OR p.355)
- Tyler: 7 OH/29 OH 3 (19,12), 7 IN/1 WV 3 (20,10), 110 PA 2 (21,8), all S1
- Union guns on and near Pritchard's Hill are S4; the HQ is S3.

**Confederate, Jackson (Valley District), side 1:**
- Jackson's HQ: Valley District HQ (11,26) S4
- Ashby 7 VA Cav 1 + Chew Horse Bty 1 (20,24) S2
- Sandy Ridge: Fulkerson 23/37 VA 2 + Carpenter Alleghany (9,21); Garnett 5/33 VA 2 + McLaughlin Rockbridge 3 (12,20); Garnett 2/4/27 VA 2.5 + Waters W. Augusta (11,22). The guns are S3. v3.6: Rockbridge had 8 pieces (pp.396-397); 2nd Va 320 + 4th Va 203 + part of the 27th (pp.389, 391).
- Burks: 21 VA/1 Bn 1.5 + Pleasants Hampden (13,28); 42 VA 1 + Lanier Danville (14,29); all S1. v3.6: 21st Va 270 + 1st Va Bn 187 (pp.403, 407); Marye's battery was under Lt. Pleasants on the field (Burks p.401); Jackson calls the Danville battery Shumaker's (p.380), while Fulkerson names Lt. Lanier (p.408). v3.9 (Archivist ruling): the counter is Lanier Danville, as Fulkerson has Lanier commanding on the field and "Shumaker's battery" is the captain's name; the briefing gives both.

The one battery not stacked with infantry is Robinson, which shares Kimball's HQ hex (the HQ is a CS 1 headquarters and escort, CS 2 in the file). Chew is with Ashby's cavalry, as a horse battery.

Confederate batteries are named for their batteries (Rockbridge, Hampden and so on). Union batteries are named by letter and regiment, which is how each side knew them. Every unit name is commander + " " + unit (`boxes[3]` + `boxes[4]`), as in every stock file, and `boxes[5..7]` repeat CS, MP and range. The validator checks this.

**Standby groups are numbered per side (v3.2 finding, high confidence).** A unit's `standbyGroup` n is the n-th entry in `rules.standby_groups` whose `side` is the unit's side, not the n-th entry overall. Evidence:
- Malvern Hill lists [side 0, side 0, side 1, side 1, side 1]; its side-1 units use groups 1-3.
- Second Bull Run lists [side 1, side 0]; units of both sides use group 1.
- Seven Pines has one side-1 entry, used by side-1 units as group 1.
- v3/v3.1 gave Confederate units groups 4 and 5. Side 1 had only two entries, and in the playtest 2 and 3 saves every Confederate unit loaded with `StandbyGroup` 0 and `StandbyActive` true. So Ashby, Jackson's HQ, Burks and the Sandy Ridge guns were free from turn 1, which is how Ashby rode into Kernstown and Rockbridge and Carpenter walked forward to (12,18) and died. The Union groups 1-3 loaded correctly (inactive, groups 1/2/3).
- The validator now checks per-side numbering and prints each group's units.

v3.3 groups. Strengths are the doubled values in the file.

| Side | Group | Units | Join turn, chance / rise | Other triggers |
|---|---|---|---|---|
| Union | 1 | Tyler | 4 (15:30), 50 / 25 | Confederate group 1 (Burks) wakes; Union main body falls to 70% |
| Union | 2 | Sullivan 13 IN/5 OH, 62 OH, 39 IL (v3.7) | 6 (16:30), 30 / 25 | Confederate group 2 (Ashby) wakes; main body 60% |
| Union | 3 | Kimball HQ, Huntington | hold | main body 50% |
| Union | 4 | Jenks, Clark, Robinson, Keeper | hold | none |
| Confederate | 1 | Burks, Pleasants (Hampden), Lanier (Danville) | 5 (16:00), 40 / 30 | Union group 1 (Tyler) wakes; main body 70% |
| Confederate | 2 | Ashby, Chew | hold | containment: 4 hexes, 6 CS |
| Confederate | 3 | Rockbridge, Carpenter, Waters | hold | none |
| Confederate | 4 | Jackson HQ | hold | main body 50% |

How the triggers play:
- **Brigades move as one (v3.7).** Each brigade's counters share one group, so the AI wakes and moves them together; the validator fails a brigade split across groups. The only split was Sullivan's: 62 OH and 13 IN/5 OH in group 2 and 39 IL in group 3, so 39 IL moved to group 2. Not changed, on purpose: the batteries (held in groups 3-4 since v3.2, after playtest 2 lost guns that marched with their infantry), Kimball's HQ (the division HQ, not a brigade) and Lanier's Danville battery (Fulkerson's battery, held in Burks's reserve group as it was not engaged). Burks's two counters already share group 1 and start adjacent in the rear; playtest 5 lost them together at (17,20) after the AI marched the whole group east of the pike beside Kernstown on turns 6-7, which is routing, not a group split (DEV_WISHLIST 26).
- **Tyler and Burks are linked both ways.** Historically Jackson fed Burks in as Tyler struck the wall.
- **Ashby is held by containment.** He stays put while at least 6 Union CS stand within 4 hexes of him. At the start that is 13 IN/5 OH (6) and WV/OH/MD/PA Cav (3), 9 in all; 13 IN/5 OH alone still meets the 6. If Sullivan's infantry leaves for the west, Ashby is free to press up the pike. Sullivan in turn wakes when Ashby does.
- **Containment is used only for Ashby's group,** whose two units share a hex facing the enemy. For a rear group, the enemy strength in range is 0 from the start, so the rule would wake it at once. The validator checks that every containment group is satisfied at the start, counting both per unit and per group.
- **The guns are held for good.** The editor says standby units still fire, defend, exert ZOC and retreat. An enemy moving next to a held unit, or attacking it, wakes its group.

**Field meanings** (editor STANDBY FORCE panel, whose fields run in the same order as the keys of Malvern Hill's entries):

| Editor field | JSON key |
|---|---|
| Join turn | `turn` |
| Chance % | `chance` |
| Rise/turn % | `rise` |
| Containment range (hexes) | `guardHexes` |
| Containment strength needed | `guardCs` |
| Joins when main body falls to % | `mainForcePct` |
| Joins when opposing group activates | `enemyGroup` |

`enemyGroup` 0 means None. That n is the opposing side's n-th group, numbered per side like `standbyGroup`, is inferred: no stock file has a non-zero value. "Hold" is turn 0, chance 0. Standby only governs the computer; a human player can move any unit.

## Combat and survival

In playtest 2 the user lost Garnett's 5/33 VA again. The save shows an AR at 1:1 (die 2) with no open hex behind him. v3 changed three things to make that rarer.

**1. A gentler combat table (`rules.crt`).** Rows are odds and columns are the die roll, 1 to 6. A high roll favours the attacker. Every value is one the stock tables use. The table never gets worse for the attacker as the odds or the roll go up. Playtests 3 and 4 confirmed it is used in the game: every logged combat matches it.

v3.4 table. Playtest 4 showed that under the must-attack rule, units in contact attack at 1:3 to 1:1 every turn, and a repulse with nowhere to go destroys them. So at those odds a middle roll is now a stand-off.

| Odds | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| 1:3 | AR | AR | C | C | C | C |
| 1:2 | AR | C | C | C | C | C |
| 1:1 | AR | C | C | C | C | DR |
| 2:1 | AR | C | C | DR | DR | DR |
| 3:1 | C | C | DR | DR | DR | DR |
| 4:1 | C | DR | DR | DR | DR | DR |
| 5:1 | DR | DR | DR | DR | DR | DE |
| 6:1 | DR | DR | DR | DR | DE | DE |

Changes from v3.3, cell by cell:
- **1:3 on a 1: AE became AR.** A beaten 1:3 attack falls back instead of vanishing. This adds no kills.
- **1:3 on a 3, 4 or 5: AR became C.** A forced 1:3 attack usually stalls. A 1 or 2 still repulses it.
- **1:2 on a 2 or 3: AR became C.** Only a 1 repulses.
- **1:2 on a 6: DR became C.** A 1:2 attack no longer dislodges anyone, and 1:2 stays below 1:1.
- **1:1 on a 2: AR became C.** Only a 1 repulses.
- **Unchanged:** 1:1 on a 6 and 2:1 on a 4-6 stay DR, so the wall can still be taken at even odds and above. 2:1 and up are as before.

Chance of each outcome per column (100,000 simulated rolls per column; they match the exact sixths):

| Odds | v3.3: C / retreat / eliminated | v3.4: C / retreat / eliminated |
|---|---|---|
| 1:3 | 17% / 67% / 17% | 67% / 33% / 0% |
| 1:2 | 33% / 67% / 0% | 83% / 17% / 0% |
| 1:1 | 50% / 50% / 0% | 67% / 33% / 0% |
| 2:1 | 33% / 67% / 0% | same |
| 3:1 | 33% / 67% / 0% | same |
| 4:1 | 17% / 83% / 0% | same |
| 5:1 | 0% / 83% / 17% | same |
| 6:1 | 0% / 67% / 33% | same |

AE no longer appears; DE is in 3 cells (the default has 15).


**How we know the table's orientation.** We checked it against 40 logged combats: playtest 1 (13), playtest 2 (21), Gaines' Mill (4) and Waterloo (2). None of these scenarios has its own `crt`. Each cell below gives the Gettysburg/Chancellorsville table value, then "←" and each logged result (P1, P2, GM = Gaines' Mill, WL = Waterloo).
- All 37 combats outside a fortress hex match that table exactly. So the layout is `crt[odds row][die - 1]`, and the stock table is also the built-in default.
- The three mismatches (`*`) all involve fortress hex (11,19) in playtest 2. Twice the attacker stood in it and an AR became C. Once the defender held it and a DR became C.

| Odds | die 1 | die 2 | die 3 | die 4 | die 5 | die 6 |
|---|---|---|---|---|---|---|
| 1:3 | AE | AE | AR | AR ← AR P2 | AR | DR ← DR P1 |
| 1:2 | AE ← AE P1, AE P2 | AR ← AR P1, C P2* | AR ← C P2* | AR ← AR P1, AR P2, AR P2 | DR ← DR P1, DR P2 | DR ← DR P1, DR P2 |
| 1:1 | AR ← AR P1, AR P2, AR WL | AR ← AR P1, AR P2, AR P2, AR WL | AR | DR ← DR P2 | DR ← DR P1, DR P2, DR P2, DR GM | DR ← DR P1, C P2* |
| 2:1 | AR | C ← C P2 | DR ← DR GM | DR ← DR P2 | DR | DE ← DE P1, DE P2, DE GM |
| 3:1 | C | DR | DR | DR | DR | DE ← DE GM |
| 4:1 | DR | DR | DR ← DR P2 | DR | DE | DE |
| 5:1 | DR | DR | DR | DE | DE | DE ← DE P2 |
| 6:1 | DR ← DR P1 | DR | DE | DE ← DE P1 | DE | DE |

**2. The wall and the ridges are `rough` (v3.4), not `fortress` (v2) or `mountain` (v3-v3.3).**
- **Fortress.** Three fortress combats in playtest 2 suggest that a unit in a fortress never retreats, so its only bad result is DE (inferred).
- **Mountain.** We replayed every move in playtests 2, 3 and 4 against the board each was played on. Of 33 retreats, none ended in a mountain hex: they went to plain, forest, marsh, rough or wasteland. Nine units were destroyed by a retreat when the only hexes they could have entered (no enemy, no enemy ZOC, stack space) were mountain:
  - playtest 2: Garnett 5/33, Robinson's battery, 1 MI Cav;
  - playtest 4: Garnett 5/33, 14 IN/84 PA, Fulkerson, Garnett 2/4/27, 1 MI Cav, 7 OH/29 OH.

  Units could retreat off mountain, and they moved onto it normally. So the engine evidently will not retreat a unit into mountain (inferred, strongly). The stock mountain costs 4 MP; ours cost 2. Movement cost is not the reason, because forest and rough (3 MP) took retreats.
- **Rough.** It has the same x2 defence, and Antietam uses it for its ridges. Our record keeps cost 2. Rough took retreats in playtests 3 and 4. The builder still calls these hexes "mountain" internally, for the board art, and writes them as `rough` (`JSON_TERRAIN`). The validator now fails any `mountain` or `fortress` hex and leaves them out of the rear-room test.
- The fences on the wall's north edges stay.

**3. Room to retreat.** The validator fails any stack with fewer than 2 neighbouring hexes that are all of these:
- on the board and passable
- outside enemy ZOC
- not full
- strictly farther from the nearest enemy

All 29 counters pass.

**4. Batteries stacked, and the two-flank test (v3.2).** Every battery starts with one non-artillery unit, never two guns alone. For every stack within 8 hexes of the enemy at the start, the validator places imaginary enemy units on every pair of the stack's non-rear neighbour hexes, and fails the stack if those two could put every rear hex in ZOC. All 10 such stacks pass. Stacks stand side by side rather than one behind the other, so that no stack fills a neighbour's retreat hex.

**Not changed:**
- **Retreat settings.** A `retreat_distance` of 2 needs a longer clear path, so it would probably kill more units, not fewer. `zoc_exit_allowed` is about walking out of ZOC during movement, not about retreats. Units die when the only retreat hex is in enemy ZOC. The save's `ZocToZocAllowed` looks related, but scenario rules have no field for it. `retreat_control` 0 is "Owner chooses" (editor screenshot).
- **`replacement` is true (v3.3).** Editor help: a unit of CS 3 or more destroyed by an AE or DE falls back up to twice its movement, away from the enemy, and fights on at half strength, rounded down. A unit lost because it has no retreat, or that cannot fall back even one hex, gets no replacement, and neither does a destroyed replacement. All strengths are doubled, so 21 of 29 units are CS 3 or more, and the odds of every attack are unchanged. To be honest about the limits: this board's table has only 4 AE/DE cells of 48, and most losses come from blocked retreats, which get no replacement. So replacements are insurance, not a cure.
- **`eliteUnit` is on for two counters a side (v3.6; three in v3.5); `suddenDeathUnit` stays false.** Editor help: once per game, when an elite unit first attacks or is attacked, every elite unit of that side moves and attacks once more. Union: Tyler 7 OH/29 OH and Tyler 7 IN/1 WV; Kimball says Tyler "deserves the highest commendation" (OR 12/1 pp.360-361). Not 110 PA, which "broke and ran" on the extreme left (Copeland, pp.347-348). 12 of 67 CS (18%). Confederate: Fulkerson 23/37 VA, which held the wall and "merit special mention" (Jackson, pp.381-382), and Garnett 2/4/27 VA, whose 27th opened the infantry fight with the 21st (p.381). Not 5/33, since Garnett ordered the 5th back "before it met the enemy" (p.382). 9 of 46 CS (20%). The HQs are left out: Kimball's sits on Pritchard's Hill beside the guns, where a Confederate probe could spend the Union round on turn 1, and Jackson's is safe in the rear, which would make his round free. The user's own file marks Garnett's Stonewall Brigade as elite, which this follows. The validator prints both lists and fails if one side has elites and the other none, or if the counts differ by more than 1 or the CS shares by more than 10 points.
- **`ai_contact_gate`** (used only by Malvern Hill) is left out, because it might freeze the AI.

## The people

- **Commanders on the map.** Kimball and Jackson have HQ counters (CS 2 in the file) with their portraits, held back in standby (Union group 3, Confederate group 4).
- **Portraits.** All of them are approved files in `historical_data/portrait_manifest.csv` on `origin/main` (3b9808b). The builder reads each one with `git show`, crops and frames it, and embeds it in the JSON as a template image. No portrait file was copied into this branch, renamed, overwritten or regenerated. Set `MA_PORTRAIT_REF` to read them from another ref.

| Leader | File on origin/main | Blob | Used on |
|---|---|---|---|
| T. J. Jackson | `mdl_CSA_TJJackson.png` | fb3e728 | Valley District HQ; region map |
| R. B. Garnett | `mdl_CSA_RGarnett.png` | 78f7290 | 2/4/27 VA, 5/33 VA; battle map |
| T. Ashby | `mdl_CSA_TAshby.png` | 012659f | 7 VA Cav |
| N. Kimball | `reference/mdl_USA_NKimball.png` | 0aa272d | Div. HQ, 14 IN/84 PA, 8 OH/67 OH; battle map |
| E. B. Tyler | `reference/mdl_USA_EBTyler.png` | 2117a48 | 7 OH/29 OH, 7 IN/1 WV, 110 PA |
| J. C. Sullivan | `reference/mdl_USA_JCSullivan.png` | b79ea1f | 13 IN/5 OH, 62 OH, 39 IL |
| J. Shields | `reference/mdl_USA_JShields.png` | ca9784a | region map only (wounded on the 22nd) |

  The manifest lists Burks, Fulkerson and Brodhead as MISSING, so their counters have no portrait. Batteries keep the NATO mark.
- **Briefing maps.** `regionMap` ("The Lower Valley, Virginia, March 1862") and `battleMap` ("Kernstown, 23 March 1862") are period-style maps with a cartouche and portrait medallions. Their text labels are in `labels` and are drawn by the game.
- **Briefing text.** The description has these sections:
  - the opening: Ashby's faulty report, Shields' wound, and the forced march
  - one section for each side
  - the afternoon, turn by turn
  - how to win
  - combat
  - the order of battle with colonels
  - counters and sources

  Each historical claim comes from the sources listed below. The format allows one description per language, so both sides read the same text, and the English is copied into every language slot.

## Counters

Each counter shows:
- the commander on top, small
- the unit in large type, fitted between 3.0 and 4.6
- the commander's portrait, where one exists, beside a NATO mark (X infantry, / cavalry, dot artillery; III for a regiment, I for a battery). v3.2: the NATO box is filled with the branch colour (infantry blue, cavalry yellow, artillery red), so the type reads at map zoom
- HQ counters: the portrait in a gold frame (v3.2)
- CS bottom left and MP bottom right
- an "R3" plate on every battery

Union counters are blue with white text. Confederate counters are grey with near-black text (#111) and a light outline. To v3.8.1 these were the stock plates.

### v3.9 counter style

The default build (`MA_COUNTER_STYLE=v39`) draws the counters with `counter_style_v39.py`; which unit gets which mark is data in `counter_style_v39.json`, scoped by the Quartermaster's proposal (`staff_notes/quartermaster_counters_v39.md`, OR = OR Ser. I Vol. 12 Pt. 1). Still only the format's two shape types (`image`, `text`) with stock keys; every mark is a small embedded PNG. `MA_COUNTER_STYLE=v381` rebuilds the v3.8.1 counters (stock plates) to `*_v381.json`; the v3.8.1 files themselves are in git at 69d1fb2.
- **Plates.** Union blue wool (a 2/2 twill) and Confederate grey jean cloth with a butternut weft cast, both subtle, with an engraved double rule (dark cut, light lip). Same base colours as the stock plates (#253a69, #b5b0a1), so Hotchkiss's References key still matches. No gold on the plain plate: gold now means elite or HQ.
- **Brigade band** across the top with a numeral or letter that reads without colour: Union 1 Kimball (crimson), 2 Sullivan (gold), 3 Tyler (green), C Brodhead (orange), A Daum's Artillery Brigade (silver, all Union batteries, p.359); Confederate 1 Garnett (blue, with Rockbridge, Carpenter, Waters), F Fulkerson (burgundy, with Danville; no brigade number in the OR), 3 Burks (green, with Hampden), C Ashby (brown, with Chew). Brigade numbers from the OR (pp.346, 387, 400). The colours are a game aid, not a period marking: there were no corps badges in March 1862. HQs carry no band.
- **Elite:** a gold inner frame and a star on exactly the four `eliteUnit` counters (Tyler 7 OH/29 OH and 7 IN/1 WV, Fulkerson 23/37 VA, Garnett 2/4/27 VA). The validator fails if the marks and `eliteUnit` disagree.
- **Colours** only where the OR mentions them: a small 34-star national colour (canton drawn as dots) on Kimball 14 IN/84 PA (p.367), Sullivan 13 IN/5 OH (pp.351, 374), Tyler 7 OH/29 OH and 7 IN/1 WV (p.376); a staff and blank flag outline, no pattern, on Garnett 5/33 VA (p.392), Garnett 2/4/27 VA (p.388) and Burks 21 VA/1 Bn (p.406), since no OR report states the Confederate pattern.
- **Guns** only where the OR states them: PARROTT on Jenks and Clark (p.359); 8 GUNS Rockbridge (pp.396-397), 3 GUNS Chew (p.385), 1 SECTION Keeper's B 1 WV (p.359). Those batteries' branch box is a little smaller to make room. Every other battery has no gun mark.
- **Ranks:** Kimball's HQ has a COL. plate with a colonel's strap (sky-blue ground, silver eagle; 1861 US regulations para. 95; p.361); Jackson's HQ a MAJ. GEN. text plate only (p.384; the CS insignia graphic was dropped, its regulation page was not viewed).
- **HQ frame** is a bevelled gilt frame in the same slot; **strengths** sit on cream cartouches in dark ink on both sides.
- **Portraits** are the same embedded images (same `portrait_crop`, same keys, same x/y/w/h). Nothing regenerated, recoloured or re-cropped.
- Staff inputs drop in without code: edit `counter_style_v39.json`, or point `MA_COUNTER_OVERRIDES` at a JSON of the same shape, merged on top; `plates.<side>.texture` may name a texture PNG. The builder fails if the table and the unit list disagree.
- Sheets: `preview_counters_v39.png` (180 px), `counters_v381_vs_v39_60px.png` (real in-game scale: the art is 2 px per world unit and a counter is 30 units) and `counters_v381_vs_v39_180px.png` (3x). `preview_kernstown_ingame_scale.png` shows Pritchard's Hill, Kernstown and Sandy Ridge with the counters at that scale.

## Board and board art

- **Terrain** comes from the HoS layer (`data/layers/kernstown_game.json`), the painted forest fraction and the 3DEP DEM, sampled at 37 points per hex.
  - **High ground** is `rough` (2 MP, x2) in the file (v3.4; it was `mountain` before, which units cannot retreat into). A hex is high ground if its topographic position on the DEM is at least 6 m or the HoS layer tags it `hill`. The modern quarry is dropped.
  - **Woods** (`forest`, 3 MP, x1) where 40% or more of the hex is wooded, plus one added polygon north of the stone wall (ABT and Hotchkiss maps).
  - **Town** (`city`) is Winchester. **Hamlets** (`wasteland` art, plain movement and defence) are Kernstown and the farm clusters.
  - **Marsh** is one hex.
- **Roads** are the Valley Pike, the Middle Road and the Cedar Creek Grade. **Trails** are the Apple Valley Road and the stone lane. **Creeks** are Opequon Creek, Hoge Run, Abrams Creek and Buffalo Lick Run. All are symmetric centre-to-centre paths, as in the stock files.
- **The stone wall** is the eastern ~1.1 km of the repo's Glass-farm wall: four hexes at (8..11, 19). Each is high ground (`rough` in the file from v3.4) with fences on its NW and NE edges, facing north toward Tyler, as Antietam's Bloody Lane does.
- **Hex names** are drawn by the game:
  - VP hexes: Winchester, Pritchard's Hill, Kernstown, Stone Wall, Bartonsville
  - CP hexes: Glass Farm, Grade Junction
  - other named hexes: Sandy Ridge, Marcauley Farm, Pritchard Farm, Mahaney House, Triplett House, Opequon Church, Opequon Ford, Milltown

  The three farmhouses are placed from the ABT 2024 map and may be up to 1 hex off. The board art does not repeat any hex name.
- **Board art** (`meta.boardArt`, 5120 x 4959 PNG). The geometry is confirmed from Antietam's fence marks: `pixel = (world − origin) x scale`, world hex centre `(√3·45·(q + ½(r&1)), 67.5·r)`, `scale` 2, `hexSize` 45, origin `(−52.471, −58.5)`.
  - It shows the repo's painted basemap, washed toward parchment, with woods, ridge hachures, the wall stones, roads, creeks and buildings.
  - v3.2: hillshade (lit from the north-west) and 5 m form lines from the 3DEP DEM, so Sandy Ridge and Pritchard's Hill read as relief; a buff tint and hachures still mark the game's high-ground hexes. A faint patchwork of fields, rail fences around the farms, shadowed tree crowns, a wide pale macadam Valley Pike, a heavier two-course stone wall with a shadow, and farmsteads (house, red bank barn, outbuilding, orchard) at Glass, Pritchard and Marcauley farms, houses at Mahaney and Triplett, and a church at Opequon. Palette 128 colours (was 96), with the small feature colours reserved.
  - It has italic road and creek names.
  - v3.5: a period title cartouche in the empty south-east corner ("Map of the Battle of KERNSTOWN, Frederick County, Virginia, Sunday, 23 March 1862") with double ruled frame, rope border and corner rosettes, and two scale bars, yards and meters, 0-1,000 each. They are drawn at the board's scale: one hex centre to centre = 300 m = 155.9 px, so 1,000 m = 519.6 px and 1,000 yd = 475.1 px (measured on the PNG). A 16-point compass rose with a degree ring sits beside it. Both are east of the pike and south of Buffalo Lick Run, on hexes with no objective, name or starting unit. They replace v3.4's plain cartouche and triangle arrow.
  - v3.6 (Hotchkiss review): a quieter, period-correct sheet.
    - Relief: hillshade exaggeration 2.5 (was 4), shade gain 0.40, form lines lighter, high-ground tint 0.18 (was 0.30), hachures a sparser 1 px brown fringe.
    - Woods: leafless March woodlots in grey-brown (sparser, smaller crowns with open glades) instead of summer olive; marsh as a wet meadow with fine tufts.
    - Stone wall: a thin, smoothed light-limestone line (mortar edge, faint shadow, stone dots) joined along the fenced hexsides, instead of v3.2's heavy dark sawtooth. The validator now checks that the painted wall lies on every fenced hexside.
    - Buildings and orchard trees are masked off roads (44 px), creeks (30 px) and trails (20 px), as Winchester's are; one that would touch them moves to a clear spot within 60 px of its hex centre or is left out. Kernstown's hamlet buildings are set square to the pike.
    - Water and lanes: Opequon Creek at stream weight, the runs as one thin line, Buffalo Lick Run carried on to the Opequon; trails a fine opaque dash; a road or creek that ends on the board edge runs off it; the Valley Pike lightly smoothed.
    - Labels: the duplicate "Middle Road" road label is gone (the game names the VP hex); Cedar Creek Grade's label moved west off the wall; label halos opaque; the region map reads "Jackson, near 40 miles in two days".
    - Brown and ink colours kept; field patchwork in March tan and pale green; paper fully opaque. The cartouche is smaller (840 x 560) with the same title, and the compass is a plain 8-point rose. New colours are reserved in the 128-colour palette.
  - v3.5: Winchester is a street grid laid along the Valley Turnpike (its main street), with buildings on the block fronts and garden trees, kept off the pike and Abrams Creek. v3.4 drew rows of identical squares over the road and the creek.
  - `hash` is our PNG's SHA-1. `style` "acw_b" and `version` 1 are copied from Antietam.
  - If the basemap (78 MB, gitignored) is missing, the builder paints plain parchment instead.

## Retreat settings, checked in v3.4

Every stock scenario and every save we have uses the same values: `retreat_control` 0 (Owner chooses), `retreat_distance` 1, `zoc_exit_allowed` false. No combat has ever been logged under any other value. So none was changed. Each is left as a test:
- **Exit from ZOC (`zoc_exit_allowed`).** This is a movement rule in the editor. Saves carry a separate `ZocToZocAllowed` with no scenario key, which may be the retreat rule. Of playtest 4's 11 losses, 3 were truly blocked by enemy ZOC (Lanier; Jackson's HQ and 21 VA/1 Bn). Only those could be helped, and only if it also governs retreats. Test: set it to Allowed in the editor, then check whether a unit retreats from one enemy-ZOC hex into another.
- **Automatic retreat control.** The owner, or the AI acting for it, already picked an open hex in all 33 logged retreats. Every loss had no legal hex, so a different chooser cannot help. Not worth testing for losses.
- **Retreat distance 2.** A unit would have to clear two hexes. Every blocked loss failed at the first hex, so this can only add losses. Not recommended.
- **Ridge terrain.** This was the main lever: see "Combat and survival" item 2.

**Replacement names.** Playtest 4's one replacement was named "Replacements ①", not "Marye Hampden". It kept Marye's counter art (`TemplateId` local_27), CS 2 (half of 4), MP 3 and range 3, and appeared 6 hexes back (twice MP 3). No scenario key sets the name; it is in the wishlist. Lanier, CS 4 and destroyed by an AE a turn earlier, got no replacement. Every hex around Lanier was enemy-held or in enemy ZOC, which fits the editor's rule that a unit that cannot fall back even one hex gets none.

## Editor fields and JSON keys (v3.3)

From the user's editor screenshots and help text, matched to keys in the stock scenarios and saves. We only write keys seen in a stock file.

| Editor field | JSON key | Evidence | Confidence |
|---|---|---|---|
| Use replacements | `scenario.rules.replacement` (bool) | name; Gettysburg true, the others false | high |
| Retreat control: Owner / Attacker / Automatic | `rules.retreat_control` 0 / 1 / 2 | stock and saves are 0 (`RetreatRule` 0); the screenshot shows Owner selected | high for 0; 1/2 inferred from button order |
| Retreat hexes 1 / 2 | `rules.retreat_distance` | stock 1 = selected button; save `RetreatDistance` | high |
| Stacking limit | `rules.stacking_limit` | 2 = selected; save `StackingLimit` | high |
| Max advancing units | `rules.max_advance_units` | 2 = selected; save `MaxAdvanceUnits` | high |
| Exit from ZOC | `rules.zoc_exit_allowed` | false = Not allowed; save `ZocExitAllowed` | high |
| Enter terrain with full movement | `rules.full_move_entry_allowed` | false = Not allowed; save `FullMoveEntryAllowed` | high |
| Enforce these rules in the game | `rules.fix_rules` | name; all stock false | medium |
| Activation cap, base per side | `rules.activation_limit.{first,second}` | every stock file; editor "+N from turn T" | high |
| Activation cap steps | `rules.activation_steps.{first,second}[] = {turn, add}` | Gaines' Mill, Chancellorsville, Second Bull Run (Gettysburg has an older flat list) | high |
| CP value of a hex (raises the cap) | `hex.pp.{first,second}` | stock 2/3 on CP hexes | high |
| Night turns | `rules.night_turns[]` | name; the user's own file [9, 10] | high |
| Standby fields | see the standby section | field order = Malvern Hill key order | high, except `enemyGroup` numbering (medium) |
| AI personality | `doctrine.blue` / `doctrine.red` | words below | see below |
| Sudden death unit | `units[].suddenDeathUnit` | name; save `SuddenDeathUnit` | high |
| Elite (surprise) unit | `units[].eliteUnit` | name; save `EliteUnit` / `EliteTriggered`; the user's own file marks Garnett | high |
| Defection | `units[].betrayalTurn/Chance/Rise/BlockPct` | names; save `Betrayal*` | high |
| Escaping off-board | `rules.exit_points_per_cs`, `rules.exit_sudden_death_cs`, `hex.exitHex`, `units[].exitPoints` | Second Bull Run, Gettysburg | high for the keys and form (used from v3.7, in Second Bull Run's dict form); medium for `boxes[19]` as the second side's flag; how exit points enter the margin, and whether exited CS counts as lost, are unknown (DEV_WISHLIST 23); the exit-points cap key was not seen |
| Flag colours (first side red) | `scenario.firstSideFlagRed` | Malvern Hill true, Chancellorsville false | high |
| Counter coaster | not found | no stock key matches a per-side coaster; `sideColors` exists in every file and Chancellorsville has per-unit `color`, but neither is proven to be the coaster | none: not set |
| Map size, Max turns | `scenario.map.width/height`, `scenario.maxTurns` | | high |
| Turn order / skip opening | `scenario.firstMove` "first" / "second" / "skipToSecond" | stock values | medium |
| Briefing images, description, scales | `meta.briefingImage`, `meta.regionMap`, `meta.battleMap`, `meta.description{lang}`, `meta.descriptionDefaultLang`, `meta.scaleMeters/Minutes/Men` | stock | high |
| Turn clock | `scenario.turnClock[] = {turn, date, time}` | stock | high |
| Victory | `victoryCondition.winLine/tacticalThreshold/operationalThreshold/strategicThreshold` | stock | high |

**AI personality words.**
- By name: `ber` Berserk, `off` Aggressive, `def` Cautious, `ultra` Ultra-Cautious, `std` Steady, `sei` Seize, `brk` Breakthrough, `line` Line.
- `dyn` is probably Auto; it could also be Maneuver.
- No word has been seen for Incompetent, Delay or Maneuver, so we don't use them.
- Saves store a number. Playtests 2 and 3 (`line` / `brk`) saved 10 / 9, which fits the editor's button order with Auto skipped: Berserk 0, Aggressive 1, Cautious 2, Ultra-Cautious 3, Steady 4, Incompetent 5, Delay 6, Seize 7, Maneuver 8, Breakthrough 9, Line 10.
- Playtests 1 and 4 (`def` / `off`) both saved 1 / 2, and all four playtests have `P1StartsFirst` false. That fits only if P1 and P2 were swapped, or if the user changed the personalities at start-up. Gaines' Mill (`sei` / `ultra`) saved 2 / 1, which fits neither. So the numbers are medium confidence; the words are high.

**Default combat table.** The editor's default (screenshot) matches the Gettysburg/Chancellorsville table in 46 of 48 cells. It differs at 3:1 on a 5 and 4:1 on a 4, where the editor shows DE and Gettysburg has DR. The editor says a table left at the default is not written to the file, and Gettysburg and Chancellorsville do write one, which fits their table not being the default. Our own table is unaffected. The v3 note "the stock table is also the built-in default" is corrected here: the default is one cell harsher in each of those two rows.

## Proposals (not built): making leaders matter

**The activation cap is already on.** Every stock file sets it, and ours has Union 5 (7 from turn 5) and Confederate 6, which is 29-46% of each force and inside the editor's 30-50% guidance. Ideas to try:
- **CP hexes at the HQs.** Make the hexes where Kimball (Pritchard's Hill) and Jackson (Sandy Ridge, behind the wall) directed the fight worth +1 or +2 CP. A side that loses its command post moves fewer units. The editor allows minus CP; whether negative `pp` values work is unconfirmed.
- **Command steps in time.** Union base 4, +2 from turn 4 (Kimball sends Tyler) and +2 from turn 7. Confederate base 5, +2 from turn 5 (Burks). Kimball's slow start and late surge then come from the cap, not only from standby.
- **Elite (surprise)** is built in v3.5 without the HQs (see "Combat and survival"). The original proposal: once per game, when an elite unit first attacks or is attacked, every elite unit of that side moves and attacks once more. Try Confederate elite = Jackson's HQ + Fulkerson + Garnett 5/33 (Jackson's flank stroke onto Sandy Ridge), and Union elite = Kimball's HQ + Tyler's three regiments (the counterattack). The leader's own counter is part of the box, so where the HQ is decides when the extra round fires. The user's own file already marks Garnett as elite.

## Confirmed from stock files vs inferred

- **Confirmed** (seen in the stock files or saves):
  - every key and value we write (the validator checks against the stock files)
  - the grid and boardArt geometry
  - the CRT layout (40 combats)
  - neutral VPs
  - named non-VP hexes
  - side-1 standby groups
  - range 3
  - battery CS 2 (4 in the file from v3.3)
  - what `replacement`, the standby fields, `eliteUnit` and the activation cap do (editor help, v3.3)
  - "image" and "text" template shapes
  - commander + unit names
  - that there is no facing or rotation field
- **Inferred:**
  - the doctrine index numbers in saves (the words are matched to buttons by name)
  - that turn 0 / chance 0 means hold
  - that a fence defends its own hex
  - which side `enemyGroup` n points to
  - that fortress hexes never retreat
  - what `boardArt.hash` does
  - **`firstMove: "second"`**, which only the user's own file uses
  - **Mountain move cost:** it keeps stock `customId` 4, but costs 2 MP instead of 4

## What the format can't do

See `DEV_WISHLIST.md`.

## Full in-game checklist (v3.7)

Tick these in the game and report anything that fails. Screenshots help.

1. [ ] Both "Kernstown 1862 (CivilWar1)" and "Kernstown 1862 (CivilWar1, no art)" appear and load.
2. [ ] **Board art** sits under the grid. The cartouche and compass rose (south-east corner) do not cover a hex name or counter. Woods, ridges, the wall, roads and creeks fall on the right hexes and do not drift toward an edge.
3. [ ] **Hex names** show once each and do not run into each other, especially Glass Farm and Stone Wall on row 19.
4. [ ] **Counters** can be read without hovering: commander, unit, portrait or NATO mark, CS (doubled: brigades 4-6), MP, and R3 on batteries.
5. [ ] **CRT.** Combat results match the v3.4 table. From 1:3 to 1:1 most rolls are C. At 1:1 only a 6 gives DR. There is no AE, and no DE below 5:1.
6. [ ] **Wall and ridges.** The wall and ridge hexes are rough (2 MP, x2). A unit there that takes a DR falls back, and a unit next to the ridge can retreat onto it.
7. [ ] **Survival.** Garnett and Ashby last into the late afternoon. Count the losses to a retreat with no open hex, and any replacements that appear after an AE or DE.
8. [ ] **Artillery.** The Pritchard's Hill guns (13,17) and the Sandy Ridge guns (12,20) are 3 hexes apart. Held guns should fire but not move.
9. [ ] **The stand at the wall.** The Steady Confederate AI holds the wall and Glass Farm rather than pushing single brigades north.
10. [ ] **Standby.**
    - A turn-1 save shows Confederate units with StandbyGroup 1-4 (not 0).
    - Tyler wakes from turn 4 or when Burks does; Burks from turn 5 or when Tyler does; Sullivan from turn 6 or when Ashby does.
    - Ashby stays while Sullivan's infantry is within 4 hexes of him.
    - The guns, Huntington and both HQs move only if an enemy comes next to them (or, for the HQs and Huntington, if their side's main body is badly reduced). v3.7: 39 IL wakes with the rest of Sullivan's brigade.
11. [ ] The Confederates move first. Union activation is 5, and 7 from turn 5. Confederate activation is 6.
12. [ ] **VPs and CPs** show their values. The Stone Wall VP and the Glass Farm CP start neutral.
13. [ ] **Victory.** winLine is 45 and the thresholds are 5/40/81. Middle Road (4,25) shows 10 VP and starts Confederate. Report the final score and whether losses moved it.
16. [ ] **Elite round.** The first time Tyler's or Garnett's/Fulkerson's brigades fight, that side's elite units get one more move and attack, once per game. Note whether the Steady AI's elite round pulls Garnett off the wall, what happens to elite units still on standby, and whether a cavalry raid goes for the Middle Road hex.
14. [ ] **Turns.** Turn 1 is 3/23 14:00, turn 11 is night, and the game ends after turn 11.
15. [ ] **Briefing.** The region and battle maps show with their portraits and labels, and the description is readable, including the new [Withdrawal] paragraph.
17. [ ] **Withdrawal (v3.7).** The six south-edge exit hexes (11-13,35) and (0-2,35) accept Confederate units and refuse Union ones. Exit one Confederate unit and save: is it in `Exited`, with `HasExited` true; do `RedVP`/`BlueVP` change; does the final score move by its CS, and which way? Does the AI Jackson exit on its own, and how early? Does anything happen at `exit_sudden_death_cs` 0?
18. [ ] **Carry-over.** Run `python3 carryover.py` on the end-of-game save and check the totals against the counters on the board.

## Rebuild and validate

The stock scenarios are game files, so they are not committed. Copy them into `mustattack/kernstown/ref/`:
- required: `antietam1862.json`, `gainesmill1862.json`, `gettysburg1863.json` and your own `user_kernstown1862.json`
- if you have them: `malvernhill1862.json`, `sevenpines1862.json`, `chancellorsville1863.json` and `secondbullrun1862.json`

Then run:

```
python3 build_kernstown_ma.py --basemap ../../data/basemap_painted_full.png   # writes both scenario files and board_art.png
python3 validate_kernstown_ma.py mKernstown1862_CW1.json
python3 validate_kernstown_ma.py mKernstown1862_CW1_noart.json
python3 render_preview.py mKernstown1862_CW1.json preview.png preview_zoom.png preview_counters.png preview_kernstown_ingame_scale.png
MA_COUNTER_STYLE=v381 python3 build_kernstown_ma.py   # optional: v3.8.1 counters, to *_v381.json
python3 counter_compare.py mKernstown1862_CW1_v381_noart.json mKernstown1862_CW1_noart.json counters_v381_vs_v39_60px.png 60
```

You need:
- Python packages: numpy, scipy, rasterio and Pillow
- git access to `origin/main`, where the portraits are
- fonts: Playfair Display for the counters (or set `MA_COUNTER_FONT`), and IM Fell English SC and IM Fell French Canon for the art

## Sources

- O.R. Series I, Vol. 12, Part 1: reports of Jackson, Shields, Kimball, Tyler and Sullivan.
- Gary Ecelbarger, *"We Are in for It!": The First Battle of Kernstown* (1997).
- Peter Cozzens, *Shenandoah 1862* (2008), as cited in the Wikipedia article on the battle. That citation is our source for the march distances, Pendleton's count and Jackson's reply, the 6 PM withdrawal, and Garnett's arrest.
- The Wikipedia order-of-battle pages for the battle, for the colonels and battery commanders.
- NPS / ABPP battle summary.
- American Battlefield Trust map *First Kernstown* (2024), `data/historic_maps/`. We used it to check the board by eye, not to georeference it.
- Jedediah Hotchkiss' Kernstown map.
- USGS 3DEP DEM, `data/dem/kernstown_3dep.tif`.
- This repo's `data/features/kernstown_features.json` and `data/layers/*`.

## Known discrepancies

- The repo's geography and the ABT map disagree in places: Middle Road, the position of Opequon Church (west of the pike on ABT, east of it in our data), and how far the wall runs. We follow the repo.
- The 4th Ohio of Kimball's brigade has no counter of its own.
- v3.6 history check (archivist), listed but not changed because they touch standby or balance: the 21st Virginia sits in Burks's late reserve (standby group 1) though it fought beside the 27th from the start; Burks's turn-5 arrival is an abstraction; Sullivan's group wakes on turn 6 though he was engaged from late morning; Robinson's battery is held on Pritchard's Hill though it moved forward historically. Consistent with the OR: turn 1 at 2 PM, Keeper's section on the left with Sullivan, Huntington in reserve, Jenks and Clark on Pritchard's Hill, the 48th Virginia absent (rear guard).
- In the user's `user_kernstown1862.json`, the roads are one-sided, and Carroll's `entryHex` is `"10,0"`. That file was not modified.

## Change history

**v3.9 (look pass, one name):**
- Counters: the v3.9 style above (Quartermaster's marks, exactly as his proposal scopes them; nothing he dropped was added). Default style; `MA_COUNTER_STYLE=v381` keeps the old counters reproducible.
- Board art: Major Hotchkiss's plate pass, applied from his patch against 69d1fb2 to `board_art.py` only: DEM-driven hachures over a sepia slope wash on the high-ground hexes (crests bare), watercolour washes (water bleed, woodlot rims, field edges, aged paper), the stone wall with a shadow and mortar ticks, letter-by-letter period lettering on the existing labels, and a References panel in the margin with a neutral counters key. v3.8.1's marsh and Hoge Run fixes kept. 123 of 128 palette colours, 4,963,377 bytes (+17,509).
- Danville battery: **Lanier Danville** again (was Shumaker Danville from v3.6). Archivist ruling: Fulkerson, OR 12/1 p.408, "the Danville Artillery, commanded by Lieut. A. C. Lanier"; Jackson's "Shumaker's battery" (p.380) is the captain's name. This reverses the v3.6 rename. Briefing (all 8 language keys), README and `CAMPAIGN_CARRYOVER.md` updated.
- Files: `mKernstown1862_CW1.json` 11,994,697 bytes (was 13,068,813: the two 512 px stock plates are no longer embedded), `_noart` 5,376,661 (was 6,474,121). Validator: 0 errors, 0 warnings on both.

**v3.8.1 (art fix):** Marsh tufts are drawn only on the hexes the scenario makes marsh, (10,17); v3.8 had spread the wet-meadow sign over Pritchard's Hill's rough south slope (q 10-13, rows 16-18), which contradicted the game's terrain. Hoge Run tapers 4 to 6 px (v3.8 had 1.6 to 5.2 px, faint west of the Pike at preview scale; v3.7 drew 5 px). Only `meta.boardArt` changed; the no-art JSON is byte-identical. Board art PNG 4,945,868 bytes.

**v3.8 (art only, no playtest yet):** Major Hotchkiss's engraved-detail pass on the board art (`board_art.py`, notes in `staff_notes/hotchkiss_art/`): tree-by-tree leafless woods, worm fences, shaded buildings with chimneys, Opequon Church cross and churchyard, ruled orchards, hatched Winchester blocks, meandering tapered creeks, cased roads and a stippled Pike, a wet-meadow sign, two springs, and an engraved neatline that breaks at the v3.7 exits (arrows kept). Only `meta.boardArt` changed; every other key in both JSONs is identical to v3.7 (the no-art file is byte-identical). Board art PNG 4,951,784 bytes (+2.1%), still 128 colours.

**v3.7 (playtest 5 follow-up, no playtest yet):**
- **Withdrawal.** Confederate exit hexes at (11-13,35) on the Valley Turnpike and (0-2,35) on the Middle Road; `exit_points_per_cs` {"first": 0, "second": 1}, `exit_sudden_death_cs` 0/0, `exitPoints` 0, as Second Bull Run. Small "To Newtown & Strasburg" and "South by the Middle Road" arrows on the board art, clear of the exit row. A [Withdrawal] briefing paragraph (all 8 language keys). winLine 45 and thresholds 5/40/81 unchanged. See "Withdrawal (v3.7)".
- **Cohesion.** Sullivan 39 IL moved from standby group 3 to group 2 with the rest of its brigade. The validator now fails a brigade split across groups, and checks the exit settings.
- **Campaign.** `carryover.py` and `CAMPAIGN_CARRYOVER.md`.
- **DEV_WISHLIST.** Items 23-27: exit semantics, limbered and unlimbered artillery, a line-of-sight display, brigade cohesion and command range, campaign carry-over.
- Not changed: CRT, retreat rules, doctrines, terrain types, portraits, counter art, `ref/user_kernstown1862.json`.

**v3.6 (staff reviews, no playtest yet):**
- **Briefing (archivist, all 8 language keys).** New epigraph from Jackson's report (OR 12/1 p.381). Opening rewritten on the OR: Jackson's orders to keep Banks in the Valley, Ashby's report and the "four regiments" intelligence, the march, Shields' division about twice Jackson's 3,000 infantry, Kimball in command, Jackson's only tactical defeat. Kimball's guns are ten rifled Parrotts (was "16 guns and 800 infantry"); Tyler goes in soon after 4 PM and the wall fight runs 5 to 6:30; Garnett's withdrawal and arrest as in the OR, with no unverified date; the afternoon note explains that the 21st Va was engaged from the start (the reserve is an abstraction) and that the 48th Va never fought. Order of battle: 1st (West) Virginia, the 39th Illinois "not in the final assault", the full cavalry, Keeper's one section, Huntington in reserve, Pleasants, Shumaker/Lanier, the 48th Va. Sources cite page ranges. Dropped as unverified: the Harpers Ferry detail, "above the elbow", the 1 April arrest date, the 3:55 PM wayside time.
- **Counters (quartermaster).** CS (file values): Jenks 5, Clark 5, Keeper 2, Brodhead's cavalry 3 (renamed WV/OH/MD/PA Cav), Rockbridge 6, Garnett 2/4/27 5, Burks 21 VA/1 Bn 3. Names: Pleasants Hampden (was Marye), Shumaker Danville (was Lanier; reversed in v3.9, see there). Totals: Union 67 (was 66), Confederate 46 (was 44). Only those 10 counters were re-rendered; portraits are unchanged.
- **Elite** is now two counters a side: Tyler 7 OH/29 OH and 7 IN/1 WV; Fulkerson 23/37 VA and Garnett 2/4/27 VA.
- **Victory.** winLine 45 unchanged; thresholds 5/40/81 (room 101). The builder now fails if the briefing's numbers differ from the file's.
- **Board art (Hotchkiss).** See "Board art" above.
- **Validator.** Stone wall on every fenced hexside; Keeper's one-section battery added to the below-CS-3 list.
- **Not changed:** CRT, retreat, doctrines, terrain types, standby groups, portraits, the cartouche title.

**v3.5 (polish, no playtest yet):**
- **Victory.** winLine 45 (status quo with the new Middle Road hex), thresholds 5/40/79 = 5/40/80% of the scarcer side's room (99). The Union strategic victory is now reachable (best +99 against 79; v3.4: best +79 against 116). Validator: winLine must be the status quo, and every level must be reachable by both sides (errors, not warnings).
- **Middle Road** (4,25), 10 VP, Confederate at the start. Balance by the numbers: Union in-reach objective swing 35 → 55, Jackson's 85; Union strategic needs 54% of Jackson's force destroyed net (v3.4 thresholds rescaled without the hex: 63%), Jackson's 13% (0% without it). A 15-VP version was rejected: too much for a raid by 1 MI Cav.
- **Elite units.** Tyler's three counters and Fulkerson + both Garnett counters (see "Combat and survival").
- **Board art.** Title cartouche with yard and meter scale bars at 300 m per hex, compass rose, Winchester street plan. Counter art and portraits are untouched (the unit templates are byte-identical to v3.4).
- **Briefing.** Victory paragraph rewritten for the new line, thresholds and routes to each result; batteries sentence names who each gun is stacked with; one sentence on elite units; battery names read "Jenks (A, 1st West Virginia)" and "Keeper (B, 1st West Virginia)".

**v3.4 (from playtest 4, 11 turns, 11 units lost):**
- **Ridge terrain.** Sandy Ridge, Pritchard's Hill and the wall are `rough` instead of `mountain`. The replayed saves show the engine never retreats a unit into mountain, which caused 6 of playtest 4's 11 losses.
- **CRT.** At 1:3 to 1:1 a middle roll is a stand-off, and AE is gone. Replaying playtest 4's 11 losses with the same die rolls, this table alone avoids 5, and with the terrain change 8. The remaining 3 (Lanier, Jackson's HQ, 21 VA/1 Bn) were truly surrounded by enemy ZOC.
- **AI.** Confederates Steady (`std`) instead of Aggressive (`off`); the Union stays Cautious.
- **Retreat settings unchanged** (see "Retreat settings, checked in v3.4").
- **Validator:** fails mountain and fortress hexes, prints the outcome odds per CRT column, and requires at least 4 stand-offs of 6 at 1:3 to 1:1, no AE above a 1, and a DR at 1:1.

**v3.3 (from the editor's help text):**
- Replacements on. Every strength is doubled (`CS_SCALE` 2, `scaleMen` 150), so brigades are 4-6 and get a half-strength second life on an AE or DE. Odds are unchanged.
- Standby groups use the editor's triggers. Tyler and Burks wake each other; Sullivan wakes when Ashby does; Ashby is held by containment while Sullivan faces him; the reserves join when the main body falls to 50-70%. The guns on both ridges are held for good (they still fire). Jackson's HQ has its own group (Confederate 4).
- AI personality: Cautious Union (`def`), Aggressive Confederates (`off`).
- Thresholds follow the editor's 5/40/80% guidance: 7/58/116. The margin now includes losses.
- Briefing: the reserve, replacement and scoring paragraphs rewritten.
- Validator: checks the standby triggers (group count, containment satisfied at the start, `enemyGroup` names a real group), that CS is 3 or more except for listed units, the doctrine words, and whether each side can reach each threshold.
- README: an editor-field-to-JSON-key table; the editor's default CRT differs from the Gettysburg table in two cells. `DEV_WISHLIST.md` was trimmed to what the editor still cannot do.
- Counter coasters were not set: no stock key for them could be confirmed.

**v3.2 (from playtest 3):**
- Standby groups are numbered per side. The Confederate groups (v3.1 numbers 4 and 5) never loaded; they are now 1-3. New groups hold the guns on Pritchard's Hill (Union 4) and Sandy Ridge (Confederate 3) until turn 6 at the earliest. The validator checks per-side numbering.
- Every battery starts stacked with one non-artillery unit. Stacks were moved by 1-3 hexes so that each keeps two rear hexes and passes a new two-flank test in the validator. Historical gun positions are kept: Rockbridge, Carpenter and Waters on Sandy Ridge, the Union guns on and beside Pritchard's Hill.
- CRT: 1:1 on a 5 is C (was DR).
- Glass Farm is a +2 CP instead of a 5-VP hex; the "Wall" CP is gone. Thresholds 6/47/94.
- Board art: DEM hillshade and form lines, fields, rail fences, farmsteads, shadowed woods, a wider pike, a heavier wall.
- Counters: branch-coloured NATO boxes, gold-framed HQ portraits.
- Briefing: the afternoon, scoring and combat paragraphs updated.

Playtest 3 notes: the save's `P1Type`/`P2Type` are 1/0, as in playtest 2 (where the user played the Confederates). So we are not sure which side the computer ran in playtest 3. The battery loss on turn 2 was at 1:1, die 6 (DR), with the retreat closed by units at (11,18) and (13,18), after the guns had moved forward to (12,18).

**v3.1 (polish):**
- Hex names:
  - "Stone Wall West" became "Wall" and "Pike & Cedar Creek Grade" became "Grade Junction"
  - "Stone Wall East", "Hoge Run Ford" and "Middle Road" are no longer hex names, because they ran into neighbouring names (the art still labels the road and the run)
  - Triplett House moved from (17,22) to (17,23)
- Board art labels: "Buffalo Lick" became "Buffalo Lick Run". The Middle Road and Abrams Creek labels moved out of the woods and the town. The cartouche date is punctuated correctly.
- Counters:
  - the Davey battery is now Keeper, per the order of battle
  - Confederate battery names lost the "Bty" suffix, so they fit at full size
  - "21 VA/1 VA Bn" became "21 VA/1 Bn"
  - the grey counters have darker text
- The briefing and map labels were proofread against the sources:
  - the march is 40 miles (25 + 15), not 36
  - "Banks' HQ" and the 2 PM Tyler label were cut as unsupported
  - the Pendleton episode was added
- The README was rewritten for the current state.

**v3 (from playtest 2):**
- the custom CRT
- the wall as mountain
- the rear-room check, with Brodhead, Keeper (then Davey) and Garnett 2/4/27 VA moved
- Kimball and Jackson HQ counters
- portraits
- period briefing maps
- briefing sections for each side
- three farmhouse names

**v2 (from playtest 1):**
- Doctrine `def/off` became `line/brk`.
- The Confederates start in depth on Sandy Ridge.
- Ashby and Chew are held east of the pike.
- Batteries became CS 2, range 3.
- The wall and Glass Farm became neutral VPs, and the wall got a CP.
- Burks became a standby reserve, and Tyler and Sullivan wake later.
- Counters were redesigned with NATO marks and R3 plates.
- Named hexes and painted board art were added.
- winLine became 55, with thresholds 6/49/98.

**v1:** first build. It loaded and ran in playtest 1.
