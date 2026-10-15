# Map samples and verified map workflow

The repository already includes four external/working-reference `.sav` files:
- `An American Civil War.sav`
- `Battle for USA.sav`
- `Hexerreich - Classic 2ACW.sav`
- `TheWarOfTheRebellion.sav`

These are **inputs for inspection, not automatically compatible templates for game write-back**. Keep the originals untouched.

The existing `scripts/parse_sav.py` prints a hex header. A **successful format round-trip** still requires:
1. Export a tiny test map with known dimensions from the installed Hex of Steel editor.
2. Compare bytes and contents with another editor-generated map differing in exactly one known feature.
3. Document observed encoding (not guesses) in `docs/sav-format.md`.
4. Implement parsing and editing; preserve unrecognized sections.
5. Load the modified map inside Hex of Steel, save it again, and inspect differences.

Keep local large experiments in `maps/samples/` or `maps/generated/` (both ignored). Do not publish copyrighted sample files without authorization. Use `reference/` for historical geography.