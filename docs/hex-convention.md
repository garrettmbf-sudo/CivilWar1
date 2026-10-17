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

## Legacy code not yet converted
- **`tools/powershell/valley_map_data.ps1`:** rectangular lat/lon rounding at 1 mile per X and Y, with no hex offset. Converting it means `HexX = round(miles_east / 0.8667)` plus the even-q row correction (even columns +½ row). Regenerating needs PowerShell, and `build_valley_map.ps1` has to be updated at the same time.
- **`tools/powershell/build_valley_map.ps1`:** hand-placed X/Y with `H=125`.
- **`tools/powershell/beautify_map.ps1`:** its comment says "even-q", but it uses N=(0,−1), so rows increase south, and its even-column NE is (c+1, r), which puts odd columns north. That is not the native layout. Its neighbour tables need replacing with the ones above before reuse.
- **Branches outside main** still use other layouts: PR #8 corridor tools, and the v3/v4 experiments, which are even-q but may have a different row direction. They must be converted deliberately when merged.
- **Kernstown:** Hotchkiss re-cuts it to native even-q as v0.4.2 on `kernstown-map`. Until that lands, `kernstown-map:scripts/hex_grid.py` (v0.4.1) is still odd-q. Other lanes don't edit it.
