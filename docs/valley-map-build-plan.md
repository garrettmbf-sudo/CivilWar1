# Valley campaign map: build plan (scale + tile reuse)

**Status:** PLAN + PROTOTYPE. No game tile has been made, no .sav written, nothing tested in Hex of Steel.
**Inputs:** bounds from PR #9 (37.70–39.71 N, 77.70–79.65 W, includes Lexington); flat-top odd-q grid in `src/hex_utils.py` (in-game check still pending); Kernstown v0.4.0 tiles (read-only, never copied into main).

## 1. Scale study
The rectangle is 169 km E–W × 223 km N–S. Hex size is measured across the flats (= centre-to-centre spacing s); column pitch is s·√3/2.

| Scale (yd/hex) | Grid (cols × rows) | Hexes | 20-mile march, in hexes | Kernstown battlefield core (~6×5 km), in hexes | All-unique tiles at Kernstown density (1.52 MB/tile) |
| --- | --- | --- | --- | --- | --- |
| 250 (Kernstown) | 856 × 979 | 838,024 | 141 | ~660 | ~1.28 TB |
| 500 | 429 × 490 | 210,210 | 70 | ~165 | ~321 GB |
| 750 | 286 × 327 | 93,522 | 47 | ~74 | ~143 GB |
| **1000** | **215 × 246** | **52,890** | **35** | **~42** | ~81 GB |
| 1760 (1 mile) | 123 × 140 | 17,220 | 20 | ~13 | ~26 GB |

Notes:
- These are bounding-box counts. Once the approved polygon drops the Piedmont east of the Blue Ridge and empty Allegheny corners, the real counts will be lower. That needs measuring after the polygon is approved; I have not guessed a figure.
- The older `valley_map_data.ps1` reports 105 × 139 at 1 mile. It uses square rounding, not odd-q.

**Known Hex of Steel limits.** Nothing invented here:
- **Large maps work.** The v8.1.6 release notes describe a **900 × 700** map (630,000 hexes): "Improved scenes unloading speed … from 13 minutes to 30 seconds on a 900x700 map". So maps of that size load, though they were slow before that fix.
- **No documented maximum.** I found no published hex-count or tile-count limit in the official manual or Steam discussions.
- **Tile loading model** (repo docs `hos_grid_and_tiles.md`, `hos_tile_overflow.md` on kernstown-map):
  - A tile's Name equals its PNG filename in `Graphics/Tiles/<Season>/`.
  - Tiles are 2000×2000 with alpha outside the hex.
  - A missing name shows as a black hex.
  - Alpha outside the hex is never drawn.
- **Not documented:**
  - whether the engine caches identical tiles;
  - texture-memory behaviour with thousands of unique 2000² tiles.

  The tile-library approach below avoids relying on either.

**Recommendation: 1000 yd per hex** (provisional, pending in-game tests):
- **Battles stay readable.** A brigade front of about 500–800 yd fits in one hex. Kernstown, Cross Keys and Port Republic become 40–70-hex battlefields where you can still manoeuvre. At 1 mile they shrink to about 13 hexes, too coarse for the six battle scenarios.
- **Map size is manageable.** 52,890 hexes is about 8% of the 900×700 map known to load. Pathfinding and AI cost should be checked first on the Kernstown-sized sample.
- **Marches can be tuned through turn length.** Jackson's 20–25 mile days come to 35–44 hexes per day. Whether that works depends on the movement points HoS gives per turn and how long a turn is (for example 3–4 h turns ≈ 5–8 road hexes). That has to be measured in-game, not assumed.
- **Fallbacks:** 750 yd if performance allows more detail; 1 mile if turn processing at 1000 yd is too slow. All scales use the same pipeline, so switching only means re-running the generators.

## 2. Tile-reuse strategy
**Kernstown inventory** (`kernstown_game.json`: 62×55 = 3,410 unique slices `SV_K_<col>_<row>`, 5.2 GB):

| Hex type | Count | Detail |
| --- | --- | --- |
| Plain | 2,964 | 2,944 open, 15 village, 3 town, 2 stone wall |
| Road | 221 | 101 dirt road, 77 Valley Pike, plus woods/hill/village/creek/stone-wall combinations |
| River (creek) | 104 | |
| Forest | 81 | |
| Hill | 39 | |
| City | 1 | |

15 hexes are flagged railroad and 7 stone wall. Every tile is a unique slice of one continuous painting, so its edges only match its original neighbours.

**What the prototype measured** (`scripts/valley_tile_plan.py`, 24×18-hex synthetic test region, 432 hexes, Kernstown columns 16–31 downscaled to 200 px):

| Run | Mean N/S seam colour difference |
| --- | --- |
| Native Kernstown neighbours (baseline) | 8.3 |
| Hashed reuse of Kernstown slices, 6 variants per class | 16.7 |
| Hashed reuse, all 766 available variants | 17.0 |
| Rim-harmonised derivatives, 6 / 12 variants | 3.4 / 3.7 |

What this means:
- **Raw reuse doesn't work.** Reusing Kernstown slices out of context doubles the seam error and shows visible hex patchwork. Adding more variants doesn't help, because the problem is edges, not repetition (`docs/previews/valley_tile_plan_v6.jpg`).
- **Rim harmonisation fixes the numbers but not the look.** Fading every rim to a class colour cuts the seam error below native, but it paints a faint hex ring, which is effectively a baked-in grid and is forbidden by the directive (`docs/previews/valley_tile_plan_v12_harmonized.jpg`).
- **Conclusion:** the Kernstown *style and pipeline* are the basis, but the Valley library must be **re-rendered** with edge-compatible borders. Reusing existing slices won't work.

