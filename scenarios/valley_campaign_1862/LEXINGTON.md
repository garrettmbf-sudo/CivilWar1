# Lexington, Virginia (VMI) — southern anchor

Added to `tools/powershell/valley_map_data.ps1`: `Lexington`, 37.7840 N, 79.4430 W, type `town`, not a VP, not Primary.
Coordinates are approximate town-centre/VMI values (PROVISIONAL — check against Hotchkiss/period maps before treating as verified).

## Bounds change
Lexington (37.784 N) lay south of the old `southBound` (37.90). `southBound` is now **37.70**.
Map height goes from ~125 to ~139 rows (1 mile/hex); width stays ~105. Lexington lands near HexY ≈ 6.
Because Y counts north from `southBound`, **every existing HexY from this script shifts by about +14**.

AGENTS.md / directive note: Lexington "may be included only if it serves the scenario scope and performance budget". The user asked for it; the cost is about 1,460 more hexes (~11%).

## Has to be regenerated (not done here; nothing faked)
- Run `valley_map_data.ps1` again (needs PowerShell; not available on this Linux box) to get new HexX/HexY tables.
- `tools/powershell/build_valley_map.ps1`: hardcoded `H = 125` and hand-placed town X/Y. Update it from the regenerated output; Lexington is **not** added there yet.
- Ridge, river and road polylines in `valley_map_data.ps1` end around 37.95 N. Blue Ridge/western ridges, the North (Maury) River and the Staunton–Lexington road (not the Valley Turnpike, which ends at Staunton) need sourced geometry south to Lexington.
- Any .sav, tile set, preview or v3/v4 prototype built from the old bounds.
- Status: RESEARCH data change only. Not rendered, not built, not game-tested.
