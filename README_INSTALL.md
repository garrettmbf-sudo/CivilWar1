# First Kernstown 1862 — install guide (Windows)

You need: Hex of Steel (Steam, version 8 or newer) and Windows PowerShell (already on every Windows 10/11 PC).

## 0. Get the map tiles (GitHub Release)
The 3410 tile images (~5.5 GB) are not in git. Download them from the release
https://github.com/garrettmbf-sudo/CivilWar1/releases/tag/kernstown-v0.3.1 :
- `Kernstown_tiles_part1of4_cols00-15.zip` … `Kernstown_tiles_part4of4_cols47-61.zip` (all four are required)
- `Kernstown_mod_base.zip` (Manifest.json and empty mod folders)

Extract every zip into the **same** folder (your `Kernstown1862_mod` folder from step 1; merge/overwrite folders when asked).
Each zip contains `mod\Graphics\Tiles\Summer\`, so together they fill `mod\Graphics\Tiles\Summer\` with all 3410 `SV_K_<col>_<row>.png` files.

## 1. Unzip
1. Right-click `Kernstown1862_mod.zip` → **Extract All…** → pick e.g. `C:\Kernstown1862`.
2. You now have `C:\Kernstown1862\Kernstown1862_mod\` containing `mod`, `tools`, `data`, `templates` and this file.

## 2. Build the scenario file (one command)
1. Close Hex of Steel.
2. Press **Start**, type `powershell`, open **Windows PowerShell**.
3. Paste these two lines and press Enter after each (change the path if you extracted elsewhere):
   ```
   cd "C:\Kernstown1862\Kernstown1862_mod"
   powershell -ExecutionPolicy Bypass -File .\tools\build_kernstown_map.ps1
   ```
   - If Hex of Steel is not in the default Steam folder, add `-GameDir "D:\SteamLibrary\steamapps\common\Hex of Steel"` (your folder) to the end of the second line.
   - The script uses `templates\ACW_sample_102x60.sav` (your American Civil War sample) as the template and as the source of the unit types (Infantry, Light Cavalry, Napoleon 12pdr, Union/Confederacy). To use another trusted .sav add `-TemplateMap "C:\path\file.sav"`.
4. It should end with `Placed 18 units` and `Wrote ...\mod\Maps\First Kernstown 1862.sav`.
   Only run this script on .sav files you trust (it uses the game's own save loader).

## 3. Copy the mod into the game
1. Press **Win+R**, paste `%USERPROFILE%\AppData\LocalLow` and press Enter.
2. Open `Valentin's studios\Hex of Steel\MODS` (on some versions the studio folder is named `War Frogs Studio`).
3. Copy the whole `mod` folder there and rename it to `First Kernstown 1862`.
   You should end up with `...\MODS\First Kernstown 1862\Manifest.json` and `...\Graphics\Tiles\Summer\SV_K_0_0.png` (3410 tiles).

## 4. Play
1. Start Hex of Steel → **MODS** → tick **Shenandoah Valley 1862 — First Kernstown** → **Apply changes** (the game may restart).
2. **Play → Custom scenario** (or open it in the **Map editor**) → choose **First Kernstown 1862**.
3. Victory points: Winchester Courthouse (primary), Kernstown and Opequon Church (secondary). The stone wall hexes on Sandy Ridge give +35 defence; the Confederate brigades there start entrenched (level 2). CSA has 10 units (~3,800 men), USA has 8 units (~8,500 men).

## If something goes wrong
- Black hexes: the mod is not active, or the folder was not copied with its `Graphics\Tiles\Summer` folder.
- "Hex of Steel not found": add the `-GameDir` option described above.
- "No template unit": the template .sav lacks that unit type; the unit is skipped and the rest still builds.
