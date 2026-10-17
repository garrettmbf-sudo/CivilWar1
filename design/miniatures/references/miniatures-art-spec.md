# Valley 1862: based-miniature unit art, image-generation spec

Style target (from the user's references: Garnett infantry with flag, Ashby cavalry, Carpenter's battery, Jackson HQ): painted 28mm-style tabletop figures on a **hex-shaped flocked grass base**. A **round portrait medallion** and a **nameplate** sit on the front edge of the base.

Data source: `garrettmbf-sudo/CivilWar1`, branch `data/opening-oob-arrivals` (PR #12, stacked on #11). Counts come from `OOB.snapshot(1862-03-23)`, the `reinforcements_1862.csv` arrival schedule, and `brigade_commands_1862.csv`. Approved portraits are **referenced by filename only**; they are never regenerated, renamed or overwritten.

---

## 1. How many images

### 1a. Opening counters (snapshot 1862-03-23), 8 images
| # | Formation | Commander (medallion) | Members | Variant |
|---|---|---|---|---|
| 1 | FRM_CS_STONEWALL (Stonewall Bde) | Garnett `mdl_CSA_RGarnett.png` | 2,4,5,27,33 VA | CS-VA-STATE |
| 2 | FRM_CS_BURKS | Burks `mdl_CSA_JSBurks.png` (MISSING) | 21,42,48 VA, 1st VA Bn (Irish) | CS-VA-STATE |
| 3 | FRM_CS_FULKERSON | Fulkerson `mdl_CSA_SVFulkerson.png` (MISSING) | 23, 37 VA | CS-VA-STATE |
| 4 | FRM_CS_ASHBY | Ashby `mdl_CSA_TAshby.png` | 7th VA Cav + Chew's battery | CS-CAV-ASHBY |
| 5 | FRM_US_KIMBALL1 | Kimball `mdl_USA_NKimball.png` | 14 IN, 8 OH, 67 OH, 84 PA | US-INF-WEST |
| 6 | FRM_US_SULLIVAN2 | Sullivan `mdl_USA_JCSullivan.png` | 5 OH, 13 IN, 62 OH, 39 IL | US-INF-WEST |
| 7 | FRM_US_TYLER3 | Tyler `mdl_USA_EBTyler.png` | 7 OH, 7 IN, 1 WV, 29 OH, 110 PA | US-INF-WEST |
| 8 | FRM_US_CAV_BRODHEAD | Brodhead `mdl_USA_TFBrodhead.png` (MISSING) | 1st MI Cav det., 1st OH Cav cos., MD/PA cav (OR 12/1 p.346) | US-CAV |

### 1b. Later arrivals: counters entering after the opening, 24 new images
CS (10): CONNER (12 GA, 25, 31 VA) · SCOTTBRA (44, 52, 58 VA) · ELZEY · STEUART · TRIMBLE · TAYLOR · MUNFORD (2 VA Cav) · FLOURNOY (6 VA Cav) · MARYLAND_DET (1st MD CS, May 23-24 only) · ASHBY_SUC (post-Ashby cavalry).
US (14): MILROY_MCD · SCHENCK_MCD · DONNELLY · GORDON · HATCH (cav) · KENLY (Front Royal) · BAYARD (cav + Bucktails) · STAHEL · KOLTES · BOHLEN · CLUSERET · FERRY2 · CARROLL4 · FRMC_CAV (unattached cav).

**Reused, no new image:** KIMBALLR = KIMBALL1, TYLERR = TYLER3, MILROY_CK = MILROY_MCD, SCHENCK_CK = SCHENCK_MCD. These keep the same brigade identity in the data.
Optional: 5 of the 24 (MUNFORD, FLOURNOY, MARYLAND_DET, KENLY, FRMC_CAV) are detachment or battalion records that `snapshot()` emits but that are not flagged `counter=Y`.

**Unit images: 32** (8 opening + 24 arrivals).

### 1c. Commander (leader) units, 46 images
HoS commanders are separate non-combatant units (manual p.47). Under the agreed mapping, each command level gets its own figure. Each distinct person gets one image.
- **Army / district / department (4):** Jackson (Valley District; also Jackson's Division, one HQ figure), Banks, Frémont, McDowell. McDowell has no row in `commanders_1862.csv` and was never in the Valley, so his figure is optional.
- **Division (6):** Ewell, Edward Johnson (Army of the Northwest), Shields, Williams, Blenker, and Kimball as acting division commander at Kernstown. Kimball is one person who also leads Kimball's brigade, so make one figure and flag it.
- **Independent / brigade (36):** Garnett, Winder, Burks, Campbell, Patton, Fulkerson, Taliaferro, Conner, Scott, Steuart, Elzey, Walker, Trimble, Taylor, B. T. Johnson, Ashby, Munford, Flournoy, Crutchfield (artillery chief; optional, no HoS echelon), Sullivan, Tyler, Brodhead, Donnelly, Gordon, Hatch, Geary, Kenly, Milroy, Schenck, Stahel, Koltes, Bohlen, Cluseret, Bayard, Ferry, Carroll.

**Total required: 32 + 46 = 78 images** (73 if the 5 optional records and McDowell are dropped).
**Optional battery set:** the repo has 34 batteries (13 CSA, 21 USA). They are attachments, not counters, in `snapshot()`. Make them only if batteries become separate HoS units, as in the "Carpenter's battery" reference.

### 1d. Variants (base templates)
| Variant | Used by | Key look |
|---|---|---|
| CS-VA-STATE | Stonewall, Burks, Fulkerson (and Scott's 44/52/58 VA, unverified) | Valley Virginians, Virginia state flag |
| CS-NW | Conner, Scott | Army of the Northwest Virginians + 12th GA; flag **unverified** |
| CS-EWELL-SILK | Trimble (15 AL, 21 GA, 16 MS, 21 NC) | Johnston's-army men, first-issue silk battle flag |
| CS-EWELL-COTTON | Elzey, Maryland Line (MARYLAND_DET; 1st MD in Steuart) | 12-star cotton battle flag with orange border |
| CS-STEUART | Steuart | mix of CS-NW Virginians + 1st MD figure |
| CS-LA-TIGERS | Taylor | Louisiana brigade with a Wheat's Tiger Rifles figure (sub-variant) |
| CS-CAV-ASHBY | Ashby, Ashby successor, Munford, Flournoy | irregular Virginia cavalry; Ashby on a white horse (opening) |
| US-INF-WEST | Kimball, Sullivan, Tyler, Ferry, Carroll, Milroy, Schenck, Cluseret | standard Western-theatre-raised volunteers |
| US-INF-EAST | Donnelly, Gordon, Kenly | Banks' eastern regiments (CT, NY, PA, MA, WI, IN, MD) |
| US-GERMAN | Stahel (incl. 39th NY Garibaldi Guard figure), Koltes, Bohlen | Blenker's German regiments |
| US-CAV | Brodhead, Hatch, Frémont unattached cav | Union volunteer cavalry |
| US-CAV-BAYARD | Bayard | cavalry + a dismounted Bucktail rifleman |
| CMD-JACKSON-HQ | Jackson | composite HQ (see §2) |
| CMD-CS-GEN / CMD-CS-COL | CS generals / colonels | mounted officer + 1-2 staff |
| CMD-US-GEN / CMD-US-COL | Union generals / colonels | mounted officer + 1-2 staff |
| (opt) ART-CS-SMOOTH / ART-CS-RIFLED / ART-US-SMOOTH / ART-US-RIFLED | batteries | gun type per battery is **not in repo data; unverified** |

The Pennsylvania Zouaves d'Afrique (REG_PAZDA) belong to Geary's command in the repo, and Geary is an HQ, not a counter. The 114th PA history calls them Banks's bodyguard. Put them on the Banks or Geary commander figure only after checking; flag.

---

## 2. Historical accuracy per variant (sources at end)
**Confederate infantry, general (spring 1862):** mixed cadet-gray and butternut/jean-wool shell jackets and frock coats, some civilian items. Headgear: kepis/forage caps and slouch hats. Arms: mostly .69/.58 muskets, some Enfields; shoulder or knapsack/blanket roll. Gear worn and dusty after the winter campaign. [S1, S8]
- **CS-VA-STATE flag:** the Stonewall Brigade regiments fought spring 1862 under **Virginia state flags** (blue field, state seal), not the ANV battle flag. The 27th VA received its first battle flag in Aug 1862. [S1, S2] → One Virginia state flag, seal rendered as an illegible emblem.
- **CS-NW:** Army of the Northwest (Johnson) flags are **unverified**. Valley units may have carried First National ("Stars and Bars") or state flags [S3, S4]. Default: First National with 11-13 stars; flag it as an assumption.
- **CS-EWELL-SILK:** Ewell's men came from Johnston's army at Centreville, where Nov-Dec 1861 Richmond silk battle flags were issued: square, 12 stars, pinkish red, gold/yellow silk edging. 15th AL documented [S3, S4] → square silk battle flag, 12 stars.
- **CS-EWELL-COTTON:** Elzey's Brigade and the Maryland Line received the spring-1862 "cotton" substitute: square, about 4 ft, blue cross without white edging, 12 white stars, narrow orange border on all four edges. [S3]
- **CS-LA-TIGERS:** Louisiana brigade mostly in issue gray-blue jean jackets and kepis. Tiger Rifles men keep red shirts, faded tan Zouave jackets, blue-and-white striped "bed-ticking" pantaloons, white gaiters; red fez in camp, slouch hat in field. [S5, S6] Flag for Taylor's brigade: **unverified** (likely silk ANV-pattern as part of Ewell's division).
- **CS-CAV-ASHBY:** irregular Virginia cavalry. Mixed civilian and gray clothing, slouch hats, sabres, revolvers, shotguns/carbines. Ashby is bearded and dark-complexioned. His white horse Tom Telegraph was mortally wounded near Mount Jackson in April 1862 [S7], so the white horse is correct for the opening image and wrong for later dates. Chew's horse-artillery gun can appear as a background element. Flag: none or company guidon (**unverified**); don't invent one.
- **Union infantry (all US-INF):** dark-blue four-button fatigue sack coat (some frock coats), sky-blue kersey trousers, M1858 forage cap; some Hardee hats. Arms: Springfield/Enfield rifle-muskets. Colours: **national colours, 34 stars** (correct Jan 1861-Jul 1863), plus a blue regimental colour with US eagle, or a state flag. [S9, S10]
- **US-GERMAN:** standard Union blue. One **39th NY Garibaldi Guard** figure in Stahel's group: Bersaglieri black round wide-brim hat with drooping dark-green cock feathers, dark-blue tunic with red collar and cuffs, red-striped trousers. [S11] Other German regiments: no verified distinctive dress, so use standard blue.
- **US-CAV / US-CAV-BAYARD:** shell jackets with yellow trim, forage caps or Hardee hats, sabre, carbine, revolver; swallow-tail guidon (Stars-and-Stripes pattern). Bayard's figure adds a **Bucktail** (13th PA Reserves) rifleman with a deer tail on the cap; Sharps rifles by 1862 for some companies is **unverified** [S12].
- **Zouaves d'Afrique (optional):** dark-blue Zouave jacket with red trim, red trousers, white gaiters, red fez with yellow tassel. [S13]
- **CMD-JACKSON-HQ:**
  - Jackson on **Little Sorrel**, a small sorrel horse (mounted hide in the VMI Museum) [S14].
  - Coat: an old, plain, faded blue VMI-professor-type officer's coat, without fancy braid [S14, S15].
  - Cap: the dark **VMI forage cap pulled low over the eyes**. That cap was worn until Fredericksburg (Dec 1862); the gray/tan cap came later and would be anachronistic here [S15].
  - Staff: Jedediah Hotchkiss holding a map; Hotchkiss was summoned after Kernstown, so he is correct from late March and early April [S16]. Add a cavalry courier.
  - **HQ flag: unverified.** A headquarters flag is documented in the Seven Days (June 1862), probably a **First National**, per Hardy [S17]. The New Jersey "Jackson HQ flag" claim was refuted [S18]. Option A (default): First National carried by a courier, flagged as an assumption. Option B: no flag.
- **CMD-CS/US generals & colonels:** mounted officer in rank-appropriate frock coat. Union generals: 1862 regulation dark-blue double-breasted frock coat (button grouping by rank) and black slouch hat or forage cap. Confederate: gray frock coat; collar insignia per rank. Kimball was a **Colonel at Kernstown** (BG from April 1862): use colonel's straps on the opening image. No HQ flags for Union officers: 1862 corps and division HQ flag systems are unverified for these commands.

---

## 3. File spec (Hex of Steel)
- **Verified (community answer and official tutorial):** unit sprites are **PNG** in `MODS/<mod>/Graphics/Units/<Country>/`. The file name must **exactly match the unit name** set in the Unit Editor (case-sensitive). Land units are made at **1024x1024**; ships at 1258x1258 (community claim). [HoS-S2, HoS-Y]
- **Verified (manual p.16):** the engine draws the counter frame, the stat numbers (soft/hard/air damage, HP, range, MP), the morale bar and the veterancy/loadout icons **over** the sprite. A NATO-symbol view (key N, p.4) is drawn natively, so the alternate "square counter with NATO symbol + stat boxes" style needs no art.
- **Not verified for units:** the repo's assembly notes (`docs/hos-modding-notes.md` §A3, map/valley-tile-plan branch) cover the **Tiles** loader only: downsample to 512 px wide, DXT-compress, pixels-per-unit 330*512/w. Nothing in the repo shows the **unit** sprite loader uses the same path. Treat 512-px resampling and the source-width scale rule as **unknown for units** until tested.
- **Recommendation:**
  - Make a 2048x2048 master and export **1024x1024 RGBA PNG with a transparent background** (no baked frame, no stat boxes, no shadow plate outside the base).
  - Centre the hex base in the lower 60%, leaving about 8% margin. Keep the medallion and nameplate legible at 128 px.
  - Test one sprite in-game at 1024 and at 512 before batch export.
  - The existing `Unit_*`/`mdl_*` art is 104x126 / 170x280; any resized copies need new names.
- **Medallion:** composite from the existing `mdl_*.png` portrait named in `portrait_manifest.csv` (pasted or traced in a post step, not regenerated). For MISSING portraits, leave a blank bronze medallion placeholder.

---

## 4. Prompts
### Master template
```
Studio product photo of a painted 28mm historical wargame miniature diorama, {SUBJECT}, American Civil War, Shenandoah Valley, {DATE} 1862. Figures: {FIGURES}. Uniforms: {UNIFORMS}. Weapons: {WEAPONS}. Flag: {FLAG}. Mounted on a single hexagonal base, flat-topped, flocked spring grass with small stones and tufts, dark brown beveled base edge. On the front edge of the base: a round bronze portrait medallion (blank face area for later compositing) and a small brass nameplate reading "{NAMEPLATE}". Hand-painted acrylic finish, subtle wash and highlights, soft studio lighting from upper left, three-quarter front view, slightly elevated camera, isolated on a fully transparent background, whole base in frame, centered, no cast shadow outside the base.
```
### Negative prompt (all images)
```
modern flags, 50-star flag, Confederate flag with 13 stars on a rectangular battle flag, Second or Third National Confederate flags, WWI/WWII gear, helmets, camouflage, khaki uniforms, modern rifles, bayonets on cavalry, machine guns, Gatling guns, rubber boots, zippers, sunglasses, plastic sheen, text other than the nameplate, logos, watermark, signature, banners with readable writing, extra limbs, malformed hands, duplicated heads, square base, round base, scenery outside the base, background, frame, stat boxes, NATO symbols
```

### Per-variant fills (SUBJECT / FIGURES / UNIFORMS / WEAPONS / FLAG / NAMEPLATE)
1. **CS-VA-STATE** (Stonewall, Burks, Fulkerson):
   - Subject: "Confederate Virginia infantry brigade stand"
   - Figures: 4-5 marching or advancing infantrymen, one colour-bearer, one officer with sword
   - Uniforms: mixed cadet-gray and butternut jean jackets, faded kepis and slouch hats, blanket rolls, worn shoes
   - Weapons: muskets and rifle-muskets with bayonets
   - Flag: "Virginia state flag, dark blue field with a central circular state seal emblem (illegible detail)"
   - Nameplate: "Stonewall Brigade – Garnett" / "Burks' Brigade" / "Fulkerson's Brigade"
2. **CS-NW** (Conner, Scott): as #1. Flag: "First National Confederate flag, red-white-red bars, blue canton with a circle of white stars" (**assumption**). Nameplate: "Conner's Brigade" / "Scott's Brigade".
3. **CS-EWELL-SILK** (Trimble): as #1 with Alabama/Georgia/Mississippi/NC men, more gray. Flag: "square silk Confederate battle flag, pinkish-red field, blue St Andrew's cross with white edging, 12 white stars, gold silk border". Nameplate: "Trimble's Brigade".
4. **CS-EWELL-COTTON** (Elzey, Maryland Det.): Flag: "square cotton battle flag, red field, blue St Andrew's cross without white edging, 12 white stars, narrow orange border on all four edges". Nameplate: "Elzey's Brigade" / "1st Maryland (C.S.)".
5. **CS-STEUART:** #2 figures plus one Marylander. Flag per #4 (Maryland Line). Nameplate: "Steuart's Brigade".
6. **CS-LA-TIGERS** (Taylor):
   - Figures: 3 Louisiana infantry in gray-blue jean jackets and kepis, plus 1-2 Tiger Rifles men in red shirts, faded tan Zouave jackets, blue-and-white striped baggy trousers, white gaiters, slouch hats
   - Flag: square ANV-pattern battle flag (**unverified**)
   - Nameplate: "Taylor's Louisiana Brigade"
7. **CS-CAV-ASHBY:**
   - Figures: 2-3 mounted cavalrymen at a gallop; Ashby leading on a **white horse** (opening image only; dark horse for later images)
   - Uniforms: mixed gray and civilian coats, slouch hats with plumes optional, sabres, revolvers, shotgun
   - Flag: none
   - Nameplate: "Ashby's Cavalry" (later: "Munford's Cavalry", "2nd Va. Cavalry – Munford", "6th Va. Cavalry – Flournoy")
8. **US-INF-WEST:**
   - Figures: 4-5 advancing Union infantry, colour-bearer, officer
   - Uniforms: dark-blue fatigue sack coats, sky-blue trousers, forage caps, one or two black Hardee hats
   - Weapons: Springfield/Enfield rifle-muskets
   - Flag: "US national colours, 34 stars in rows, 13 stripes" (+ optional blue regimental colour with eagle)
   - Nameplate: "Kimball's Brigade" (Colonel straps), etc.
9. **US-INF-EAST:** as #8. Nameplate: "Donnelly's Brigade" / "Gordon's Brigade" / "Kenly – Front Royal".
10. **US-GERMAN:** as #8. Stahel's image adds one Garibaldi Guard figure (black wide-brim Bersaglieri hat with drooping dark-green cock feathers, dark-blue tunic with red collar and cuffs). Nameplate: "Stahel's Brigade" / "Koltes' Brigade" / "Bohlen's Brigade".
11. **US-CAV:** 2-3 mounted troopers in blue shell jackets with yellow trim, forage caps, sabres, carbines; swallow-tail Stars-and-Stripes guidon. Nameplate: "Brodhead's Cavalry" / "Hatch's Cavalry" / "Frémont's Cavalry".
12. **US-CAV-BAYARD:** #11 plus one dismounted rifleman with a **deer tail on his cap**. Nameplate: "Bayard's Command".
13. **CMD-JACKSON-HQ:**
    - Figures: Jackson mounted on a small sorrel horse, gaunt, bearded, stiff posture; a staff officer (Hotchkiss) standing with an unrolled hand-drawn map; a cavalry courier holding a flag
    - Uniforms: Jackson in a plain, faded, dark-blue old professor's officer coat and a dark forage cap pulled low over his eyes; staff in gray
    - Flag: "First National Confederate flag" (**unverified**; alternate render with no flag)
    - Nameplate: "Jackson – Valley District". Medallion: `mdl_CSA_TJJackson.png`.
14. **CMD-CS-GEN / COL:** mounted officer plus one standing aide; gray frock coat with rank collar insignia; no flag. Nameplate: name and rank, e.g. "Brig. Gen. R. S. Ewell" (medallion `mdl_CSA_REwell.png`).
15. **CMD-US-GEN / COL:** mounted officer plus one aide; dark-blue frock coat, shoulder straps, black slouch hat or forage cap; no flag. Nameplate e.g. "Maj. Gen. N. P. Banks" (medallion `mdl_USA_NPBanks.png`).
16. **(opt) ART-*:** gun plus limber and 3-4 crew. Gun type (6-pdr smoothbore, 12-pdr howitzer, 10-pdr Parrott, 3-inch Ordnance rifle) **must be confirmed per battery first**. Union crew in blue with red artillery trim; CS crew mixed gray. Nameplate e.g. "Carpenter's Battery".

---

## 5. Flags & open items
- **Valley District flags:** Stonewall Brigade on state flags is sourced. All other CS brigade flags are inferred from army of origin; regiment-level flags are unverified.
- **Jackson's HQ flag in spring 1862:** unverified (First National is an assumption).
- **Ashby's horse after April:** the replacement horse colour is unverified.
- **Gun types per battery:** not in repo data. ART_WESTAUGUSTA probably conflates Waters' and Carpenter's batteries (OR 12/1 pp.381-401).
- **Repo data issues:** `REG_VA12` is labelled "12th Georgia" (ID mismatch). REG_PAZDA is assigned to Geary, not Banks.
- **Union officer HQ flags:** not used (unverified).
- **Portraits:** MISSING portraits (Burks, Fulkerson, Brodhead, and others in the manifest) mean a blank medallion until approved art exists.

## Sources
- S1 stonewallbrigade.net, Equipage of the Stonewall Brigade: https://stonewallbrigade.net/equipage-of-the-stonewall-brigade/
- S2 stonewallbrigade.net, Cedar Mountain (27th VA first battle flag Aug 1862): https://stonewallbrigade.net/stonewall-brigade-at-cedar-mountain/
- S3 Confederateflags.org, Battle Flags of the ANV (silk 1861 issue; cotton substitute to Elzey's Brigade & Maryland Line): https://confederateflags.org/army/fotcanv/
- S4 CivilWarTalk thread citing ADAH 15th Alabama silk flag and Biggs/Cannon on First Nationals in the Valley: https://civilwartalk.com/threads/battle-flags-in-the-valley-may-1862.6418/
- S5 Louisiana Tigers 1862 uniforms (Warren letters): https://www.liquisearch.com/louisiana_tigers/1862_uniforms
- S6 Wheat's Tigers plate notes: https://thewarinamericanhistory.wordpress.com/2018/12/23/1st-special-battalion-louisiana-infantry-wheats-tigers-1862-62-plate/
- S7 Rude's Hill marker (Ashby's white horse Tom Telegraph mortally wounded, April 1862): https://www.hmdb.org/m.asp?m=254867
- S8 Adolphus, The Quintessential Confederate Cap: https://adolphusconfederateuniforms.com/the-quintessential-confederate-cap-part-i-overview.html
- S9 NPS Antietam, Flags (Union regulation colours): https://www.nps.gov/anti/learn/historyculture/flags.htm
- S10 34-star US flag period (Kansas admitted Jan 1861; 35th star Jul 1863): standard vexillology, verify against a museum reference before print
- S11 NY State Military Museum, 39th NY Garibaldi Guard dress: https://museum.dmna.ny.gov/unit-history/infantry/39th-infantry-regiment/thorny-rose/gurkhas-and-garibaldians
- S12 PRVCHS, The Bucktails: https://www.prvchs.org/the-pennsylvania-reserves/13th-pennsylvania-reserves-1st-rifles-bucktails-infantry/
- S13 Collis Zouaves (114th PA history; Zouaves d'Afrique as Banks's bodyguard): https://www.palmettoriflemen.org/ZouaveArchive/Federal/Pennsylvania_114thInfantryRegiment.html
- S14 VMI Museum, Stonewall Jackson at VMI (Little Sorrel, uniforms, cap): https://www.vmi.edu/research/museums-and-archives/vmimuseum/stonewall-jackson-at-vmi/
- S15 Adolphus (Jackson's first, dark VMI cap worn until Fredericksburg; gray cap after), same URL as S8
- S16 Jackson's Valley Campaign (Hotchkiss summoned after Kernstown): https://en.wikipedia.org/wiki/Jackson's_Valley_Campaign (confirm against Hotchkiss, *Make Me a Map of the Valley*)
- S17 M. C. Hardy, "Carrying Jackson's Flag" (Confederate Veteran 38:248): http://michaelchardy.blogspot.com/2018/06/carrying-jacksons-flag.html
- S18 NJ State Archives guide (refuted Jackson HQ flag claim): https://nj.gov/state/archives/guides/sdea0013.pdf
- HoS-M Official manual pp.4, 16, 47: https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1240630/manuals/1e929c3c9d09670cb450bdf6272b9522dfb4bc5b/Manual.pdf
- HoS-S2 Steam, unit image thread: https://steamcommunity.com/app/1240630/discussions/0/3838801285229788338/
- HoS-Y Official modding tutorial: https://www.youtube.com/watch?v=sGADvjll8pU
