# Kernstown unit coordinates: change for Quartermaster (v0.4.2)

**Owner of `data/layers/kernstown_units.json`: Quartermaster.** This file was *not* edited by the map work.
Please re-issue it in the new coordinates below and add `"grid_convention": "game-native"` at the top level.

## What changed
From v0.4.2 the Kernstown map uses Hex of Steel's own hex convention (see `docs/decisions.md`):
flat-top, origin (0,0) = south-west hex, rows increase north, **even columns raised half a row**
(`MapGO.cs:452-459`). The old pipeline raised **odd** columns, so the old (col,row) put every even-column
hex half a row off in game. The map is now 62 x 54 (was 62 x 55): the old even-column row 0 and odd-column
row 54 were half/fully outside the painted map and were dropped (all open ground, no units).

The ground does not move: every hex keeps the same centre (within 9 m). Only the numbers change:

```
new_col = old_col
new_row = old_row - 1   if old_col is even
new_row = old_row       if old_col is odd
```
(`scripts/hex_grid.py: legacy_oddq_to_game`). No unit is lost: no unit was on a dropped hex.

## New coordinates for the 18 units in the current file
| Side | Unit | old col,row | **new col,row** | |
|---|---|---|---|---|
| Confederacy | Stonewall Bde (Garnett) 2,4,5,27,33 VA | 17,23 | 17,23 | same |
| Confederacy | Fulkerson's Bde 23,37 VA | 15,23 | 15,23 | same |
| Confederacy | Burks' Bde 21,42,48 VA, 1 VA Bn | 17,20 | 17,20 | same |
| Confederacy | Ashby's 7th Virginia Cavalry | 27,17 | 27,17 | same |
| Confederacy | Chew's Horse Artillery | 26,18 | 26,17 | moved |
| Confederacy | Rockbridge Artillery (Poague) | 16,22 | 16,21 | moved |
| Confederacy | Carpenter's Alleghany Battery | 18,22 | 18,21 | moved |
| Confederacy | Caskie's Hampden Artillery | 15,22 | 15,22 | same |
| Confederacy | Wooding's Danville Artillery | 20,22 | 20,21 | moved |
| Confederacy | Pleasants' Battery | 20,21 | 20,20 | moved |
| Union | 1st Bde (Kimball) 14 IN, 8,67 OH, 84 PA | 25,26 | 25,26 | same |
| Union | 2nd Bde (Sullivan) 39 IL, 13 IN, 5,62 OH | 29,24 | 29,24 | same |
| Union | 3rd Bde (Tyler) 7 IN, 7,29 OH, 110 PA, 1 WV | 17,25 | 17,25 | same |
| Union | Btry A West Virginia Arty (Jenks) | 25,27 | 25,27 | same |
| Union | Btry B West Virginia Arty | 27,27 | 27,27 | same |
| Union | Btry E 4th US Artillery (Clark) | 26,27 | 26,26 | moved |
| Union | Btry L 1st Ohio Arty (Robinson) | 26,26 | 26,25 | moved |
| Union | Brodhead's Cav (MI/PA/MD/WV/OH detachments) | 13,25 | 13,25 | same |

Stone-wall hexes (DamageModificator 35) in the new grid: 14,22  15,23  16,22  17,23  18,22  19,22  20,22.
Stonewall Brigade (17,23) and Fulkerson (15,23) are still on wall hexes, as before.

## Until the file is re-issued
`tools/build_kernstown_map.ps1` detects a units file **without** `"grid_convention": "game-native"` and applies the
rule above to the units only (with a warning), so v0.4.2 scenarios already place the units correctly. When you
re-issue the file in the new coordinates, you **must** add the marker, or the builder would move even-column units
a second time. After that the shim can be deleted (see the TEMPORARY block in the builder).
