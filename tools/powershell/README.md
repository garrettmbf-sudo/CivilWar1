# Original ValleyCampaign PowerShell map tools

These are source copies of the user's locally developed map scripts, imported October 15, 2026. On 2026-10-17 their hex math was converted to the game's native even-q layout: all three map scripts dot-source `HexEvenQ.ps1`, a port of `src/hex_utils.py` (see `docs/hex-convention.md`). Otherwise their original filenames and comments are preserved. They are development tools, **not yet verified release assets**.

| File | Purpose |
| --- | --- |
| `map_reader.ps1` | Load/read and reserialize trusted Hex of Steel `.sav` files via local game assemblies. |
| `build_valley_map.ps1` | Experimental Shenandoah geographic terrain/scenario builder using a game-save template. |
| `valley_map_data.ps1` | Geographic feature/coordinate definitions; since 2026-10-17 the builder takes all its geography from here. |
| `beautify_map.ps1` | Experimental post-processing for roads, rivers, edges and terrain transitions. |
| `HexEvenQ.ps1` | Shared native even-q hex math (port of `src/hex_utils.py`; tested by `tests/test_powershell_even_q.py`). |
| `ValleyFrame.ps1` | Shared 1-mile frame, grid size (122 × 140) and lat/lon → hex rule for `valley_map_data.ps1` and `build_valley_map.ps1`. |

## Before running
- Scripts contain **absolute Windows paths** for the original user's machine; adapt paths for your installation and working directory.
- `beautify_map.ps1` currently overwrites its input by default and copies its output **directly into a Steam Workshop mod directory**. Do **not** run it against subscribed Workshop originals. Use copies in an isolated local development mod and establish backups.
- Road and river tracing now walks game-adjacent hexes (`Get-HexLine`), but the source waypoints are still unvalidated. They may also overwrite tile mechanics while adjusting artwork.
- Scripts deserialize .NET BinaryFormatter payloads. Use **trusted local .sav files only**; BinaryFormatter is unsafe for untrusted serialized input.
- `build_valley_map.ps1` reads its geography from `valley_map_data.ps1` (one copy). The ridge and river waypoints are still only partly verified; see the comments in the data script.
- These files are archived source evidence, not proof that a rendered or serialized map loads correctly in-game.

## Planned next steps
1. Consolidate geographic features in one canonical projected-coordinate dataset.
2. ~~Replace square-grid interpolation with hex-grid road/river routing~~ (done 2026-10-17, native even-q). Waypoints still need validation.
3. Keep map rendering/visuals separate from terrain and combat rules.
4. Remove destructive defaults and hardcoded Steam Workshop deployment.
5. Validate genuine .sav round trips against the installed Hex of Steel build.

Related: [map-format verification](../../docs/sav-format.md), [map data area](../../maps/README.md).
