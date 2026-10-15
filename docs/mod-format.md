# Mod Format Notes

This file documents the structure we expect from Hex of Steel mods and how to package them for distribution.

Current assumptions
- The game loads custom content from a mod package.
- The final package should be zip-based for distribution.
- Game-ready content should live under `/mod`.
- We should use an intermediate JSON representation before exporting to `.sav`.

Likely package structure
- `/mod/metadata.json`
- `/mod/maps/`
- `/mod/scenarios/`
- `/mod/config/`
- `/mod/assets/`

Rules for packaging
- Keep data that is human-editable in JSON or YAML.
- Build a zip only after validation passes.
- Keep the artifact reproducible by writing a deterministic build script.

Unknowns
- The exact Hex of Steel mod loader format is not yet confirmed.
- We must validate against community mods or sample files before claiming compatibility.
