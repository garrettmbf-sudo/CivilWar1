# Kernstown counter review — four native designs

Review candidates based on `kernstown-v0.4.0`; not merged or installed in Hex of Steel.

Open `previews/four_designs_details.png` for enlarged art, `previews/four_designs_map_comparison.jpg` for all four treatments on the actual map, and `previews/four_designs_dense_20.png` for the decisive adjacent-hex test. Individual map panels preserve their original pixel dimensions. The source map is the branch's existing painted Kernstown preview, not a newly imagined battlefield or a game screenshot.

A is a historical command card. B is a traditional wargame counter. C adds the repository's illustrated troop sprites and an officer medallion. D prioritizes the officer portrait. All use the same faction palette, positions, naming, center pivot, and 56 px visible width against 88 px point-to-point hex width. B is the recommended A/B hybrid: restrained board-counter geometry with approved historical imagery and a cream, oxblood, navy, and muted brass palette.

## Scale and terrain visibility

Normal comparison scale is a proposed camera target: 44 px outer hex radius, 250 yards between neighboring centers. Every transparent sprite is resized to a 70 px square canvas with a 56 px opaque width. The editable source uses a 160-unit square viewBox with a 128-unit counter width. The four heights differ deliberately. This is a pixel-scale design proof, not confirmation of the engine's sprite/world-size settings.

The same twenty units appear in every map panel: the branch's eighteen units at their exact existing hex coordinates, plus two explicitly artificial headquarters placements. Kimball's acting headquarters repeats his officer identity, not an additional combat brigade. In the second test, all twenty are arranged on adjacent hexes near Sandy Ridge; these placements have no historical meaning. No counters overlap at the proposed scale.

B occupies about 53% of one hex's area, versus about 62% for A, 56% for C, and 71% for D (thresholded alpha area; see `coverage_metrics.json`). This area ratio is not an exact intersection with a hex polygon. Local roads and walls under a counter remain obscured. The much smaller whole-viewport coverage percentages must not be mistaken for local terrain clearance. At farther zoom, name readability degrades; a simplified engine zoom view and selected-unit panel remain necessary.

## Identity and information

Six officer sources are exact byte matches to the approved portrait blobs in the repository's main-branch inventory: Garnett, Ashby, Jackson, Kimball, Tyler, and Sullivan. See `source_register.csv` and the executable identity checks. Each entire original image is proportionally fitted into its allocated rectangle; no face generation, recoloring, retouching, or cropping occurs. SVG masters embed those original bytes. Original project files are never changed.

Officers without approved portraits receive formation symbols; no substitute faces are invented. Unit artwork for C comes from the existing source mod, preserved as supplied. Asset rights are inherited/uncleared: these are review materials, not a cleared public art release.

Strength and movement fields deliberately show dashes because no sourced per-unit starting values have been established here. Morale, fatigue, supply and forced-march state have separate example SVGs/PNGs with redundant color and letter/symbol markings. These example states are not historical start conditions. Forced-march capability is distinct from an active forced march; capability and its numeric rule must be verified in the unit interface before binding a game overlay. Concurrent condition precedence remains an integration decision.

## Historical cross-check

The [National Park Service Kernstown order of battle](https://www.nps.gov/articles/000/first-battle-of-kernstown.htm) supports Jackson's command, Garnett/Burks/Fulkerson, Ashby's cavalry, and Kimball's acting division command with the three Union brigades. Colonel Kimball's portrait is the existing approved asset; uniform insignia in a portrait does not assert his March 23 rank. No rank stars or troop-quality ratings are inferred from photographs.

The source deployment is retained for comparison, not certified as a final historical scenario. NPS marks Danville and Pleasant's batteries unengaged and does not list Hampden in that OOB; the branch places these on the field. Those discrepancies need roster review before release. Battery officer names follow the branch and have not all been independently verified. Short Virginia battery labels avoid treating the later state name as a March 1862 state designation. Subordinate regiment lists stay in the unit interface.

## Editable masters and packaging

- `masters/`: 80 unit/design SVGs plus five state examples. Text, frames, military symbols, and embedded image objects remain editable.
- `sprites/512`, `sprites/256`, `sprites/128`: transparent RGBA PNGs; consistent canvas and center pivot.
- `sprites/*_atlas.png` and `atlas_manifest.json`: per-design atlases with pixel rectangles; no engine-specific loader assumptions.
- `source/`: unchanged approved image copies with original filenames.
- `roster.json`: identity-to-artwork mapping and placement provenance.

Assets intentionally live in `design/counters`, outside `mod/Graphics`, until the winner is approved and its engine bindings are verified. The branch currently places units using existing named templates; replacing them requires testing loader naming, per-brigade overrides, icon scale, selection outlines, UI statistics, AI behavior, and save/load inside Hex of Steel. No Unity/Harmony patch or working game integration is claimed.

## Rebuild

Requires Python 3 with Pillow, Node.js with `sharp`, and the existing full-resolution `previews/kernstown_full.jpg` (6635 by 6723). A local alternative named `previews/counter_source_full.jpg` is also recognized. Existing `kernstown_full_nogrid.jpg` is only 2000 px and is not a substitute for the normal-scale proof. Use the project's bundled runtime if system Python is unavailable.

```powershell
python design/counters/build_counter_masters.py
node design/counters/render_counter_masters.cjs
python design/counters/build_counter_previews.py
python -m unittest discover -s design/counters -p 'test_*.py'
```

The raster files are rendered directly from the SVG masters with Sharp, not independently painted stand-ins. No image generation model was used. Tests cover source-byte identity, embedded portrait identity, deployment preservation, transparent PNG sizes, atlas metadata, and adjacent-hex clearance. The host does not include pytest; unittest is the executable validation fallback. A real in-game camera/import test remains outstanding.
