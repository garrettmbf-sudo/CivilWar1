# Kernstown 1862 (CivilWar1): a Must Attack scenario

`mKernstown1862_CW1.json` is a First Kernstown (23 March 1862) scenario for *Sekigahara 1600: Must Attack!*. It is in the same format the game's Wargame Maker exports. `build_kernstown_ma.py` generates it from this repo's Kernstown map data.

**Status: v3.1, not tested in the game.** v1 and v2 loaded and ran in the game. In playtest 1 the user played the Union, and in playtest 2 the Confederates. v3 is rebuilt from playtest 2, and v3.1 is a polish pass on v3. Both files pass `validate_kernstown_ma.py`. Nobody has loaded v3 or v3.1 yet, so treat them as unverified until someone does.

| File | What it is |
|---|---|
| `mKernstown1862_CW1.json` | The scenario with painted board art (13.1 MB, UTF-8, no BOM) |
| `mKernstown1862_CW1_noart.json` | The same scenario without `boardArt` (6.6 MB). Use it if the art fails to load or does not line up. Everything else matches the main file. |
| `DEV_WISHLIST.md` | What we would like the game to add, written for the developer |
| `build_kernstown_ma.py` | Rebuilds both files from `data/` |
| `board_art.py` | Paints `meta.boardArt` on the Must Attack grid |
| `ma_grid.py` | The Must Attack hex grid: odd-r pointy-top, edges 0=E, 1=SE, 2=SW, 3=W, 4=NW, 5=NE |
| `validate_kernstown_ma.py` | Checks a scenario against the stock scenarios |
| `render_preview.py` | Draws `preview.png` (whole board), `preview_zoom.png` (Sandy Ridge to Kernstown) and `preview_counters.png` (all 29 counters). The previews are assembled from the file. They are not game screenshots, and the hex-name font in them is our guess. |

## Install

We have not confirmed where the game keeps scenario files.

1. Find the folder that holds the stock scenarios (for example `antietam1862.json`), or the folder where the Wargame Maker saves its exports.
2. Copy `mKernstown1862_CW1.json` into that folder. Copy `mKernstown1862_CW1_noart.json` too if you want the fallback.
3. Start the game and load **Kernstown 1862 (CivilWar1)** from the scenario list or the Wargame Maker.
4. If it is not listed, import it from the Wargame Maker, and report what happened.

Do not overwrite `user_kernstown1862.json`. It is the user's own file, and these files have different names.

## What to test first

1. **The combat table takes effect.** Log a few combats and compare each result with the table under "Combat and survival". The quickest check: at 1:1, a die roll of 3 or 4 should give C (no effect). The default table gives AR on a 3 and DR on a 4.
2. **The wall.** When a unit on the wall (row 19, columns 8 to 11) takes a DR, it should fall back, not stay put or die.
3. **Garnett and Ashby survive** into the late afternoon. Count the units lost to a retreat with no open hex.
4. **The briefing.** The region and battle maps show with their portraits, and the description reads correctly.
5. **The hex names** (Glass Farm, Wall, Stone Wall, and the others) do not run into each other.

The full checklist is at the end of this file.

## The scenario at a glance

- **Board.** 32 x 36 hexes, about 300 m a hex, from beyond Sandy Ridge east to Opequon Creek and from Bartonsville north to Winchester.
- **Turns.** 11 turns of 30 minutes. Turn 1 is 3/23 at 14:00. The Confederates move first (`firstMove: "second"`).
  - Turn 10 (18:30) falls in twilight. Turn 11 (19:00) is a night turn (`night_turns: [11]`), and the game ends after it.
  - We computed the light for Winchester on 23 March 1862 (NOAA formula, local mean time): sunset 18:14, civil dusk 18:41. The briefing rounds these to 6:15 and 6:40.
- **Activation.** Union 5, rising to 7 from turn 5; Confederate 6.
- **Doctrine.** `blue: line, red: brk`, the Antietam pair. What each word means is inferred, not documented.
- **Retreat rules.** `retreat_control` 0, `retreat_distance` 1, `zoc_exit_allowed` false and `full_move_entry_allowed` false. These are the only values any stock file uses. `stacking_limit` is 2.

### Victory

