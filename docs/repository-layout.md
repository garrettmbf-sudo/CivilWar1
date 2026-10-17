# Repository organization and safe migration plan

**Status:** organizational layout documented, **no bulk asset move**. Many game files, portrait assets and scenario paths may refer to existing locations.

## Current inventory (October 14, 2026)
- Large legacy asset collection at repository root: `mdl_CSA_*.png`, `Unit_*.png`, and other artwork.
- Additional portrait assets under `reference/`, including existing Union portraits and `reference/mdl_CSA_JAWalker.png`.
- Four .sav map samples under `maps/`: `An American Civil War.sav`, `Battle for USA.sav`, `Hexerreich - Classic 2ACW.sav`, `TheWarOfTheRebellion.sav`.
- Historical reference images `reference/Stonewall in the ValleyMap.jpg` and `reference/SJW IIMap.jpg`.
- `docs/3574617535/` contains mod/Harmony examples and binary libraries; do not assume redistribution rights.
- Python tooling under `src/` and `scripts/`; tests under `tests/`; draft scenarios under `scenarios/`.

## Canonical ownership going forward
| Path | Meaning | Rule |
| --- | --- | --- |
| Root game-named image assets | Existing historically audited or game-named inputs | **Do not move/rename in phase 1** |
| `reference/` | Non-release references and known existing portrait files | Record provenance, not auto-distribute |
| `historical_data/` | Portrait inventory, future dated formations, commanders, OOB | CSV/YAML/JSON with explicit IDs |
| `maps/` | Existing map samples and map pipeline documentation | Retain sample originals |
| `scenarios/valley_campaign_1862/` | Primary scenario (full Valley campaign); per-battle folders beside it, see `scenarios/README.md` | Keep historical dates and links |
| `mod/` | Verified release-ready resources only | No untested placeholders |
| `docs/` | Design, format notes, workflow and audit trail | Separate facts from hypotheses |
| `src/`, `scripts/`, `tests/` | Reusable code, command-line tools, and tests | Tests for each behavioral change |

## Before any future physical migration
1. Audit every reference to the old path in scenario, metadata, UI, and mod loader.
2. Prepare an explicit old→new manifest; preserve exact basename and user-approved identity.
3. Test a complete mod load and portrait selection against the changed paths.
4. Commit the migration separately with clear rollback notes.
5. Do not remove originals before verifying that the installed game no longer requires them.

Existing duplicate format notes are preserved as compatibility pointers rather than deleted.