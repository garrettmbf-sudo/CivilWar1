# Ratings → Hex of Steel unit-editor stats (deterministic)

Generator: `python -m src.hos_stats` writes `historical_data/hos_unit_stats_1862.csv`. Tests are in `tests/test_hos_stats.py`.
Inputs:
- `unit_ratings_1862.csv` and `command_ratings_1862.csv` (PR #13)
- the OOB (`src/oob.py`) for class, regiment membership and command echelon

Scale assumptions: 500 yd/hex. `docs/valley-map-build-plan.md` (map branch) gives MP for roughly 1-hour tactical turns: 9 road MP for infantry, 14 for cavalry.

**Turn-length conflict (flag):** at 500 yd/hex, a native **1-day** turn would mean about 70 hexes of march. That is far outside the stock MP range of about 3-9, and loadout caps such as horses (max MP 3) are hard-coded. The MP values here therefore assume the plan's frozen-date / turn-clock approach. If true 1-day turns are used, MP must be rescaled (one `BASE` table change) and the map scale revisited.

Only engine fields are emitted:
- soft/hard/air damage, armor, HP, ammo, fuel, movement points, attack range, visibility, rank
- for commanders: range (= command radius) and soft/hard damage (= % bonus)

There is no "defense" field in HoS (Armor applies vs. hard attacks), and no per-unit morale field.

## Combat units (one row per rating date)
| Field | Formula |
|---|---|
| quality `q` | `(training − 3) + (experience − 3)`, range −4…+4 |
| soft_damage | class base + 2·q (inf 20, cav 14, art 24) |
| hard_damage | max(1, base + q//2) (inf 4, cav 2, art 6); no armoured targets in 1862 |
| air_damage, armor | 0 |
| hp | 20 × regiments on that date, clamped 20-100. **Proxy:** the repo has no brigade-level returns (`HP_PROXY_REGIMENT_COUNT`) |
| ammo / fuel | inf 6/45, cav 5/70, art 5/45 (balance placeholders) |
| movement_points | inf 9, cav 14, art 7 |
| range | inf/cav 1; artillery 3. Smoothbore = 3, rifled = 4, but gun type isn't in the repo data (`GUN_TYPE_UNVERIFIED_RANGE_3`) |
| visibility | inf/art 1, cav 2 (recon) |
| rank (starting experience 1-5) | `round(0.6·experience + 0.4·cohesion_morale)` |

**Cohesion/morale** has no per-unit field: HoS morale is a global option with dynamic levels. So cohesion feeds **only the starting rank**. It isn't put into Armor, because Armor only affects hard attacks and would be meaningless here.

Regiments and batteries use their **own rating** when there is one (`OWN_RATING`): the latest regiment- or battery-level row dated on or before the brigade's rating date. Rows whose basis says "inherits [brigade] rating" don't count as direct evidence. Without a direct rating, the unit **inherits the parent brigade's rating** (`INHERITED_FROM_PARENT`).

**Excluded (unrated):** REG_OH13C, ART_PLEASANTS, ART_US_WVB, ART_US_ADDHOW and ART_US_PAE stay in the OOB with their flags but get no stats. They're listed with an `excluded_reason` in `historical_data/hos_unit_stats_excluded_1862.csv` and don't count toward brigade HP.

**Legacy id:** REG_VA12 was renamed to REG_GA12 (12th Georgia, OR 12/1 p.476). The PR #13 ratings files still use the old id, which `src.oob.LEGACY_ID_ALIASES` resolves when the files are read. Batteries attached to HQ/artillery groups have no unit rating and are not emitted.

## Commander units
| Field | Formula |
|---|---|
| echelon | highest level commanded on the rating date, from `brigade_commands` → formation level (brigade/detachment/battalion → brigade; division; department; army). Override: `FRM_CS_NW` → division, since the Army of the Northwest had about 2 brigades |
| range (radius) | brigade 1-2, division 3-4, department 5-6, army 6-7. The upper value is used if `(initiative + administration)/2 ≥ 3.5` |
| soft_damage (= % bonus) | `clamp(2·tactical + (initiative − 3) + (reliability − 3), 1, 15)` |
| hard_damage | soft // 2 |
| rank | round(mean of the four ratings) |
| hp/mp/vis | 20 / 14 / 2 (placeholders) |

Bonuses don't stack in-engine (highest wins). No echelon floor is applied, so a skilful brigade leader can out-buff a poor army commander locally. That is deliberate.

## Balance / no scripted outcome
- No faction term appears anywhere in the formulas (a test checks this).
- Sum of (soft × HP/100) for rated formations:
  - 3/23: CSA 50 vs USA 54
  - 5/25: CSA 134 vs USA 38
  - 6/8: CSA 141 vs USA 166
- The late-May gap mirrors the real numbers (about 16-17k vs 6.5k) and the June totals favour the Union. Outcomes depend on play and on the scenario's victory points, not on stat bias.

## Flags in the CSV
- `PROVISIONAL_RATING`: the source row is provisional.
- `HP_PROXY_REGIMENT_COUNT`: HP comes from the regiment count.
- `NO_REGIMENTS_ON_DATE`: the formation has no regiment rows on that date (e.g. FRM_US_CAV_BRODHEAD), so HP is at the floor.
- `GUN_TYPE_UNVERIFIED_RANGE_3`, `INHERITED_FROM_PARENT`, `ECHELON_OVERRIDE`.
