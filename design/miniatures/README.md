# Kernstown miniature review, March 23, 1862

Four **review candidates**, not installed game content: Garnett/Stonewall,
Ashby cavalry, Kimball infantry and Jackson HQ. Source of art/OOB requirements:
`references/miniatures-art-spec.md`, recovered from the user's referenced chat.
OOB checked against `data/opening-oob-arrivals` at
`4357bfeb5d0a555da3336685984e534d82232ec3`; exact opening snapshot retained
in `evidence/opening_snapshot.json`. This branch does not merge that branch's data.

## Outputs and reproduction

- `masters/*_blank.png`: generated stands before any real portrait is inserted.
- `masters/*_composited_2048.png`: normalized working masters with original
  portraits fitted whole into medallions, plus deterministic names.
- `sprites/1024/<Country>/*.png`: preferred RGBA Unit Editor import candidates.
- `sprites/512/<Country>/*.png`: diagnostic alternatives, **half the world size**
  under the inspected source-width loader rule; never interchangeable size tests.
- `previews/four_unit_review.jpg`: four-unit contact sheet.
- `previews/native_scale_zoom.jpg`: offline scale harness at S=10/20/40/80.
- `evidence/build_receipt.json`: original portrait paths/hashes and output hashes.

With Python and Pillow (created using Pillow 12.3.0, Windows Georgia Bold font),
run from the repository root:

```text
python -m scripts.build_miniature_assets
python -m scripts.preview_miniature_assets
python -m pytest -q
```

An optional local comparison against the previous candidate Kernstown map:
`python -m scripts.preview_miniature_assets --map <full-map.jpg> --output <local-output.jpg>`.
This uses the prior artwork's own north-up odd-q registration and source radius
72.590249px; it does not certify a playable scenario or correct historical positions.
Jackson's example location is illustrative. The candidate map image is not copied
into this branch. Published or unknown-rights board-game art remains reference only.

All original `mdl_*.png` paths are unchanged. The builder resolves actual paths
from `historical_data/portrait_manifest.csv`, requires `approved_existing`, and
fits the **entire** portrait rectangle inside the circle. No auto-crop, face
generation, retouching or rank correction. Original Kimball art is retained even
if its uniform depicts a later rank. MISSING Burks/Fulkerson resolve to blank;
unknown filenames fail rather than substituting an officer.

## Installed-engine findings

Read-only inspection: installed Steam build **25825936**, Unity 2021.3.45f1.
Assembly SHA256 `56c43159feff012193aeda208247cca516cdba5e461bc9a00bdd4980ed40c95a`.
Resources SHA256 `38c8d80155c8111f8a681b64c0da4218236fd8176d765e9a2e0ef6ffebb36c6f`.
No game binaries or decompiled source are included.

| Inspected method / asset | Observed behavior |
| --- | --- |
| `ModsManager.<CR_LoadContent>d__71.MoveNext`, IL 157d–1844, Units branch | Reads PNG/JPG/JPEG, downsamples to width 512 preserving aspect; bilinear blit, mipmapped texture, clamp wrapping; normal unit images call `Compress(true)`; filenames starting `Counter` have special handling |
| Same loader, IL 17f7–183f | Sprite PPU = `100 * 512 / originalWidth`, center pivot; **not terrain's 330 rule** |
| `Utils.GetUnitSprite`, IL 0075–00b8 | Normal path matches unit Country + space + Name against loaded mod graphics; then country/shared/resource fallbacks |
| `UnitGO.SetSprite`, IL 0034–0044 | Assigns `Utils.GetUnitSprite(unit)` to unit renderer; also updates native background/icons separately |
| `CameraGO.Zooming`, IL 0033–0130 | Orthographic camera; scroll/key changes target size, clamp then Lerp using unscaled delta and speed 15; zoom step factor uses 6 below/equal S=45, 30 above, multiplied by player setting |
| `CameraGO..ctor` | minZoom=5, maxZoom=1000; Start also has map-dependent initial framing; these constructor values alone are not a live-map measurement |
| `PlayerSettings.Reset`, IL 0501–0503; `UIManager.Update`, 06d5–06e6 | Default NATO key is KeyCode 110 (N), remappable; calls native switch |
| `UIManager.SwitchNATOrepresentation`, IL 0020–006e | Flips global `isNATO`, iterates player units, calls `UnitGO.SetSprite` |
| `Utils.GetUnitSprite`, IL 0292 onward | NATO path chooses symbols by unit properties; commanders choose `Commander`; no assumption that custom brigade names select NATO images |
| `Utils.GetUnitBackground`, IL 0018–0041 | NATO non-air background uses `Counter full square`; planes use round background |
| `resources.assets`: ordinary and core Unit prefabs | root scale 0.37, Unit representation child scale 1; source measurements retained in `evidence/prefab_transforms.json` |
| `MapGO.RespawnPlayerUnits` | Instantiates ordinary/core prefab under unitsParent and places at tile coordinates; scene parent overrides remain a live-test concern |
| `MapGO.GenerateMapAndInitializePlayers`, IL 070b–0756 | x = col*4.42; y = row*5.10 + (even column ? 2.55 : 0) |

