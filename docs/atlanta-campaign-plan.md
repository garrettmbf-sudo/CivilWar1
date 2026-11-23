# Atlanta Campaign (1864): map set, side choices, and campaign sim plan

**Status:** PLAN. Nothing here has been built or tested in Hex of Steel (HoS). Dates and orders of battle come from general knowledge of the campaign and must be sourced (§9) before any unit is placed. Extents are estimates, to be replaced by the geographic pipeline (`docs/roadmap.md` M2).

**Scope decision needed:** `AGENTS.md` makes the 1862 Valley the mission and lists 1864 as legacy planning. Atlanta is a second campaign, or a replacement. Until the owner decides, this doc stays a proposal and the Valley work is not displaced.

## 1. Design principle: every map is a choice, not a corridor

Sherman's campaign was a sequence of "assault the fortified line, or go around it". A map is only useful if it holds both. Every map therefore contains:

1. **The fortified line** the Confederates can hold.
2. **At least one flank route** that costs time and supply but avoids the line.
3. **The Western & Atlantic Railroad**, Sherman's supply line, with a depot or bridge that can be cut.
4. **River crossings or passes** that decide the flank.
5. **Cavalry work**: screening, scouting, and raiding. Recon units see 2 hexes and move twice (`docs/valley-map-build-plan.md` §1.1), so cavalry is the only way to see a flank march coming. Fog of war should stay on.

The Confederate side gets matching choices: hold, withdraw, counterattack an isolated column, or raid the railroad. Without these the Union player always wins by flanking.

## 2. Map set

Windows of one master map (§3). Dates are historical; extents are rough estimates in miles (width x height).

| # | Map | Dates | Extent | Anchor terrain |
|---|---|---|---|---|
| M1 | Rocky Face, Dug Gap, Snake Creek Gap | 7-12 May | 25 x 25 | Rocky Face Ridge, Mill Creek (Buzzard Roost) Gap, Dug Gap, Snake Creek Gap, Dalton |
| M2 | Resaca, Calhoun, Lay's Ferry | 13-16 May | 25 x 20 | Oostanaula and Conasauga Rivers, Resaca works, Lay's Ferry, Calhoun |
| M3 | Adairsville, Kingston, Cassville, Etowah | 17-23 May | 25 x 28 | Adairsville valley, Kingston, Cassville ridge, Etowah River, Rome road |
| M4 | Allatoona, Dallas, New Hope Church | 23 May-6 June | 30 x 25 | Allatoona Pass, Burnt Hickory, Dallas, New Hope Church, Pickett's Mill, Acworth |
| M5 | Kennesaw, Marietta, Kolb's Farm | 10 June-3 July | 28 x 22 | Pine, Lost, Brush and Kennesaw Mountains, Mud Creek, Olley's Creek, Smyrna |
| M6 | Chattahoochee crossings | 5-10 July | 28 x 20 | Roswell to Sandtown, the Confederate river line, Pace's and Isham's Ferries |
| M7 | Peachtree Creek, Decatur, Atlanta | 17-28 July | 25 x 25 | Peachtree Creek, Decatur, Georgia Railroad, Bald Hill, Ezra Church |
| M8 | Atlanta to Jonesboro | 28 July-6 Sept | 30 x 30 | Atlanta works, East Point, Utoy Creek, Macon & Western Railroad, Jonesboro, Lovejoy's |
| M9 | Cavalry raids | 27 July-31 Aug | 40 x 40 | Stoneman-McCook raid, Kilpatrick's raid, Wheeler's raid on the railroad |

M1 and M2 touch and can be built as one Dalton-to-Calhoun strip (about 25 x 32 miles) if the engine allows it. If the owner already has a Resaca-Calhoun map, M2 is done and M1 is its northern neighbor. **I found no Resaca/Calhoun map in this repo.**

Hex count is miles x hexes-per-mile on each axis. At 1 mile per hex the whole campaign is on the order of 5,000 hexes; at 500 yd per hex a single 25 x 25 mile map is about 4,900 hexes, 1.5x Kernstown's 3,348 tiles (about 2.9 GB). That cost is why the scale in §3 matters.

## 3. Master map and scale

- **One master map** Dalton to Lovejoy's, built once from geographic data (USGS 3DEP elevation, hydrography, GNIS names, roads and railroad traced from period maps). M1-M9 are windows cut from it, so a unit leaving one map enters the next at the same coordinates.
- **Hex convention:** HoS native flat-top even-q (`docs/hex-convention.md`, `src/hex_utils.py`). Each window is cut on an even-column boundary so coordinates keep their meaning.
- **Scale:** the starting target is 1 mile per hex (`AGENTS.md`). The Valley build plan argues for 500 yd for artillery and musket adjacency. The same question applies here and the stress test decides it. Brigade counters are the maneuver unit either way.
- **Unverified engine limits:** one unit per hex; map-size and performance ceilings; whether the editor can set per-unit visibility. Test before promising a scale.

