# Kernstown 1862 (CivilWar1): a Must Attack scenario

`mKernstown1862_CW1.json` is a First Kernstown (23 March 1862) scenario for *Sekigahara 1600: Must Attack!*, in the format the in-game Wargame Maker exports. It was built from this repo's Kernstown map data, not drawn by hand.

**Status: not tested in the game.** The file passes `validate_kernstown_ma.py`, which compares it with the stock scenarios, but nobody has loaded it in the game yet. Until someone does, treat it as unverified.

| File | What it is |
|---|---|
| `mKernstown1862_CW1.json` | The scenario (5.2 MB, UTF-8, no BOM, compact JSON like the stock files) |
| `build_kernstown_ma.py` | Rebuilds the scenario from `data/` (it is deterministic: the same inputs give the same bytes) |
| `ma_grid.py` | The Must Attack hex grid: odd-r pointy-top, edges 0=E, 1=SE, 2=SW, 3=W, 4=NW, 5=NE |
| `validate_kernstown_ma.py` | Checks the scenario against the stock scenarios |
| `render_preview.py`, `preview.png` | Renders the board, roads, rivers, fences, VP/CP hexes and units |

## Install (path not verified)

1. Copy `mKernstown1862_CW1.json` into the game's scenario folder. We have not confirmed where that folder is. Look next to the stock `antietam1862.json` and the other stock scenarios, or wherever the Wargame Maker saves its exports, and put the file in the same folder.
2. Start the game. Open the scenario list or the Wargame Maker, then load **Kernstown 1862 (CivilWar1)**.
3. If the game does not list the scenario, try importing it from the Wargame Maker. Then report what happened.

## Rebuild and validate

The stock scenarios are game files, so they are not committed. Export or copy them into `mustattack/kernstown/ref/`: `antietam1862.json`, `gainesmill1862.json`, `gettysburg1863.json`, and your own `user_kernstown1862.json`. Then run:

```
python3 build_kernstown_ma.py            # needs numpy, scipy, rasterio, Pillow; reads data/ in this repo
python3 validate_kernstown_ma.py         # exits 1 on any error
python3 render_preview.py mKernstown1862_CW1.json preview.png
```

The counter font is Playfair Display, the same font the stock templates name. Set `MA_COUNTER_FONT` to point at a local copy of it.

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
- **The stone wall** is the eastern ~1.1 km of the repo's Glass-farm wall, running from the Glass farm to the ridge crest. On the board it is four hexes (8..11, 19). Each has a fence on its NW and NE edges, so it faces north toward Tyler. Fences are one-sided, the same pattern as Antietam's Bloody Lane.

## Order of battle (situation at 2 PM)

Each strength point is roughly 300 infantry, or one battery. Batteries are CS 1, MP 3, range 2, and show an "R2" badge. Cavalry are CS 1, MP 6.

