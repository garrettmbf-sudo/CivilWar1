# Original ValleyCampaign PowerShell map tools

These are **unaltered source copies** of the user's locally developed map scripts, imported October 15, 2026. Their original filenames and comments are preserved. They are development tools, **not yet verified release assets**.

| File | Purpose |
| --- | --- |
| `map_reader.ps1` | Load/read and reserialize trusted Hex of Steel `.sav` files via local game assemblies. |
| `build_valley_map.ps1` | Experimental Shenandoah geographic terrain/scenario builder using a game-save template. |
| `valley_map_data.ps1` | Separate geographic feature/coordinate definitions, currently not authoritative for the builder. |
| `beautify_map.ps1` | Experimental post-processing for roads, rivers, edges and terrain transitions. |

## Before running
- Scripts contain **absolute Windows paths** for the original user's machine; adapt paths for your installation and working directory.
- `beautify_map.ps1` currently overwrites its input by default and copies its output **directly into a Steam Workshop mod directory**. Do **not** run it against subscribed Workshop originals. Use copies in an isolated local development mod and establish backups.
- Existing scripts use unvalidated hex-grid route tracing; roads and rivers may be disconnected. They may also overwrite tile mechanics while adjusting artwork.
- Scripts deserialize .NET BinaryFormatter payloads. Use **trusted local .sav files only**; BinaryFormatter is unsafe for untrusted serialized input.
- `build_valley_map.ps1` and `valley_map_data.ps1` currently hold partly duplicated coordinate information. Do not treat either output as validated historical geography.
- These files are archived source evidence, not proof that a rendered or serialized map loads correctly in-game.

## Planned next steps
1. Consolidate geographic features in one canonical projected-coordinate dataset.
2. Replace square-grid interpolation with validated hex-grid road/river routing.
3. Keep map rendering/visuals separate from terrain and combat rules.
4. Remove destructive defaults and hardcoded Steam Workshop deployment.
5. Validate genuine .sav round trips against the installed Hex of Steel build.

Related: [map-format verification](../../docs/sav-format.md), [map data area](../../maps/README.md).
