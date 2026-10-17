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
Aligned with `docs/history/hos_rating_crosswalk.md` (PR #13, HoS 8.4.15 manual).

| Field | Formula |
|---|---|
| soft_damage | round(class base × (1 + 0.05·(training − 3))), i.e. training 1…5 → −10%…+10% (bases: inf 20, cav 14, art 24). Experience is **not** applied here, because the engine already gives +4% damage per rank above 1 (manual p.18) |
| hard_damage | max(1, round(base × the same factor)) (inf 4, cav 2, art 6); no armoured targets in 1862 |
| air_damage, armor | 0 |
| hp | 20 × regiments on that date, clamped 20-100, then × cohesion factor (cohesion 1 → 70%, 2 → 85%, 3-5 → 100%; crosswalk option b, straggling/desertion). **Proxy:** no brigade-level returns in the repo (`HP_PROXY_REGIMENT_COUNT`) |
| ammo / fuel | inf 6/45, cav 5/70, art 5/45 (balance placeholders) |
| movement_points | inf 9, cav 14, art 7 |
| range | inf/cav 1; artillery 3. Smoothbore = 3, rifled = 4, but gun type isn't in the repo data (`GUN_TYPE_UNVERIFIED_RANGE_3`) |
| visibility | inf/art 1, cav 2 (recon) |
| rank (starting rank 1-4) | `round((2·experience + cohesion_morale)/3)`, **capped at 4** |

**Rank cap 4:** at rank 5 the engine assigns a random WW2 medal-winner "hero" from the unit's type if one exists for the country (manual 8.4.15 p.18-19, crosswalk). No 1862 unit may start at rank 5; a test checks this. Units can still earn rank 5 in play unless the mod supplies custom heroes.

**Cohesion/morale** has no per-unit field: HoS morale is a global option with dynamic levels (manual p.29). Cohesion feeds two things:
- starting rank, because rank lowers the retreat chance (p.40)
- starting HP for cohesion 1-2

It isn't put into Armor, because Armor only applies against hard attacks.

Regiments and batteries use their **own rating** when there is one (`OWN_RATING`): the latest regiment- or battery-level row dated on or before the brigade's rating date. Rows whose basis says "inherits [brigade] rating" don't count as direct evidence. Without a direct rating, the unit **inherits the parent brigade's rating** (`INHERITED_FROM_PARENT`).

**Excluded (unrated):** REG_OH13C, ART_PLEASANTS, ART_US_WVB, ART_US_ADDHOW and ART_US_PAE stay in the OOB with their flags but get no stats. They're listed with an `excluded_reason` in `historical_data/hos_unit_stats_excluded_1862.csv` and don't count toward brigade HP.

REG_VA12 has been renamed to REG_GA12 (12th Georgia, OR 12/1 p.476) everywhere, including the #13 files (b7a3b96), so no alias is needed. Batteries attached to HQ/artillery groups have no unit rating and are not emitted.

## Commander units
| Field | Formula |
|---|---|
| echelon | highest level commanded on the rating date, from `brigade_commands` → formation level (brigade/detachment/battalion → brigade; division; department; army). Override: `FRM_CS_NW` → division, since the Army of the Northwest had about 2 brigades |
| range (radius) ← **administration** | echelon base (brigade 2, division 4, department 5, army 6) +1 if admin ≥ 4, −1 if admin ≤ 2, clamped to the band (brigade 1-2, division 3-4, department 5-6, army 6-7) |
| soft_damage (= % bonus) ← **tactical** | brigade 1/3/5/7/9 % for tactical 1-5, × 1.3 division, × 1.5 department, × 1.6 army, rounded, max 15 |
| hard_damage | 0 (no armour in 1862; crosswalk) |
| movement_points ← **initiative** | 14; initiative 5 → 15, initiative ≤ 2 → 13 |
| rank | round((initiative + tactical + administration)/3), capped at 4 (the commander's own rank effects are unverified) |
| reliability | **not used.** There is no engine parameter. It informs scenario design only (delayed arrivals, D-shield AI) |
| hp/vis | 20 / 2 (placeholders) |

Bonuses don't stack in-engine (highest wins, manual p.47). The echelon multiplier means a higher commander usually dominates overlapping radii, but a skilful brigade leader (tactical 5 = 9%) can still beat a weak army commander (tactical 2 = 5%).

**Formula change (this revision):**
- Training alone sets the soft-attack offset (was training + experience).
- Cohesion now trims HP for cohesion 1-2.
- The commander bonus comes from tactical × echelon (was tactical + initiative + reliability), and hard bonus is 0 (was soft/2).
- Range comes from administration (was initiative + administration).
- Initiative now sets commander MP.
- Rank is capped at 4 for units and commanders.

## Balance / no scripted outcome
- No faction term appears anywhere in the formulas (a test checks this).
- Sum of (soft × HP/100) for rated formations:
  - 3/23: CSA 47 vs USA 55
  - 5/25: CSA 123 vs USA 38
  - 6/8: CSA 126 vs USA 161
- The late-May gap mirrors the real numbers (about 16-17k vs 6.5k) and the June totals favour the Union. Outcomes depend on play and on the scenario's victory points, not on stat bias.

## Flags in the CSV
- `PROVISIONAL_RATING`: the source row is provisional.
- `HP_PROXY_REGIMENT_COUNT`: HP comes from the regiment count.
- `NO_REGIMENTS_ON_DATE`: the formation has no regiment rows on that date (e.g. FRM_US_CAV_BRODHEAD), so HP is at the floor.
- `GUN_TYPE_UNVERIFIED_RANGE_3`, `INHERITED_FROM_PARENT`, `ECHELON_OVERRIDE`.

## Unverified: placed-unit starting state
No Hex of Steel source shows that the scenario/map editor can set a placed unit's starting **XP/rank, HP or entrenchment** (crosswalk "Unverified"; the editor's per-unit keys are only G/D/P, manual p.4). The `rank` and cohesion-reduced `hp` columns are therefore **targets**. Possible delivery routes:
- separate unit-type records with HP and attack baked in
- core-unit carry-over in a campaign (p.25)
- the store "Veteran" option, which gives rank 3 (p.22-23)
- a Harmony mod setting `Unit.Lvl`/HP on turn 1, which is community code and untested

All of these need an in-game test before they're relied on.
