# Hex of Steel mod packaging — verification status

**Not yet verified:** a complete native package layout, loader behavior, or a ready-to-install release.

The proposed `mod/` folder remains reserved for **tested game-ready assets**, not reference images or arbitrary zip contents. `docs/3574617535/` keeps only the HarmonyCore manifest and folder notes as **research examples**. Its DLLs were removed on 2026-10-17, so get them from the official **HarmonyCore** mod, Steam Workshop id **3574617535** (https://steamcommunity.com/sharedfiles/filedetails/?id=3574617535), which ships `0Harmony.dll`/`HarmonyCore.dll`.

Validation required before releasing:
1. Inspect the installed game's actual mod folder structure and compatible Workshop mods.
2. Record exact data/config names, dependency locations and game version.
3. Verify packaging by loading the mod in-game.
4. Exclude proprietary binaries and images whose redistribution permission is unverified.

Legacy path `docs/mod_structure.md` remains for compatibility but points here.