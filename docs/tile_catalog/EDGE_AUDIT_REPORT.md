# Shenandoah 1862 — Six-edge atlas QA (blocking audit)

**Verdict: BLOCKED FOR GAME USE.** These are concept illustration sheets, not independently validated Hex of Steel tiles. None was installed into a native `.sav` during this audit.

## Audited scope

- **41 source art files** inventoried by the script: **32 presumed hex atlases**, **six standalone object sheets**, and **three dense composites needing hand segmentation**. Other miscellaneous images in the workspace were intentionally excluded.
- **234 individual candidate tile crops** examined, **1,404 border slots** sampled (six sides per candidate).
- Shape heuristic: **186 point-top**, **19 possible flat-top**, **29 uncertain**. The apparent flat-top candidates are *not approved*: several are known false positives from border shadows/adjacent-tile collisions. Visual examination of representative atlases confirms a systematic **point-top illustration versus flat-top game target mismatch**.
- All **234 samples were extracted from opaque (non-alpha) artboards**, so they would require carefully masked transparent sprites.
- **Four** candidate boundaries passed a *near-pixel Lab color/texture screening* against a different tile on the same sheet; **1,400** did not. This is *not a count of broken route connections*: exact texture equivalence is more restrictive than geometric edge fit, while being insufficient to establish actual route topology.
- **Zero typed road/rail/river/fence/stone-wall exits have a documented reciprocal port manifest**. Therefore **zero routes are certified**, regardless of how connected any pair looks.

## Immediate blockers

1. **Wrong grid orientation:** most illustrated hexes have a top/bottom *point*, whereas CivilWar1 specifies horizontal *flat sides* north/south. Correct the footprints and redraw ports; rotating the entire painting would rotate geographical north and lighting and is not sufficient.
2. **No exact six-edge feature register:** road, pike, railway, creek, river, rail fence, and stone wall must each declare their exit edge, normalized offset, thickness, material, and neighbor. Two pieces that merely touch or look plausible are not a verified match.
3. **No continuous elevation edge profile:** six edges must carry world-derived elevation samples; a house beside a raised mountain sprite cannot be joined just by image masking.
4. **Unverified bridges/rails:** every road/water and rail/water crossing requires a correct bridge/ford type and a dated historical source; the game must not create passability from an artistic intersection.
5. **Transparent cropping:** original sheets have gray backgrounds rather than isolated alpha sprites; naive rectangular cropping would create obvious gray gaps on the game board.

## Tools delivered

- `validate_tile_edges.py` — reads candidate sheets and produces per-tile **all-six-sides** visual edge records and file hashes.
- `port_validation.py` — checks flat-top orientation, opposite-side reciprocity, precisely matching exit type, offset, width, material, shared elevation profile, perimeter exits, documented crossing type.
- `test_atlas_scan.py`, `test_port_validation.py` — **18 local regression tests** passing.
- `results/tile_edge_audit.csv` — row per tile with six-sided summary.
- `results/edge_details.json` — **six individual side comparisons for each candidate tile**.
- `results/audit_summary.json` — source hashes, counts and failures.
- `edge_geometry_visual_audit.png` — diagram contrasting a real concept road sprite with target flat-top edge numbering.

## Interpretation and safe repair strategy

**Keep all illustrations as style references. Do not directly drop them into a Hex of Steel tile directory.** For game assets, generate standardized flat-top hex canvases from one georeferenced world-elevation/texture field; draw road, rail, river and fences as separate deterministic edge-port overlays. Terrain landmarks, farm buildings and outbuildings are overlays placed inside these shared canvases. Make a 3×3 tessellation fixture and reject any open interior feature exit. Historical verification of the 1862 map coordinates is a separate required gate.

### Running again

```bash
python -m unittest -v test_atlas_scan.py test_port_validation.py
python validate_tile_edges.py --input /path/to/art --out /path/to/qa
```

The scanner relies on conservative ochre-vs-gray separation and heuristic source-grid detection. For irregular collages, hand-segment first; the atlas scanner **does not** use computer vision to semantically certify bridges, fences or roads. Only authored typed-port manifest checks can pass that gate.