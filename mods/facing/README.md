# Facing mod for Hex of Steel (CivilWar1)

The mod adds 6-way facing to ground units:
- units keep their facing when attacked;
- flank and rear attacks deal more damage (front ×1.0, flank ×1.25, rear ×1.5, set in `FacingConfig.json`);
- a chevron on each counter shows the facing;
- `.` and `,` turn the selected unit in place for MP;
- AI units turn toward the nearest enemy at the end of their turn.

See `INSTALL.md` and `TESTING.md`.

## Ground truth
Every patched or touched member was checked against the decompiled `Assembly-CSharp.dll` that the developer ships in the official templates:
- **Assembly:** `acorsicanfrog/Template-Mod-Harmony` commit 5fd716b, 2026-10-07; the same file is in `Example-Mod-Harmony`. sha256 `495f9af5a582fee9ead9dda2ae72f1dc0ce814dedcd910b682af7beb04d97c44`. `MultiplayerManager.VERSION = "8.4.14"`.
- **Decompiler:** ILSpy 8.2. The decompiled source stays on the build box and is not committed.
- **Harmony:** `0Harmony.dll` 2.4.1.0, the template's copy. At runtime it is provided by the official HarmonyCore mod.
- `tests/FacingMath.Tests/GameSignatureTests.cs` re-checks every signature below against the DLL on each build.

| Patch | Target (exact signature) | Evidence |
| --- | --- | --- |
| Prefix, replaces vanilla for managed units | `UnitGO.RotateUnit(TileGO p_departureTileGO, TileGO p_arrivalTileGO)` → void | `UnitGO.cs:4141`. Called per path step at `:1664`, MP replay at `MultiplayerManager.cs:1793`. Vanilla sets 6 directions only for `AllowedRotations.ALL` and E/W for `LEFT_RIGHT`. |
| Prefix: only the active side may turn | `UnitGO.RotateAttackedUnit(UnitGO p_unitGOtoRotate, UnitGO p_refUnitGO)` → void | `UnitGO.cs:4001`. Callers `:2586` (attacker), `:3459` (support), `:3666` (Retaliate turns the defender), `:5814`, `MultiplayerManager.cs:1128` |
| Prefix: E/W flip only, plus chevron | `UnitGO.SetUnitRotation()` → void | `UnitGO.cs:6954`. Vanilla Z-rotates `unitSprite` for ALL units and coerces LEFT_RIGHT units to WEST. |
| Postfix: arc multiplier on `__result` **and** `Unit.FinalDamage` | `Unit.GetPotentialDamage(UnitGO p_targetUnitGO, bool p_isRetaliation, bool p_isSupportiveFire)` → int | `Unit.cs:1517`. The preview (`UnitGO.cs:4964-4992`) and real hits (`AttackUnit :2631` → `Attack :3219 CurrHP -= unit.FinalDamage`) read `FinalDamage`; `AI.CheckForAttack` ranks targets by the return value. Squad of Steel patches the same method. |
| Prefix: AI re-face | `TurnManager.NextTurn(bool p_sendRPC)` → void | `TurnManager.cs:262`. `currPlayer` is still the player ending the turn. |
| MonoBehaviour: turn in place | reads `UnityEngine.Input.GetKeyDown` by reflection (Squad of Steel's method); writes `Unit.CurrMP` (byte) and `Unit.FacingRotation` | `Unit.cs:232`, `:274` |

## Grid geometry
The project uses the game's native layout: flat-top **even-q**, with rows increasing north and no conversion layer (decided 2026-10-17, `docs/decisions.md`). `MapGO` places tiles at `x = col × 4.42`, `y = row × 5.1`, plus **2.55 for EVEN columns**:
- world +y is north;
- **even columns sit half a row north**.

The mod does **not** call the game's neighbour list (`Utils.GetAllTilesNeighbours`). It takes the vector between the two tiles' centres, computed from `Tile.PosX/PosY` with the game's own `MapGO` formula (`FacingMath.GameCenter`), and snaps it to the nearest of the six 60° sectors (`FacingMath.DirectionOf`). On that geometry, each of the game's six neighbours lands in its named sector: N, NE, SE, S, SW, NW for both even and odd columns (`GameGeometryNeighbours` tests).

The fixture `tests/fixtures/hex_utils_neighbors.json` (288 cases) is regenerated from the even-q `src/hex_utils.py` (PR #9), which uses the same formula. The tests check `GameCenter` against `hex_utils.game_position`, and check that every `hex_utils` port is the direction `DirectionOf` returns.

## Facing storage
- The mod reuses the vanilla serialised field `Unit.FacingRotation` (enum `FacingRotations : byte`). N, NE, SE, S, SW and NW map to facings 0–5.
- The vanilla values EAST and WEST (left/right-only units; WEST = 0 is the default) are read through `legacyEastFacing`/`legacyWestFacing`.
- No new save data is needed.

## Redistribution
The game and Unity DLLs are compile-time references only. They are fetched from the official template into `.hos-libs/` (gitignored) and are **not** in the repo or the zip. The zip ships only `HexOfSteelFacing.dll`, the manifest, the config, a thumbnail and the docs.
