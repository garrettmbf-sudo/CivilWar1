# Historical data — Shenandoah Valley, March–June 1862

- `portrait_manifest.csv`: current **repository filename audit**, preserving existing paths and spelling. `PRESENT` means file exists; existing likenesses were previously audited by the user. `MISSING` means no matching portrait file found on the checked branch.
- Portrait filenames are **immutable identifiers for the current asset pipeline**; rank and unit assignment are separate, time-dependent historical records.
- The roster includes field generals plus key colonels because every independently represented brigade requires a leader. `review` priority marks officers whose participation/assignment needs source validation, not a challenge to portrait identities.
- The next files should be `commanders_1862.csv`, `formations_1862.csv`, `assignments_1862.csv`, and `strength_returns_1862.csv`, each dated and sourced. **Do not populate made-up figures.**
- Avoid unit duplication during historical mergers, attachments, wounds and reassignments.

Run `python scripts/check_portrait_manifest.py` to verify file references and missing statuses.