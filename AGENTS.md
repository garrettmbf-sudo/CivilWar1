# AGENTS.md

This file defines the working conventions for this repository. It should be treated as the operating manual for both human contributors and AI assistants.

Mission
- Reverse-engineer the Hex of Steel `.sav` map format using sample files.
- Build Python tooling to inspect, parse, validate, and generate map data.
- Produce a structured mod package under `/mod`.
- Document the binary format, unit roster, and campaign design in `/docs`.

Operating rules
1. Read `AGENTS.md` and `README.md` before proposing repo changes.
2. If the exact Hex of Steel mod format is unknown, say so explicitly and propose a reverse-engineering plan using sample files.
3. When requesting or writing code, outline a short plan first, then add code with comments and tests.
4. Prefer Python for tooling and use `struct`, `numpy`, and `pytest` where appropriate.
5. Use an intermediate JSON representation before exporting any generated map data to `.sav`.
6. Keep all game-ready files inside `/mod`. Keep all tooling inside `/src`.
7. Store historical references under `/reference` and format notes under `/docs`.
8. Use `snake_case` for all files and directories.
9. Prefix map artifacts with `map_` and scenario artifacts with `scenario_`.
10. Never commit large binaries unless they are needed as sample `.sav` files for reverse-engineering.
11. Preserve the distinction between working tooling and distribution-ready content.

Repository structure
- `/mod` — build-ready mod package, map export area, or final zip payload
- `/src` — parser, generator, validation, and utility code
- `/docs` — binary format notes, mod layout, units, and scenario design
- `/reference` — screenshots, historical references, notes, and community references
- `/samples` — sample `.sav` files used for reverse engineering only
- `/tests` — automated tests for parsing and packaging

Naming conventions
- Map files: `map_<campaign>_<year>.sav` or `map_<region>_<variant>.json`
- Scenario files: `scenario_<campaign>_<year>.json`
- Python modules: `snake_case.py`
- Tests: `test_<feature>.py`

Reverse-engineering workflow
1. Collect sample `.sav` files into `/samples`.
2. Use a simple parser to dump the first 64 bytes and identify signatures, dimensions, and metadata layout.
3. Compare multiple samples with different dimensions and terrain to infer field offsets.
4. Document each discovery in `/docs/sav-format.md`.
5. Implement a corresponding parser in `/src` and validate with sample data.
6. Move from inferred file structure to a stable intermediate JSON format.
7. Export to `.sav` only when the format is well understood.

Contribution expectations
- Keep notes small, concrete, and evidence-based.
- Record the exact file, byte offset, and observed pattern when documenting a discovery.
- Prefer reproducible tests over undocumented assumptions.
- Propose a reverse-engineering plan before claiming a format is understood.

Current initial tasks
- Draft a complete AGENTS.md and repo rules.
- Create parsers for the first 64 bytes of `.sav` files.
- Build a basic hex grid utility for neighbors and distance.
- Package `/mod` into a zip with `build_mod.py`.

This file should be updated as new discoveries change the repo’s assumptions.
