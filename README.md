# CivilWar1 — Jackson's Valley Campaign, 1862

An in-progress **Hex of Steel** modification focused exclusively on the **March–June 1862 Shenandoah Valley Campaign**. The first release targets a historical campaign map, individually movable brigade counters, accurate dated organizations, Union and Confederate headquarters, and direct Hex of Steel gameplay.

**Current status: RESEARCH AND TOOLING.** No playable campaign, verified .sav writer, or working exclusive command-assignment patch is claimed yet.

## What is being built

- **Geography:** Winchester–Staunton, the Luray Valley, Massanutten, and the western approaches through McDowell and Franklin. Start by testing **one geographic mile per hex**; retain historical valley widths, the Valley Pike, rivers, roads, and mountain gaps.
- **Period:** Kernstown (March 23) through Port Republic (June 9), 1862.
- **Forces:** Historical Union and Confederate **brigades as combat counters**, with distinct cavalry and artillery where appropriate.
- **Command:** Visible headquarters with geographically limited bonuses, attached to historical command relationships where verified and technically possible. Keep native direct movement; no replacement orders engine.
- **Graphics:** Attractive historical-map terrain and existing **user-audited** general portraits. Never rename, replace, or relocate audited image files without first testing all game references.

**Not part of this first release:** a US-wide map, the 1864 Valley campaign, Gettysburg, or an independent game engine.

## Repository guide

| Path | Contents | Status |
| --- | --- | --- |
| `docs/` | Roadmap, engine-format notes, asset layout, scenario design | Documentation; some formats unverified |
| `reference/` | Historical and third-party map images, additional portraits | Reference only; rights must be checked before reuse |
| Root `mdl_*.png` / `Unit_*.png` | Existing art with established names | **Frozen paths** until consumer/dependency audit |
| `historical_data/` | Portrait manifest and future sourced OOB / formation history | Inventory ready; historical OOB TBD |
| `maps/` | Existing .sav samples; generated files kept separate | Samples **not** evidence of writer compatibility |
| `scenarios/1862/` | Campaign design and planned scenarios | In progress |
| `scenarios/1864/` | Archived future concept, **out of scope** | Preserve; do not expand |
| `src/`, `scripts/`, `tests/` | Hex math, inspection, experimental tools, automated tests | Mixed readiness; see roadmap |
| `mod/` | Reserved for **verified** game-ready output | No completed release yet |

Important starting files:
- [Development roadmap](docs/roadmap.md)
- [Repository asset policy](docs/repository-layout.md)
- [Portrait manifest](historical_data/portrait_manifest.csv)
- [Reference/source register](reference/source_register.csv)
- [Scenario specification](docs/scenario-design.md)
- [Working-format status](docs/sav-format.md)

## Local testing (Python 3.10+)

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python scripts/parse_sav.py "maps/An American Civil War.sav" --len 64
```

The header dumper **only inspects bytes**. `scripts/generate_sav.py` does **not** generate playable maps, and the current validator cannot certify a .sav as game-loadable. Do not use their output as a playable scenario.

Next required evidence: a known-working **small map exported from the installed Hex of Steel editor**, the game's exact version, and a successful load/save/reload test. Keep proprietary game files out of public releases.

See [AGENTS.md](AGENTS.md) before editing.