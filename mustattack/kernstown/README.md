# Kernstown 1862 (CivilWar1): a Must Attack scenario

`mKernstown1862_CW1.json` is a First Kernstown (23 March 1862) scenario for *Sekigahara 1600: Must Attack!*, in the format the in-game Wargame Maker exports. It was built from this repo's Kernstown map data, not drawn by hand.

**Status: v3, not tested in the game.** v1 and v2 loaded and ran in the game: playtest 1 had the user as the Union, playtest 2 as the Confederates. v3 is rebuilt from playtest 2. It passes `validate_kernstown_ma.py`, but nobody has loaded v3 yet, so treat it as unverified until someone does.

| File | What it is |
|---|---|
| `mKernstown1862_CW1.json` | The scenario with painted board art (13.1 MB, UTF-8, no BOM) |
| `mKernstown1862_CW1_noart.json` | The same scenario with no `boardArt` (6.6 MB): the fallback if the art fails to load or misaligns |
| `build_kernstown_ma.py` | Rebuilds both files from `data/` |
| `board_art.py` | Paints `meta.boardArt` on the Must Attack grid |
| `ma_grid.py` | The Must Attack hex grid: odd-r pointy-top, edges 0=E, 1=SE, 2=SW, 3=W, 4=NW, 5=NE |
| `validate_kernstown_ma.py` | Checks a scenario against the stock scenarios |
| `render_preview.py` | Draws `preview.png` (whole board), `preview_zoom.png` (Sandy Ridge to Kernstown) and `preview_counters.png` (all 29 counters). The previews are put together from the file; they are not game screenshots. |

## What changed in v3 (from playtest 2)

Playtest 2 had the user as the Confederates. Garnett's 5/33 VA was destroyed again. The save shows the cause: an AR at 1:1 (die 2) with no open hex behind him. The report also asked for the game to feel more personal. v3 has two parts: survival, and people.

### Part A: survival

