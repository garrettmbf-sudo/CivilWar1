# Hex grid convention (single project standard)

**Status: PENDING an in-game corner-tile test.** This matches the Kernstown tooling (`kernstown-map:scripts/hex_grid.py`), but the user is still confirming it in Hex of Steel.

- **Layout:** flat-top, ODD-Q offset.
- **Columns:** run west → east.
- **Rows:** numbers increase **NORTH** (`ROW_DIRECTION = 1` in `src/hex_utils.py`). Odd columns are shifted **half a row north**.
- **Neighbour spacing:** one hex measured centre to centre, which is the same as across opposite flat sides. The column pitch is `spacing·√3/2`.
- **Edge ports:** 0=N, 1=NE, 2=SE, 3=S, 4=SW, 5=NW. `opposite = (p+3) % 6`.
- **Native tile:** a 2000×2000 PNG with a centred hex 1910 px wide (vertex to vertex) × 1672 px tall (flat to flat), per `kernstown-map:data/hex_mask.png`.

## If the in-game test shows rows increase southward
Set `ROW_DIRECTION = -1` in `src/hex_utils.py`. That is the only edit needed. `tests/test_hex_utils.py` already checks the flipped mode.

## Corner-tile test to run in Hex of Steel
Paint distinct tiles at (0,0), (1,0), (0,1) and (last col, last row), then load the map. The test should confirm:
- which screen corner holds (0,0);
- whether column 1 sits higher or lower than column 0.

## Legacy code not yet converted
- **`tools/powershell/valley_map_data.ps1`:** rectangular lat/lon rounding at 1 mile per X and Y, with no odd-q offset. Converting it means `HexX = round(miles_east / (√3/2))` plus the odd-q row correction. Regenerating needs PowerShell, and `build_valley_map.ps1` has to be updated at the same time.
- **`tools/powershell/build_valley_map.ps1`:** hand-placed X/Y with `H=125`.
- **Branches outside main** still use other layouts: v3/v4 experiments (EVEN-Q) and PR #8 corridor tools. They must be converted deliberately when merged.
- **Kernstown files:** untouched; they already define this convention.
