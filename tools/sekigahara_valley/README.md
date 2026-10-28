# Sekigahara / Wargame Maker conversion experiment

**Current deliverable: v3 editor import kit.** See `IMPORT_KIT_GUIDE.md`.
The latest workflow composes a continuous landscape and extracts 49 positioned
square textures with exact point-top bounding boxes. `build_continuous_proof.py`
builds the 7 × 7 proof; `build_import_kit.py` makes the 15 editable named counters,
generic terrain library and standalone PNGs. `finalize_import_kit.py` checks image
dimensions, fitting margins and tile source rectangles, then creates the ZIP.
Original generated terrain masters and the exact built-in image prompts are
included under `terrain_masters/` and `terrain_prompts_v3.json`.

The earlier screenshot-sampling prototype described below is retained as an
experiment. Its repeated independent terrain pictures are not the final
continuous-landscape art pipeline.

This isolated adapter implements the user's 28 October 2026 request to try the
installed Sekigahara editor with existing Valley Campaign artwork. It does not
change the Hex of Steel mod or its coordinate helpers.

The first output is **Valley 1862 - Kernstown Playtest.json**, a 31 × 36 board,
400 m between neighboring centers, 15 counters, two provisional objectives and
10 turns. Strengths, movement, ranges and victory bands are playtest values.

## Build

Python 3 with Pillow:

```powershell
python tools/sekigahara_valley/build_scenario.py --workspace "PATH_TO_PROJECT_MIRROR" --game "C:/Program Files (x86)/Steam/steamapps/common/Sekigahara 1600" --output "PATH_TO_OUTPUT"
```

Inputs are the project mirror's `counter-design-work/data/layers/` JSON,
`counter-design-work/previews/kernstown_full_nogrid.jpg`, and local sprite copies
under `output/counters/reference/civilhex/Land Units/`. The installed Cowpens
scenario supplies an observed serialization skeleton. No shipped game assets
are copied into the repository. Generated JSON embeds local art and is intended
for local review; redistribution rights have not been established.

In the editor, use Scenario → Open to select the generated JSON. Preserve any
current scenario with Scenario → Save to a separate filename first.

## Verified and pending

The installed editor accepted the generated scenario and displayed 15 units,
1,116 hexes, two objectives and **No problems found** in its pre-save check.
Native game movement, combat, AI, save/load and performance remain unverified.
An editor import alone is not proof of native playability.

## Limits of this first adapter

- Art is resampled from the existing 2,000-pixel preview, not the original tile
  masters. Its old hex marks and rendering artifacts remain visible.
- The old local layer describes odd-q geography and north-increasing rows.
  The adapter maps through meter coordinates into point-top odd-r, south-increasing
  rows. This is a local legacy import convention, not a change to the repository's
  canonical Hex of Steel convention. Art extent alignment is approximate.
- Terrain classification is nearest-center sampling. Road cells cost one;
  painted roads and streams have no connected native edge network yet. Rivers
  currently cost three rather than imposing crossing barriers.
- One texture entry per hex preserves continuous source imagery. Large terrain
  catalog performance and native terrain-ID behavior need measurement.
- Hampden, Danville and Pleasants batteries are omitted in response to issues
  already recorded in the local counter review. Remaining roster and deployment
  are approximate and require dated historical review.
- No true 3D geometry, DEM displacement, line of sight, supply, or command-radius
  system is implemented or promised by the editor import.

Next acceptance gate: editor export/reimport with semantic comparison, followed
by a native game move, combat, turn advance and save/reload. Then rebuild from
original terrain masters and verified road/river vectors before scaling to the
full March–June campaign.
