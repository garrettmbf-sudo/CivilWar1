# Mod structure for Hex of Steel — recommended layout

This document sketches a stable on-disk layout for the mod. The goal is that the `mod/` subdirectory can be zipped or copied into the game's mod folder and be recognized by the game (adjust as we discover exact game mod layout requirements).

Suggested layout:

mod/
  assets/            # optional artwork, sound — keep game-specific names
  maps/              # generated .sav files and map metadata (for distribution)
  rules/             # unit definitions and balancing files
  scenarios/         # scenario description files that the game loads
  metadata.json      # mod name, author, version, supported game versions

Note: We will refine this to match Hex of Steel's expected mod packaging after inspecting shipped mods or the game's mod loader.
