# Hex of Steel .sav file format — evidence log

**Status: UNVERIFIED for reliable writing and round-tripping.** No published signature, header layout or game-compatible generator has been confirmed in this repository.

Sample files available under `maps/`: `An American Civil War.sav`, `Battle for USA.sav`, `Hexerreich - Classic 2ACW.sav`, `TheWarOfTheRebellion.sav`.

The former `HSAV` magic bytes in `scripts/generate_sav.py` were invented for a placeholder, **not a genuine demonstrated .sav header**. They must never be used to claim compatibility.

## Verification protocol
1. Export two small .sav maps directly from Hex of Steel, changing only one terrain hex between exports.
2. Inspect bytes; determine whether data is textual, binary, compressed, or wrapped.
3. Compare known fields (map size, coordinates, terrain, roads, units, metadata) and document offsets/schemas **with reproducible evidence**.
4. Write a conservative patcher that round-trips original content while preserving unknown fields.
5. Re-import into the **same game build**, save and verify gameplay.

## Record template
- Game version and export method:
- Sample path:
- Observed bytes/offsets:
- Interpretation (confirmed or hypothesis):
- Controlled-difference evidence:
- In-game round-trip result:

`scripts/parse_sav.py` and `src/sav_parser.py` are **read-only header inspection tools**. Until verification, `scripts/generate_sav.py` refuses output and `scripts/validate_sav.py` cannot give a "playable" pass.