| Hex | VP | Start |
|---|---|---|
| Winchester (25,3) | 30 | Union |
| Pritchard's Hill (13,15) | 20 | Union |
| Kernstown (16,20) | 15 | Union |
| Stone Wall (10,19) | 15 | neutral |
| Glass Farm (8,19) | 5 | neutral |
| Bartonsville (12,32) | 10 | Confederate |

- **Command points.** Wall (9,19) is +2 and Grade Junction (18,18), where the Cedar Creek Grade meets the pike, is +2. Both start neutral.
- **winLine 55.** That is the score if nothing changes hands: Union 65 minus Confederate 10.
  - Jackson holds the wall and Glass Farm until dark: about 35, a Confederate tactical result.
  - Kimball takes the wall and keeps his own ground, as happened historically: about 75, a Union tactical win.
- **Thresholds 6 / 49 / 98.** They come from a formula that fits all six stock scenarios exactly (inferred): operational = 0.2 x (total CS) + 0.4 x (total VP), which here is 0.2 x 55 + 0.4 x 95 = 49. Tactical is operational / 8, and strategic is 2 x operational.

### Order of battle

One strength point is about 300 men. A full battery is CS 2 and Chew's horse battery CS 1. Guns have MP 3 and range 3, infantry MP 4, cavalry MP 6. HQ counters are CS 1, MP 4. `S#` is the standby group.

