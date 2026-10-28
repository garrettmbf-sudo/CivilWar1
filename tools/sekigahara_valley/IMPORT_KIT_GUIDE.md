# Valley 1862 editor import kit — continuous map proof v3

**Start with Scenario → Open → Valley 1862 - Continuous Landscape Proof v3.json.**
Save your current scenario first. This 7 × 7 art board demonstrates a single
landscape divided across the editor's hexes: woodland, meadow, hamlet and lane
share the same ground and continue across boundaries. No units or victory
objectives are included on the art proof. It is illustrative, not Kernstown.

The 49 files under **07_Continuous_Map_Proof/Terrain_Uploads** belong to exact
positions. Their filenames contain column and row; the placement manifest lists
the editor's four-digit coordinate. Do not paint these as random repeating
terrain types. Opening the proof scenario places all 49 automatically.
Their 512-square PNGs intentionally encode the full non-square hex bounding box;
do not crop or aspect-fit them. They look compressed as standalone square images
and regain their intended proportions when mapped to the editor's hex box.

**Valley_1862_Joined_Map_Terrain_Catalog_v3.json** imports these positioned pieces
as a separate catalog if needed. The four generic textures below remain useful
for sketches, but individually repeating them is not the final continuous-map
workflow. The earlier 31 × 36 Kernstown starter is included for unit/deployment
reference, not as a finished historical map.

For the reusable unit and generic terrain library, select
**01_Imports/Valley_1862_Complete_Catalog_v2.json**.

1. In the editor open **Database → Import catalog** and select that file.
2. The terrain catalog contains Meadow, Woodland, High Ground, Village and a
   provisional Channel. The unit catalog contains 15 named counters.
3. To inspect everything on a small board, use **Scenario → Open** and select
   **Valley 1862 - Asset Fitting Board v2.json**. Save your current scenario first.
4. For the larger construction starter, open
   **Valley 1862 - Kernstown Import Kit v2.json** instead.

Importing a catalog adds reusable assets. Opening a scenario replaces the
currently open board. The split terrain-only and unit-only catalogs are
alternatives to the complete catalog; importing all three is unnecessary.
Stable v2 IDs let this editor skip duplicate catalog entries on repeat import.

## Manual image uploads

| Folder | Files | Use |
|---|---|---|
| 02_Terrain_Uploads | 1024 × 1024 PNG | Terrain → Upload image |
| 03_Counter_Uploads | 512 × 512 PNG | Finished counter image, including fixed names and values |
| 04_Unit_Art | 704 × 608 transparent PNG | Editable counter's artwork layer only |
| 05_Previews | JPG | Reference sheets; do not upload as terrain |
| 06_Reference | JSON, CSV, prompts | Asset identity, fitting checks, field guidance and provenance |

Terrain upload images fill the whole square. **Do not crop them into hexagons**
or add a white/transparent hex border. The editor applies its own point-top mask.
The preview's hex silhouette is for inspection only.

For manual unit construction, use the **art-only** PNG in one image layer:
**X = 0; Y = 0; W = 22; H = 19**. The intrinsic image proportions are exactly
22:19. Its transparent margins protect the complete source artwork.
The base counter is **30 × 30** editor units. Keep the name/formation band above
Y = -9.5 and strength/movement near Y = +11.2. The imported catalogs already do
this and link names/values to their editable registry fields.

The ready-made 512-square counter PNG is an alternative single image layer:
**X = 0; Y = 0; W = 30; H = 30**. Remove competing artwork/text layers first.
Its printed values are fixed pixels; changing B5 or B6 will not repaint them.
Use the catalog versions when values should remain editable.

Registry: **B0 = side (0 Union, 1 Confederacy); B3 = commander/short name;
B4 = formation; B5 = combat strength; B6 = movement; B7 = range**.
The automatic unit ID remains managed by the editor.

## Hex settings

Place names are separate from terrain names. Renaming a terrain type changes
its library label; it does not name a town on the board. Select the map hex and
enter its Place name. No unsourced farmstead names were added to the starter.

The starter retains two explicitly provisional position objectives. VP values
are 5 for either side; CP is 0, so no activation-cap effects are asserted.
Sudden-death and board-exit options are off. They are scenario rules, not art.
The screenshot's editor note says per-side VP values are editor-only for this
version; the native game must be tested before relying on asymmetric scoring.

## Geometry and remaining work

This target uses point-top odd-r. For radius R, width is sqrt(3)R, height 2R,
column pitch sqrt(3)R and row pitch 1.5R. Odd rows shift right by half a width.
At 400 m center spacing R = 230.940108 m, width = 400 m, height = 461.880215 m,
and row pitch = 346.410162 m. PNG pixel size controls sharpness, not ground scale.

The terrain is illustrative, generated with the built-in image tool; the ridge
is relief artwork, not a DEM-derived 3D mesh or a verified named mountain.
These shared images are a terrain library, not a continuous surveyed basemap;
transition tiles and geographically continuous ridge art remain future work.

The larger board inherits approximate terrain classification and deployment
from the previous prototype. It removes the old screenshot texture and its
second hex geometry. Roads and river edge networks still need manual tracing.
Channel cells are provisional fordable terrain (cost 3), not enforced barriers.
Unit values are playtest settings, not sourced troop strengths. Native gameplay,
AI and save/reload have not been verified for v2. The v2 JSON and PNGs have
structural and fitting checks, but this kit has not been imported into the live
editor during this turn; the user is handling imports.

Existing unit artwork is copied from the project's canonical units directory;
its redistribution rights have not been established. The package is for local
editor use. Audited officer portraits and original artwork were not modified.
