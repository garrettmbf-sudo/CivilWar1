# Historical ratings → Hex of Steel crosswalk (HISTORIAN GUIDANCE ONLY)

> This file suggests how the 1-5 historical ratings in `historical_data/unit_ratings_1862.csv` and `command_ratings_1862.csv` could inform Hex of Steel parameters. **The final game numbers belong to the Quartermaster bot.** Nothing here edits `units/units.yaml` or any stat file. The `hos_notes` column in both ratings CSVs repeats these suggestions per row; it is also guidance only.

Game version checked: **Hex of Steel 8.4.15** (Steam public branch, patch notes 7 Oct 2026 [P]). The mechanics below come from the official manual "Last updated: November 9th 2025" [M]. I found no later manual on Steam, so anything changed after Nov 2025 is unverified.

## Sources
- [M] Official manual, Nov 9 2025, Steam store asset: https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1240630/manuals/a49cf88ca3078c0ce8c3c67ee168f508dd428c0c/Manual.pdf . Page = the "Page N of 65" footer. The Oct 25 2025 revision (…/1e929c3c…/Manual.pdf), cited in `docs/hos-unit-mechanics.md`, differs only in minor wording (diffed).
- [P] Patch notes 8.4.15: https://steamcommunity.com/app/1240630/announcements/ and https://steamdb.info/patchnotes/25771925/ ; branch list https://steamdb.info/app/1240630/depots/
- [S1] Developer reply on commander bonuses: https://steamcommunity.com/app/1240630/discussions/0/4342111082246068198/ (via `docs/hos-unit-mechanics.md`)
- [S3] Developer: loadout effects are hard-coded: https://steamcommunity.com/app/1240630/discussions/0/603026374004886409/
- [S5] Developer: Unit/Tile editor changes save into an activated mod: https://steamcommunity.com/app/1240630/discussions/0/4522261847578295157/
- [S6] Map editor: press D over a unit to toggle its "defensive"/stationary shield: https://steamcommunity.com/app/1240630/discussions/0/592882992704221593/ ; the keys G/D/P are also listed in [M] p.4
- [S7] Community Harmony mod code (not official) showing `Unit.Lvl`, `BaseMaxHP`, `MaxHP`, `CurrHP`, `Unit.AddXP`, `Utils.UpdateUnitStatsOnTurnOne`: https://steamcommunity.com/app/1240630/discussions/2/840627927552969287/
- Rejected source: the Steam guide "Scenario Editor Guide" (id 2912414954) describes XP 0-399, steps and suppression. It is for **Unity of Command II**, not Hex of Steel (checked on the page's app header), so it is not used.

## Confirmed Hex of Steel parameters
| Parameter | What the engine does | Source |
|---|---|---|
| Rank / XP | 5 ranks. Rank 1 = 0 XP, rank 2 = 15, rank 3 = 40, rank 4 = 75, rank 5 = 120. Each rank above 1 gives +10 HP and +4% damage. XP: +2 per attack, +5 per kill, +3 per VP captured. Healing manpower costs 1 XP per 10 HP and can lower the rank. Max rank 5; XP unlimited | [M] p.18 |
| Rank 5 Hero | A random medal-winner hero "from its type" (WW2 historical) is assigned at rank 5 if any exists for the country | [M] p.18-19 |
| Veteran purchase option | "Veterans will spawn with a rank of 3 (+30HP and +8% damage)" (store customization) | [M] p.22-23 |
| Core units | In campaigns, core units carry over "all their stats and history" between scenarios | [M] p.25 |
| HP (strength) | Manpower/health; damage dealt is proportional to HP (50% HP = -50% damage) | [M] p.15, p.28 |
| Soft / hard / air attack, armor, attack range, ammo, fuel/supplies, movement points, visibility | Per unit-type stats; visibility base 1, recon 2. Infantry vs infantry: 100% of armor applies | [M] p.14-15, p.28 |
| Action points | 2 per turn (attack/move etc.) | [M] p.17 |
| Morale | **Optional global setting**, not a per-unit stat. When on, each unit has a dynamic level: Excellent +10%, Good +5%, Average 0, Bad -5%, Awful -10% damage. Raised by winning attacks, capturing VPs and manpower resupply; lowered by losing VPs | [M] p.29, p.28 |
| Retreat | Base threshold 30% of current HP in incoming damage. High rank and high morale reduce the retreat chance, bad morale raises it, and "lower quality infantry" (militia, conscripts) retreat more | [M] p.40 |
| Entrenchment | +1 level per turn without moving; max 3 (4 with a policy); -15% attacker damage per level; reset by moving; artillery removes 1 level per attack | [M] p.31, p.28 |
| Encirclement / surrender | -15% retaliation per extra adjacent enemy; a unit that cannot retreat surrenders | [M] p.39, p.41 |
| Supply (optional "Complex Supplies") | 0-100% rate from cities, airfields and purchasable supply depots along road/rail paths; caps per-turn ammo/fuel/HP resupply (heal speed 35%). Reduced by adjacent enemies and bad weather. **Not from commanders** | [M] p.35, p.57 |
| Zone of Control, Upkeep, Manpower | Optional mechanics (7.0.0, 7.1.0, 6.3.2) | [M] p.62-64 |
| Commanders | Separate non-combat unit. **Range stat = bonus radius**. Its soft/hard/air "damage" stats become % damage bonuses for all friendlies in the radius. Bonuses don't stack (highest kept); no attack or retaliation; death is final; can't be bought in campaign scenarios | [M] p.47; [S1] (bonus is applied to final damage) |
| Loadouts | Horses: max MP 3, fuel 80 (towed artillery option). Loadout effects are hard-coded | [M] p.23; [S3] |
| Unit Editor | Edits unit-type records saved into an activated mod | [S5] |
| Map/scenario editor per-unit keys | G = unit is a kill objective, D = defensive (stationary AI), P = paratrooper state | [M] p.4; [S6] |

**Not found in any Hex of Steel source (treat as non-existent unless proven):** a per-unit morale/cohesion value, suppression, an initiative stat, leader traits or skills, a commander-subordinate link, and supply from an HQ.

**Unverified:**
- Whether the map editor can set a placed unit's starting XP, rank, HP, entrenchment or "veteran" flag. No HoS source found; right-click in game shows unit history [M] p.4.
- Whether the morale level can be set at scenario start.
- Whether a custom unit can be assigned the militia/conscript "quality" class used by the retreat rule.
- Commander armor → defense bonus (old manual only).
- The commander's own rank/XP effects.
- Whether harmony-level `Unit.Lvl`/XP fields can be set by a mod at scenario start. [S7] is community code; it suggests yes but is untested.

## Crosswalk: units
| Historical field (1-5) | HoS parameter(s) it informs | Suggested mapping | Notes |
|---|---|---|---|
| experience | **Rank/XP** (+10 HP, +4% damage per rank; retreat resistance) | 1 → rank 1 (0 XP); 2 → rank 2 (15-39); 3 → rank 3 (40-74); 4 → rank 4 (75-119); 5 → top of the rank-4 band (100-119) | Avoid rank 5 unless the mod supplies Custom Heroes; stock heroes are WW2 medal winners [M] p.18-19. Delivery: core-unit carry-over in a campaign [M] p.25, the Veteran option = rank 3 [M] p.23, or a Harmony mod [S7]. Direct editor XP entry is UNVERIFIED |
| cohesion_morale | **No direct per-unit parameter.** Global morale is dynamic only [M] p.29 | Nearest levers: (a) fold it into the starting rank, because rank lowers retreat chance [M] p.40; the `hos_notes` use rank ≈ round((2×exp + cohesion)/3), capped at 4. (b) Starting HP for straggling/desertion: cohesion 1 → ~70% HP, 2 → ~85%, 3-5 → full. (c) If a "lower quality" class can be applied to custom units, use it for cohesion 1-2 (UNVERIFIED) | Examples: 1st Md (CS) mutiny, Ashby's cavalry, Blenker's starved division |
| training | Unit-type **soft attack** (fire discipline), optionally **armor** (infantry vs infantry armor applies 100%, [M] p.28) and **MP** (march discipline) for foot units | Soft attack vs side template: 1 → -10%, 2 → -5%, 3 → 0, 4 → +5%, 5 → +10%. Armor/MP only if Quartermaster chooses | Requires separate unit-type records (Unit Editor in a mod [S5]); a per-instance setting is UNVERIFIED. Horse-loadout MP is hard-coded [S3] |

## Crosswalk: commanders
| Historical field (1-5) | HoS parameter(s) | Suggested mapping | Notes |
|---|---|---|---|
| tactical_skill | Commander **soft-damage stat → % soft-damage bonus** | Brigade echelon: 1 → 1%, 2 → 3%, 3 → 5%, 4 → 7%, 5 → 9%. ×1.3 division, ×1.5 department, ×1.6 army. Hard/air = 0 (no armour or air in 1862) | Highest bonus wins, so army-level values override brigade leaders in overlapping radii [M] p.47 |
| administration | Commander **Range** (radius) | Echelon base (brigade 2, division 4, department 5, army 6; matches the bands in `docs/hos-unit-mechanics.md` §3) +1 if admin ≥ 4, -1 if ≤ 2 | Supply is not an HQ function in HoS [M] p.35. The nearest supply lever is depot placement and the Complex Supplies setting; that is scenario design, not a commander stat |
| initiative | Commander **movement points** (keeping up with the troops) | 1-2 → -1 MP vs the side's commander default; 3-4 → 0; 5 → +1 | No initiative stat exists. Scenario-level levers: earlier arrival, aggressive AI (no D shield) |
| reliability | **No engine parameter** | Scenario-design levers only: delayed reinforcement turns, D-shield (stationary) AI for commands that historically held back, or Quartermaster lowering the bonus by 1-2 points | E.g. Garnett's withdrawal, Carroll's unburnt bridge, Steuart's delayed pursuit |

## Per-row values
`hos_notes` (last column of both ratings CSVs) applies the tables above to every row. The commander echelon is taken from `brigade_commands_1862.csv` on the rating date (highest level held). Exception: Shields on 03-23 holds no command row because he was wounded and Kimball commanded the field; his note says "echelon brigade", which Quartermaster should treat as division/off-field.
