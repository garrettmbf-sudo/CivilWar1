# Facing mod: install

**Status:** compiled and unit-tested on Linux against the reference DLLs in the official Harmony template. **Not yet run inside Hex of Steel.** Use `TESTING.md` to prove it works.

**Requirements:**
- Hex of Steel **8.4.14 or later**. The mod was compiled against `Assembly-CSharp.dll` from `acorsicanfrog/Template-Mod-Harmony`, commit 5fd716b (7 Oct 2026), sha256 `495f9af5a582fee9ead9dda2ae72f1dc0ce814dedcd910b682af7beb04d97c44`, `MultiplayerManager.VERSION = "8.4.14"`.
- The official **HarmonyCore** mod (Steam Workshop id 3574617535), subscribed and **enabled**. It provides `0Harmony.dll` 2.4.1. This mod does not bundle Harmony.
- PC only. Harmony mods don't run on mobile.

## Install
1. Unzip `HexOfSteelFacing-0.1.0.zip`. It contains one folder, `Facing/`.
2. Copy `Facing/` into the game's mods folder (`Application.persistentDataPath/MODS`, read by `ModsManager.CR_LoadContent`):
   - **Windows:** `%USERPROFILE%\AppData\LocalLow\War Frogs Studio\Hex of Steel\MODS\Facing\`
   - **macOS:** `~/Library/Application Support/War Frogs Studio/Hex of Steel/MODS/Facing/` (UNVERIFIED path)
   - **Linux:** `~/.config/unity3d/War Frogs Studio/Hex of Steel/MODS/Facing/`
3. The result should be:
   ```
   MODS/Facing/Manifest.json
   MODS/Facing/FacingConfig.json
   MODS/Facing/Thumbnail.jpg
   MODS/Facing/Libraries/HexOfSteelFacing.dll
   ```
4. Start the game, open **Mods**, enable **HarmonyCore** and **Facing**, and restart if asked.
5. Check `Player.log` (Windows: `%USERPROFILE%\AppData\LocalLow\War Frogs Studio\Hex of Steel\Player.log`). It should contain:
   - `[MOD:Facing] Registering facing mod 0.1.0`
   - `Loaded …FacingConfig.json: front 1 flank 1.25 rear 1.5`
   - `Patched methods: UnitGO.RotateUnit, UnitGO.RotateAttackedUnit, UnitGO.SetUnitRotation, Unit.GetPotentialDamage, TurnManager.NextTurn` (the order may differ).

## Controls
- `.` turns the selected unit clockwise and `,` turns it counter-clockwise. Each turn costs 1 MP (`turnInPlaceMPCost`).
- Turning in place only works on your own turn, and never in real-time multiplayer.
- The chevron on each ground counter points the way the unit faces.

## Config (`FacingConfig.json`, read once at mod start)
| Setting | Default | Meaning |
| --- | --- | --- |
| `frontMultiplier`, `flankMultiplier`, `rearMultiplier` | 1.0 / 1.25 / 1.5 | Damage multipliers. Front = the faced hexside. Flank = the two adjacent hexsides. Rear = the three back hexsides. |
| `applyToSupportiveFire` | true | Also apply to support fire |
| `legacyEastFacing`, `legacyWestFacing` | 1 (NE) / 5 (NW) | Facing for units stored with the vanilla EAST/WEST values. The editor default is WEST, so placed units face NW until they move or turn. |
| `showChevron`, `chevronDistance`, `chevronScale`, `chevronColorHex` | | Chevron drawing (world units) |
| `turnInPlaceEnabled`, `turnInPlaceMPCost`, `rotateClockwiseKey`, `rotateCounterClockwiseKey` | | Turn in place. Keys are Unity `KeyCode` names. |
| `aiRefaceEnabled`, `aiRefaceRadius` | true / 6 | At the end of an AI player's turn, its units turn toward the nearest enemy within 6 hexes |

## Multiplayer
- Every player must run the same mod and config.
- The game lists gameplay mods in the host request (`ServerGameService`), and an active assembly mod disables Ironman (`Mod.HasGameplayImpact`).
- **PBEM and hotseat:** facing travels inside the save (`Unit.FacingRotation` is serialised).
- **Real-time:** movement and attack rotations replay through the game's own RPC calls (`MultiplayerManager` calls `RotateUnit`/`RotateAttackedUnit`), so they stay in sync. Turn in place is disabled there because it has no RPC.

## Uninstall
Disable or delete `MODS/Facing`. Saves stay loadable: facing is stored in a vanilla field, and vanilla turns it back into a sprite rotation.

## Build from source (Linux, macOS or Windows, .NET 8 SDK)
```
cd mods/facing
./tools/fetch_libs.sh        # copies the template's reference DLLs into .hos-libs/ (gitignored, never commit)
./tools/build_release.sh     # build + 39 tests + zip to /workspace/dist (override with DIST=...)
```
