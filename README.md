# CivilWar1: Hex of Steel Shenandoah Valley Mod

This repository exists to support a large-scale American Civil War mod for Hex of Steel, centered on the Shenandoah Valley and campaigns of 1862 and 1864.

The project is intentionally structured for reverse engineering and incremental development:
- We do not assume the Hex of Steel `.sav` format is public or stable.
- We collect sample maps and use them to infer the binary format.
- We keep human-readable design documents and scenario plans in version control.
- We generate game-ready map data through an intermediate JSON format before exporting to `.sav`.

Repository layout
- /mod: game-ready mod files, packaging output, and materials intended for distribution
- /src: all tooling, parsers, generator utilities, and build scripts
- /docs: format notes, design docs, and scenario references
- /reference: historical notes, screenshots, and external references
- /samples: sample `.sav` files used for reverse engineering and testing only
- /tests: automated validation for parser and packaging scripts

Quick start
1. Install Python 3.10+.
2. Create a virtual environment.
3. Install dependencies: `pip install -r requirements.txt`
4. Run the parser on a sample file: `python src/sav_parser.py samples/sample_map.sav`
5. Build distributable mod package: `python src/build_mod.py --output dist/mod.zip`

Important rules
- Prefer Python tooling (`struct`, `numpy`, `pytest`).
- Use `snake_case` for file names and directories.
- Use intermediate JSON (for example `hexwright`) before exporting to `.sav`.
- Do not commit large binary files unless they are required for reverse engineering.
- Keep notes and discoveries in `/docs` and historical materials in `/reference`.

This README is the main entry point for contributors. See AGENTS.md for repo-specific operating rules.
