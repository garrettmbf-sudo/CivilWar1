# Kernstown — awaiting approval (no slice)

## Winchester (March 1862 sparse rebuild)
- ~39 buildings: contiguous brick commercial strip on Loudoun St only (with vacant-lot gaps)
- Side streets: detached houses, yards, gardens, outbuildings, orchards, vacant lots
- Landmarks: Courthouse, Taylor Hotel, Jackson's HQ (Gothic cottage), Christ Episcopal + Kent St Presbyterian + 3 churches
- Fort Collier + Fort Alabama: painted earthwork ridges + cgpt2 battery/redoubt sprites
- Labels: WINCHESTER, Courthouse, Taylor Hotel, Jackson's HQ, Fort Collier

## Kernstown battlefield
- VEX dropped to 1.0; soft hillshade map-wide; ~60 ft contour interval, thinned in town
- Sandy Ridge: mosaic of 1–3 hex leafless gray-brown woodlots + open fields (not solid forest)
- Meadow between ridges: marshy with tufts/wet glints
- Pritchard-Grim farm: cgpt2 stone farmhouse + bank barn + log cabin + tenant
- Kernstown village: ~11 buildings on Pike + Cedar Creek Grade
- Opequon Church: cgpt2 stone church with graveyard
- Stone wall: thinner light limestone gray, continuous ~7 hexes
- Field walls near town; muddy tan early-spring fields

## New sprites (cgpt2_*)
Cut from user sheets via rembg (buildings only; skipped road/river/field):
stone_house, stone_farmhouse, bank_barn, stone_church_graveyard, brick_church_graveyard,
mill_wheel, covered_bridge(s), stone_arch_bridge, rr_trestle, depot_water_tower,
earthwork_battery, earthwork_redoubt

## Previews
- previews/closeup_winchester.jpg
- previews/closeup_sandy_wall_pritchard.jpg
- previews/kernstown_full.jpg

## 2026-10-16 — procedural art pass + mod build HALTED (switching to painted sections)
Done / saved:
- scripts/texture_pass.py (new): reference-sheet patch quilting (ground, woods), plowed fields,
  New Market-style hex_patchwork (hex-edge fields + fences). Patches in data/assets/refpatches/rRcC.png.
- scripts/compose_painted_map.py edits: ground quilt + hex patchwork wired in; woods quilt; fewer tree sprites;
  darker low-elevation stops (east-side pale fix); muted gray-blue creeks with stony bank pebbles;
  stone wall redrawn as one smoothed polyline ~38% inside Confed hexes (not on grid edge);
  more solid Winchester side streets; preview grid alpha 210->150; dumps data/layers/painted_forest_fraction.json.
  NOT RENDERED: run was killed; previews/ and data/basemap_kernstown.png are still the OLD art.
- scripts/build_game_layers.py (new, not yet run): writes data/layers/kernstown_game.json
  (woods dmg25 MP3, town dmg40, marsh MP4, Pike/roads MP1, wall dmg35 x7, primary VP 42,41, secondary 27,20 + 30,19).
- tools/build_kernstown_map.ps1: rewritten to read kernstown_game.json, enforce wall/VP rules, -GameDir/-Season/-TemplateMap
  params, GeometryOnly tile check. Parses cleanly in pwsh 7.4 (/tmp/pwsh). Untested against game DLLs.
Not done: re-slice tiles (still 576 old tiles, need 3410), Manifest update, README_INSTALL.md, dist zip, git branch.
Notes: docs say do NOT bake grid into tiles; tiles must be 2000x2000 per official tutorial (~370 MB est. for 3410).

## 2026-10-16 — painted full map + mod package
- painted_sections/build_sandy_ridge.py (section test, FULL=1 mode), build_full_map.py, slice_full_tiles.py
- data/basemap_painted_full.png -> 3410 SV_K tiles (Summer, 2000px, no grid), ~6.4 GB
- Natural straight fieldstone wall (least-squares line through wall hexes), not hexside zigzag
- data/layers/kernstown_units.json (15 brigade/battery units) read by tools/build_kernstown_map.ps1
- dist/Kernstown1862_mod.zip (6.7 GB, stored). UNTESTED in game.
