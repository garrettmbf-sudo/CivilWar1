# Hex grid convention (single project standard)

**Status: DECIDED, 2026-10-17.** The project uses Hex of Steel's **native** layout. There is no conversion layer: our `(col, row)` is the game's `(PosX, PosY)`. Major Hotchkiss decided this from `MapGO.cs:452-459` and the evidence in `/workspace/parity_check/` on the box (see `docs/decisions.md`).

- **Layout:** flat-top, **EVEN-Q** offset.
- **Columns:** run west → east. **Rows:** numbers increase **NORTH**, because Unity y points up.
- **Shift:** **even** columns sit half a row **north** of odd columns.
- **Game placement** (`MapGO`): `x = col·4.42`, `y = row·5.1 + (2.55 if col is even)`. The column-to-row pitch ratio is **4.42 : 5.1** (0.8667; a regular hex would be 0.8660). `src/hex_utils.py` uses these exact constants (`game_position`, `hex_center`).
- **Neighbours** (`Utils.GetAllTilesNeighbours`), with ports 0=N, 1=NE, 2=SE, 3=S, 4=SW, 5=NW and `opposite = (p+3) % 6`:

| Port | Even column | Odd column |
| --- | --- | --- |
| N | (c, r+1) | (c, r+1) |
| NE | (c+1, r+1) | (c+1, r) |
| SE | (c+1, r) | (c+1, r−1) |
| S | (c, r−1) | (c, r−1) |
| SW | (c−1, r) | (c−1, r−1) |
| NW | (c−1, r+1) | (c−1, r) |

- **Axial:** `q = col`, `r = row − (col + (col & 1)) // 2`. Cube coordinates are `(q, r, −q−r)`, and distance is the axial or cube distance.
- **Native tile:** a 2000×2000 PNG with a centred hex 1910 px wide (vertex to vertex) × 1672 px tall (flat to flat), per `kernstown-map:data/hex_mask.png`.

The old odd-q layout and its `ROW_DIRECTION` switch are removed. `tests/test_hex_utils.py` checks neighbours and positions against transcriptions of the game's own code.

## PowerShell map tools (converted 2026-10-17)
`tools/powershell/beautify_map.ps1`, `valley_map_data.ps1` and `build_valley_map.ps1` all dot-source `tools/powershell/HexEvenQ.ps1`. That file is a line-for-line port of this module (neighbours, axial, distance, `game_position`, `hex_center`, `point_to_offset`, `hex_line`):
- `valley_map_data.ps1` snaps lat/lon (in miles) to the nearest even-q hex at 1 mile per row. The map is now 123 × 140.
- `build_valley_map.ps1` keeps its hand-placed waypoints in frame miles. It converts them to hexes, traces roads and rivers as chains of game-adjacent hexes, and judges ridges at each hex's true centre. The map is 122 × 125.
- `beautify_map.ps1` uses the game's neighbour table.

`tests/test_powershell_even_q.py` checks them against this module. It parses the formulas always, and runs them under `pwsh` when pwsh is available; that part is skipped on CI unless `RUN_PWSH_TESTS=1`. The river/road art lookup in `beautify_map.ps1` (edge pair → River1–9) still needs an in-game check, because the old neighbour table was mirrored north/south.

## Legacy code not yet converted
- **Branches outside main** still use other layouts: PR #8 corridor tools, and the v3/v4 experiments, which are even-q but may have a different row direction. They must be converted deliberately when merged.
- **Kernstown:** Hotchkiss re-cuts it to native even-q as v0.4.2 on `kernstown-map`. Until that lands, `kernstown-map:scripts/hex_grid.py` (v0.4.1) is still odd-q. Other lanes don't edit it.
