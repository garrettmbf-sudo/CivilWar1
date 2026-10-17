# Decisions log (kernstown-map)

Settled decisions for the Kernstown map; change them only with the user's say-so. The project-wide log is
General Eggbot's `docs/decisions.md` (PR #19). This entry is the Kernstown detail of its **D15** ("Hex parity, resolved Q1:
even-q native, per MapGO.cs ... no conversion layer; `ROW_DIRECTION` removed"); D15 also supersedes D9's "no re-render"
for this re-cut. If the two ever disagree, D15 wins.

## 2026-10-17: Grid convention: match the game (even-q, rows north, 4.42:5.1)

**Decision.** Every Kernstown script, data file, tile name and validator uses Hex of Steel's own hex convention,
with **no conversion layer**:

- flat-top hexes; hex `(col,row)` = `Tile[col*SizeY + row]` = tile `SV_K_<col>_<row>.png`;
- origin `(0,0)` is the **south-west** hex; columns increase east, **rows increase north**;
- **even columns are raised half a row** (even-q);
- column pitch : row pitch = **4.42 : 5.1** (world units); the 0.857 (sqrt(3)/2) ratio is not used.

**Source (decompiled Assembly-CSharp, Hex of Steel 8.4.14):**

- `MapGO.cs:452-459`, tile placement. Odd column: `(col*4.42, row*5.1)`; even column: `(col*4.42, row*5.1 + 2.55)`. Unity +y is up/north, and `CameraGO` has no rotation.
- `Utils.cs:1666-1706`, neighbours. Even col: `(c±1,r)`, `(c±1,r+1)`. Odd col: `(c±1,r)`, `(c±1,r-1)`. Plus `(c,r±1)`. This is consistent only with even columns raised.
- `ModsManager.cs` ~996-1027 (`Graphics/Tiles`), tile sprites. Each PNG is resized to 512 px wide with `pixelsPerUnit = 330*512/srcWidth`, which means **330 source px per world unit**, pivot at the centre. For our 2000 px tiles: row pitch 1683 px, column pitch 1458.6 px. The TileGO prefab scale is a Unity asset, not code, and is assumed to be 1; the slicer's 21.5 px bleed covers ±20 px of error.
- The ACW sample .sav confirms rows run north: New Orleans is at y=6, Pittsburgh at y=57.

**`ROW_DIRECTION = -1` is wrong and is removed** (D15). Rows do not run south, and no row flip, parity flip or "display conversion"
is applied anywhere. The pre-v0.4.2 pipeline (`scripts/hex_grid.py` "odd-q, odd columns shifted down") raised
**odd** columns. In the game this put every other column half a row off, which showed as a one-hex jog at every column
seam (the v0.4.1 Pike). Any code or document that flips rows, raises odd columns, or uses 0.857 for
this map is a bug.

**Consequences (v0.4.2).**

- The grid was re-indexed, not re-drawn: `new(c,r) = legacy(c, r+1 if c even else r)`. Hex centres on the ground are unchanged (within 9 m).
- The map is now 62 x 54. The legacy even row 0 and odd row 54 were dropped: 62 hexes, all open ground, no units.
- See `scripts/migrate_legacy_oddq_to_game.py` and `docs/kernstown_unit_coord_change.md`.
- Validators place tiles exactly as `MapGO.cs:452-459` does: `tools/validate/*`, `docs/EDGE_VALIDATION.md`.
- One temporary exception, kept only until the units file is re-issued: `tools/build_kernstown_map.ps1` converts unit hexes from `kernstown_units.json` (owned by Quartermaster) until that file carries `"grid_convention": "game-native"`. Remove the shim after that.