## 4. Per-map choices

### M1 Rocky Face / Snake Creek Gap (7-12 May)
| | Options |
|---|---|
| **Union** | **A** Frontal at Buzzard Roost (Thomas). **B** Assault Dug Gap (Geary's division tried this on 8 May and was repulsed). **C** Send McPherson's Army of the Tennessee through Snake Creek Gap to Resaca, behind the Confederate army (historically he found Cantey's infantry at Resaca on 9 May and pulled back). **D** Cavalry screens north to hold Wheeler. |
| **Confederate** | Hold Rocky Face; scout Snake Creek Gap with cavalry; bring Polk's Army of Mississippi up to Resaca; fall back to Resaca (historically 12 May). |
| **Win / VP** | Union: Resaca railroad bridge or Dalton. Confederate: keep Johnston's army intact and the railroad open. |
| **Key tension** | Option C wins the campaign if the Union player commits fully and the Confederate scouting fails. |

### M2 Resaca / Calhoun / Lay's Ferry (13-16 May)
| | Options |
|---|---|
| **Union** | **A** Assault the fortified line north of Resaca. **B** Turn the Confederate left (Hooker's attack, 14 May). **C** Cross the Oostanaula at Lay's Ferry with Sweeny's division on pontoons (14-15 May) toward Calhoun and the railroad behind Resaca. |
| **Confederate** | Hold the works; counterattack the Union left (Hood's attack, 14 May); fall back across the Oostanaula and burn the bridges (historically night of 15-16 May); hold Calhoun. |
| **Win / VP** | Union: Resaca, plus the Calhoun road net. Confederate: hold Resaca through turn N, or withdraw with the army intact. |
| **Key tension** | Option C only works if the Union can get a crossing and hold the bridgehead. |

### M3 Adairsville / Kingston / Cassville (17-23 May)
| | Options |
|---|---|
| **Union** | **A** Stay on the railroad. **B** Split into parallel columns (historically) and send a detachment to Rome (Davis took it 18 May). **C** Force the Etowah crossings early. |
| **Confederate** | Accept battle where the Adairsville valley narrows; set a trap for an isolated Union column at Cassville (planned 19 May, aborted); split at Kingston; fall back across the Etowah to Allatoona. |
| **Win / VP** | Union: Kingston, Cassville, Etowah bridge. Confederate: a favorable engagement or an orderly withdrawal. |
| **Key tension** | Parallel columns give speed but invite a Confederate strike on an isolated corps. |

### M4 Allatoona / Dallas / New Hope Church (23 May-6 June)
| | Options |
|---|---|
| **Union** | **A** Assault Allatoona Pass (a strong position Sherman avoided). **B** Swing right to Dallas, leaving the railroad (historical). **C** Swing left toward Acworth. |
| **Confederate** | Hold Allatoona; shift to the New Hope Church line (historical); counterattack detached columns (Pickett's Mill, 27 May); raid the supply line with cavalry. |
| **Win / VP** | Union: Allatoona Pass and Acworth. Confederate: hold the line to Marietta. |
| **Key tension** | Leaving the railroad costs supply (§7) and gives Johnston the initiative. |

### M5 Kennesaw / Marietta / Kolb's Farm (10 June-3 July)
| | Options |
|---|---|
| **Union** | **A** Left via Brush Mountain and Big Shanty. **B** Frontal assault at Pigeon Hill / Cheatham Hill (27 June, historical failure). **C** Right via Powder Springs, Kolb's Farm and Olley's Creek to turn the Confederate left (historical decision after the assault failed). |
| **Confederate** | Hold the Pine / Lost / Brush Mountain line; the Mud Creek line; the Kennesaw line; counterattack on the Union right (Hood at Kolb's Farm, 22 June); fall back to Smyrna and the river. |
| **Events** | Polk killed at Pine Mountain, 14 June: a commander is removed and replaced (Loring, then Stewart from 23 June). |
| **Key tension** | The assault on Kennesaw is available and costly; the right-flank swing works but needs time and a clear road net. |

### M6 Chattahoochee crossings (5-10 July)
| | Options |
|---|---|
| **Union** | **A** Cavalry seizes Roswell and the upstream crossing. **B** Schofield crosses at Isham's Ferry. **C** Thomas crosses at Pace's Ferry. **D** Feint at several fords to spread the Confederates. |
| **Confederate** | Defend the river line (the Shoupade works); shift reserves to answer feints; counter-attack a bridgehead before it consolidates; withdraw across the river (9-10 July). |
| **Win / VP** | Union: two bridgeheads that threaten Atlanta. Confederate: contain every crossing. |
| **Key tension** | Johnston cannot cover every ford, but he does not know which crossing is real. Scouting decides it. |

### M7 Peachtree Creek / Decatur / Atlanta (17-28 July)
| | Options |
|---|---|
| **Union** | **A** Advance from the north across Peachtree Creek (Thomas). **B** Swing east to Decatur and cut the Georgia Railroad (McPherson, 18 July). **C** Extend west toward Ezra Church. |
| **Confederate** | **A** Hit Thomas as he crosses Peachtree Creek (20 July). **B** Flank march around the Union left (Hardee, 22 July, the engagement WDS Scenario 097 covers). **C** Strike the Union right as it extends (Ezra Church, 28 July). **D** Withdraw into the Atlanta works and stand a siege. |
| **Events** | Hood replaces Johnston on 17 July (commander and AI posture change). McPherson killed on 22 July (Logan, then Howard). |
| **Key tension** | Hood's attacks are bold but costly; a defensive player may do better than history. |

### M8 Atlanta to Jonesboro (28 July-6 Sept)
| | Options |
|---|---|
| **Union** | **A** Siege and shelling (historical, until late August). **B** Extend the right to cut the Atlanta & West Point Railroad (East Point, Utoy Creek). **C** Swing the army south to Jonesboro and the Macon railroad (late August, historical decision). **D** Cavalry raids (see M9). |
| **Confederate** | Hold the works; send Hardee and Lee to Jonesboro; counterattack the Union near Jonesboro (31 Aug-1 Sept); evacuate Atlanta and destroy stores (night of 1 Sept). |
| **Win / VP** | Union: Atlanta (primary), Jonesboro and the Macon railroad (secondary). Confederate: keep the Macon railroad and the army. |
| **Key tension** | Cutting the Macon railroad forces Hood to give up the city. |

### M9 Cavalry raids (27 July-31 Aug)
A cavalry-only scenario set that uses recon and screening (the user's emphasis):
- **Stoneman-McCook raid** (late July): two Union cavalry columns toward Lovejoy's Station; McCook raided the railroad, then both were caught near Newnan (Brown's Mill) and Sunshine Church.
- **Kilpatrick's raid** (18-22 Aug): around Atlanta to Jonesboro and Lovejoy's.
- **Wheeler's raid** (from about 10 Aug): Confederate cavalry north into Georgia and Tennessee to cut Sherman's railroad.

The Union side picks a target and a route; the Confederate side must find the column with cavalry before it reaches the railroad.

## 5. Branch graph

HoS maps carry `NextMap`, `NextMap2`, `NextMapDefeat`, `NextMap2Defeat` fields (the Kernstown builder blanks them; `tools/build_kernstown_map.ps1`). Their semantics are unverified; the plan assumes victory, alternate victory, defeat and alternate defeat.

```
M1 --C succeeds--> M2' (Resaca trapped, CSA in march column)
 |--A/B/C fails or historical--> M2
M2 --C bridgehead holds--> M3' (Calhoun lost, CSA withdraws early)
 |--otherwise--> M3
M3 --Union splits and CSA trap succeeds--> M3 aftermath (Union loses a corps' worth of strength)
 |--otherwise--> M4 (A or B or C chosen on M3 result)
M4 --Union takes Allatoona--> M5 (earlier start, Union nearer Marietta)
 |--Union swings to Dallas--> M4 -> M5 (historical)
M5 --Kennesaw assault repulsed--> M5 (right swing)
 |--Union turns the left--> M6
M6 --2 bridgeheads--> M7
 |--none--> M6 repeats with a later date
M7 --Union holds--> M8
 |--Confederate wins Peachtree/Atlanta--> M7 again, Union weaker
M8 --Macon railroad cut--> end (Atlanta falls)
 |--held--> M8 continues (campaign extends)
M9 --runs alongside M7 and M8; outcomes alter supply (§7)
```

Alternate maps (M2', M3') are small edits to a window: the same terrain with different starting positions.

## 6. How armies are placed: the campaign sim

The user's request: armies on each map should come from a simulation of the campaign up to that point, not from hand-placed units. The plan has three layers.

### 6.1 Sim v0: dated baseline (no combat)
A script reads a dated order of battle and produces each map's starting units.
- **Inputs:** `historical_data/atlanta/` (new): formations with parent and commander by date; strength returns by date; arrival and departure events (Polk's Army of Mississippi joining at Resaca in mid-May; Blair's XVII Corps arriving in early June; Wheeler's cavalry; the Georgia Militia in July); a coordinate table of known positions on each map's start date.
- **Output:** one `units.json` per map, in the same game-native format as Kernstown (`"grid_convention": "game-native"`), with `Entrench` levels, strength, and commander.
- **Placement rule:** a unit starts at its historical position on the map's start date; if none is documented, it starts along its approach road at the march distance from the previous map's exit.
- **Test:** every unit on every map traces to a source row with a date; no unit appears on two maps at once.

### 6.2 Sim v1: branch-aware carry-over
When the player's result changes the path, the sim recomputes the next start state.
- **Carry-over fields per unit:** present strength (percent of the dated return), entrenchment, supply days, fatigue, commander.
- **Casualties:** losses on map N reduce strength on map N+1. Brigades below a threshold merge or drop out. Rates come from sourced returns, not invention.
- **Reinforcement and exit:** units leave a map at its exit edge and enter the next at the matching master-map edge hex, with the arrival turn set by the road march distance.
- **Branches:** a successful Snake Creek flank starts M2' with Confederates in march column and Union at the Resaca bridge; a failed one starts M2 historically. The same pattern applies at each node in §5.
- **Test:** a scripted branch replay (win, lose, alt) gives the same start state twice (deterministic) and respects all carry-over rules.

### 6.3 Sim v2 (optional): operational layer
Only if v0 and v1 work. Armies move as nodes on the master-map road graph a day at a time; contact triggers the matching map; off-screen combat resolves by a simple table. This is the "campaign game" mode and the largest scope. It should not start until M1 and M2 are playable in HoS.

### 6.4 HoS fields to verify
- Whether surviving units carry between maps in a campaign (`IsCampaign`, core units) or must be rebuilt by the builder.
- The event system for timed reinforcements (the builder clears `Events`, `EventIDs`, `listOfVPThatNeedsToBeHeld`).
- How commanders are represented (`docs/hos-commander-radius-restriction.md`) so Polk's death and Hood's appointment can be scripted.

## 7. Supply and the railroad

Sherman's real constraint was the single railroad. Model it in the engine's own terms:
- The Western & Atlantic Railroad is a Railroad-flagged hex chain (as in `build_game_layers.py`); trains extend movement (`docs/valley-map-build-plan.md` §1.1).
- A cut railroad stops trains and reduces Union movement and ammunition; the Union repairs it with engineers over turns. Raids (M9) and Confederate cavalry attacks on it are therefore real threats.
- Leaving the railroad (M4, M8) is a choice with a cost: fewer turns of supply before the army must return to it or capture another line.
- Verify first: ammunition and supply mechanics (`docs/hos-unit-mechanics.md`).

## 8. Milestones

| Step | Deliverable | Exit test |
|---|---|---|
| P0 | Owner decisions (§10) | Recorded in `docs/decisions.md` |
| P1 | Source register for Atlanta (§9) | `reference/source_register.csv` filled; no unsourced unit |
| P2 | Master-map geographic pipeline for M1-M2 | Test region shows correctly placed terrain, roads, railroad |
| P3 | M1 + M2 scenario, one side playable | Loads in Play, both flank options exist, tested in game |
| P4 | Sim v0 for M1-M2 | Start units match sourced positions |
| P5 | Remaining maps in order M3-M8 | Each loads and offers both options |
| P6 | Sim v1 carry-over and branches | Scripted replay deterministic; branches verified in game |
| P7 | M9 cavalry scenarios | Scouting and screening work under fog of war |

Rule from `AGENTS.md` item 3 applies: do not emit `.sav` files labeled playable until a test in HoS confirms it.

## 9. Sources and rights

- **Orders of battle and strengths:** *Official Records of the War of the Rebellion*, Series I, Vol. 38 (parts 1-5): dated returns and reports. Public domain.
- **Maps:** *Official Military Atlas of the Civil War*; Library of Congress campaign maps; USGS 3DEP and hydrography for terrain.
- **Narrative:** Albert Castel, *Decision in the West* (1992); Richard McMurry, *Atlanta 1864* (2000); Jacob D. Cox, *Atlanta* (1882); Sherman's and Johnston's memoirs.
- **WDS material:** the repo holds `03_Atlanta (full).map` and four preview images (Scenarios 003, 070, 084, 097). They are third-party. `AGENTS.md` rule 4 forbids redistributing third-party artwork or data without permission. Use them as private reference only, and log provenance in `reference/source_register.csv`. I cannot read the `.map` file, so nothing here was taken from it.
- `!!!NEWJuly1GBCampaign.oob` in the repo is a **Gettysburg** order of battle, not Atlanta.

## 10. Decisions needed

1. Is Atlanta a second campaign alongside the Valley, or a replacement?
2. What hex scale is the WDS Atlanta map, and where is the existing Resaca/Calhoun map?
3. Scale for the HoS maps: 1 mile per hex, 500 yd, or decided by the stress test?
4. Start with M1+M2 as one strip, or M2 alone?
5. Sim v2 (operational layer): in scope, or chained scenarios only?
