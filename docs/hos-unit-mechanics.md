# Hex of Steel — unit data, commanders (leaders) & counter art

Research notes for mapping the 1862 Valley OOB onto **Hex of Steel** (Steam app 1240630,
developer "Valentin's studios" / A Corsican Frog). Everything below is cited; items marked
**UNVERIFIED** must be tested in-game before we rely on them.

## Sources
- [M] Official manual (current, Steam store asset): https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1240630/manuals/1e929c3c9d09670cb450bdf6272b9522dfb4bc5b/Manual.pdf — page refs are the manual's "Page N of 65" footers.
- [M-old] Earlier manual revision: https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1240630/manuals/a629ccb39360b1023aa0d2b2921e98e1c6b311de/Manual.pdf
- [S1] Steam discussion "Generals and their bonus" (developer reply): https://steamcommunity.com/app/1240630/discussions/0/4342111082246068198/
- [S2] Steam discussion "How to change the unit image?": https://steamcommunity.com/app/1240630/discussions/0/3838801285229788338/
- [S3] Steam discussion "Editing Units" (developer replies): https://steamcommunity.com/app/1240630/discussions/0/603026374004886409/
- [S4] Steam discussion "Where are downloaded mods located?": https://steamcommunity.com/app/1240630/discussions/0/744883366278488584/
- [Y] "[OFFICIAL] Hex of Steel – How to Mod (Step-by-Step Tutorial)": https://www.youtube.com/watch?v=sGADvjll8pU
- [G] Community Harmony/DLL mod scaffolder: https://github.com/mxovd/hos_mod_setup

## 1. Unit stat fields (Unit Editor)
From [M] pp.14-16 ("Unit stats" / "Unit counters"):

| Field | Meaning in engine |
|---|---|
| Soft attack (damage) | vs. non-armoured targets (infantry, unarmoured artillery) |
| Hard attack | vs. armoured vehicles and ships |
| Air attack | vs. aircraft |
| Visibility | hexes seen through fog of war; base 1, recon 2 |
| Attack range | hexes at which it can attack; no line-of-sight terrain blocking |
| Ammunition | attacks before resupply |
| Fuel / supplies | movement budget in terrain cost (road 1, plain 2, forest 3 …) |
| HP | manpower/health; 0 = destroyed |
| Armor | armour points |
| Movement points | max fuel spent per turn |

Other per-unit state: **rank & XP** (5 ranks; rank 5 may receive a random *Hero*) [M] pp.18-19;
2 action points/turn [M] p.17; entrenchment 0-3 (-15% attacker damage per level) [M] p.31.
Loadout effects (e.g. horses: max MP 3, fuel 80) are **hard-coded**, not editable [M] p.21-23, [S3].

**Morale** is an *optional game setting*, not an editable stat: when on, each unit has a dynamic level
Excellent/Good/Average/Bad/Awful (+10/+5/0/-5/-10% damage), raised by winning fights and manpower
resupply, lowered by losing VPs [M] p.29, p.28. Shown as the coloured bar on the counter [M] p.16.

**Supply** (optional "Complex Supplies"): a 0-100% rate from supply sources (cities, airfields 50%,
purchasable Supply depots 100%) along road/rail paths, reduced by adjacent enemies; it caps per-turn
ammo/fuel/HP resupply [M] p.35, p.57. Supply does **not** come from commanders/HQ units.

## 2. Commanders (the leader / command-radius mechanic) — EXISTS
[M] p.47 "Commanders"; [M-old] "Generals"; [S1]:
- A **Commander** is a special, **separate, non-combatant unit** on the map (not an attachment).
- Its **Range stat = command radius** in tiles. Manual example: Auchinleck, range 7 → every friendly
  unit within 7 tiles is buffed (highlighted area when selected/hovered).
- Its **Soft / Hard / Air damage stats become % bonuses** for friendlies in radius (Auchinleck 14/12/5 →
  +14% soft, +12% hard, +5% air). [M-old] says armour is treated the same way (defence bonus) —
  **UNVERIFIED in current build**. Developer [S1]: the % is applied to the *final* computed damage, after
  other modifiers, so it is not a flat add to base stats.
- **Bonuses do not stack**: with several commanders covering a unit, only the highest bonus per category
  applies [M] p.47, confirmed in testing by [S1].
- Cannot attack or retaliate; can be bought only once; death is permanent; cannot be bought in campaign
  scenarios; cost cash, or HQ points with the Policies option [M] p.47, p.61.
- Per-leader data = an ordinary unit record in the Unit Editor (name, country, picture, soft/hard/air
  damage → bonus %, range → radius, MP, HP, cost). So radius and bonus are set **per commander unit**.
