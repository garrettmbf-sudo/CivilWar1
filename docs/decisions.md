# Decisions log

Settled decisions; change them only with the user's say-so, and add the date (ET) and PR. Open questions are at the bottom; resolved ones move up into the table.

| # | Decision | Date (ET) | Where |
| --- | --- | --- | --- |
| D1 | Timezone for the project is **ET**. | 2026-10-17 | user |
| D2 | **Hex of Steel stays the engine** (engine evaluation found no better fit; facing is feasible via Harmony). | 2026-10-17 | PR #10 `docs/engine-evaluation.md` |
| D3 | **One big Valley sandbox map** is the goal; linked fixed battle maps are not the default. Stays the goal until proven impossible. | 2026-10-17 | PR #10 `docs/valley-map-build-plan.md` §6 |
| D4 | Scale **500 yd per hex, provisional**; fallback **750 yd**, then **1 mile**. File size does not decide the scale. | 2026-10-17 | PR #10 §1, §6.1 |
| D5 | **Piedmont removed** from the map; the east edge lies just east of the Blue Ridge. | 2026-10-17 | PR #10 `map_shape.json` |
| D6 | **Eastern Blue Ridge passes** are kept with roads to east-edge exits; they serve as **Richmond exits** (and Union entries). | 2026-10-17 | PR #10 `blue_ridge_passes.csv`, `east_exit_edges.csv` |
| D7 | **Western roads to Romney and McDowell** are on the map. | 2026-10-17 | PR #10 `western_roads.csv` |
| D8 | **Lexington** (VMI) is on the map at the **south edge**. | 2026-10-17 | PR #9 `LEXINGTON.md` |
| D9 | **Kernstown** is the **250-yd standalone** test map, left as-is (no re-render; read-only for other lanes). | 2026-10-17 | user |
| D10 | Tile strategy: **edge-matched library + regional tint/brightness modulation from a low-res painted basemap + unique hero tiles** (towns, battlefields, pike/river corridors); 7-bit + oxipng encoding; sector maps only as last resort. | 2026-10-17 | PR #10 §3–4 |
| D11 | **Byte-identical duplicates removed**, except files in distinct slots (log in `docs/inventory/dedupe_2026-10-17.csv`). | 2026-10-17 | PR #9 |
| D12 | **Flat-top hex layout.** Superseded in its parity by D15. | 2026-10-17 | PR #9 `docs/hex-convention.md` |
| D13 | **Campaign start 1862-03-22 at dawn** (user decision, recorded in PR #15 `docs/history/campaign_start.md`; code change in PR #17). | 2026-10-17 | PR #15, #17 |
| D14 | **Unit facing via the Harmony mod**; the user wants it. | 2026-10-17 | PR #18 `mods/facing` |
| D15 | **Hex parity (resolved Q1):** even-q native, per MapGO.cs, decided by Major Hotchkiss 2026-10-17; Kernstown re-cut as v0.4.2. Flat-top, even columns shifted half a row north, rows increase north, column-to-row pitch 4.42:5.1, no conversion layer; `ROW_DIRECTION` removed. | 2026-10-17 | `MapGO.cs:452-459`; PR #9 / #10 `src/hex_utils.py`, `docs/hex-convention.md` |

## Open questions
| # | Question | Owner | Notes |
| --- | --- | --- | --- |
| Q2 | **Campaign time model:** Harmony variable-turn clock at 500 yd vs native day turns at 1 mile (concession ladder). Needs the blank-map stress test and a Harmony clock prototype. | General Eggbot + user | PR #10 §6.1 |
| Q3 | **Facing parameters:** front/flank/rear multipliers (1.0/1.25/1.5 default), turn-in-place cost (1 MP), whether the **AI gets a free end-of-turn re-face**. | user (Eggbot implements) | PR #18 `FacingConfig.json` |