**Union, Kimball (Shields' division), side 0:**
- Kimball's HQ: Shields' Div. HQ (13,14) S3
- Kimball: 14 IN/84 PA 3 (12,16), 8 OH/67 OH 3 (14,16)
- Batteries: Jenks A 1 WV Bty and Clark E 4 US Bty (13,17), Robinson L 1 OH Bty (13,16), Keeper B 1 WV Bty (16,17)
- Brodhead: 1 MI Cav 1 (6,12), OH/MD Cav 1 (19,21)
- Sullivan: 13 IN/5 OH 3 (19,18) S2, 62 OH 2 (20,16) S2, 39 IL 1 (24,14) S3
- Tyler: 7 OH/29 OH 3 (19,12), 7 IN/1 WV 3 (20,10), 110 PA 2 (21,8), all S1
- Huntington H 1 OH Bty (22,6) S3

**Confederate, Jackson (Valley District), side 1:**
- Jackson's HQ: Valley District HQ (12,24) S5
- Ashby 7 VA Cav 1 and Chew Horse Bty 1 (20,24) S5
- Fulkerson 23/37 VA 2 (9,21)
- Garnett: 2/4/27 VA 2 (10,23), 5/33 VA 2 (11,22)
- Waters W. Augusta (11,21), and McLaughlin Rockbridge with Carpenter Alleghany (12,20)
- Burks: 21 VA/1 Bn 2 (13,27), 42 VA 1 (13,28), with Marye Hampden (14,28) and Lanier Danville (14,29), all S4

Confederate batteries are named for their batteries (Rockbridge, Hampden and so on). Union batteries are named by letter and regiment, which is how each side knew them. Every unit name is commander + " " + unit (`boxes[3]` + `boxes[4]`), as in every stock file, and `boxes[5..7]` repeat CS, MP and range. The validator checks this.

| Group | Side | Units | Turn | Chance / rise |
|---|---|---|---|---|
| 1 | Union | Tyler | 4 (15:30) | 50 / 25 |
| 2 | Union | Sullivan 13 IN/5 OH, 62 OH | 6 (16:30) | 30 / 25 |
| 3 | Union | Kimball HQ, 39 IL, Huntington | never (hold) | 0 / 0 |
| 4 | Confederate | Burks, Marye, Lanier | 5 (16:00) | 40 / 30 |
| 5 | Confederate | Jackson HQ, Ashby, Chew | never (hold) | 0 / 0 |

"Hold" (turn 0, chance 0) is inferred from the Antietam and Malvern Hill hold groups to mean "stay put unless threatened". Standby only governs the computer. A human player can move any unit.

## Combat and survival

In playtest 2 the user lost Garnett's 5/33 VA again. The save shows an AR at 1:1 (die 2) with no open hex behind him. v3 changed three things to make that rarer.

**1. A gentler combat table (`rules.crt`).** Rows are odds and columns are the die roll, 1 to 6. A high roll favours the attacker. Every value is one the stock tables use. The table never gets worse for the attacker as the odds or the roll go up.

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

AE appears in 1 cell (the default has 3) and DE in 3 cells (the default has 15).

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

**2. The wall is `mountain`, not `fortress`.** Those three fortress combats suggest that a unit in a fortress never retreats, so its only bad result is DE (inferred). That made the wall a death trap. Historically Garnett fell back from it. Mountain keeps the x2 defence and lets a beaten unit retreat. The fences on the wall's north edges stay.

**3. Room to retreat.** The validator fails any stack with fewer than 2 neighbouring hexes that are all of these:
- on the board and passable
- outside enemy ZOC
- not full
- strictly farther from the nearest enemy

All 29 counters pass.

**Not changed:**
- **Retreat settings.** A `retreat_distance` of 2 needs a longer clear path, so it would probably kill more units, not fewer. `zoc_exit_allowed` is about walking out of ZOC during movement, not about retreats. Units die when the only retreat hex is in enemy ZOC. The save's `ZocToZocAllowed` looks related, but scenario rules have no field for it. What `retreat_control` 0 means is not confirmed.
- **`replacement` stays false.** Only Gettysburg sets it to true, and we don't know what it does. Saves carry `IsReplacement` and `EliminatedTurn`, which suggests eliminated units return (inferred). To test it, set it to true in the editor, get a unit eliminated, save, and look for `IsReplacement` units in the save.
- **`eliteUnit` and `suddenDeathUnit` stay false.** No stock unit sets either to true. The save fields `EliteUnit` / `EliteTriggered` suggest elite status is a one-shot trigger (inferred). Sudden death on Jackson would end the game the moment he was lost. Both can be tried as editor toggles.
- **`ai_contact_gate`** (used only by Malvern Hill) is left out, because it might freeze the AI.

## The people

- **Commanders on the map.** Kimball and Jackson have 1-CS HQ counters with their portraits, held back in standby groups 3 and 5.
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
- the commander's portrait, where one exists, beside a NATO mark (X infantry, / cavalry, dot artillery; III for a regiment, I for a battery)
- CS bottom left and MP bottom right
- an "R3" plate on every battery

Union counters are blue with white text. Confederate counters are grey with near-black text (#111) and a light outline. These are the stock plates.

## Board and board art

- **Terrain** comes from the HoS layer (`data/layers/kernstown_game.json`), the painted forest fraction and the 3DEP DEM, sampled at 37 points per hex.
  - **High ground** is `mountain` (2 MP, x2), or `rough` (3 MP, x2) where it is wooded. A hex is high ground if its topographic position on the DEM is at least 6 m or the HoS layer tags it `hill`. The modern quarry is dropped.
  - **Woods** (`forest`, 3 MP, x1) where 40% or more of the hex is wooded, plus one added polygon north of the stone wall (ABT and Hotchkiss maps).
  - **Town** (`city`) is Winchester. **Hamlets** (`wasteland` art, plain movement and defence) are Kernstown and the farm clusters.
  - **Marsh** is one hex.
- **Roads** are the Valley Pike, the Middle Road and the Cedar Creek Grade. **Trails** are the Apple Valley Road and the stone lane. **Creeks** are Opequon Creek, Hoge Run, Abrams Creek and Buffalo Lick Run. All are symmetric centre-to-centre paths, as in the stock files.
- **The stone wall** is the eastern ~1.1 km of the repo's Glass-farm wall: four hexes at (8..11, 19). Each is `mountain` with fences on its NW and NE edges, facing north toward Tyler, as Antietam's Bloody Lane does.
- **Hex names** are drawn by the game:
  - VP hexes: Winchester, Pritchard's Hill, Kernstown, Stone Wall, Glass Farm, Bartonsville
  - CP hexes: Wall, Grade Junction
  - other named hexes: Sandy Ridge, Marcauley Farm, Pritchard Farm, Mahaney House, Triplett House, Opequon Church, Opequon Ford, Milltown

  The three farmhouses are placed from the ABT 2024 map and may be up to 1 hex off. The board art does not repeat any hex name.
- **Board art** (`meta.boardArt`, 5120 x 4959 PNG). The geometry is confirmed from Antietam's fence marks: `pixel = (world − origin) x scale`, world hex centre `(√3·45·(q + ½(r&1)), 67.5·r)`, `scale` 2, `hexSize` 45, origin `(−52.471, −58.5)`.
  - It shows the repo's painted basemap, washed toward parchment, with woods, ridge hachures, the wall stones, roads, creeks and buildings.
  - It has italic road and creek names, a cartouche and a north arrow.
  - `hash` is our PNG's SHA-1. `style` "acw_b" and `version` 1 are copied from Antietam.
  - If the basemap (78 MB, gitignored) is missing, the builder paints plain parchment instead.

## Confirmed from stock files vs inferred

- **Confirmed** (seen in the stock files or saves):
  - every key and value we write (the validator checks against the stock files)
  - the grid and boardArt geometry
  - the CRT layout (40 combats)
  - neutral VPs
  - named non-VP hexes
  - side-1 standby groups
  - range 3
  - battery CS 2
  - "image" and "text" template shapes
  - commander + unit names
  - that there is no facing or rotation field
- **Inferred:**
  - what each doctrine word means
  - that turn 0 / chance 0 means hold
  - that a fence defends its own hex
  - the threshold formula and scoring
  - that fortress hexes never retreat
  - what `replacement`, `eliteUnit` and `boardArt.hash` do
  - **`firstMove: "second"`**, which only the user's own file uses
  - **Mountain move cost:** it keeps stock `customId` 4, but costs 2 MP instead of 4

## What the format can't do

See `DEV_WISHLIST.md`.

## Full in-game checklist (v3.1)

Tick these in the game and report anything that fails. Screenshots help.

1. [ ] Both "Kernstown 1862 (CivilWar1)" and "Kernstown 1862 (CivilWar1, no art)" appear and load.
2. [ ] **Board art** sits under the grid. Woods, ridges, the wall, roads and creeks fall on the right hexes and do not drift toward an edge.
3. [ ] **Hex names** show once each and do not run into each other, especially Glass Farm, Wall and Stone Wall on row 19.
4. [ ] **Counters** can be read without hovering: commander, unit, portrait or NATO mark, CS, MP, and R3 on batteries.
5. [ ] **CRT.** Combat results match the v3 table. There is no AE except at 1:3 on a 1, and no DE below 5:1.
6. [ ] **Wall.** The wall hexes cost 2 MP and defend x2. A unit there that takes a DR falls back.
7. [ ] **Survival.** Garnett and Ashby last into the late afternoon. Count the losses to a retreat with no open hex.
8. [ ] **Artillery.** The Pritchard's Hill guns (13,17) and the Sandy Ridge guns (12,20) are in range of each other on turns 1–2, and someone fires.
9. [ ] **The stand at the wall.** The Confederate AI holds the wall and Glass Farm rather than attacking at bad odds.
10. [ ] **Standby.**
    - Tyler wakes from turn 4, Sullivan from turn 6, and Burks with Marye and Lanier from turn 5.
    - 39 IL, Huntington, Ashby, Chew and both HQs move only if threatened.
11. [ ] The Confederates move first. Union activation is 5, and 7 from turn 5. Confederate activation is 6.
12. [ ] **VPs and CPs** show their values. The wall and Glass Farm start neutral.
13. [ ] **Victory.** winLine is 55 and the thresholds are 6/49/98. Report the final score.
14. [ ] **Turns.** Turn 1 is 3/23 14:00, turn 11 is night, and the game ends after turn 11.
15. [ ] **Briefing.** The region and battle maps show with their portraits and labels, and the description is readable.

## Rebuild and validate

The stock scenarios are game files, so they are not committed. Copy them into `mustattack/kernstown/ref/`:
- required: `antietam1862.json`, `gainesmill1862.json`, `gettysburg1863.json` and your own `user_kernstown1862.json`
- if you have them: `malvernhill1862.json`, `sevenpines1862.json`, `chancellorsville1863.json` and `secondbullrun1862.json`

Then run:

```
python3 build_kernstown_ma.py --basemap ../../data/basemap_painted_full.png   # writes both scenario files and board_art.png
python3 validate_kernstown_ma.py mKernstown1862_CW1.json
python3 validate_kernstown_ma.py mKernstown1862_CW1_noart.json
python3 render_preview.py mKernstown1862_CW1.json preview.png preview_zoom.png preview_counters.png
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
- In the user's `user_kernstown1862.json`, the roads are one-sided, and Carroll's `entryHex` is `"10,0"`. That file was not modified.

## Change history

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