- **Heroes** are different: random medal-winner bonuses auto-assigned to rank-5 units; "Heroes are not
  commanders" [M] p.19. Mods can add them (Custom Heroes folder) [Y].

What does **NOT** exist (per manual; none described anywhere in [M]):
- No commander→subordinate link or chain of command: a commander buffs **every** friendly in radius,
  regardless of brigade/division/corps. No "attached to unit X" field.
- No leader-specific morale, initiative, rally, activation or command-point system; no command-span
  penalty for being out of radius (units out of radius simply get no bonus).
- No supply-from-HQ; no formation modes (line/column/square).
- No stacking of multiple leaders' bonuses.
- Leader effects are limited to soft/hard/air (and possibly armour) % within one radius.

## 3. Mapping the 1862 command hierarchy onto commanders
Because bonuses don't stack and have no hierarchy, echelon is expressed only by **radius and bonus size**
in the per-commander Unit Editor record, plus scenario placement:

| Echelon (our data) | HoS representation | Proposed radius | Bonus (soft %) | Notes |
|---|---|---|---|---|
| Brigade commander (`brigade_commands_1862.csv`) | Commander unit placed with/adjacent to its brigade counter | 1-2 | low (≈5) | Keeps brigade leaders mostly affecting their own brigade; neighbour brigades may also benefit (engine can't prevent it) |
| Division (Ewell, Shields/Kimball, Williams, Blenker) | Commander unit behind the division's brigades | 3-4 | ≈8 | Covers brigades of its division when placed centrally |
| Corps / Department (Banks, Frémont, McDowell) | Commander unit | 5-6 | ≈10 | Covers divisions |
| Army (Jackson, Valley District) | Commander unit | 6-7 (manual's example scale) | ≈12-15 | Covers divisions; highest bonus wins where radii overlap |

Rules for generating scenarios from `src/oob.py` snapshots:
1. One Commander unit per `commander_of(formation, date)`; vacancy rows produce none (e.g. `FRM_US_FRMC_CAV`).
2. Brigade counters stay infantry/cavalry units; `type=hq` formations emit only a Commander unit.
3. Place each commander within radius of the formations listed by `command_chain()`; since the engine
   ignores the chain, correctness depends on placement only.
4. Because only the highest bonus applies, set brigade < division < corps < army bonuses so higher
   echelons override, and use radius to model reach. All numbers above are balance **proposals**, untested.
5. Commander death is permanent → model Ashby (killed 6/6), Elzey/Steuart (wounded 6/8) as scenario-to-scenario
   roster changes from `brigade_commands_1862.csv`, not in-scenario mechanics.
6. **UNVERIFIED:** whether a commander occupies a tile exclusively (blocking a combat unit) and whether
   scenario-placed (not purchased) commanders behave identically. Test in the editor before mass generation.

> Radius restriction to specific units: see [hos-commander-radius-restriction.md](hos-commander-radius-restriction.md).

## 4. Custom units, mod structure, counter art
- Create a mod in-game (Mods menu). Local mods: `%USERPROFILE%\AppData\LocalLow\Valentin's studios\Hex of Steel\MODS`;
  Workshop copies: `steamapps\workshop\content\1240630\` (read-only, Steam restores them) [S4], [S3].
- Mod folder contains `Manifest.json`, `Graphics/` (sub-folders e.g. `Units/<Country>/`), `Custom Units`,
  `Custom Countries`, `Custom Heroes`, `Custom Tiles`, `Maps`, `Sounds`, libraries [Y], [G].
- Units are edited in the in-game **Unit Editor**; unit identity = name + country; CSV exports are produced
  manually by choice, not auto-generated [S3], [Y]. Code mods use Harmony DLLs [G] (see `docs/3574617535/`).
- **Unit art is a sprite image, not a stat-derived NATO symbol**: PNG, **1024×1024** for land units
  (ships 1258×1258 per a community answer), file name must match the unit name exactly (case-sensitive),
  placed under `Graphics/Units/<Country>/` [S2], [Y]. The game also has a **NATO-symbol display toggle (key N)**
  [M] p.4 — engine-generated, not per-unit art.
- The counter frame (soft/hard/air damage, HP, range, MP, morale bar, veterancy/loadout icons) is drawn by the
  engine over the sprite [M] p.16.
- Repo note: existing `Unit_*.png` / `mdl_*.png` are 104×126 and 170×280 respectively — **not** the 1024×1024
  size cited above. Whether the engine rescales them is UNVERIFIED; approved portraits must not be
  regenerated or overwritten — any resized copies would need new filenames and user approval.
