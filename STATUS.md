# First Kernstown 1862 — scenario status

## Overview
Standalone tactical scenario for **First Kernstown, 23 March 1862** in Hex of Steel.
62x55 hexes at ~250 yards per hex. 3,410 unique painted tiles (Summer, 2000x2000 px, no baked grid).

## Map features
- **Winchester (March 1862):** ~39 buildings on Loudoun St commercial strip with side streets, outbuildings, orchards. Landmarks: Courthouse (primary VP), Taylor Hotel, Jackson's HQ, Fort Collier, Fort Alabama earthworks.
- **Sandy Ridge stone wall:** 7 hexes with DamageModificator 35 (between forest 25 and city 40). Natural straight fieldstone line, not hex-grid zigzag.
- **Kernstown village:** ~11 buildings on Valley Pike and Cedar Creek Grade (secondary VP).
- **Opequon Church:** stone church with graveyard (secondary VP).
- **Pritchard-Grim farm:** stone farmhouse, bank barn, log cabin.
- **Terrain:** early-spring palette — leafless woods, tan/brown fields, marshy meadows, muted gray-blue creeks, Valley Pike, Winchester & Potomac RR.

## Order of battle (18 units)

### Confederate (Jackson's Valley District, ~3,800 men)
| Unit | Template | Position | Entrench | Source |
|------|----------|----------|----------|--------|
| Stonewall Bde (Garnett) 2,4,5,27,33 VA | Infantry | 17,23 | 2 | SRC007 |
| Fulkerson's Bde 23,37 VA | Infantry | 15,23 | 2 | SRC007 |
| Burks' Bde 21,42,48 VA, 1 VA Bn | Infantry | 17,20 | 0 | SRC007 |
| Ashby's 7th Virginia Cavalry | Light Cavalry | 27,17 | 0 | SRC007 |
| Chew's Horse Artillery | Napoleon 12pdr | 26,18 | 0 | SRC007 |
| Rockbridge Artillery (Poague) | Napoleon 12pdr | 16,22 | 0 | SRC007 |
| Carpenter's Alleghany Battery | Napoleon 12pdr | 18,22 | 0 | SRC007 |
| Caskie's Hampden Artillery | Napoleon 12pdr | 15,22 | 0 | SRC007 |
| Wooding's Danville Artillery | Napoleon 12pdr | 20,22 | 0 | SRC007 |
| Pleasants' Battery | Napoleon 12pdr | 20,21 | 0 | SRC007 |

### Union (Shields' Division under Col. Kimball, ~8,500 men)
| Unit | Template | Position | Source |
|------|----------|----------|--------|
| 1st Bde (Kimball) 14 IN, 8,67 OH, 84 PA | Infantry | 25,26 | SRC007 |
| 2nd Bde (Sullivan) 39 IL, 13 IN, 5,62 OH | Infantry | 29,24 | SRC007 |
| 3rd Bde (Tyler) 7 IN, 7,29 OH, 110 PA, 1 WV | Infantry | 17,25 | SRC007 |
| Btry A West Virginia Arty (Jenks) | Napoleon 12pdr | 25,27 | SRC007 |
| Btry B West Virginia Arty | Napoleon 12pdr | 27,27 | SRC007 |
| Btry E 4th US Artillery (Clark) | Napoleon 12pdr | 26,27 | SRC007 |
| Btry L 1st Ohio Arty (Robinson) | Napoleon 12pdr | 26,26 | SRC007 |
| Brodhead's Cav (MI/PA/MD/WV/OH detachments) | Light Cavalry | 13,25 | SRC007 |

## Victory conditions
- **Primary:** Winchester Courthouse (42,41)
- **Secondary:** Kernstown (27,20), Opequon Church (30,19)

## Game mechanics
- Stone wall hexes: DamageModificator 35, Confederate units start entrenched level 2
- Woods: MP 3, dmg 25. Town: dmg 40. Marsh: MP 4. Pike/roads: MP 1. Hill: dmg 15.
- HoS has no hexside/directional combat — wall bonus applies to all attacks into wall hexes.

## Build status
- `tools/build_kernstown_map.ps1` reads `kernstown_game.json` + `kernstown_units.json`, loads HoS DLLs, writes .sav. Parses cleanly in pwsh 7.4. **Untested against running game.**
- 3,410 SV_K tiles sliced from continuous painted basemap (Summer folder, no grid).
- `mod/Manifest.json` present. See `README_INSTALL.md` for installation.

## Art provenance
- Terrain basemap: procedurally composed from elevation data, feature layers, and painted sprites.
- Sprites prefixed `cgpt_` / `cgpt2_` / `cgpt3_`: AI-generated (ChatGPT image generation). Buildings cut from user-provided reference sheets via rembg.
- Historic map overlays in `data/historic_maps/`: Hotchkiss sketches (public domain), ABT battlefield maps.
- Source register for individual assets: **not yet created** — pending `reference/source_register.csv`.