**Library design:**
1. **Edge-class (Wang-style) area tiles.**
   - Every tile in an area class (open/fields, woods, hill, mountain slope, ridge crest, wet meadow, orchard…) is rendered with the Kernstown painter, and the outer ~8% band of each tile comes from one shared world-space texture for that class.
   - Then any two same-class tiles meet invisibly, with no ring: the band is continuous texture, not a flat colour.
   - **Transition tiles** handle class boundaries (open↔woods, valley↔mountain). They are keyed by which of the 6 edges face the other class, giving at most 64 masks per pair; only the masks that actually occur get rendered.
2. **Deterministic variant choice.**
   - Each hex picks its variant from `blake2b(seed, class, port_mask, col, row) % n`.
   - If that variant is already used by a neighbour, the next one is taken, so identical tiles never touch when a class has 3 or more variants.
   - Rebuilding is reproducible: the same seed always gives the same map.
3. **Linear features by port mask.**
   - Road, pike, creek, river and rail tiles are keyed by class plus a 6-bit port mask (0=N … 5=NW).
   - `validate_ports` rejects any port that has no reciprocal on the neighbouring hex.
   - Crossings (road×creek, pike×river, rail×river) are separate tiles and are only used where a crossing record exists. A bridge is never inferred from a road meeting a river.
4. **No mirror or rotation transforms.** The art is a north-looking oblique view lit from the NW, so mirroring moves shadows to the wrong side and rotating breaks the oblique perspective. Variety comes from painted variants and the deterministic choice only. Small per-hex colour jitter was rejected because it breaks seams.
5. **Hero tiles.** Unique tiles (`SV_HERO_<id>`) are rendered as continuous Kernstown-style paintings and sliced like v0.4.0. Their outer ring must blend into the surrounding class tiles' border texture.

   | Battlefield cores | Hexes at 1000 yd |
   | --- | --- |
   | Kernstown | ~42 |
   | McDowell | ~42 |
   | Front Royal | ~42 |
   | Winchester | ~42 |
   | Cross Keys | ~42 |
   | Port Republic | ~42 |
   | Lexington/VMI | small town hero |

   Also: about 45 towns and villages, and the Blue Ridge and Massanutten gaps.
6. **Naming.**
   - `SV_<CLASS>_<v>`, `SV_<CLASS>_P<mask>_<v>`, `SV_T_<A>_<B>_M<mask>_<v>`, `SV_HERO_<id>`.
   - The .sav refers to each hex's tile by name.
   - Only Summer/Spring folders are produced until seasonal tiles are tested.

**Unique-tile and disk estimates** (library approach, 1.52 MB/tile at Kernstown density):
- **Base library, about 720 tiles, the same at every scale:**
  - area: 10 classes × 12 variants = 120
  - linear: 5 classes × ~20 used masks × 3 variants = 300
  - crossings: ~60
  - transitions: ~240
- **Hero tiles scale with hex size.**

| Scale | Hero battlefield tiles | Town/gap tiles | Total unique | Approx. size |
| --- | --- | --- | --- | --- |
| 250 yd | ~4,640 | ~610 | ~5,970 | ~9.1 GB |
| 500 yd | ~1,160 | ~180 | ~2,060 | ~3.1 GB |
| 750 yd | ~520 | ~80 | ~1,320 | ~2.0 GB |
| **1000 yd** | **~290** | **~70** | **~1,090** | **~1.7 GB** |
| 1 mile | ~100 | ~50 | ~870 | ~1.3 GB |

These are planning estimates. Battlefield core is about 30 km² per site; towns are 4 large, 14 town and 27 village/gap. Lossless masters stay outside the runtime package.

**Note:** Kernstown's 250-yd slices cannot go straight onto a 1000-yd grid. One 1000-yd hex covers 16 Kernstown hexes. Battlefield hero tiles must be re-rendered from the same DEM/feature pipeline at the new scale.

## 3. Prototype
`scripts/valley_tile_plan.py`:
- assigns tiles with the hashed-variant rule;
- validates port reciprocity;
- renders a low-res mosaic from downscaled tiles;
- reports the seam metric.

Command:
`python scripts/valley_tile_plan.py --game-json <kernstown_game.json> --thumbs <dir of downscaled SV_K_*.png> --out <dir> [--variants N] [--harmonize]`

Tests in `tests/test_valley_tile_plan.py` cover:
- determinism and seed sensitivity;
- that identical neighbours never occur;
- port reciprocity and mask-matched names;
- that the validator catches one-sided ports;
- that hero tiles are never re-chosen.

The test region is synthetic, not georeferenced. Roads and creeks appear only as overlay lines, because Kernstown has no port-indexed road tiles.

## 4. Next steps
1. Approve the polygon and scale.
2. Run the in-game corner-tile test and a 52k-hex blank-map load/turn test.
3. Build the shared-border renderer for the open/woods/hill classes and check a 9×9 stitch.
4. Render the linear tiles from the port-mask set.
5. Re-render Kernstown as a 1000-yd hero region.
