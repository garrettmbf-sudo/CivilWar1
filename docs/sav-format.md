# Reverse Engineering Notes

This document tracks discoveries about the Hex of Steel `.sav` file format.

Current status
- The binary file format is not public.
- We need sample `.sav` files to infer the layout.
- The first 64 bytes are the most important initial observation point.

What to record
- File size and endianness
- Magic bytes or header signatures
- Map dimension values
- Metadata offsets and any obvious strings
- Terrain or unit encoding patterns
- Differences between known map samples

Template for a new discovery
- Sample file: `samples/<name>.sav`
- Offset(s): `0xNN` or decimal offset
- Observation: what was found
- Interpretation: hypothesis about the field
- Evidence: related note or comparison

Current note
- This repo is intentionally in a discovery phase.
- The first task is to dump the first 64 bytes of a sample payload and record the observed layout before implementing broader parser logic.

## Discovery log

### 2026-10-15 — real HoS saves added (`maps/*.sav`)
- Sample files: `maps/Hexerreich - Classic 2ACW.sav`, `maps/TheWarOfTheRebellion.sav`
- Offset(s): `0x00`
- Observation: both begin `00 01 FF FF FF FF 01 ... F"Assembly-CSharp..."` — Unity
  **BinaryFormatter** (legacy .NET serialization), uncompressed. By contrast
  `An American Civil War.sav` / `Battle for USA.sav` start with high-entropy
  bytes (encrypted or compressed variant; needs separate treatment).
- Observation: GameData object graph exposes fields `SizeX`, `SizeY`,
  `TilesTable` (a `Dictionary<Tile,string>`), `listOfPlayers`, `gameSettings`;
  Tile records include `<Name>`, `<Type>`, `<Season>`, `<OwnerName>`,
  `<CityName>`.
- Interpretation: each tile's terrain is its **string Name**, not a numeric id.
- Evidence: tile-name frequency scan of the Hexerreich save (~2,700 tiles) shows
  the working vocabulary: Plain, Field, Rocky plain, HillForest, ThinForest1-3,
  ThickForest1-3, Mountain, Desert, Marsh, Big Lake, Village; named streams
  River + River1-23 (+ EndRiver1-6); road/rail overlays Road1-24, Railroad1-9,
  *Intersection, *Bridge, *BridgeRailroad, RailroadCross*, Coast/Harbour sets.
- Action taken: `src/map_generator.py` now emits per-tile HoS names via
  `HOS_TILE_NAMES` (South Fork=River1, North Fork=River2, main stem=River3,
  towns=Village, Pike=Road1) and adds Field / Rocky plain / ThickForest codes;
  renderer legend uses the HoS names. Next step: parse the BinaryFormatter
  object records properly to recover SizeX/SizeY and the tile grid order.
