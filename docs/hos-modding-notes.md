# Hex of Steel modding notes (research log, 17 Oct 2026)

Each claim has a source and a confidence level: **VERIFIED** = official manual or developer statement; **REPORTED** = community post or store text; **UNKNOWN** = not found, so test or inspect it. Nothing here has been tested in our own game build yet.

Main sources:
- [M] Official manual, updated 25 Oct 2025 (Steam CDN PDF).
- [DEV-VID] Official "How to Mod" tutorial, https://youtu.be/sGADvjll8pU.
- [S-*] Steam threads, linked inline.
- [RN] Release notes.
- [EX] Official Harmony example, https://github.com/acorsicanfrog/Example-Mod-Harmony.

| Topic | Finding | Status / source |
| --- | --- | --- |
| **Tile format** | Custom tiles must be **2000×2000 PNG**. The filename equals the tile Name, in the mod's `Graphics/Tiles/<Season>/` folder. The hex shape comes from the stock Plain alpha. | VERIFIED [DEV-VID] |
| **Smaller tiles (1024/512)** | No source found. The earlier "512" idea came from other games' modding, not HoS. | UNKNOWN. Needs an in-game test: one 1024² and one 512² tile next to stock tiles. |
| **Tile reuse across hexes** | A tile is a *type* placed on any number of hexes. Stock maps reuse Plain, Forest and so on everywhere. Stock maps also pick randomly among variants (e.g. Bocage 1/2/3), but the developer said custom tiles cannot join that random pool "at this time" (May 2024). | VERIFIED [M; reddit r/hexofsteel 1ct0qk0, dev reply]. So we place our variants deterministically. |
| **Map size** | Store text: "HUGE maps (up to 72.000 tiles)" (older wording). v8.1.6 notes: scene unloading "from 13 minutes to 30 seconds on a 900x700 map". | REPORTED [RAWG store copy] / VERIFIED [RN 8.1.6]. The actual cap is UNKNOWN. A blank 468×478 test is needed. |
| **Large-map mods** | *A World Map WWII*: 62.5 MB Workshop download, about 22 MB save files, and multiplayer uploads fail at that size. *Jun1941*: Eastern Front at 10 km per hex. They stay small by reusing stock tile types, not unique art. | REPORTED [Workshop 3258781793; S-594011910715766664; SteamDB patch 14728552] |
| **Visibility / spotting** | Base 1 hex, recon 2. The user confirms visibility can be set per unit in the unit editor (e.g. cavalry 3–4). | VERIFIED [M] + user |
| **Recon units** | Move twice, are exempt from ZoC, and give +15% damage to friendlies attacking an adjacent enemy. | VERIFIED [M] |
| **Attack range** | Whole hexes, no line-of-sight or terrain blocking. Stock artillery uses 1–4; values above 4 are UNKNOWN. | VERIFIED [M] |
| **Action points / movement** | 2 actions per turn (one move plus one attack). Road costs 1 MP per hex, plain 2, forest 3. Horse-drawn sets max MP 3. | VERIFIED [M] |
| **Zone of control** | Optional (v7.0.0+), applies to adjacent hexes. Not applied by recon, commanders, militia, units out of ammo, or units under 30% HP. | VERIFIED [M] |
| **Turn length** | Scenario setting **days per turn**. 0 freezes time, which stops manpower growth and other time effects. Examples in sources: 1 day and 7 days per turn. Research speed scales with it. **No sub-day (hour) setting found.** | VERIFIED [S-603040419439446713 dev; RN 6.6.0 on SteamDB 9577545; App Store notes]. Hours per turn: UNKNOWN, likely unsupported natively. |
| **Day/night** | No day/night mechanic documented. | UNKNOWN, probably absent |
| **Events / messages** | Triggers include date reached and turn ("not before X turns"). Each has a chance % rolled every time it triggers. Messages go to a target country, or to everyone if none is set. Event actions include spawning units. Units spawned by events had 0 manpower/morale until a fix. | VERIFIED [S-689745580010986380 dev; S-806848929007296225 dev; App Store notes] |
| **Reinforcements** | Event spawns (by date/turn), reinforcement tiles (cannot be captured; blocked if every neighbouring hex is occupied), and deployment around owned VPs after a wait. | VERIFIED [M] |
| **Victory** | Regular, secondary and major VPs. You usually win by holding all major VPs. Turn limit is set in the editor. With no turn limit, the scenario runs until all major VPs are taken. | VERIFIED [M; S-3825284962823928066 dev] |
| **Units leaving the map** | No exit or "move off-map" mechanic documented. | UNKNOWN. Needs Harmony, or an approximation such as exit VPs or event-removal. |
| **Linked scenarios** | Custom campaigns carry **core units** between scenarios with their stats and history. Base campaigns allow 5 core units plus 2 per commander rank, editable in modded campaigns. | VERIFIED [M] |
| **Trains** | Units embark on an urban tile next to rail and get greatly extended MP. | VERIFIED [M] |
| **Harmony** | Official example: GameModification lifecycle, patches on `TurnManager.NextTurn`, `AI.GatherEnemyVictoryPoints`, `AI.CheckWinningWar`, `Player.GetManpowerGrowth`. Targets .NET Framework 4.8. `mxovd/hos_mod_setup` decompiles the user's own `Assembly-CSharp.dll` for reference. | VERIFIED [EX; github.com/mxovd/hos_mod_setup] |
| **Repo samples** | `docs/3574617535/` holds `0Harmony.dll`, `HarmonyCore.dll`, `Manifest.json` and empty BinaryFormatter lists. There is no game logic to inspect in the repo. | VERIFIED (inspected) |

**Discarded source:** the Steam "Scenario Editor Guide" (filedetails 2912414954), which says "days per turn 1–4", is about **Unity of Command 2**, not Hex of Steel. Its settings are not used here.
