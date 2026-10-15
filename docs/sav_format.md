# Reverse-engineering Hex of Steel .sav format

This is a living document. Add sample `.sav` files to `maps/samples/` (they are gitignored by default) and record differences here.

Sections to fill as we work:
- File header layout and magic bytes
- Endianness and integer sizes
- Map metadata (width, height, scale, name)
- Terrain tile encoding
- Unit placement and unit record layout
- Scenario-turn metadata

First actionable steps
1. Collect example `.sav` files exported from Hex of Steel (small maps too). Put them in `maps/samples/`.
2. Run `scripts/parse_sav.py` to dump header bytes and help detect patterns.
3. Update this document with discovered offsets and field decodings.
