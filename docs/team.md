# Team: lanes, branches, stacking, reviews

All four bots push as `garrettmbf-sudo`; the user (repo owner) is the only merger. Times are **ET**.

## Lanes
| Lane | Bot | Owns | Label |
| --- | --- | --- | --- |
| Coordination, repo, engine | **General Eggbot** | CI, `.github/`, `docs/team.md`, `docs/decisions.md`, repo layout, engine research (`docs/hos-modding-notes.md`, `docs/engine-evaluation.md`), Harmony mods in `mods/` (e.g. `mods/facing`) | `lane:repo`, `lane:engine` |
| Map and art | **Major Hotchkiss** | `maps/`, map build plan and tooling (`scripts/valley_*`, `tools/powershell/valley_map_data.ps1`), tiles, previews, `scenarios/*/data/` map CSVs, **Kernstown** and the `kernstown-map` branch | `lane:map` |
| Units | **Colonel Quartermaster** | `historical_data/` OOB tables, `src/oob.py`, unit stats, counters and sprites | `lane:units` |
| History | **Captain Archivist** | `docs/history/`, `historical_data/sources_1862.csv`, citations and fact checks across lanes | `lane:history` |

## Branch naming
`lane/short-name`, using these prefixes:
- `map/` (Hotchkiss)
- `data/` or `units/` (Quartermaster)
- `history/` (Archivist)
- `mod/` or `engine/` (Eggbot engine work)
- `repo/` (Eggbot repo work)

Examples: `map/valley-tile-plan`, `history/verify-pr10-map-data`, `mod/facing`. One topic per branch. Never commit to `main`, never force-push, never delete branches; only the user merges or closes.

## Stacking rules
1. **Base choice:** a PR that needs unmerged work is opened **against that PR's branch**, not `main`. Label it `status:stacked` and write "Stacked on #NN" as the first line.
2. **Merge order:** the base merges first. After it merges, GitHub retargets the stacked PR to `main`; the owner then fixes any conflicts on their own branch (merge, not rebase, so nobody force-pushes).
3. **Depth:** keep stacks short (≤3). If two lanes stack on the same base (e.g. #13 and #15 on #12), each owner resolves the shared-file conflicts (usually `historical_data/sources_1862.csv`) when the first one lands.
4. **Cross-lane fixes:** a bot that finds an error in another lane's files opens a PR **into that lane's branch** (as #16 did into #10) and doesn't merge it; the owning bot folds it in.
5. **Kernstown:** `kernstown-map` and Kernstown files are Hotchkiss-only. Other lanes read them; they don't edit them.

## Reviews
| Change touches | Reviewer |
| --- | --- |
| Map shape, passes, roads, tiles, Kernstown | Hotchkiss (+ Archivist for coordinates/names) |
| OOB, strengths, dates, unit stats | Quartermaster (+ Archivist for citations) |
| Any historical claim, coordinate, 1862 name | Archivist |
| CI, repo layout, Harmony mods, engine docs | Eggbot |
| Decisions in `docs/decisions.md`, merges, closes | **the user** |

Labels: `status:needs-user` (waiting on a user decision), `status:needs-ingame-test` (only Hex of Steel can prove it), `status:blocked` (conflict or dependency), `status:stacked`.

## CI
`.github/workflows/ci.yml` runs on every push and PR (Linux): `pytest`, `python src/oob.py` (OOB validation), `python scripts/check_portrait_manifest.py`. PowerShell tooling isn't run in CI. A red CI blocks merge once branch protection is on.
