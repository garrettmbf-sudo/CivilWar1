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
| **Smaller tiles (1024/512)** | **Corrected by the assembly (see §A3):** the loader downsamples every modded tile to **512 px wide** and DXT-compresses it. The tile's on-map size is `source width / 330` world units. | 512-px source files would render ~4× too small natively. A Harmony patch could fix this. In-game test needed. |
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
| **Units leaving the map** | No exit mechanic. Event checks have no "unit on tile" condition (§A2). | Native approximation: a VP on the exit hex, triggered when it is lost (`VP_LOSS`). Real exits need Harmony. |
| **Linked scenarios** | Custom campaigns carry **core units** between scenarios with their stats and history. Base campaigns allow 5 core units plus 2 per commander rank, editable in modded campaigns. | VERIFIED [M] |
| **Trains** | Units embark on an urban tile next to rail and get greatly extended MP. | VERIFIED [M] |
| **Harmony** | Official example: GameModification lifecycle, patches on `TurnManager.NextTurn`, `AI.GatherEnemyVictoryPoints`, `AI.CheckWinningWar`, `Player.GetManpowerGrowth`. Targets .NET Framework 4.8. `mxovd/hos_mod_setup` decompiles the user's own `Assembly-CSharp.dll` for reference. | VERIFIED [EX; github.com/mxovd/hos_mod_setup] |
| **Repo samples** | `docs/3574617535/` holds `0Harmony.dll`, `HarmonyCore.dll`, `Manifest.json` and empty BinaryFormatter lists. There is no game logic to inspect in the repo. | VERIFIED (inspected) |

**Discarded source:** the Steam "Scenario Editor Guide" (filedetails 2912414954), which says "days per turn 1–4", is about **Unity of Command 2**, not Hex of Steel. Its settings are not used here.


## Addendum (17 Oct, second pass): assembly and save-file evidence

### Sources for this pass
- **[DLL]** `Assembly-CSharp.dll`, as shipped by the developer in the official example mod `acorsicanfrog/Example-Mod-Harmony` (`Libraries/`, repo commit dated 2026-10-07). Decompiled with ILSpy 8.2 on the box for reading only; nothing decompiled is committed. Version caveat: this is the reference DLL in the example repo, which may lag the live Steam build.
- **[SAV]** `templates/ACW_sample_102x60.sav` on `kernstown-map`, read with `git show` (read-only). It is a raw-deflate .NET BinaryFormatter stream (`GameData` → `Map`).
- **[DEV-U]** Developer post, Unity forum, 7 Sep 2022: https://discussions.unity.com/t/hex-of-steel-wwii-turn-by-turn-wargame/893576
- **[DEV-S]** Developer replies on events, Steam, Jan 2026: https://steamcommunity.com/app/1240630/discussions/0/689745580010986380/
- **[CL]** Changelog notes via app-store and iPa4Fun version histories.
- **[SoS]** Squad of Steel, a community Harmony mod: https://github.com/murdockpeter/squadofsteel

### A1. Campaign branching: VERIFIED limited [DLL][SAV]
- Each scenario `Map` stores 4 strings: `NextMap`, `NextMap2`, `NextMapDefeat` and `NextMap2Defeat`. The editor has 4 matching input fields (`MapEditorGO.SetNextMap1/2`, `SetNextMap1Defeat/2Defeat`).
- `UIManager.ManageNextScenarioButtons(GameOutcomes)`:
  - on **VICTORY**, shows up to 2 buttons (NextMap, NextMap2);
  - on **DEFEAT**, shows up to 2 buttons (NextMapDefeat, NextMap2Defeat).
  - The player clicks one; the end text adds "txt-choice campaign" when NextMap2 is set.
  - Campaign transitions are disabled in PBEM and real-time multiplayer.
- `enum GameOutcomes { NONE, VICTORY, DEFEAT }`: **there is no draw or minor/major victory tier**. Turn limit, held-VP and damage conditions resolve into one of the two outcomes.
- **So branching is:** outcome (win/loss) × player choice (≤2) → next `.sav`. There is no branching on events, VPs held, flags or random rolls. Core units and commander XP/rank carry over (`MainMenu.listOfPlayersToBeSavedBetweenCampaign`).
- **Examples:**
  - Official Soviet campaign tree: a Steam thread reports a wrong path ("Wrong path in the campaign tree (soviet)", steamcommunity.com/app/1240630/discussions/0/644694245644449030/).
  - Changelog: "Custom campaign scenario choice had the '.sav' extension shown on the UI", and "Choices UI elements for next scenario(s) in campaigns were not translated" [CL].
  - The "major victory → path A, minor → path B" branching seen on Slitherine forums is **Panzer Corps**, not HoS. Don't cite it.
- **File structure:** no separate campaign file. A campaign is a chain of scenario `.sav` files linked by those 4 fields, plus `IsCampaign`, `IsLastScenario`, `OriginalCampaignCountry`, `XPPerScenario`, `XPperMajorVP/SecondaryVP/NormalVP`, `BaseCoreUnitValue` and `NumberOfNewCoreUnitPerRank` [SAV field list].

