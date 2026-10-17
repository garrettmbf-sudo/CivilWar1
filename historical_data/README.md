# Historical data — Shenandoah Valley, March–June 1862

- `portrait_manifest.csv`: current **repository filename audit**, preserving existing paths and spelling. `PRESENT` means file exists; existing likenesses were previously audited by the user. `MISSING` means no matching portrait file found on the checked branch.
- Portrait filenames are **immutable identifiers for the current asset pipeline**; rank and unit assignment are separate, time-dependent historical records.
- The roster includes field generals plus key colonels because every independently represented brigade requires a leader. `review` priority marks officers whose participation/assignment needs source validation, not a challenge to portrait identities.
- The next files should be `commanders_1862.csv`, `formations_1862.csv`, `assignments_1862.csv`, and `strength_returns_1862.csv`, each dated and sourced. **Do not populate made-up figures.**
- Avoid unit duplication during historical mergers, attachments, wounds and reassignments.

Run `python scripts/check_portrait_manifest.py` to verify file references and missing statuses.
## Source citation convention (all CSVs)

- Every row's `sources` column is **required** (enforced by `validate()` in `src/oob.py`).
- Format: pipe-separated tokens, each `SRCxxx` or `SRCxxx p.N` / `SRCxxx p.N-M`, optionally followed by a parenthetical qualifier, e.g. `SRC007|SRC009 p.664` or `SRC009 p.844 (S.O. 98, Apr 6)`.
- Every `SRCxxx` must exist in `sources_1862.csv`; page numbers refer to the edition/scan named in that source's `citation`.
- `SRC009`/`SRC010` pages (OR Ser. I Vol. 12 Pts. 1/3) were read from the running heads of the archive.org scans; a page that could not be confirmed is written `(OR page UNVERIFIED)` rather than guessed.
- `brigade_commands_1862.csv`: an empty `commander_id` is a **documented vacancy** and its `sources` must say so (contain "vacan..."), e.g. Frémont's "Unattached Cavalry" at Cross Keys (OR 12/1 p.664 names no commander).
- Counters (`counter=Y`) must have regiments and a command record on every active day; pre-existing gaps still under research are enumerated in `KNOWN_EMPTY_COUNTER_GAPS`.