**Union, Kimball (Shields' division), side 0**

| Unit | CS-MP | Start |
|---|---|---|
| Kimball 14 IN / 84 PA | 3-4 | Pritchard's Hill |
| Kimball 8 OH / 67 OH | 3-4 | Pike north of Kernstown |
| Jenks A 1 WV, Clark E 4 US, Robinson L 1 OH, Davey B 1 WV | 1-3 r2 each | Pritchard's Hill / Kernstown |
| Brodhead 1 MI Cav; Ohio/Md/WV Cav | 1-6 each | Middle Road (west) and east of Kernstown |
| Sullivan 13 IN / 5 OH; 62 OH | 3-4; 2-4 | East of the pike, **standby group 2** (from 16:00) |
| Tyler 7 OH / 29 OH; 7 IN / 1 WV; 110 PA | 3-4; 3-4; 2-4 | Pike toward Winchester, **standby group 1** (from 15:00) |
| Sullivan 39 IL; Huntington H 1 OH | 1-4; 1-3 r2 | Reserve, **standby group 3** (never committed; wakes only if threatened) |

Union totals: 20 infantry CS, 6 batteries, 2 cavalry.

**Confederate, Jackson (Valley District), side 1**

| Unit | CS-MP | Start |
|---|---|---|
| Ashby 7 VA Cav | 1-6 | East of the pike near Bartonsville |
| Chew horse artillery | 1-3 r2 | East of the pike |
| Fulkerson 23 / 37 VA | 2-4 | South end of Sandy Ridge |
| Garnett 2 / 4 / 27 VA; 5 / 33 VA | 2-4 each | Behind Fulkerson |
| Burks 21 VA / 1 VA Bn; 42 VA | 2-4; 1-4 | Bartonsville |
| McLaughlin Rockbridge, Carpenter Alleghany, Waters W. Augusta, Marye Hampden, Lanier Danville | 1-3 r2 each | With the infantry |

Confederate totals: 9 infantry CS, 6 batteries, 1 cavalry. That matches about 2,700 infantry engaged against about 6,000.

Corrections to `data/layers/kernstown_units.json`:
- Carroll did not command a brigade at Kernstown, so 8 OH and 67 OH are under Kimball.
- The battery commanders are the ones at Kernstown: McLaughlin, Marye, Lanier and Waters.
- Pleasants' battery and the 48th VA are left out because they were not engaged.

## Victory, activation and balance

- **VP hexes** (the same value for both sides, as in all stock files):

  | Hex | VP | Initial control |
  |---|---|---|
  | Winchester | 30 | Union |
  | Pritchard's Hill | 20 | Union |
  | Kernstown | 15 | Union |
  | Stone Wall | 15 | Confederate |
  | Bartonsville | 10 | Confederate |

- **CP hexes**, using the Gettysburg pattern: Sandy Ridge crest +2 and Pike & Cedar Creek Grade +2.
- **Starting score** from the Union (first side) view: 65 − 25 = **+40**.
- **`winLine` 45; thresholds 10 / 72 / 144.**
  - In the stock files, `winLine` sits near the historical result. Operational is about 0.8 × total VP and strategic about 2 × operational. We copied those ratios here (90 VP total).
  - The Union has to *gain* to win. If Jackson sits on the wall and trades evenly, the score stays about +40, below the line: a narrow Confederate result.
  - The historical outcome is Kimball taking the wall while holding his own ground. That gives about +70, a Union tactical win.
  - If Jackson takes Pritchard's Hill or Kernstown, the score falls fast, toward a large Confederate win.
  - Nothing is scripted. Both sides can reach every outcome.
- **The Confederates move first** (`firstMove: "second"`, taken from the user's own Kernstown file).
- **Activation caps:**
  - Union 5, rising to 7 at turn 5 (16:00). This models Kimball's slow, fragmented command after Shields was wounded.
  - Confederate 6.
  - For scale: stock Antietam is 14/18 of 100 units, and the user's file is 6/7 of 15.
- **Standby groups** (stock rules, same shape as Antietam's three groups):

  | Group | Units | Earliest turn | Chance / rise per turn |
  |---|---|---|---|
  | 1 | Tyler | T3 (15:00) | 40 / +30 |
  | 2 | Sullivan | T5 | 30 / +25 |
  | 3 | 39 IL, Huntington | Never (turn 0, chance 0, like Antietam's V Corps) | – |

- **Turns:** 11 turns, 14:00–19:00 on 23 March. Sunset is about 18:15, and turn 11 (19:00) is a night turn. Jackson retreated at about 19:30.
- **No elite units.** Garnett's brigade is famous, but at Kernstown it ran out of ammunition and fell back, so an elite rating isn't justified.

## In-game test checklist

Please tick these in the game and report anything that fails. Screenshots help.

1. [ ] The scenario appears in the list as "Kernstown 1862 (CivilWar1)", and the description shows in your language. English is used for every language slot.
2. [ ] The region and battle schematic maps show, with labels.
3. [ ] The board is 32 x 36. Winchester is in the north-east, Bartonsville in the south, and Sandy Ridge is the west-centre band of high ground.
4. [ ] Terrain art and costs: pasture is plain, woods are forest, the hachured tiles are high ground (2 MP, x2 defence), and Kernstown uses the house tiles.
5. [ ] Roads and rivers draw as continuous lines with no dangling stubs. The pike runs from Winchester through Kernstown to Bartonsville.
6. [ ] The stone wall shows as a fence on the north edges of hexes 8..11 in row 19, and it gives defence against an attack from the north only.
7. [ ] Counters: Union counters are blue and Confederate counters grey, and each shows its name, CS on the left and MP on the right. Batteries show "R2" and fire two hexes.
8. [ ] There are 15 Union and 12 Confederate units, never more than 2 per hex. Tyler and Sullivan show as standby, and Tyler wakes from turn 3 onward.
9. [ ] The Confederates move first. Union activation is 5, and 7 from turn 5.
10. [ ] The VP hexes show their names and values, with the correct initial owner. The two CP hexes show "+2".
11. [ ] The opening score is about +40 for the Union, and the victory screen uses winLine 45 and thresholds 10/72/144.
12. [ ] Turn 1 is 3/23 14:00, turn 11 is night, and the game ends after turn 11.
13. [ ] Playtest balance: report the final score of a few games for each side. If the Confederates win too easily, raise the Union activation cap or lower `winLine`.

## Schema assumptions (where the stock files do not settle it)

- **`firstMove: "second"`.** This value appears only in the user's own file. Antietam and Gaines use "first", and Gettysburg uses "skipToSecond".
- **Fences.** We assume a fence defends the hex that owns it, against attacks across that edge. That is our reading of Bloody Lane.
- **CP hexes.** We copied Gettysburg's `pp` ints and its `"+N"` strings in boxes 16/17 into an Antietam-schema file. The validator allows them because they appear in stock.
- **Night turns and activation steps.** Only one stock file shows each: `night_turns` only in the user's file, and `activation_steps` entries only in Gaines Mill.
- **Standby semantics.** These are inferred from the stock values, not from documentation.
- **The "R2" badge** is a new image in place of the stock NATO-A emblem, at the same position. Range itself is in the unit field and in `boxes[7]`.
- **Mountain terrain.** It keeps stock `customId` 4, but its move cost is changed from 4 to 2 to represent a gentle ridge.
- **No board art.** We set no `boardArt`, since not every stock file has one.

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
