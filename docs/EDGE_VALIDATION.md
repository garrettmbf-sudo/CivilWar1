# Tile edge validation (v0.4.2, game-native grid)

## Game placement model (used by every validator)
- Tile placement follows `MapGO.cs:452-459` exactly. Tile `SV_K_c_r` is hex (PosX=c, PosY=r).
  - Odd column: placed at world `(c*4.42, r*5.1)`.
  - Even column: placed at `(c*4.42, r*5.1 + 2.55)`. Even columns are raised half a row.
  - +y is north, so rows run north from (0,0) in the SW corner.
- Neighbours follow `Utils.cs:1666-1706`.
- Tile sprite scale (`ModsManager.cs`, Graphics/Tiles) is 330 source px per world unit, pivot at the centre.
  - Row pitch 1683 px, column pitch 1458.6 px.
  - The cell hex has half-height 841.5 px and vertex half-width 972.4 px inside each 2000 px PNG.
- All of this is implemented once, in `scripts/hex_grid.py`. Validators import it; none has its own convention.
- The slicer (`painted_sections/slice_full_tiles.py`) maps the master at the same isotropic scale. The alpha is the cell hex plus 21.5 px of bleed (1.5 px antialiased ramp), so ±20 px of placement error stays covered.

## Tools
| Tool | Output |
|---|---|
| `tools/validate/validate_tile_edges.py <dir> <csv> <png>` | `previews/edge_validation_v042{.csv,_summary.txt,.png}` |
| `tools/validate/check_pike_continuity.py <dir>` | `previews/pike_continuity_summary.txt`. Bisects every Pike seam crossing to the shared cell boundary and compares both tiles. |
| `tools/validate/reassemble_tiles.py <dir>` | `previews/reassembled_from_tiles.jpg`, `seam_closeup_stone_wall.jpg`, `seam_closeup_pike_road.jpg`, **`pike_game_placement.jpg`** (master vs tiles under game placement) |
| `tools/validate/check_buildings.py` | Checks that no painted building footprint overlaps the Pike, roads, lanes, streets, the railroad or creeks |

Setting `PARITY_CONTROL=1` runs the edge or Pike check with the old odd-raised stagger, as a negative control.

## Results: final compressed tiles, 3348, 62 x 54
- **Edges:** 9813 edges.
  - dE mean 2.62, median 2.58, p95 3.91. The within-tile texture floor at the same separation is 2.63.
  - 0 alpha seams; 0 edges with less than 20 px of bleed.
  - The feature-lag heuristic flags 801 of 9104 edges. This is texture noise, at the same rate as v0.3.1 "after" (805).
  - Negative control (odd-raised): dE mean 6.46, 6145 edges with dE > 5, 4703 feature-misaligned.
- **Pike:** 89 seam crossings, 64 of them across column seams.
  - Tile vs neighbouring tile at the boundary: dE mean 0.18, max 1.10. Min alpha 255. 0 crossings with dE > 10.
  - Steps between Pike hexes: 89/89 adjacent.
  - Tiles vs master: dE mean 1.21, p99 3.85.
  - Negative control: dE mean 36.3, max 72.1, 57 crossings > 10. This is the v0.4.1 one-hex jog.
- **Buildings:** 217 checked, 0 on roads, rail or water. 164 were nudged off at paint time (max 45 px).

Not yet tested in game. The 330 px/unit scale assumes the TileGO prefab scale is 1. The bleed covers ±20 px if it is not.
