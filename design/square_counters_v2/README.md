# First Kernstown 1862 — painted square counter review

18 separate 1024 × 1024 transparent RGBA PNGs, using the supplied ten Confederate and eight Union units. This is an art/import candidate, not a verified playable mod. Existing game art, source portraits, saves and mod files were not overwritten.

## Visual convention

- Brigades: anonymous ordinary infantry in 1862 field dress, not commander portraits.
- Cavalry: mounted troopers in faction field dress. Batteries: period field gun and crew.
- Portraits are reserved for division and army commanders. There are no such HQs in this eighteen-unit list; all eighteen counters are portrait-free.
- Confederate burgundy and Union navy bands; unit designation above, commander surname and supplied full commander below. Battery B's commander is marked unconfirmed.
- Illustrations use six shared faction/type paintings. Each of the eighteen labelled unit PNGs is unique; these are not eighteen separately researched uniform reconstructions. Generic troops and displayed gun/figure counts do not assert regiment-specific dress, personnel strength or battery gun counts.

## Files and installation

`MODS/First Kernstown 1862/Graphics/Units/Confederacy/` and `.../Union/` contain the eighteen exports, with the exact supplied counter names as filenames. The mod's actual Country and Name fields must match these paths, including punctuation. The package does not change a unit database or install a scenario.

`masters/` contains eighteen editable SVGs with live text and frame geometry and an embedded original painting atlas. The art is raster; the layout is editable vector. `source/formation_sheet.png` retains the unmodified generated source. The five available commander filenames remain recorded as unused in `roster_manifest.json`; their source files are untouched and are not needed to rebuild this set.

`all_18_counters.png` is the review sheet. `deployment_map_preview.png` uses the user's coordinates. `adjacent_map_preview.png` uses artificial dense placements. Both use the previous painted Kernstown preview for private visual review, not a screenshot from Hex of Steel. The underlying reference map is not included as a release asset. No native game stat overlays, selection outlines or NATO backgrounds are simulated.

The transparent canvas has a 64-pixel margin and a 896-pixel visible square. At the inspected engine projection (1080-pixel viewport height, orthographicSize 20, root scale 0.37, 1024 source width), canvas width is about 102 pixels and visible counter width about 90 pixels. Using a 512-wide source instead changes world size under the inspected loader; do not substitute a resized export without testing.

## Evidence and remaining checks

The validation files record dimensions, alpha, safe margins, eighteen unique file hashes, no portrait inserts, and canvas separation in both offline map layouts. The roster, composition, starting positions and entrenchment values are user-supplied and retained in the manifest; they have not been independently certified here. In particular, WV labels are retained shorthand, not a claim that West Virginia existed as a state on March 23, 1862. Historical roster questions and generic equipment depictions remain separate from visual approval.

In-game import, readable names at the chosen camera zoom, overlay clearance, NATO switching, AI turn and save/reload remain untested. No Harmony patch or zoom switching is included. Local PNG correctness and non-overlap do not establish game compatibility.

## Rebuild

Run `build_square_counters.py` with Python/Pillow, then `render_square_counters.cjs` with Node/Sharp, then `preview_square_counters.cjs`. Rendering scripts point to this machine's bundled Sharp installation; change that require path for another machine. The map preview script points to the existing local Kernstown reference preview and is optional. Building PNGs does not require that map.

Formation art was generated with the built-in ImageGen tool on October 17, 2026. See `generation_prompt.txt`; no commander identity was generated. The source atlas is preserved without retouching. Art is pending human visual/historical approval and live game import testing.
