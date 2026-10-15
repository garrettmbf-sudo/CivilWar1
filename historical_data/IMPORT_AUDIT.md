# Recovered 1862 Valley OOB — audit status

Source: user-provided `workspace.tar`, Git commit `d0670cd65717e3da5aefb078c103041ceb358a65` authored by qwen.ai[bot].

**Status:** Recovered research data, **not yet a game-compatible Hex of Steel army package.**

Nine historical CSV tables and `src/oob.py` were imported from the archived Git commit. The archived `portrait_manifest.csv` was deliberately **not** imported: the canonical manifest on `main` has already been approved by the user, with exact existing asset paths and a different schema. No portrait files were changed.

Locally verified after applying these files to current `main`:
- `python src/oob.py`: validation OK; 50 formations, 96 regiments, 45 commanders, 34 batteries.
- Historical snapshots: March 23 (8 counters / 3 HQ); May 8 (11/7); May 25 (18/9); June 9 (27/10).
- Eight local Python tests passed, including `tests/test_oob_1862.py` and the portrait-manifest and hex-grid tests.

**Known open defects**, not fixed in this preservation/import PR:
1. March brigades under `FRM_CS_JACKSONDIV` refer to an HQ active only from May 20 onward; some Union parent HQs similarly inactive at certain snapshot dates. The existing validator does not test active parentage.
2. Some date snapshots contain counters missing a current commander or regimental membership. Needs manual reconciliation.
3. Detachment flags allow concurrent regimental assignment but do not quantify manpower split.
4. Research source CSV records many provisional citations; historical manpower/command assignments require documentary corroboration.
5. No verified native Hex of Steel field mapping, unit conversion, game save/load roundtrip, or playable scenario.

Next: add tests asserting that each counter's parent HQ is active at the snapshot date; implement dated formation-parent assignments, source-backed detachments, and game schema integration. Keep this recovery import separate from the large map work.