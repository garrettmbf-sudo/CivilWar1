# Shenandoah 1862 — map repair preflight (historical + tile-art audit)

**Status: RESEARCH/TESTABLE PREFLIGHT; NOT A PLAYABLE .sav AND NOT AN ELEVATION MESH.**
This repository contains many excellent tile images, but names of images are not proof
of matching edge connections, and named waypoints are not evidence of georeferencing.
Keep the user's existing save and audited art untouched during this work.

## Source evidence and scope

- User-supplied period topographic map, October 15, 2026 (`valley map1.png`):
  extensive contour/hachure relief, ridge chains, streams, roads, farms and
  annotations. The visible scan's orientation and coordinate control need
  registration before any pixel-to-hex transfer. Do not mistake drawn grid
  lines or fold seams for new roads.
- User-supplied period New Market-area map (`valley map 2.png`): named
  **New Market**, roads, stream network, ridge/forest and farmstead labels.
  Names difficult to read at the provided magnification must be marked
  `NEEDS_SOURCE_TRANSCRIPTION`, never silently guessed.
- Earlier user-supplied Winchester/Kernstown period detail: town and adjacent
  named hill/run/road network. This is the proper basis for a separate battle
  map once scale control is established; the AI-illustrated example is **not**
  a georeferenced source.
- User-supplied 125x130 PowerShell v4 (`build_valley_map.ps1`,
  `beautify_map.ps1`) is a *coordinate hypothesis*, not an approved historical
  digitization or an in-game verified result.

## Proven topology faults: original asset sprites vs builder

- Every route uses an independently maintained six-port mask: 0=top,
  1=upper-right, 2=lower-right, 3=bottom, 4=lower-left, 5=upper-left.
  Backward directions are `(dir + 3) % 6`. Map layout is even-q.
- River 6/7/8/9 connect ports `(0,4)/(0,2)/(1,3)/(3,5)`; **Railroad**
  6/7/8/9 connect `(0,2)/(1,3)/(3,5)/(0,4)`. Sharing the numbering
  table makes the railroad sprites turn the wrong way.
- River 10/11/12 are visibly three-port assets for `(1,3,5)`, `(0,2,4)`,
  `(0,1,3)`. At a different junction, a 2-port fallback cannot show the
  third branch. Variants 13+ and all unused rail cross sprites require
  **individual** artwork-port verification before automated use.
- 22 asset files in the supplied `civilhex.zip` are byte-identical, including
  `Hill.png`, `RailroadCross5.png` to `RailroadCross15.png` and multiple
  incomplete river bridge/forest files. These are not distinct renderings.
- No `Road*.png` in the provided root custom tile directory was available
  for auditing. Native game art might supply roads; confirm actual sprites.
- The v4 parser yields **25 river/rail cells without a verified visual
  variant**, **50 road/rail–river cell intersections needing bridge/ford
  review**, and **128 road+rail shared cells** (counts include endpoints and
  route junctions). This is an *audit queue*, not proof of 50 missing bridges.
- Current tile-priority branches erase an underlying road or railroad when
  a river, bridge, mountain or city takes the sole visual tile slot. Keep
  independent topology/layers for routing; draw supported composites only.

## Command

```bash
python -m src.valley_map_topology \
  tools/powershell/build_valley_map_v4_candidate.ps1 \
  --assets /path/to/unpacked/civilhex \
  --output maps/generated/valley_topology_preflight.json
```

A nonzero status is deliberate when unsupported shapes, unsafe intersections,
or out-of-bounds geometry remain. The script **never executes PowerShell,
imports game libraries, writes a .sav, or copies into Workshop directories**.
The generated report is for review, not proof that the tile appears in-game.

## Correct workflow — functionality before polish

1. Freeze input `.sav` files and preserve exact filenames; work in a standalone
   mod directory with backups and a source hash.
2. Georeference the historical maps to modern control points with historical
   uncertainty bounds, and choose a measured world-to-hex transform. Confirm
   the campaign scale before attributing 1860s features to hex coordinates.
3. Trace each road, river and railroad as a network of **edges**, not just a
   set of occupied tile names. Preserve fork names; two touching parallel
   features do not automatically join. Store layers separately.
4. Audit all exact edge masks against actual tile PNGs. Missing masks need
   new **correctly constructed** composites or network redraws, not nearest
   approximations. Audit any named ford/bridge from maps or primary records;
   do not convert an unverified river-road intersection into a bridge.
5. Composite/overlay features while preserving terrain elevation and gameplay
   fields. Town footprints must grade into the local slope; no city tile may
   silently eliminate a river or railroad.
6. Use a single continuous DEM-derived height function (same world coordinate
   -> same vertex elevation for both neighboring hexes) for an eventual 3-D
   presentation. Noise must be applied in world coordinates, and boundary
   normals must match. Shader/mesh support in HoS **is not yet verified**.
   Until proven, use stepped/hill-slope tile families with consistent outlines
   and do not claim that a 2-D PNG creates true mesh elevation.
7. Run reciprocal-edge checks, crossings audit, historical feature-review
   queue, tile availability tests, performance checks, then an actual HoS
   game version-specific load, move, fight and save/reload test.

## Historical notes

The separate `docs/valley_feature_notes.csv` is a **provisional named-feature
register**. Its `candidate_x` and `candidate_y` are positions from the current
builder (not surveyed coordinates); no row is automatically placed on the live
map or promoted to victory point. Add verified source identifiers, an original
map scan crop/coordinate, and confidence before generating tooltips or hex
labels. In particular, mountain gaps are **terrain/pass** annotations, not
capturable towns. Fords and bridges need their own 1862 status, direction and
seasonal passability fields.

## Separate battle map — permission granted, not yet implemented

Build a **Winchester–Kernstown** battle map at *500 yards between adjacent hex
centers* **only after** map projection, native tile edge matching and in-game
save/load behavior are verified. Its hex footprint must be computed from the
actual historical source bounds, not guessed from an illustration. Regiments
or brigade formations must fit the tactical frontage; keep this separate from
one-mile operational counters.

