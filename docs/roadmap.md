# 1862 Valley Campaign — implementation roadmap

Every milestone requires evidence. "Code exists" is not equivalent to "loads and runs inside Hex of Steel."

| Milestone | Goal | Exit test | Status |
|---|---|---|---|
| M0 | Freeze audited assets, document scope and inventory | Approved paths recorded, no destructive moves | In progress |
| M1 | Confirm genuine Hex of Steel map/scenario serialization | Small editor-exported map inspected, changed, reloaded in game | Not verified |
| M2 | Reproducible geographic-to-hex pipeline | Test region shows correctly located terrain/roads and one-mile hex scale | Not started |
| M3 | Full Valley operational map | Winchester, Staunton, Luray, Massanutten, McDowell, Franklin connected accurately | Not started |
| M4 | Dated 1862 order of battle | Units, commanders, assigned parent formations, reinforcements and sources validated | Not started |
| M5 | Commander eligibility prototype | A brigade receives only authorized HQ effects; save/load and AI checked | Not verified |
| M6 | Campaign scenario March–June 1862 | Maneuver, fighting, alternate outcomes, Union and CSA sides tested in game | Not started |
| M7 | Release packaging and polish | Reproducible installation and end-to-end game playtest | Not started |

## Highest-priority work
1. Import/test a **small known-working editor-exported map**; compare with existing `maps/*.sav` and document format evidence.
2. Build a geographic test strip across the main Valley, Massanutten, and the Luray Valley. **Do not collapse the Valley to 1–2 hexes.**
3. Build a sourced, date-specific order of battle for Jackson/Ewell/Johnson and Banks/Shields/Frémont; brigades are maneuvering units.
4. Investigate actual bonus-selection and parent-command data; use Harmony only if the engine permits a reliable patch.
5. Validate the playable 1862 campaign before discussing new theaters.

## Engineering stop signs
- Unverified map format: do not emit .sav files labeled playable.
- Unverified Harmony entry point: do not claim hierarchical command is implemented.
- Insufficient map performance at one-mile scale: report measured constraints; do not silently shrink historical valleys.
- An asset is legally restricted or of unknown provenance: maintain reference status; exclude from redistributable packages.

`scenarios/1864/` is retained as legacy planning material only.