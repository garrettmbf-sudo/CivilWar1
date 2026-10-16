# CivilWar1 — Winchester → Strasburg → New Market (250-yard corridor prototype)

**Status: PLAYTEST ENGINEERING PROTOTYPE. Not a verified March 1862 map and not a finished native `.sav`.**

This prototype adopts the **Kernstown `kernstown-map` branch's best methods** without copying its unique terrain images into unrelated locations:

1. **One shared world-coordinate grid** (`flat-top odd-q`) for every map section. No mixing even-q and odd-q helper functions. Opposite hex-edges are validated mathematically.
2. **A continuous ground canvas first, sliced tiles second.** Roads, trees, fences, and other details are painted on the world surface and cut into native hex sprites only at export. No road segments randomly stamped per hex.
3. **Stock Hex of Steel alpha** for each 2000×2000 tile, with graphic resolution and seasonal asset paths unchanged. Do not bake dark grid strokes into artwork.
4. **Typed network metadata** for the Valley Pike and rail/water layers. Every Pike crossing has two reciprocal ports stored in `data/valley_pike_edge_manifest.csv`; crossings remain **blocked until documented**.
5. **Historical source hierarchy:** digitize Hotchkiss and S. Howell Brown period documents; survey missing elevation with a DEM; validate each name and bridge's existence and dates. Do not assume current roads equal the 1862 roadbed.
6. **Artwork vs gameplay independence:** buildings, trees, bare March vegetation, and outbuildings are ornaments over the terrain; the game collision, movement, and VP attributes belong to hex data.
7. **Mandatory six-edge and image QA** before accepting any finished atlas.

## Files

- `previews/valley_corridor_continuous_250yd.jpg` — **whole geographic corridor**, north at top; minor grid overlay for inspection only. Continuous Pike through all ten settlement anchors.
- `previews/strasburg_nine_hex_stitch.png` — **real 2000×2000 pixel sprite slicing** from one seamless shared source canvas; demonstrates how geometry survives export and reassembly. Artwork is deliberately schematic, **not a final hand-painted product**.
- `tiles_demo/SV_CORRIDOR_*.png` — **nine native-size sample graphics** using the stock `Plain.png` alpha mask. These show export format, not final visual quality.
- `data/corridor_topology.json` — world grid, town anchor points, continuous Pike list, reciprocal neighbor links and historical qualification markers.
- `data/valley_pike_edge_manifest.csv` — exact reciprocal direction for all consecutive Pike hexes.
- `qa/compression_benchmark.json`, `qa/compression_summary.json` — codec size and per-pixel checks.
- `src/valley_corridor.py` — prototype renderer/topology builder.
- `src/native_slice_demo.py` — 3×3 source-canvas-to-native-tile slicing and pixel consistency proof.
- `src/benchmark_tile_compression.py` — Pillow codec experiment (needs the stock and v4 sample ZIPs for the original benchmark).
- `tests/test_corridor.py` — 15 project tests.

## Scale & geographic disclaimer

250 **yards across opposite hex sides** (center spacing) = 228.6 meters; one mile is **~7.04 hex-widths**. This prototype's bounding box runs from 38.608° to 39.222°N, 78.790° to 78.090°W, creating a **308 × 301 = 92,708-position** grid (includes terrain away from the road). The interpolation of the Valley Pike between its named settlements is a **placeholder**, not a verified period tracing. The purported North Fork and creek routes are **schematic**; they cannot set ford, bridge, or movement flags. The preview's relief is a procedural stand-in because the only referenced DEM in the Kernstown branch covers Kernstown.

Native Hex of Steel loading has **not** been run against this prototype; no `.sav` is produced and the existing mod files remain unchanged.

## How to regenerate

Inside this folder, with Python, Pillow, numpy, scipy, scikit-image installed:

```bash
python src/valley_corridor.py
python src/native_slice_demo.py
python -m unittest discover -s tests -v
```

`native_slice_demo.py` requires the stock `maps/Plain.png` **already present in the CivilWar1 repository** (when located at `tools/valley_corridor/`); it also knows the user-provided `/mnt/data/civilhex.zip` test environment. **Do not add or re-license the proprietary stock game asset as a new project file.**

## Image compression findings (loss vs compatibility)

The eight tested 2000×2000 PNG files are three original Hex of Steel stock tile graphics, three existing CivilWar1 v4 sprites and two small native prototype tiles — **NOT** the large Kernstown release art. Check `qa/compression_benchmark.json` before extrapolating:

- Existing indexed PNGs are often **already optimized**: lossless Pillow PNG `optimize=True` had a **median size ratio 1.0** in these samples (no benefit at the median; all files decoded pixel-identically).
- **Lossless WebP** saved more in our sample (median **0.405× original**) with pixel-identical output, **but Hex of Steel's native custom tile loader is documented to look for PNG**, so WebP can be used for distribution/source backups only unless a tested engine integration changes this.
- 256-color paletted conversion sometimes saved bytes but **did lose detail**; minimum sampled SSIM was **0.875**. **Do not wholesale-quantize the painted Kernstown art.** Keep RGBA PNG masters.
- **Biggest practical improvement:** stop requiring one individually compressed 2000×2000 bitmap for *every* hex. Use reusable plain/forest/field base variants with a strictly compatible six-edge profile, and reserve distinct baked imagery for roads, rivers, town clusters, named farms, special crossings and battlefield details. More dynamic variations would require a tested Unity/Harmony draw overlay and should not be assumed native.
- The existing Kernstown release is roughly **5.5 GB for 3,410 tiles (~1.6 MB each)**. At that density, naive one-image-per-cell for 92,708 cells could approach **150 GB** even before other assets. Do not build the full map in that way.
- Slice/render in **geographic chunks**, with a one-hex bleed; validate the overlapping strip by sampled pixel hashes and 6-port network manifests before release. Use separately packaged town/battlefield map regions if Unity import/performance is unacceptable.

## Historical sources and hard boundaries

- Hotchkiss period Valley coverage and formation history (NPS): https://www.nps.gov/articles/000/jedediah-hotchkiss-maps-of-the-shenandoah-valley.htm
- LOC 1860s Winchester–New Market maps: https://www.loc.gov/item/2005625054/
- NPS period Valley Turnpike road history: https://www.nps.gov/articles/000/valley-turnpike.htm
- LOC 1863 Hotchkiss sketches of Winchester–Woodstock roads: https://www.loc.gov/resource/g3882s.cwh00151/
- **Critical rail warning:** a rail link between Winchester and Strasburg was *proposed*, not an operational 1862 line. The Winchester and Potomac served Winchester toward Harpers Ferry, and the Manassas Gap Railroad served the eastbound Strasburg line. Do not draw a continuous north–south Valley railroad.

**Next acceptance criteria:** coordinate the historical Pike polyline against Hotchkiss/Brown, integrate a genuine DEM across all 92k grid cells, settle all bridges/fords/rail links with an evidence registry, replace schematic painted textures with high-fidelity art, run full six-edge checks, then produce a separate test `.sav` with a verified Unity assembly version. Nothing is merged into a player's existing map until that test passes.