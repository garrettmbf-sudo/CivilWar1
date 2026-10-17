# Repository inventory and reconciliation — 17 Oct 2026

Read-only audit of `main` (ba8a79e), `kernstown-map` (c125296, release `kernstown-v0.4.0`) and the open Valley branches/PRs #1, #5–#8. Nothing on any of those branches was modified.

## What exists
| Area | Location | Notes |
| --- | --- | --- |
| Historical OOB | `historical_data/*_1862.csv`, `src/oob.py`, `tests/test_oob_1862.py` | Canonical. Only copy. Preserve and extend. |
| Commander portraits | 179 `mdl_*.png` at repo root, 35 in `reference/`; `historical_data/portrait_manifest.csv` | Approved/audited. **Not moved or renamed.** `scripts/check_portrait_manifest.py` passes. |
| Unit counters | `Unit_*.png` at root and 86 files under `units/` | Many root files are byte-identical to `units/` copies (see duplicate list). Not deleted — game consumers may use root names (AGENTS.md rule 2/5). |
| Map samples | `maps/` (140 files, .sav samples + tile PNGs) | Preserved. |
| HoS mod/Harmony samples | `docs/3574617535/` | Reference only; binaries not for redistribution. |
| Valley 1-mile PowerShell tools | `tools/powershell/{valley_map_data,build_valley_map,beautify_map,map_reader}.ps1` | Canonical copy. Byte-identical copies also on `kernstown-map:tools/`. |
| Python hex / .sav tools | `src/hex_utils.py`, `src/sav_parser.py`, `scripts/*sav*.py` | |
| Kernstown v0.4.0 | branch `kernstown-map` (unrelated root history, 136 MB tree; 62×55 hexes @250 yd; 3,410 tiles in release zips) | Read only — being finished by another agent. |
| PR #1 `shenandoah-valley-hex-map-9814d` | `src/binary_formatter.py`, `src/map_generator.py` | Competing .sav writer; overlaps `src/sav_parser.py`. |
| PR #5 / #6 | `experiments/valley_v3`, `valley_v4`, `src/valley_map_topology.py`, `*_v4_candidate.ps1` | #6 is #5 plus 3 files (#5 is a strict subset). 125×130-hex prototypes. |
| PR #7 | `tools/edge_qa/validate_tile_edges.py`, tile catalog | Second edge validator, separate from Kernstown's `tools/validate/validate_tile_edges.py`. |
| PR #8 | `tools/valley_corridor/` | 250-yd Winchester–New Market corridor (~92,700 positions). Different scale from the 1-mile campaign. |

## Conflicts / duplication found
1. **Hex conventions conflict (unresolved):** `src/hex_utils.py` = pointy-top odd-r/even-r axial helpers; `kernstown-map:scripts/hex_grid.py` = flat-top odd-q, rows increasing northward, 250 yd; `valley_map_data.ps1` = plain lat/lon→(X,Y) rectangular rounding, no hex offset at all, Y grows north from `southBound`; `build_valley_map.ps1` uses its own hand-placed X/Y table with `H=125`; v3/v4 experiments use EVEN-Q. The engine-correct layout is not yet confirmed in-game. Proposed single convention: Kernstown's flat-top odd-q (matches stock flat-top tile masks), to be verified in Hex of Steel before converting the others.
2. **Two map-dimension sources for the Valley:** `valley_map_data.ps1` computes bounds, `build_valley_map.ps1` hardcodes `H=125` and town X/Y. They drift as soon as bounds change (see Lexington).
3. **Two tile-edge validators** (Kernstown `tools/validate/` vs PR #7 `tools/edge_qa/`) — should merge into one.
4. **Two .sav approaches:** PR #1 `binary_formatter.py` vs Kernstown `build_kernstown_map.ps1` (deserialises a trusted template via game assemblies) vs `scripts/generate_sav.py` placeholder. None is GAME_LOAD_TESTED here.
5. **Duplicate PowerShell tools:** 4 byte-identical files on `kernstown-map:tools/` and `main:tools/powershell/`.
6. **Duplicate docs:** `docs/sav_format.md`→`sav-format.md`, `docs/mod_structure.md`→`mod-format.md` (already pointer stubs; kept).
7. **Duplicate image blobs on main:** 60 groups (15 involve `mdl_` portraits, e.g. root `mdl_CSA_CSWinder.png` = `reference/mdl_CSA_CSWinder.png`; also `mdl_CSA_WHJackson.png` = `mdl_CSA_WHTJackson.png`). Listed in `duplicate_blobs_main.csv`. Nothing removed — identical bytes under two approved names need a user decision.
8. **Kernstown installer** pulls its build scripts from the moving `kernstown-map` branch (`$Branch`) rather than the tag — the directive asks for these to be pinned. Not changed (Kernstown is off limits).

## Reconciliation matrix
| System | Authoritative material | Conflict | Action |
| --- | --- | --- | --- |
| Historical OOB | `historical_data/` CSVs | Incomplete dated assignments | Preserve, validate, extend |
| Portraits | `portrait_manifest.csv` + existing files | Missing portraits; identical-byte duplicates | Preserve; research gaps; user decides on duplicates |
| Kernstown terrain | v0.4.0 art + pipeline | 250-yd tactical scale | Reuse pipeline, not slices; move to `scenarios/kernstown/` only after the other agent finishes |
| Full Valley geography | `valley_map_data.ps1` (+ v3/v4/corridor) | Provisional coords, mixed grids | Georeference, pick one grid, rebuild |
| Tile connections | two six-edge validators | Divergent code | Merge into one |
| Native saves | Kernstown PS builder, PR #1 | Not game-tested | Verify in-game |
| Installation | Kernstown `install.ps1` | Branch-pinned source, size | Pin to tag, harden (later, by Kernstown owner) |
