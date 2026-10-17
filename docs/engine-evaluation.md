# Engine evaluation: unit facing in Hex of Steel, and alternative engines (17 Oct 2026)

Sources are cited inline. **[DLL]** means the developer-shipped `Assembly-CSharp.dll` from the official example mod `acorsicanfrog/Example-Mod-Harmony` (repo commit 2026-10-07), decompiled with ILSpy 8.2 on the box for reading only; nothing decompiled is committed. Version caveat: it may lag the live Steam build. **[SAV]** means `templates/ACW_sample_102x60.sav` on `kernstown-map`, read-only. UNKNOWN marks anything not verified.

## Part 1: Unit facing in Hex of Steel via Harmony

### 1.1 What already exists in the engine [DLL][SAV]
- **Units are serialised.** `Unit` is `[Serializable]` and is written by BinaryFormatter inside the `.sav`. Each `Unit` has `int ID`.
- **A facing field already exists:** `Unit.FacingRotation` (enum `FacingRotations : byte` = WEST, EAST, NORTH, SOUTH, NORTH_EAST, NORTH_WEST, SOUTH_EAST, SOUTH_WEST). It is **already saved in .sav files**: `<FacingRotation>k__BackingField` appears in the sample save's member table.
- **Who may rotate:** `Unit.AllowedRotation` (NOT_SETUP / LEFT_RIGHT / ALL / NONE), set per unit type (`SetDefaultAuthorizedRotation`).
- **Facing on movement:** `UnitGO.RotateUnit(departure, arrival)` is called on every path step (`UnitGO` ~l.1664) and on multiplayer replay (`MultiplayerManager` ~l.1793).
  - For `ALL` units it sets one of **6 hex directions**: N, S, NE, NW, SE, SW. These match our flat-top grid, since N/S are same-column neighbours.
  - For `LEFT_RIGHT` units it only sets EAST or WEST.
- **The defender turns to face the attacker:** `UnitGO.RotateAttackedUnit(target, attacker)` is called on attack, retaliation and support fire (`UnitGO` ~l.2586/3459/3666/5814; `MultiplayerManager` ~l.1128).
- **Drawing:** `UnitGO.SetUnitRotation()` rotates or flips the sprite transform. `ALL` units use −90/90/180/0/−150/−30/150… degrees; `LEFT_RIGHT` units get a Y-axis flip. NATO-counter mode skips rotation.
- **Facing is purely visual today.** No combat code reads `FacingRotation`.

### 1.2 How combat is resolved [DLL]
- **Damage pipeline:** `Unit.GetPotentialDamage(UnitGO target, bool isRetaliation, bool isSupportiveFire)` builds a `BattleContext(attacker, target, damageType, isRetaliation, isSupportiveFire)`.
  - It then applies, in order: Health, Armour, Mechanized, Train, FrozenTerrain, Ships-support, CAS-vs-ships, …, Hero, Policies, PoliticalUnit, BadWeather, Morale, Torpedo, Flamethrower, Mountaineer, **Hills**, UnfavorableEnvironment, Landing, CombinedArms, Recon, Commander, Engineers, **Entrenchment**, **Encirclement**, ShipsVsLand, **Terrain**, RepeatedAttacks.
  - It is clamped to ≥0 between steps, and each modifier fills a `*Breakdown` field shown in the combat tooltip.
- **Encirclement (the only flanking-like rule):**
  - `ApplyEncirclementDamageModifier` uses `unitGO.CalculateEncirclement()`, which counts adjacent enemy ground units (not commanders or trains).
  - If the count is ≥2, the **firing** unit's damage drops by 15% × (n−1). So a surrounded unit retaliates and attacks more weakly.
  - There is no attack-direction bonus.
- **Callers:** `GetPotentialDamage` is used for real attacks, retaliation, support fire and ambush (`UnitGO`), for the combat-preview tooltip (`UnitGO` ~l.4964), and **26 times in `AI.cs`**.
- **How the AI picks attacks:**
  - `AI.CheckForAttack` fills `_dicOfDamagePerUnit` from `GetPotentialDamage` and lists the units it can kill.
  - `AI.GetAttackRiskRewardRatio` adds weight for VPs, bridges, allied neighbours of the attacker and of the target (a crude "gang-up" bias), and entrenched or VP positions.
  - The AI has no notion of direction.

