# Contributor and AI-agent instructions — CivilWar1

## Mission and scope
Deliver **one playable Stonewall Jackson Shenandoah Valley Campaign, March–June 1862, inside Hex of Steel**. Use direct manual counter movement. One-mile-per-hex is the starting design target; establish actual engine and performance limits before promising a final scale.

## Non-negotiable preservation rules
1. All existing officer portrait **identities and filenames have been audited by the user**. Treat them as approved. Do not relabel, rename, overwrite, auto-crop, or relocate the original `mdl_*.png` portraits, including spellings such as `mdl_USA_RSchenk.png`. New images must receive unique filenames. Do not invent a second "corrected" face for a name.
2. Preserve `maps/*.sav` reference samples, `reference/` image sources, and the source mod. A possible game consumer may use the current root asset filenames.
3. Do not claim .sav interoperability based on the `HSAV` placeholder. Only a test performed in Hex of Steel confirms playability. Never overwrite a real map with a placeholder export.
4. Do not add or redistribute proprietary Hex of Steel binaries, third-party mods, or published board-game artwork without permissions. Harmony binaries are not kept in the repo. Players and developers get them from the official **HarmonyCore** mod, Steam Workshop id **3574617535** (https://steamcommunity.com/sharedfiles/filedetails/?id=3574617535), which ships `0Harmony.dll`/`HarmonyCore.dll`.
5. Changes to the original portraits or bulk asset moves require explicit user authorization and a verified migration of every consumer path.

## Current project boundaries
- **In:** full 1862 Valley campaign, Valley Pike, main Valley / Luray Valley, Massanutten, Shenandoah rivers, McDowell/Franklin western approaches; researched Union and Confederate brigade OOBs; commander relationships; map production and test tools.
- **Out:** 1864 Valley campaign, national eastern-US map, Petersburg, Gettysburg, new orders engine.
- Historical rank and command must follow **dated** assignments. Jackson's 1862 organization was not the later numbered-corps structure.

## Workflow
1. Inspect `README.md`, `docs/roadmap.md`, `docs/repository-layout.md`, and `historical_data/portrait_manifest.csv`.
2. Favor small patches and tests. Before editing a binary format, record actual samples and observed evidence in `docs/sav-format.md`.
3. Keep experimental map-generation code distinct from verified, game-ready mod content.
4. Put sourced historical rosters in `historical_data/` with source citations and dates. Never present invented strengths or command assignments as fact.
5. Use descriptive snake_case for **new tooling files**; retain existing portrait, texture, game file names **exactly as supplied**.
6. Run `python -m pytest -q` after Python changes; note when tests cannot be run or a game-based validation is missing.
7. Before a bulk move, inspect any references to the path in scenarios/mod metadata; prepare a migration plus rollback. Prefer an asset index to moving files prematurely.
8. Summarize actual modifications, files, test results, blockers, and next step. No unsupported "fully operational" claims.

## Current near-term deliverable
A verified Hex of Steel map round-trip and a small Shenandoah maneuver experiment with distinct brigades and headquarters. For external artwork, record origin, license, and permitted uses in `reference/source_register.csv`.