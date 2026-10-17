# Merge plan (2026-10-17 ET)

Only the user merges or closes anything. Conflicts below come from simulating the merges, in this order, in a scratch worktree of `main`.

## Ordered merge plan
| Step | PR | Branch → base | Lane | Status |
| --- | --- | --- | --- | --- |
| 1 | #11 | data/oob-fixes-citations → main | units | merges clean |
| 2 | #12 | data/opening-oob-arrivals → #11 | units | clean after #11 |
| 3 | #13 | history/veterancy-command-ratings → #12 | history | clean |
| 4 | #14 | data/hos-stats → #13 | units | clean |
| 5 | #15 | history/campaign-start-oob → #12 (sibling of #13) | history | **conflict** in `historical_data/sources_1862.csv` after #13/#14. Archivist merges main into the branch and resolves it. |
| 6 | #17 | data/opening-0322 → #15 | units | **conflicts** in `artillery_1862.csv`, `assignments_1862.csv`, `brigade_commands_1862.csv`, `commanders_1862.csv`, `sources_1862.csv` (including the predicted Crutchfield line vs #14). Quartermaster resolves after #15. |
| 7 | #9 | reorg/valley-campaign-layout → main | repo | clean |
| 8 | #16 | history/verify-pr10-map-data → #10 | history | **conflict** with the #10 fixes (96c8a0b) in `sources_1862.csv` and `tools/powershell/valley_map_data.ps1`. Archivist resolves; user merges into #10. |
| 9 | #10 | map/valley-tile-plan → #9 | map | draft; the user marks it ready, then merges after #9 |
| 10 | #18 | mod/facing → main | engine | clean; needs the in-game test before merge |
| 11 | #19 | repo/workflow → main | repo | clean |

When a base PR merges, retarget its stacked PRs to `main` (GitHub does this automatically if the base branch is deleted; otherwise run `gh pr edit N --base main`).

## Close as superseded (user decides)
- **#5**: fully contained in #6 (`git merge-base --is-ancestor` true).
- **#1, #7, #8**: old drafts that use other hex layouts; replaced by #9/#10.
- **#6**: old v4 playtest map on the old layout, stacked on #5. Likely superseded by #10; needs the user's call.

## Branches already fully in main (user may delete)
- chore/import-valley-map-tooling
- chore/organize-valley-1862
- cleanup/move-non-units-pngs
- compare/grok-valley-artwork-20261015
- feat/recover-1862-historical-armies-oob

## Leave as-is (Hotchkiss, no PRs)
- kernstown-map
- art/kernstown-miniatures-zoom-review
- counters/kernstown-four-design-comparison

## Status after the merge run (2026-10-17 ET)
- **Merged into main:** #11, #12, #13, #14, #9, #20 (Harmony DLLs removed), then this PR (#19, squash). **#16** merged into #10's branch.
- **Closed (superseded):** #1, #5, #6, #7, #8. **Deleted branches:** the five listed above.
- **Blocked on Captain Archivist:**
  - **#15:** conflict with main in `historical_data/sources_1862.csv`.
  - **#10:** conflict with main in `historical_data/sources_1862.csv`; the map's SRC020-030 rows vs main's SRC009/010/050-055 (SRC021/022 and SRC009/010 cite the same OR volumes).
- **Blocked behind #15:** **#17** (Quartermaster resolves the unit and OOB CSV conflicts once #15 lands).
- **Waiting for the user's in-game test:** #18.