### 1.3 Spare data fields
- **Per unit, no spare free-form slot.** Unit fields like `CustomName` are user-visible. Mods can't add serialised fields to `Unit` without breaking the BinaryFormatter layout.
- **But `FacingRotation` itself is the slot,** already saved and already updated on movement.
- **Game-level storage:** `GameData.ModDataBag` (`ModPropertyBag : ISerializable`, with `TryGet`/`TrySet` by string key; it also keeps unknown keys) is saved with the game. It can hold per-unit data keyed by `Unit.ID`, e.g. an explicit "faced" flag or a facing for units we keep `LEFT_RIGHT` for art reasons.

### 1.4 Feasibility per feature
| Feature | Approach | Difficulty | Update-break risk |
| --- | --- | --- | --- |
| Facing value per unit (6 directions) | Reuse `FacingRotation`; set our unit types to `AllowedRotation=ALL`. **Native, no code.** | Trivial | Low |
| Change facing during movement | Native (`RotateUnit` sets the last-step direction). Add a "turn in place" key costing MP (SoS has a keybind handler precedent). | Easy (auto) / moderate (manual turn, needs UI + MP cost) | Low / medium |
| Stop the defender auto-turning to face the attacker (otherwise flanking is impossible) | Prefix `UnitGO.RotateAttackedUnit` → return false for our units. | Easy | Medium (private call sites may change) |
| Flank and rear bonus | Postfix `Unit.GetPotentialDamage`: hex direction from target to attacker vs target `FacingRotation` → front / flank / rear multiplier (e.g. ×1.0 / ×1.25 / ×1.5). Also write a breakdown value. | Easy–moderate | Medium (signature is public; the pipeline has changed before) |
| Sprite rotation | Native rotation spins side-view figures, which looks wrong for our art. Instead, prefix `SetUnitRotation` to keep the E/W flip and add a **facing chevron** child sprite on the counter, rotated to the facing. | Moderate (UI sprite) | Medium |
| Save/load | Native for `FacingRotation`. Use `GameData.ModDataBag` for any extra state. | Trivial | Low |
| AI awareness, offensive | Automatic: the AI ranks targets with `GetPotentialDamage`, so a postfix makes it prefer flank and rear shots. | Free with the bonus patch | – |
| AI awareness, defensive (face threats, refuse flanks) | Postfix the AI end-of-unit-move to re-face toward the nearest enemy. Real line-holding needs AI rewrites. | Easy (re-face) / hard (formation logic) | High (`AI.cs` is a 10k-line private class) |
| Multiplayer | Moves replay `RotateUnit` and attacks replay `RotateAttackedUnit`, so facing stays consistent if **both** players run the same mod. Mods with assemblies count as `HasGameplayImpact()` (Mod.cs), are listed in the host request (`ServerGameService`), and disable Ironman. | Survives with the mod on all clients | Medium |

### 1.5 Minimal proof-of-concept patch (outline, not yet written)
```
[HarmonyPatch(typeof(UnitGO), nameof(UnitGO.RotateAttackedUnit))]  Prefix: if mod unit → return false (keep facing)
[HarmonyPatch(typeof(Unit), nameof(Unit.GetPotentialDamage))]      Postfix(Unit __instance, UnitGO p_targetUnitGO, bool p_isSupportiveFire, ref int __result):
     dir = HexDir(target tile → attacker tile)          // native even-q, same as src/hex_utils.py / Utils.GetAllTilesNeighbours
     rel = (dir - Facing6(target.FacingRotation)) mod 6   // 0 = front, 1/5 = flank, 2/4 = rear-flank, 3 = rear
     __result = round(__result * table[rel])              // skip when artillery fires at range (UNKNOWN design)
[HarmonyPatch(typeof(UnitGO), nameof(UnitGO.SetUnitRotation))]    Postfix: update a child chevron sprite to the facing
[HarmonyPatch(typeof(TurnManager), nameof(TurnManager.NextTurn))]  Postfix: AI players re-face toward nearest enemy (crude)
Unit types: AllowedRotation = ALL (unit editor / Modified base units).
```
- **Precedent:** Squad of Steel (github.com/murdockpeter/squadofsteel) patches exactly `Unit.GetPotentialDamage`, `UnitGO.AttackUnit`/`Attack`/`Retaliate` and `TurnManager.NextTurn` (`Scripts/Combat/SquadOfSteelCombatPatches.cs`). It adds line of sight, suppression and probabilistic combat. It has no facing rules. No other community mod with facing was found (UNKNOWN beyond the GitHub search for "hex of steel").
- **Verdict:** facing is **feasible, and cheaper than expected**, because the engine already stores, saves, syncs and auto-updates a 6-direction facing. The main work is the flank-bonus postfix, suppressing the auto-turn, a chevron marker and a crude AI re-face. Estimate: a few days for a proof of concept, with medium breakage risk on game updates.
- **In-game tests:**
  - Does an `ALL` unit's sprite rotate visibly?
  - Does `RotateAttackedUnit` suppression hold in a PBEM replay?
  - Does the combat preview show the patched value?

