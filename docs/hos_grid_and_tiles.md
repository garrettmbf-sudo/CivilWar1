# Hex of Steel grid vs custom tiles

## Verified
- Custom tiles are **2000×2000 PNG**, flat-top hex, **transparent outside** the hex (alpha mask from stock `Plain.png`).
- Filename = tile `Name`; folder `Graphics/Tiles/<Season>/` (official tutorial uses **Summer**; Winter also exists).
- Engine looks up art by **Name + Season**; missing graphic → black hex.
- Stock `maps/Plain.png` has **no dark hex outline stroke** — rim pixels are terrain color; shape is alpha.

## Grid overlay in-game
- Official manual keybindings list **map image overlay** controls (move/scale/opacity), not a hex-grid show/hide toggle.
- No documented “show hex grid” setting found in the manual excerpt or Steam discussions reviewed 2026-10-15.
- v5.3.0 “Borders” = **national/country borders**, not per-hex grid lines.
- “Show tile info” shows type/MP/coordinates — does not draw a grid.

## Implication
- **Do not bake grid lines into tile PNGs.** The playable grid is formed by tessellating hex sprites.
- Preview/cartography tools may draw a **separate adjustable grid layer** (default faint) for editing review only.
- If a future HoS build adds a hex-outline toggle, seamless tile art will still work; stroked tiles would double-line.

## Confidence
- Tile size/path/alpha: **High** (repo samples + official mod tutorial).
- No hex-grid toggle: **Medium–High** (manual + discussion search; not exhaustively tested in running game here).
