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

## Opening OOB and arrival schedule

- Campaign opening date is **1862-03-22** (dawn, the day before Kernstown; user decision 2026-10-17), `OPENING_DATE` in `src/oob.py`. The opening counters cite the OR Kernstown casualty returns: Confederate SRC009 p.384 (Ashby p.385-386), Union SRC009 p.346-347.
- `reinforcements_1862.csv` is the arrival/entry schedule. Columns: `event_id,date,event_type,subject_id,detail,effect,sources,location,covers,date_certainty`.
  - `covers`: pipe-separated formation IDs that enter with this event.
  - `date_certainty`: `confirmed` (OR states the date), `approximate` (OR brackets it, or the repo's modelling date differs), or `unverified` (no OR page found yet).
  - `modelled_entry` rows mark formations that were already in theatre but that the database models only from a later date. They are not historical arrivals.
- `arrival_schedule_errors()` (part of `validate()`) requires that every formation active after the opening is covered by an event, that every event has a location and certainty, and that confirmed/approximate events carry a `SRCxxx p.N` page.