## Part 2: Alternative engines
| Engine | Facing | Scale fit (1862 operational Valley, 500 yd–1 mi, hours–days) | Custom-art ceiling | AI | Modding openness | Cost of moving our work |
| --- | --- | --- | --- | --- | --- | --- |
| **Hex of Steel (+Harmony)** | Stored and saved; combat needs a patch (Part 1) | Any hex scale; time in days only (hours need Harmony, see hos-modding-notes) | High: arbitrary 2000-px PNG per tile (downsampled to 512 in game), custom unit sprites; continuous-basemap slicing works (Kernstown) | Decent generic operational AI; facing-naive | Official Harmony template, mod data bag, editors | **None** |
| **WDS / John Tiller Civil War Battles** | **Native**: facing costs per unit type (johntillersoftware.com/CivilWarBattles/user/paramdata.html) | **Tactical**: 125-yd hexes, ~20-min turns, regiments (…/user/overview.html). Too fine for an 80-day Valley sandbox; single battles only | Low–medium: terrain drawn from fixed per-hex tile bitmap sets in the game's `Map` folder; community "MapMods" swap those sets (forum.wargameds.com viewtopic t=3683; Rolf Hall graphics). **Assessment:** no support for a continuous painted map; full replacement of 2D tiles yes, but still tile-per-terrain. That is why the maps look dated. | Competent tactically, known weak on the offensive (community consensus, UNKNOWN cite) | Closed engine; map and scenario editors ship with the games (assessment); data files editable; no code modding | High: rebuild the map in its editor at 125 yd, re-enter OOB; our art is unusable at its tile scale |
| **Matrix/Slitherine ACW titles** (Strategic Command ACW; Grand Tactician; Ultimate General) | SC: no; GT/UG: real-time, not hex | SC: strategic (whole war); GT/UG: real-time battles | SC: low; GT/UG: closed | Varies | Limited data modding | Very high / mismatch |
| **Unity of Command II engine** | No | Fixed engine-wide map; **no released map editor**, scale cannot change (unityofcommand.net forums t=1824; Steam modding guide 1912050840) | None for new maps | Good | Scenario editor only | Not possible |
| **Battle for Wesnoth** (GPL) | **Native**: `unit.facing`, and "backstab" doubles damage with an enemy behind the target (wiki LuaAPI/types/unit; weapon_specials.cfg) | Engine-agnostic hexes; turns abstract; time-of-day cycle native | Medium: 72-px hex tiles with transition rules and multi-hex overlays (wiki Create_Art, TerrainGraphicsWML). A large painted map is UNKNOWN or awkward. | Fantasy-skirmish AI, not operational (supply, ZoC) | Fully open (WML + Lua, C++ source) | High: reimplement ZoC, supply, reinforcements, operational AI |
| **VASSAL** | Rotatable counters (manual) | Any | High (any image as map) | **None** (no AI; players enforce rules) | Open | Medium for art; no solo play |
| **Freeciv-style hex engines** | No | Strategic/civ | Low–medium | Civ AI | Open | High, wrong genre |
| **Unity from scratch** | Whatever we build | Exact | Unlimited | Must be written: the biggest cost | Total | Very high (months–years) |

## Recommendation
**Stay on Hex of Steel.**
- It is the only candidate that already combines:
  - a working pipeline for beautiful custom maps (Kernstown v0.4.x);
  - custom sprites;
  - an operational AI;
  - any hex scale;
  - an official mod API.
- Facing turns out to be mostly native. The flank and rear rules are a small, precedented Harmony patch.

**Why the others don't fit:**
- WDS has facing but is locked to 125 yd, 20-minute battles with dated tile art.
- Unity of Command can't make new maps.
- Wesnoth has facing but would need the whole operational layer rebuilt.
- VASSAL has no AI.
- Unity from scratch only makes sense if HoS fails the map-size stress test *and* the Harmony time mod is impossible. Neither is shown yet.

**Next steps:**
1. In-game facing tests (§1.5).
2. Write the proof-of-concept facing mod alongside the time-clock mod.
3. Re-evaluate only if the 500/750-yd stress test fails.
