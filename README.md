# CivilWar1 — Hex of Steel American Civil War Mod

This repository is the working home for a large-scale American Civil War mod for Hex of Steel.

Goals
- Provide tooling to reverse-engineer and generate Hex of Steel `.sav` map files.
- Provide documentation for the `.sav` format, mod structure, unit stats, and scenarios.
- Store mod files in a game-loadable format and make it easy for humans and AI to contribute.

Repository layout (high-level)
- docs/             — Design notes, format docs, and contributor guides
- scripts/          — Python tools to parse/generate/validate .sav files
- units/            — Unit definitions (YAML) and stats
- maps/             — Map templates, sample maps, and generated .sav outputs (gitignored large binaries)
- scenarios/        — Scenario definitions for 1862 and 1864 campaigns
- mod/              — Game-ready mod package layout (assets, rules, scenarios)

Start here:
- docs/README.md — onboarding and next steps for adding sample .sav files for reverse engineering.

