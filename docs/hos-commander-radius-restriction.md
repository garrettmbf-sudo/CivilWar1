# Can a Hex of Steel commander's radius be restricted to specific units?

Short answer: **not with data alone. A code mod could probably do it, and the developer supports that route.**
Nothing here was decompiled or patched by us, and no game code is included in this repo.

## 1. Stock engine (data / editors only): no
- The manual describes a commander buffing **all friendlies** within its Range radius. Bonuses don't stack and the highest one wins (official manual p.47: https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1240630/manuals/1e929c3c9d09670cb450bdf6272b9522dfb4bc5b/Manual.pdf).
- The Unit Editor, scenario editor and mod folders expose no "commander → subordinate units" field. Mod folders hold `Manifest.json`, `Custom units`, `Custom countries`, `Custom heroes`, `Custom tiles`, `Graphics`, `Maps`, `Sounds` and `Libraries` (official tutorial https://www.youtube.com/watch?v=sGADvjll8pU, plus the HarmonyCore layout in `docs/3574617535/`).
- Loadout/unit-modification rules are hard-coded (developer, https://steamcommunity.com/app/1240630/discussions/0/603026374004886409/).

## 2. Code mods (Unity/Mono + Harmony): feasible, officially supported
- Update 8.0.0 (Sept 2025) built HarmonyLib into the game "to allow full code injection" (patch news https://store.steampowered.com/news/app/1240630/view/535487694763984666 , summarized at https://www.reddit.com/r/computerwargames/comments/1nqs2h5/).
- The developer (A Corsican Frog) publishes an **official template mod**, https://github.com/acorsicanfrog/Template-Mod-Harmony, and the HarmonyCore Workshop library, https://steamcommunity.com/sharedfiles/filedetails/?id=3574617535 (already mirrored in `docs/3574617535/`). He tells modders to build against `Assembly-CSharp.dll` and to inspect it with ILSpy (https://steamcommunity.com/app/1240630/discussions/0/767436134178378567/).
- Code mods are C# `net48` DLLs placed in the mod's `Libraries/` folder. That means Unity on the Mono runtime with a moddable `Assembly-CSharp`. **BepInEx is not needed**: the game's own mod loader loads Harmony mods. A community scaffolder exists: https://github.com/mxovd/hos_mod_setup.
- Public mod code references a `Unit` class with `IsCommander`, `OwnerPlayer` and `Type`/`FilterType` (developer thread https://steamcommunity.com/app/1240630/discussions/2/840627496100669606/). So a Harmony **postfix/prefix on the commander-bonus calculation** could check that the buffed unit belongs to the commander's formation, keyed by a unit-name prefix or a custom-unit naming convention. **UNVERIFIED:** we don't know the exact method that computes commander bonuses. Finding it means opening `Assembly-CSharp.dll` locally in ILSpy, which the developer endorses, as part of a separate, deliberate step.
- Costs and risks:
  - Every player needs the mod; the developer says any non-graphical mod is required on all clients, including in multiplayer and PBEM.
  - Patches break when the game updates, because the developer reworks functions often.
  - Mobile users can only sideload.

## 3. Legal / EULA
- The developer explicitly invites code modding through Harmony and ILSpy inspection, which is strong evidence that local inspection for modding is sanctioned.
- I did not find a game-specific EULA. The Steam Subscriber Agreement (https://store.steampowered.com/subscriber_agreement/) governs, and generally forbids redistributing game content.
- **Do not commit or redistribute `Assembly-CSharp.dll`, decompiled sources, or game assets.** Distribute only our own compiled patch DLL and data.
- Note that the existing `docs/3574617535/Libraries/*.dll` (Harmony binaries, MIT-licensed third-party code) are flagged in `docs/mod-format.md` as research copies, not for redistribution.
- Workshop items accepted for sale are under Valve's terms. Keep the mod free unless that's reviewed.

## 4. In-engine workarounds (no code)
1. **Placement + radius tuning** (see hos-unit-mechanics.md §3): brigade leaders get range 1-2, division 3-4, corps/department 5-6, army 6-7. Bonuses grow with echelon because only the highest bonus applies. Keep brigades of different divisions physically separated in scenario setup.
2. **Countries as stand-ins for corps/departments**: custom countries (e.g. "Valley District", "Mountain Department", "Dept. of the Rappahannock") on the same side. **UNVERIFIED:** whether "friendlies" includes allied-country units. If commanders buff only their own country, this gives true per-command restriction, e.g. Frémont's leaders wouldn't buff Shields' brigades. This needs an in-game test before we adopt it.
3. **Unit classes**: give commanders a bonus in only one category. Soft damage helps infantry/artillery and hard damage barely matters in 1862, so tuning the categories doesn't restrict who is buffed, only how much it matters.
4. **Scenario design**: leaders appear only in scenarios where their command fights. Arrivals follow `historical_data/reinforcements_1862.csv` via reinforcement tiles/spawn turns. Leader death and replacement is handled between scenarios (death is permanent in-engine).
5. **Heroes** can't be assigned deliberately (they're random at rank 5), so they aren't usable for named brigade commanders.

## Recommendation
Prototype option 2 (custom countries per department/corps) with an in-game test first, because it's data-only. If cross-country buffing happens, consider a small Harmony postfix in a separate PR, after confirming the target method locally.