### A2. Time model: day-granular only, natively [DLL][SAV]
- **Turn length:** `Map.NumberOfDaysThatGoesByPerTurn` is an **Int32** [SAV type table; DLL `Map.cs`]. The editor parses it with `int.Parse` and coerces blank or negative to 0. There is no fractional value and **no hour, minute or time-of-day field** anywhere in `Map`, `GameSettings` or `TurnManager`.
- **Turn advance:** in `TurnManager`, if days > 0 then `Date = Date.AddDays(days)`; at 0 the date never moves.
- **Day-scaled systems:** weather forecast accuracy, research rate (`/7`, with 0.1 at 0 days), manpower and income timers (`/30`, `182/days`), and the AI manpower heuristic all read days per turn. At 0 days some of these freeze or use fallbacks; turn this off for ACW anyway.
- **Event conditions:** `enum CheckTypes { NONE, TURN_COUNT, DATE, VP_LOSS, VPS_LOSSES, VPS_LOSSES_ONE_OF, WAR_DECLARATION, ALLIANCE_MADE, UNIT_DESTROYED }`.
  - Modifiers: `Chance` (d100 rolled **once, at trigger**, per [DEV-S]), `MaxExecutions`, `DontCheckBeforeTurnCount`/`Date`, `AIonly`/`HumansOnly` and a check tile.
  - **Not available:** unit-enters-tile, unit-count, or a random-each-turn condition. The d100 is rolled only when the condition fires.
- **Event actions:** `SHOW_MESSAGE, ADD_MONEY, ADD_HQ_POINTS, MAKE_PEACE(_FACTION), MAKE_ALLIANCE, DECLARE_WAR, SPAWN_UNIT, FACTION_CHANGE, COUNTRY_CHANGE, ADD_UNIT_RESERVE, CHANGE_VP_OWNERSHIP, CAPITULATION, DESTROY_TILE, RESET_INCOME, …FIXED_INCOME…, SET_TILE, ADD_VP, REMOVE_VP, SET_TILE_NAME, ADD_PLAYER, REMOVE_PLAYER`.
- **Correction to my earlier note:** a "chance per turn" random deadline does **not** work natively, because the roll happens once per trigger. A native randomised date needs several `TURN_COUNT` events with chances that chain via VP/tile changes. That is fragile. Use Harmony.

### A3. Tiles, map size, performance [DLL][DEV-U][CL]
- **Tile loader** (`ModsManager`, folder `Tiles`, accepts .png/.jpg/.jpeg):
  - `LoadImage` → blit to **512 × (512·h/w)** → `Texture2D.Compress` (DXT) → sprite with pixels-per-unit `330·512/w`.
  - On-map size is therefore set by the *source* width (w/330 units). That is why 2000-px sources are required to match stock tiles. In-game detail is capped at 512 px per tile.
  - Memory: about **0.25 MB per unique tile** (DXT5, 512²), all loaded at mod start.
- **Consequences:**
  - (a) Painting detail above 512 px per hex is invisible in game.
  - (b) Unique slices for every hex are impossible on memory grounds, not just disk: 122,709 × 0.25 MB ≈ 31 GB at 500 yd.
  - (c) A one-method Harmony patch could load 512-px files at the right scale, cutting disk use ~15×. This is UNTESTED.
- **Map size:**
  - `MapEditorMenu.NewMap` does `int.Parse` on X/Y with **no clamp**. The map is a rectangular `Tile[,]` and **every cell becomes a GameObject** with a sprite renderer and collider (`MapGO`; [DEV-U]). Hexes outside our polygon still cost.
  - The developer reports ">60k hexagons… still runs at 120 FPS" with 5–10 s loading [DEV-U].
  - Changelog: "Improved scenes unloading… from 13 minutes to 30 seconds on a **900x700 map**" (630k cells) [CL, app-store history]. So very large maps load, but slowly.
  - Community "World Map WWII" mod: saves start at ~22 MB and break online multiplayer; offline works (steamcommunity.com/app/1240630/discussions/0/594011910715766664/).
  - Stock tile textures are 1024² on PC and 256² on mobile (developer reply, App Store listing).
- **Our sizes** (bounding rectangle, i.e. what the game instantiates):

| Scale | Rectangle | Cells |
| --- | --- | --- |
| 500 yd | 468×478 | ~224k |
| 750 yd | ~313×319 | ~100k |
| 1 mile | ~133×136 | ~18k |

  Above about 100k is beyond any reported smooth play; 500 yd is 3.7× the developer's 60k claim. Needs a blank-map stress test.

### A4. Harmony feasibility (official hook points) [DLL][SoS]
- **Turn clock** (easy-moderate):
  - postfix `TurnManager.NextTurn` (shown in the official example's `TurnManagerPatch.cs`);
  - keep our own hour counter in the mod data bag (`GameData._modDataBag`, saved with the game);
  - replace `ShowTurnNumberAndDate` text.
- **Variable turn length** (moderate-hard): scale each unit's movement points per turn ("operational" vs "contact" turns); the AI's pathing must still behave. SoS already ships per-scenario "scale profiles" with `turnMinutes` (Operational 5 km/360 min, Company 1 km/60 min), but uses them for labels and combat falloff, not movement.
- **Map exits** (moderate): on an end-of-move hook, detect a Confederate unit on an exit hex, remove it, and record it in the mod data. Victory then reads that record.
- **Hidden Richmond deadline** (easy): roll on scenario start, store it in the mod data bag, send messages via the existing `SHOW_MESSAGE` UI or a popup (the example mod has popup code), and adjust from state each turn.
- **Night** (moderate): a flagged turn that sets visibility to 0, applies a combat penalty, and allows only march/rest.
- **Cost of any of these:** Harmony mods run on PC only and break when the game updates. Multiplayer needs every player to have the mod.
