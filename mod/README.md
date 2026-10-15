# Mod packaging

Place game-ready files under `mod/` using the structure described in docs/mod_structure.md. Example:

mod/
  metadata.json
  maps/
  scenarios/
  rules/

Do not commit generated .sav files to the mod/ directory in the repo root; instead, generate them in maps/generated/ then copy the target files into mod/maps/ for packaging releases.