| # | Item | v2 | v3 | Why |
|---|---|---|---|---|
| A1 | `rules.crt` | not set (built-in table, same as Gettysburg / Chancellorsville) | Custom softer table (below) | Elimination now needs much better odds. AE drops from 3 cells to 1 (1:3, die 1 only). DE drops from 15 cells to 3 (5:1 die 6, 6:1 die 5-6). Many AR / DR cells become C (no effect). Every value is one the stock tables use. The table is monotonic: a higher die or better odds is never worse for the attacker. |
| A2 | Stone wall hexes (8..11,19) | `fortress` terrain | `mountain` terrain (x2 defence, 2 MP); fences on NW/NE kept | In playtest 2 all three fortress combats came out as C where the table says AR or DR (see the evidence below). So a unit in a fortress never retreats, and its only bad result is DE. That turned the wall into a death trap, the opposite of what happened historically, when Garnett fell back from it. Mountain gives the same x2 and lets the unit be pushed back. |
| A3 | Start hexes | Some stacks had one or no open hex behind them | Brodhead 1 MI Cav (7,12)→(6,12), Davey B 1 WV Bty (17,18)→(16,17), Garnett 2/4/27 VA (10,22)→(10,23) | The validator now fails any stack with fewer than 2 neighbours that are on the board, passable, outside enemy ZOC, have stack room, and are strictly farther from the nearest enemy. All 29 counters pass. |
| A4 | `retreat_control` 0, `retreat_distance` 1, `zoc_exit_allowed` false, `full_move_entry_allowed` false | same | **unchanged** | These are the only values in any stock file or save, so nothing else can be shown to work. `retreat_distance` 2 needs a longer clear path, so under the ZOC-blocked retreat rule it would probably kill more units, not fewer. `zoc_exit_allowed` controls walking out of ZOC during movement, not retreating. Retreats die by entering ZOC (the save's `ZocToZocAllowed`), and scenario rules have no field for that. Turning `zoc_exit_allowed` on would also let units walk away from contact and would change how the AI fights. What 0 means for `retreat_control` (owner chooses?) is not confirmed. |
| A5 | `replacement` | false | **unchanged** | Only Gettysburg sets it to true, and what it does is not known. Saves carry `IsReplacement` and `EliminatedTurn`, which suggests that eliminated units come back (inferred). **Test for the user:** set it to true in the editor, get a unit eliminated, save, and look for units with `IsReplacement` in the save. |

The v3 CRT (rows are odds, columns are die 1-6, and a high die favours the attacker):

| Odds | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| 1:3 | AE | AR | AR | AR | AR | C |
| 1:2 | AR | AR | AR | C | C | DR |
| 1:1 | AR | AR | C | C | DR | DR |
| 2:1 | AR | C | C | DR | DR | DR |
| 3:1 | C | C | DR | DR | DR | DR |
| 4:1 | C | DR | DR | DR | DR | DR |
| 5:1 | DR | DR | DR | DR | DR | DE |
| 6:1 | DR | DR | DR | DR | DE | DE |

**How the table's orientation was established.** The orientation was checked against 40 combats logged in playtest 1 (13), playtest 2 (21), Gaines' Mill (4) and Waterloo (2). None of those four scenarios has its own `crt`. Each cell below shows the Gettysburg/Chancellorsville stock table value, then "←" and every logged result (P1, P2, GM = Gaines' Mill, WL = Waterloo). All 37 combats outside a fortress hex match the stock table exactly. So `crt[odds row][die-1]` is the layout, and the stock table is also the built-in default. The three mismatches (`*`) all involve the fortress hex (11,19) in playtest 2: twice the attacker stood in it (an AR became C), and once the defender held it (a DR became C).

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

### Part B: making it personal

- **Commanders on the map.** Two new 1-CS HQ counters carry portraits:
  - Kimball, "Shields' Div. HQ", at (13,14)
  - Jackson, "Valley District HQ", at (12,24)

  Both sit in hold standby groups (3 and 5), so the AI keeps them back. Neither is `suddenDeathUnit`. Stock never sets it to true, and on Jackson it would end the game the moment he fell.
- **Portraits.** Six brigade or army commanders have portrait counters, using the approved files in `historical_data/portrait_manifest.csv` on `origin/main` (3b9808b). The builder reads each one read-only with `git show`. Nothing was copied into this branch, renamed, overwritten or regenerated. Each one is cropped and framed, then embedded in the JSON as a template image.

| Leader | File on origin/main | Blob | Used on |
|---|---|---|---|
| T. J. Jackson | `mdl_CSA_TJJackson.png` | fb3e728 | Valley District HQ counter; region map |
| R. B. Garnett | `mdl_CSA_RGarnett.png` | 78f7290 | 2/4/27 VA, 5/33 VA; battle map |
| T. Ashby | `mdl_CSA_TAshby.png` | 012659f | 7 VA Cav |
| N. Kimball | `reference/mdl_USA_NKimball.png` | 0aa272d | Div. HQ, 14 IN/84 PA, 8 OH/67 OH; battle map |
| E. B. Tyler | `reference/mdl_USA_EBTyler.png` | 2117a48 | 7 OH/29 OH, 7 IN/1 WV, 110 PA |
| J. C. Sullivan | `reference/mdl_USA_JCSullivan.png` | b79ea1f | 13 IN/5 OH, 62 OH, 39 IL |
| J. Shields | `reference/mdl_USA_JShields.png` | ca9784a | region map only (he was wounded on the 22nd) |

  Burks, Fulkerson and Brodhead have no portrait yet; the manifest lists them as MISSING. Batteries keep the NATO mark.
- **Briefing maps.** `regionMap` ("The Lower Valley, March 1862") and `battleMap` ("Kernstown, 23 March 1862") are new period-style engraved maps with a cartouche, medallions and the stone-wall line. The region map shows Jackson and Shields; the battle map shows Kimball on the east and Garnett on the west.
- **Briefing text.** The description now has:
  - an opening on Ashby's faulty "four regiments" report
  - a section headed *If you command the Union* and one headed *If you command the Confederates*
  - *The afternoon*: a turn-by-turn timeline
  - *How to win*
  - *Combat*: the softer table and the wall
  - an order of battle with the colonels
  - counter sources

  The format has a single description for each language, so both sides read the same text. It is copied into every language slot.
- **More named places**, placed by reference to the ABT 2024 map (±1 hex): Marcauley Farm (12,21), Mahaney House (15,22), Triplett House (17,22).
- **Not used, and why:**
  - `eliteUnit` (Stonewall Brigade): stock never sets it to true, and the save fields `EliteUnit` / `EliteTriggered` suggest a one-shot trigger we can't describe. It can be tried as an editor toggle.
  - `briefingImage`: always `""` in stock, so its format is unknown.
  - Turn-clock labels: entries take only `turn`, `date` and `time`.
  - Tooltip and box fields: stock tooltips are the name only, and boxes 8-19 are always 0. Colonels and strengths go in the description instead.

### What the format can't do (for the developer)

- scripted events or messages on a turn
- leader casualties or wounding
- morale or ammunition
- step losses or remnant units (what `replacement` does is unclear)
- tooltip text for each unit
- turn names or labels
- a separate briefing (or briefing image) for each side
- rally
- facing
- control of the ZOC-to-ZOC (retreat-into-ZOC) rule from the scenario
- control over how fortress terrain retreats
- standby holds that bind a human player

## In-game test checklist (v3)

1. [ ] Both files load. The Kimball and Jackson HQ counters and the portrait counters draw correctly.
2. [ ] **CRT.** Eliminations are rare: no AE except at 1:3 on a 1, and no DE below 5:1. Log a few combats and compare them with the table above.
3. [ ] **Wall.** A unit on the wall (now mountain) that takes a DR moves back instead of being frozen in place or eliminated.
4. [ ] **Garnett and Ashby survive** at least until late afternoon in a Confederate game. Count how many units are lost to a retreat with no open hex.
5. [ ] The HQs stay back under AI control.
6. [ ] The region and battle briefing maps show, with their portraits.
7. [ ] The new place names show once each.

## What changed in v2 (from playtest 1)

Playtest 1 report: the map was plain. Ashby was destroyed in Kernstown. Garnett's brigade was destroyed rather than falling back. No artillery did anything. The Confederates never made a stand at the stone wall. The counters needed hovering to identify.

What the save (`playtest1_save.json`, turn 5) and the v1 file show:
- Batteries were CS 1 and range 2 (about 600 m on a 300 m hex). They were nearly always out of range or attacking at 1:3.
- The Confederate doctrine "off" sent Fulkerson into a 1:2 attack, which ended AE.
- The v1 command point on the Sandy Ridge crest drew Garnett *behind* the wall rather than onto it.
- Ashby was free to move and rode alone into Kernstown.
- Units that took a DR with no open hex behind them were lost.

| # | Item | v1 | v2 | Why |
|---|---|---|---|---|
| 1 | Doctrine | `blue: def, red: off` | `blue: line, red: brk` | Antietam's pair, where a Union attacker faces a held line with fences. "off" produced the reckless 1:2 attacks. The meaning of each word is inferred from the stock pairs and is not documented. |
| 1 | Confederate start | Lon/lat points south of the ridge, with Garnett stacked behind Fulkerson | Explicit hexes in depth on Sandy Ridge: Fulkerson (9,21) woods, Garnett (10,22) ridge and (11,22) wooded ridge, Waters (11,21), McLaughlin + Carpenter (12,20) | Every unit starts on x2 ground, two hexes south of the wall, with open hexes behind it to the south and south-west to retreat into. A DR with nowhere to go is what killed Garnett. Historically he fell back from the wall at dusk; v2 gives the AI room to do the same. |
| 2 | Ashby 7 VA Cav | CS 1-6, near the pike north of Bartonsville, free to move | CS 1-6, stacked with Chew at (20,24), east of the pike about 1 km south of Kernstown, with an open rear, **standby group 5 (held: turn 0, chance 0)** | Ashby had about 290 troopers on the field (one point per ~300 men, so CS stays 1). All afternoon he screened Sullivan east of the pike and did not attack the village. Holding the group stops the AI throwing him into Kernstown alone. "Held" is inferred from Antietam's V Corps and Malvern's side-1 hold groups (turn 0, chance 0). If the hold freezes him even when he is attacked, set group 5's `turn` to 6 and `chance` to 20. |
| 2 | Chew | `Horse Arty` CS 1, range 2 | `Horse Bty` CS 1, range 3, stacked with Ashby, group 5 | Three guns, like Antietam's Pelham horse battery (CS 1). |
| 3 | Stone wall hexes (8..11,19) | `plain`, fences on NW/NE | Stock `fortress` terrain (Gettysburg's record: `customId` 7, move 1, defence x2) with a new stone-wall tile; fences kept on NW/NE | It is cover on a crest, not an obstacle. Defence x2 is now the wall hex itself, not only the fence. |
| 3 | Stone Wall VP (10,19) | 15, Confederate-held | 15, **neutral** (`initialControl` null, `boxes[15]` 0, the Second Bull Run "Groveton" pattern) | Neither side held it at 2 PM. The wall is now something to run for and hold. |
| 3 | Glass Farm VP (8,19) | none | 5, neutral | Fulkerson's end of the wall. It gives the AI a reason to hold the whole wall, not one hex. |
| 3 | CP Sandy Ridge crest | +2 on the crest behind the wall | removed; that hex is now named "Sandy Ridge" | It pulled Garnett off the wall in the playtest. |
| 3 | CP Stone Wall West (9,19) | none | +2 | The command bonus now sits on the wall. No stock hex is both a VP and a CP, so it goes on the next wall hex. |
| 3 | Burks' brigade, Marye, Lanier | Free to move from turn 1 | **Standby group 4**: side 1, turn 5 (16:00), chance 40, rise 30. Starts at (13,27), (13,28), (14,28), (14,29) | Jackson's reserve came up to the wall about 5 PM. Side-1 standby groups appear in Seven Pines and Second Bull Run. |
| 4 | All field batteries | CS 1, range 2 | **CS 2, range 3** (MP 3) | A full battery is CS 2 in the stock ACW files. Stock range 2 on 500–700 m hexes is 1.0–1.4 km. On our 300 m hexes the same reach is 3 hexes, and range 3 itself is stock (Malvern Hill, Second Bull Run). |
| 4 | Union guns | Lon/lat points around Pritchard's Hill | Jenks + Clark at (13,17), Robinson at (13,16) on Pritchard's Hill, Davey at (17,18) | Jenks and Clark start 3 hexes from McLaughlin + Carpenter at (12,20). The Pritchard's Hill versus Sandy Ridge duel is in range on turn 1. |
| 1 | Tyler standby | turn 3, chance 40, rise 30 | turn 4, chance 50, rise 25 | Kimball sent Tyler in about 3:30–4 PM. This gives Jackson time to reach the wall first, as he did. |
| 1 | Sullivan standby | turn 5 | turn 6 | Sullivan's regiments reached the ridge late. |
| 5 | Facing / mirroring | none | **not supported; not added** | No stock unit, template or save has a facing, rotation or flip field. All 2,368 image shapes and 4,448 text shapes in the 8 stock files have only position, size and font fields. The new NATO marks are symmetric, so nothing points the wrong way. "Properly pointed" is handled through AI routing instead: doctrine, VP/CP placement and standby groups. |
| 6 | Counters | Name (shrunk to fit), CS, MP, stock musket/sabre/cannon icon, "R2" badge | Commander on top (small); unit in large type (auto-fit, 3.0–4.6); a NATO mark (X infantry, / cavalry, dot artillery; III for regiments, I for a battery); CS bottom left; MP bottom right; an "R3" plate on guns. Union counters are blue with white text, Confederate grey with dark text (stock plates and colours). | Readable without hovering. Unit names are now `box3 + " " + box4` (commander + unit), the convention in every stock unit. |
| 6 | Hex names | VP and CP hexes only | Also: Sandy Ridge (10,21), Stone Wall East (11,19), Opequon Church, Pritchard Farm, Hoge Run Ford, Opequon Ford, Milltown, Middle Road | `name` + `boxes[9]` on a non-VP hex, as Antietam does. The editor says the game draws hex names on the map, so they are **not** painted into the art. |
| 7 | Board art | none | `meta.boardArt` (5120 x 4959 PNG, 96-colour palette, 4.9 MB) | See "Board art" below. |
| 8 | Victory | winLine 45, thresholds 10/72/144 | winLine **55**, thresholds **6/49/98** | See "Victory and balance" below. |

Unchanged: board, terrain classification, roads/rivers/trails, turns (11 x 30 min from 14:00, turn 11 night), Confederates move first, activation caps (Union 5, rising to 7 at turn 5; Confederate 6), infantry strengths (Union 20, Confederate 9), the 39 IL/Huntington reserve (group 3).

### Not changed, and why

- **Retreat rules.** `retreat_distance` 1, `retreat_control` 0 and `zoc_exit_allowed` false are the same in all eight stock files, so we have no evidence of what other values do. v2 attacks the cause instead: start positions with open rears and x2 ground.
- **Custom CRT.** Gettysburg and Chancellorsville carry a `rules.crt` table (8 odds rows x 6 die rolls). Adding one could cut DE results further. We left it out because Antietam-schema files do not use it and its row order (which odds each row is) is inferred. It is an option if units still die too easily.
- **`ai_contact_gate`** (Malvern only: `{"first":0,"second":1}`). It might make the Confederate AI wait for contact before moving. It could also freeze the AI, so we did not use it. It is an optional setting.

## Board art

- **Geometry (confirmed from stock).** Antietam's art has dotted fence marks drawn on exactly the fenced hexsides, which fixes the formula: `pixel = (world − origin) x scale`, with world hex centre `(√3·45·(q + ½(r&1)), 67.5·r)`, `scale` 2, `hexSize` 45, origin `(−52.471, −58.5)`. The image is transparent outside the board's hex outline, as in Antietam. The validator checks the image size against the grid.
- **What is drawn.** The ground is this repo's own painted basemap (`data/basemap_painted_full.png`, v0.4.2, built by `painted_sections/build_full_map.py`), resampled onto the grid, softened and washed toward parchment so the counters read. Over it, and taken from the game terrain so the art matches the rules:
  - woods (tree crowns) and ridges (buff tint with hachures)
  - the stone wall as field stones on the fenced hexsides
  - roads and creeks along the same hexes the game uses (the Pike drawn wider), and dashed trails
  - farm buildings, Kernstown and Winchester blocks
  - italic road and creek names (the game draws hex names itself)
  - a title cartouche and a north arrow
- **Assumptions:**
  - `hash` is the SHA-1 of our PNG. Antietam's hash is also a 40-character SHA-1, but we don't know what it hashes.
  - `style` "acw_b" and `version` 1 are copied from Antietam. "acw_b" may mean the game can also paint its own art (inferred).
- **Missing basemap.** The painted basemap is gitignored (78 MB). If `--basemap` (or `KERNSTOWN_BASEMAP`) doesn't point at it, the builder uses plain parchment ground with the same overlays.

## Victory and balance

- **VPs (both sides the same value, as in all stock files):**

  | Hex | VP | Start |
  |---|---|---|
  | Winchester | 30 | Union |
  | Pritchard's Hill | 20 | Union |
  | Kernstown | 15 | Union |
  | Stone Wall (10,19) | 15 | neutral |
  | Glass Farm (8,19) | 5 | neutral |
  | Bartonsville | 10 | Confederate |

- **CPs:** Stone Wall West (9,19) +2 and Pike & Cedar Creek Grade (18,18) +2. Both are neutral.
- **Score.** Our assumption is that the score is VP held by the Union minus VP held by the Confederates, possibly plus losses; the playtest save at turn 5 still showed 0/0, so the score seems to be worked out at the end. At the start the score is 65 − 10 = **55** = `winLine`.
  - **Jackson holds the wall and Glass Farm until dark:** about 35, a Confederate tactical result. This is the respectable result Jackson can hold out for.
  - **Kimball takes the wall and keeps his own ground (the historical result):** about 75, a Union tactical win.
  - **Jackson takes Pritchard's Hill or Kernstown:** the score drops toward an operational Confederate win.
- **Thresholds** come from a formula that matches all six stock scenarios exactly: operational = 0.2 x (total CS, both sides) + 0.4 x (total VP), tactical = operational / 8, strategic = 2 x operational. Here that is 0.2 x 53 + 0.4 x 95 = 49, giving **6 / 49 / 98**. The formula is inferred; the validator warns if the file drifts from it.

## Order of battle (v2)

One strength point is about 300 men. A full battery is CS 2 and a horse battery CS 1. Guns are MP 3, range 3. Infantry is MP 4 and cavalry MP 6. `S#` is the standby group.

**Union, Kimball (Shields' division), side 0:** Kimball 14 IN/84 PA 3 (12,16), 8 OH/67 OH 3 (14,16); Jenks A 1 WV Bty and Clark E 4 US Bty 2 r3 (13,17); Robinson L 1 OH Bty 2 r3 (13,16); Davey B 1 WV Bty 2 r3 (17,18); Brodhead 1 MI Cav 1 (7,12), OH/MD Cav 1 (19,21); Sullivan 13 IN/5 OH 3 (19,18) S2, 62 OH 2 (20,16) S2; Tyler 7 OH/29 OH 3 (19,12), 7 IN/1 WV 3 (20,10), 110 PA 2 (21,8), all S1; Sullivan 39 IL 1 (24,14) S3; Huntington H 1 OH Bty 2 r3 (22,6) S3.

**Confederate, Jackson (Valley District), side 1:** Ashby 7 VA Cav 1 and Chew Horse Bty 1 r3 (20,24) S5; Fulkerson 23/37 VA 2 (9,21); Garnett 2/4/27 VA 2 (10,22), 5/33 VA 2 (11,22); Waters W. Augusta Bty 2 r3 (11,21); McLaughlin Rockbridge Bty and Carpenter Alleghany Bty 2 r3 (12,20); Burks 21 VA/1 VA Bn 2 (13,27), 42 VA 1 (13,28); Marye Hampden Bty 2 r3 (14,28); Lanier Danville Bty 2 r3 (14,29), all four S4.

| Group | Side | Units | Turn | Chance / rise |
|---|---|---|---|---|
| 1 | Union | Tyler | 4 (15:30) | 50 / 25 |
| 2 | Union | Sullivan 13 IN/5 OH, 62 OH | 6 (16:30) | 30 / 25 |
| 3 | Union | 39 IL, Huntington | never (hold) | 0 / 0 |
| 4 | Confederate | Burks, Marye, Lanier | 5 (16:00) | 40 / 30 |
| 5 | Confederate | Ashby, Chew | never (hold) | 0 / 0 |

## Confirmed from stock files vs inferred

- **Confirmed (seen in the stock files):**
  - every key and value type we write (checked by the validator against all eight stock files)
  - the grid and boardArt geometry
  - the `fortress` terrain record
  - neutral VPs (`boxes[15]` 0)
  - named non-VP hexes
  - side-1 standby groups
  - range 3
  - battery CS 2
  - template shapes limited to "image" and "text"
  - the unit name being commander + unit
  - the absence of any facing or rotation field
- **Inferred (not documented):**
  - what each doctrine word means
  - standby turn 0 / chance 0 as "hold unless threatened"
  - that a fence defends its owning hex
  - the threshold formula and the scoring
  - what `boardArt.hash` hashes
  - what `ai_contact_gate` and `crt` row order do

## Install (path not verified)

1. Copy `mKernstown1862_CW1.json` (and, if wanted, `mKernstown1862_CW1_noart.json`) into the game's scenario folder. We have not confirmed where that folder is. Look next to the stock `antietam1862.json` and the other stock scenarios, or wherever the Wargame Maker saves its exports, and put the file in the same folder.
2. Start the game. Open the scenario list or the Wargame Maker, then load **Kernstown 1862 (CivilWar1)**.
3. If the game does not list the scenario, try importing it from the Wargame Maker. Then report what happened.

## Rebuild and validate

The stock scenarios are game files, so they are not committed. Copy them into `mustattack/kernstown/ref/`: `antietam1862.json`, `gainesmill1862.json`, `gettysburg1863.json`, your own `user_kernstown1862.json`, and if you have them `malvernhill1862.json`, `sevenpines1862.json`, `chancellorsville1863.json` and `secondbullrun1862.json`. Then run:

```
python3 build_kernstown_ma.py --basemap ../../data/basemap_painted_full.png   # writes both scenario files and board_art.png
python3 validate_kernstown_ma.py mKernstown1862_CW1.json
python3 validate_kernstown_ma.py mKernstown1862_CW1_noart.json
python3 render_preview.py mKernstown1862_CW1.json preview.png preview_zoom.png preview_counters.png
```

The builder needs numpy, scipy, rasterio and Pillow. The counter font is Playfair Display, the same font the stock templates name; set `MA_COUNTER_FONT` to point at a local copy. The art fonts are IM Fell English SC and IM Fell French Canon.

## Board

- The board is 32 x 36 hexes at 300 m per hex, about 9.6 km west to east and 9.4 km north to south. Each turn is 30 minutes. The north-west corner is at 78.255 W, 39.192 N.
- It runs west to east from beyond Sandy Ridge to Opequon Creek, and south to north from Bartonsville to Winchester.
- The brief asked for roughly 45-50 x 40 hexes. That is not possible: the whole source map (62 x 54 HoS hexes at 250 yd) comes to only about 41 x 47 at 300 m. The board is therefore clipped to the ground the battle was fought over.
- Terrain comes from re-sampling the HoS layer (`data/layers/kernstown_game.json`), the painted forest fraction and the 3DEP DEM, using 37 sample points per hex:
  - **High ground** (`mountain` 2 MP / x2, or `rough` 3 / x2 where wooded). A hex counts as high ground if its topographic position on the DEM is at least 6 m, or if it carries a HoS `hill` tag. Topographic position is the DEM smoothed over 150 m, minus its mean over 1.8 km, so the regional rise to the west does not count. This picks out Sandy Ridge and the Pritchard's Hill knoll. Single isolated high-ground hexes are dropped, and so is the modern quarry north-west of Kernstown (the deep pit and its spoil banks).
  - **Woods** (`forest` 3 / x1) where 40% or more of the hex is wooded. One polygon was added: the woods north of the stone wall that Tyler attacked through. The repo has no woods there, but the ABT and Hotchkiss maps both show them.
  - **Town** (`city`): Winchester. **Hamlet** (`wasteland` art, plain movement and defence): Kernstown and other farm clusters.
  - **Marsh**: only where the repo's Pritchard–Sandy Ridge meadow polygon lies on low ground. Most of that polygon lies on the ridge in the DEM, so only one hex is left as marsh.
- Roads are the Valley Pike, the Middle Road and the Cedar Creek Grade. Trails are the Apple Valley Road and the stone lane. Rivers are Opequon Creek, Hoge Run, Abrams Creek and Buffalo Lick Run. Every road, river and trail is a symmetric centre-to-centre path, as in the stock files.
- **The stone wall** is the eastern ~1.1 km of the repo's Glass-farm wall, running from the Glass farm to the ridge crest. On the board it is four hexes (8..11, 19). In v3 each is `mountain` terrain (v2 used `fortress`; see v3 A2) with a fence on its NW and NE edges, so it faces north toward Tyler. Fences are one-sided, the same pattern as Antietam's Bloody Lane.

## In-game test checklist (v2, still applies except item 4)

Please tick these in the game and report anything that fails. Screenshots help.

1. [ ] Both "Kernstown 1862 (CivilWar1)" and "Kernstown 1862 (CivilWar1, no art)" appear in the scenario list and load.
2. [ ] **Board art.** The painted map shows under the grid. Woods, ridges, the stone wall, roads and creeks sit on the hexes with that terrain and do not drift toward any edge. If it is offset or missing, use the no-art file and report what you saw.
3. [ ] Hex names (Sandy Ridge, Stone Wall, Glass Farm, Opequon Church, Hoge Run Ford and the others) are drawn by the game, once each, with no doubled labels.
4. [ ] The wall hexes (8..11, row 19) show the stone-wall tile, cost 1 MP and defend x2. The fences on their north edges still show.
5. [ ] **Counters.** You can read each counter without hovering: commander, unit, NATO mark, CS bottom left, MP bottom right, and "R3" on every battery. Union counters are blue, Confederate grey.
6. [ ] **Artillery.** Batteries can fire 3 hexes. On turn 1–2 the Pritchard's Hill guns (13,17) and the Sandy Ridge guns (12,20) are in range of each other, and someone fires.
7. [ ] **The stand at the wall.** The Confederate AI moves onto and holds the wall and Glass Farm rather than attacking at bad odds. It does not sit on the Sandy Ridge crest behind the wall.
8. [ ] **Retreat.** Confederate units that take a DR fall back south or south-west instead of being eliminated. Count how many units are lost to DR with no retreat hex.
9. [ ] **Ashby and Chew** stay east of the pike south of Kernstown unless they are attacked, and do not ride into Kernstown alone. If they never move even when attacked, report it.
10. [ ] **Standby.** Tyler wakes from turn 4, Sullivan from turn 6, and Burks with Marye and Lanier from turn 5. 39 IL and Huntington wake only if threatened.
11. [ ] The Confederates move first. Union activation is 5, and 7 from turn 5. Confederate activation is 6.
12. [ ] The VP hexes show their values. Wall and Glass Farm are neutral at the start, and the two CPs show "+2".
13. [ ] **Victory.** winLine is 55 and the thresholds are 6/49/98. Report the final score and result. The target is a Union win if Kimball takes the wall and a respectable Confederate result if Jackson holds it until dark.
14. [ ] Turn 1 is 3/23 14:00, turn 11 is night, and the game ends after turn 11.

## Schema assumptions (where the stock files do not settle it)

- **`firstMove: "second"`.** This value appears only in the user's own file. Antietam and Gaines use "first", and Gettysburg uses "skipToSecond".
- **Fences.** We assume a fence defends the hex that owns it, against attacks across that edge. That is our reading of Bloody Lane.
- **CP hexes.** We use Gettysburg's `pp` ints and its `"+N"` strings in `boxes` 16/17, with `initialControl` null.
- **Night turns and activation steps.** `night_turns` has stock examples only in the user's file. `activation_steps` entries appear in Gaines Mill, Chancellorsville and Second Bull Run.
- **Standby semantics, doctrine words and the threshold formula** are inferred from the stock values, not from documentation (see "Confirmed vs inferred").
- **New images:**
  - the "R3" plate (`img_emb_range3`), placed in the stock NATO-A emblem slot
  - six NATO marks (`img_nato_{inf,cav,art}_{us,cs}`)
  - all are ordinary template "image" shapes; range itself is the unit field and `boxes[7]`
- **Mountain terrain.** It keeps stock `customId` 4, but its move cost is changed from 4 to 2 to represent a gentle ridge.
- **boardArt.** `hash` is our PNG's SHA-1, and `style` is copied from Antietam. See "Board art".

## Sources

- O.R. Series I, Vol. 12, Part 1: reports of Jackson, Shields, Kimball, Tyler and Sullivan.
- Gary Ecelbarger, *"We Are in for It!": The First Battle of Kernstown* (1997).
- NPS / ABPP battle summary.
- American Battlefield Trust map *First Kernstown* (2024), `data/historic_maps/abt2024-1.png`. We used it to check the board by eye, not to georeference it: the fit left ~500 m residuals.
- Jedediah Hotchkiss' Kernstown map.
- USGS 3DEP DEM, `data/dem/kernstown_3dep.tif`.
- This repo's `data/features/kernstown_features.json` and `data/layers/*`.

## Known discrepancies

- The repo's geography and the ABT map disagree in places: Middle Road (west of Sandy Ridge in the repo, east of it on ABT), the position of Opequon Church, and how far the wall runs. The repo is taken as the source of truth.
- In the user's `user_kernstown1862.json`, the roads are one-sided (asymmetric), and Carroll's `entryHex` is `"10,0"`, a format the stock files never use. That file was not modified.