No zoom-based alternate-art selection was found in the inspected camera,
unit-rendering, sprite-lookup and NATO switch paths. This is a bounded static-code
finding, not proof about every possible mod or future game version.

At viewport height H, camera size S, root scale 0.37 and unchanged scene parents:
`sprite canvas width = originalWidth / 100 * 0.37 * H / (2*S)`.
At H=1080 and 1024 source: 204.60, 102.30, 51.15, 25.57 px for S=10,20,40,80.
Visible miniature width is smaller because transparent margins are included.
The harness approximates the 512-wide bilinear stage, not Unity BC3 compression,
mip selection, lighting, UI, rotation or filtering exactly.

## Native NATO assessment and switching decision

The native N toggle already changes symbol/background and retains dynamic unit
information. It is global and manual, not a demonstrated automatic zoom feature.
The first prototype therefore supplies **only miniature sprite art**; it does not
bake the second reference's frame, NATO symbol or arbitrary stats into PNGs.

Offline visual inspection: portraits and short labels are useful near S=10;
at S=20 they are marginal, and at S=40/80 they do not identify officers reliably.
This supports testing NATO at wide zoom. **No Harmony switching was implemented**:
runtime native-N comparison has not passed, and a global toggle would need to
respect the user's manual N choice rather than repeatedly overwrite it.

If the live comparison later demonstrates a real need, consider an opt-in,
camera-projected-pixel threshold with hysteresis and per-unit cached sprites,
respecting manual NATO mode and native SetSprite refreshes. Thresholds, Harmony
entry points, UI behavior, save/load and AI interaction remain proposals.

## Actual validation and remaining game check

Completed: dated snapshot cross-check; approved-file and Git blob preservation;
RGBA dimensions, transparency and margins; missing-portrait and unknown-filename
gates; measured scale math including 512/1024 trap; offline four zoom previews;
visual inspection of all four composites. Full suite: **17 passed**.

The pinned legacy `construct==2.10.56` install fails under bundled Python 3.12
because it imports removed `imp`. Existing tests do not need that dependency;
the suite ran with pytest 7.3.1/click 8.1.7 installed separately and a workspace
temporary directory. No dependency upgrade was mixed into this art patch.

Computer Use returned **“Computer Use was not approved to use hex of steel”**
when attempting to open the installed game. Consequently: **no in-game sprite
import, N-key visual comparison, screenshot, AI/UI test, save/load test, or
playability claim**. The sheets are offline visualizations, not game captures.

To complete the game gate in a disposable mod created by the editor:

1. Create four units whose exact Name and Country match `asset_manifest.json`;
   use actual editor country spelling. Country names here follow the previous
   Kernstown candidate (`Confederacy`, `Union`), not a validated current unit table.
2. Copy one 1024 candidate to `Graphics/Units/<Country>/<exact Name>.png` in that
   disposable mod. Do not overwrite originals, stock art, workshop art or a save.
3. Put infantry, cavalry and commander on adjacent tiles; test normal/N at
   several zooms. Check portraits against native stats, health, icons and rotation.
4. Test the same source at 512 separately, expecting half-world-size under this
   build's loader. Capture dimensions and actual orthographicSize if instrumented.
5. Check command unit NATO symbol, selection, AI turn, save/reload and normal
   graphics restoration. Only then decide whether Harmony adds value.

Art limitations: generated miniature poses/counts are decorative, not personnel
strengths. Garnett's Virginia seal is illustrative, not a verified specific flag.
Ashby/Jackson have no unverified banners. Kimball's inaccurate generated national
colour was rejected and removed. Jackson's courier is generic and carries a
folded dispatch; Hotchkiss is not assigned to the March 23 HQ. These are review
art candidates pending historical/visual approval, not final historical reproductions.
