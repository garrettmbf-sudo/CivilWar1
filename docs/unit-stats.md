# Unit Stats

Starting point for Civil War unit data for the mod. **Engine facts are in
[hos-unit-mechanics.md](hos-unit-mechanics.md); this file must not assume fields
Hex of Steel does not have.**

Corrections (verified against the official HoS manual, see hos-unit-mechanics.md):
- **Morale is not a per-unit stat field.** It is an *optional global setting*; when on, each unit carries a dynamic morale level (Excellent/Good/Average/Bad/Awful = +10/+5/0/-5/-10% damage) changed by combat results, VP gains/losses and manpower resupply. You cannot author a "morale: 60" value per unit type.
- **There are no formation modes** (line/column/square, etc.) in the engine. Do not design around them.
- Editable per-unit stats are: soft/hard/air damage, armor, HP, attack range, visibility, ammunition, fuel, movement points, cost, plus flags/specializations exposed in the in-game Unit Editor.

Focus areas
- Unit type: infantry, cavalry, artillery, commander (HoS "Commander" class)
- Soft/hard/air damage, armor, HP, movement points, fuel, ammo, range, visibility
- Weapon type -> soft-damage/range balancing
- Historical notes and campaign-era relevance

Example entry (values are placeholders, not verified balance)
- `union_infantry_brigade`
  - faction: Union
  - class: infantry
  - soft_damage / hard_damage / air_damage: TBD / TBD / 0
  - hp: TBD (strength conversion unverified, see SRC008)
  - movement_points: TBD, range: 1, visibility: 1
  - weapon: rifled musket (flavour; no engine weapon field verified)
