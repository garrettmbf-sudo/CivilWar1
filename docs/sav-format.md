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
