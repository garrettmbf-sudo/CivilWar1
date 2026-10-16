# Tile edge validation (v0.3.1)

Validator: `tools/validate/validate_tile_edges.py` (CSV: previews/edge_validation_{before,after}.csv, heatmaps previews/edge_validation_{before,after}.png).
Reassembly: `tools/validate/reassemble_tiles.py` -> previews/reassembled_from_tiles.jpg, previews/seam_closeup_stone_wall.jpg, previews/seam_closeup_pike_road.jpg.

Game layout model: SV_K_c_r -> hex (c,r) (kernstown_game.json, tile_name == SV_K_col_row for all 3410), flat-top odd-q, rows increase north,
odd columns half a row north (scripts/hex_grid.py). Tiles abut by the stock alpha hex data/hex_mask.png: 1910 x 1672 px centred at (999.5, 999.5)
inside the 2000 px PNG -> col pitch 1432.5 px, row pitch 1672 px. 9997 unique edges, 96 samples per edge, 6 px inside each tile.

## Root cause
The old slicer stretched a 2R x 2R basemap square across the full 2000 px PNG, then cut it with the 1910x1672 stock mask. The hex content was
therefore 4.7 % (horizontal) / 3.6 % (vertical) too zoomed: each tile showed slightly less than its own hex, so features jumped at every
edge (~45-60 px offsets at the tile edges). Parity/orientation/name mapping were already consistent (verified: a parity-flipped composite is grossly
discontinuous). Alpha was a binary NEAREST-resized mask with no overlap (risk of hairline seams under game filtering).

## Fix (painted_sections/slice_full_tiles.py)
- Basemap hex mapped exactly onto the stock hex: sx = 1910/(2R), sy = 1672/(sqrt3 R) (affine, bicubic).
- Analytic hex alpha with 4 px bleed beyond the hex edge and a 1.5 px antialiased ramp.
- Tiles kept at 2000x2000 (stock HoS tile size / mask; shrinking not verified as safe in-game, so not done).

## Metrics
Before: edges=9997 mean_dE=6.91 median_dE=6.28 p95_dE=12.66 dE>5=8190 feature_edges=9730 feature_misaligned(>=30px)=8530 alpha_seam_edges=0 bad_edges=9492
After:  edges=9997 mean_dE=3.13 median_dE=2.91 p95_dE=5.38 texture_floor_dE=3.18 dE>5=690 feature_edges=9780 feature_misaligned(>=30px)=805 alpha_seam_edges=0 bad_edges=1327

After the fix the cross-edge dE (3.13) equals the within-tile texture noise floor at the same 12 px separation (3.18), i.e. edges are
statistically indistinguishable from tile interiors. Remaining "bad"/"feature lag" flags are dominated by painted-texture noise
(the lag detector is a heuristic); spot-check closeups across the pike and the stone wall show continuous features.
Not tested in-game yet.
