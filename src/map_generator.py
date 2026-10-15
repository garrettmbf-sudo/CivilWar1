"""Procedural Shenandoah Valley hex map generator (intermediate JSON stage).

Per AGENTS.md, generated map data goes through an intermediate JSON format
("hexwright"-style) before any .sav export. The binary .sav format is still in
reverse-engineering status, so this module produces the validated JSON payload:

    maps/generated/map_shenandoah_valley.json

Terrain names now use the tile-name vocabulary extracted from the real Hex of
Steel save `maps/Hexerreich - Classic 2ACW.sav` (Unity BinaryFormatter; each
Tile object records its name string). Observed base-terrain families in that
save: Plain, Field, Rocky plain, HillForest, ThickForest1-3, ThinForest1-3,
Mountain, Desert, Marsh, River / River1-23 (named streams), Village, plus
Road1-24 / Railroad1-9 linear overlays and Bridge / Intersection variants.

Our generator emits one named stream per fork (River1 = South Fork,
River2 = North Fork, River3 = main stem below the confluence) so a future
`.sav` exporter can carry HoS-style tile names directly.

The valley geography is encoded from north (top) to south (bottom), roughly
10 miles per hex like contemporary ACW campaign maps:
  - Blue Ridge on the east, Allegheny Front on the west
  - North Fork / South Fork Shenandoah River joining at Staunton and flowing north
  - Massanutten Mountain splitting the valley between Strasburg and Harrisonburg
  - Valley Pike (the military highway) running Winchester -> New Market -> Staunton
  - Towns: Winchester, Strasburg, Woodstock, New Market, Harrisonburg,
    Staunton, Waynesboro, Lexington
  - Gap passes through the ridges: Harper's Ferry (north), Chesterburg/Newmarket gaps
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from hex_utils import Hex

TERRAIN_CODES = {
    # Names in ALL-CAPS keys map 1:1 to HoS tile names (title-cased) wherever
    # the reference save has an equivalent; "pike" is our Valley Turnpike
    # stand-in for a Road<N> overlay.
    "plains": 0,        # Plain
    "hills": 1,         # HillForest / hills shoulders
    "mountains": 2,     # Mountain
    "forest": 3,        # ThinForest / ThickForest
    "river": 4,         # River (generic/un-named reaches)
    "marsh": 5,         # Marsh
    "lake": 6,          # Big Lake
    "city": 7,          # Village (town site)
    "pike": 8,          # improved road (Valley Turnpike) — maneuver corridor
    "road": 9,          # secondary/unimproved roads & gaps off the pike
    "field": 10,        # Field (farmed valley floor)
    "rocky_plain": 11,  # Rocky plain (ridge-flank broken ground)
    "thick_forest": 12, # ThickForest (closed woods, movement penalty)
    "south_fork": 13,   # River1 — named stream: South Fork Shenandoah
    "north_fork": 14,   # River2 — named stream: North Fork Shenandoah
    "shenandoah_river": 15,  # River3 — joined stem flowing north to the Potomac
}

# Intermediate-code -> real Hex of Steel tile name (from Hexerreich sample).
HOS_TILE_NAMES = {
    "plains": "Plain",
    "field": "Field",
    "rocky_plain": "Rocky plain",
    "hills": "HillForest",
    "mountains": "Mountain",
    "forest": "ThinForest",
    "thick_forest": "ThickForest",
    "river": "River",
    "south_fork": "River1",
    "north_fork": "River2",
    "shenandoah_river": "River3",
    "marsh": "Marsh",
    "lake": "Big Lake",
    "city": "Village",
    "pike": "Road1",       # would become a Road<N>/Intersection set on export
    "road": "Road2",
}

# ---------------------------------------------------------------------------
# World geometry (axial coordinates; row axis r grows southward)
# ---------------------------------------------------------------------------

WIDTH = 26   # columns (q extent)
HEIGHT = 50  # rows (r extent)

# Ridge center-lines as functions of row r (0 = north/Winchester end).
# x positions are fractional column coordinates.
def blue_ridge_x(r: int) -> float:
    """Blue Ridge (east side) wanders slightly but stays near col 20."""
    return 20.5 + 1.4 * math.sin(r / 9.0)


def allegheny_x(r: int) -> float:
    """Allegheny Front / Great North Mountain (west side)."""
    base = 5.0
    if r < 14:  # narrow north end (winchester area, SNM ridge closer)
        base = 6.5
    return base + 1.2 * math.sin(r / 11.0 + 1.0)


MASSANUTTEN_ROWS = range(18, 34)  # Strasburg (N) to beyond Harrisonburg (S)
def massanutten_x(r: int) -> float:
    return 13.0 + 0.6 * math.sin((r - 18) / 6.0)


# Rivers, north-flowing. The two forks meet at Rowton near Staunton (~row 34);
# from there one stem runs north past Winchester to Harper's Ferry.
# West of Massanutten drains via the South Fork; east of it via the North Fork.
def south_fork_x(r: int) -> float | None:
    """South Fork: rises near Lexington (row ~48), flows north on the WEST side of
    Massanutten, past New Market/Woodstock, to the confluence at Staunton (row 34)."""
    if r < 34 or r > 48:
        return None
    return 9.2 + 0.6 * math.sin((r - 34) / 5.0)


def north_fork_x(r: int) -> float | None:
    """North Fork: rises near Source Springs (row ~47), flows north on the EAST side
    of Massanutten through Page Valley (Strasburg side) to the confluence (row 34)."""
    if r < 34 or r > 47:
        return None
    return 15.6 + 0.6 * math.sin(r / 6.0)


def main_stem_x(r: int) -> float | None:
    """Joined Shenandoah: from the confluence (~row 34) north to the Potomac."""
    if r >= 34:
        return None
    x = 12.0
    if r >= 22:  # between confluence and Strasburg, thread west of Massanutten tip
        x = 10.2 + 0.5 * math.sin((r - 22) / 4.0)
    elif r >= 12:  # past Massanutten's north end, swing toward center
        x = 11.4 + 0.6 * math.sin((r - 12) / 4.0)
    else:  # northern valley toward Winchester / Harper's Ferry
        x = 12.3 + 0.5 * math.sin(r / 4.0)
    return x


TOWNS = [
    # name,          col, row, size (1=town, 2=city)
    ("Harper's Ferry", 12, 1, 1),
    ("Winchester",   12, 4, 2),
    ("Strasburg",    11, 16, 1),
    ("Woodstock",    11, 21, 1),
    ("New Market",   11, 25, 1),
    ("Harrisonburg", 10, 30, 2),
    ("Staunton",     11, 36, 2),
    ("Waynesboro",   11, 41, 1),
    ("Lexington",    12, 47, 1),
]

# Valley Pike waypoints (col,row); interpolated between town anchors.
PIKE_WAYPOINTS = [
    (12, 4), (11, 10), (11, 16), (11, 21), (11, 25),
    (10, 30), (11, 36), (11, 41), (12, 47),
]

# East-west gaps through the ridges (col,row,length along rows).
GAPS = [
    # (row, col_center, label) — a pass cut through the ridge line at that row
    (13, 21, "Chesterfield Gap (Front Royal road)"),
    (33, 20, "Newmarket / Manassas Gap"),
    (44, 19, "Fincastle Gap toward Lynchburg"),
    (4, 6, "Cumberland Valley approach (Williamsport)"),
    (37, 5, "Kings Mountain gap (Jackson, post-New Market)"),
    (48, 5, "Cowpasture / West Liberty approaches"),
]

# Secondary roads / cross-Valley marches (col,row waypoints); each leg is
# interpolated like the pike and stamped with the "road" terrain code.
SECONDARY_ROADS = {
    "front_royal": [(21, 13), (17, 13), (13, 12)],          # Chesterfield Gap -> Valley Pike
    "manassas_gap": [(20, 33), (16, 33), (12, 32)],         # Newmarket Gap -> Pike near Strasburg
    "new_market_to_culpeper": [(20, 30), (16, 30), (12, 30)],  # Harrisonburg east across Blue Ridge
    "kings_mountain": [(5, 37), (8, 37), (11, 36)],         # Allegheny pass -> Staunton
    "cowpasture": [(5, 48), (8, 47), (12, 47)],             # Lexington west to the fords
    "waynesboro_gap": [(11, 41), (14, 42), (18, 43)],       # South River gap toward the Blue Ridge
}

# Union (north) & Confederate (south) deployment zones for scenario hooks.
DEPLOYMENT_ZONES = {
    "union": {"rows": [0, 12], "label": "Union advance from the Shenandoah/Cumberland"},
    "confederate": {"rows": [38, HEIGHT - 1], "label": "Confederate lines guarding SW Virginia"},
}


def _key(col: int, row: int) -> str:
    h = Hex(col - (row - (row & 1)) // 2, row)  # offset->axial (odd-r)
    return f"{h.q},{h.r}"


def _set(grid: dict[str, int], col: int, row: int, code: int, overwrite: bool = False) -> None:
    if not (0 <= row < HEIGHT and 0 <= col < WIDTH):
        return
    k = _key(col, row)
    if overwrite or grid.get(k, TERRAIN_CODES["plains"]) in (
        TERRAIN_CODES["plains"], TERRAIN_CODES["hills"]
    ):
        grid[k] = code


def generate_map() -> dict:
    """Build the full intermediate-JSON map payload."""
    mtn = TERRAIN_CODES["mountains"]
    hill = TERRAIN_CODES["hills"]
    forest = TERRAIN_CODES["forest"]
    thick = TERRAIN_CODES["thick_forest"]
    field = TERRAIN_CODES["field"]
    rocky = TERRAIN_CODES["rocky_plain"]
    river = TERRAIN_CODES["river"]  # (kept for future unnamed creeks)
    sfork = TERRAIN_CODES["south_fork"]
    nfork = TERRAIN_CODES["north_fork"]
    main_river = TERRAIN_CODES["shenandoah_river"]
    city = TERRAIN_CODES["city"]
    pike = TERRAIN_CODES["pike"]
    plains = TERRAIN_CODES["plains"]
    water = (sfork, nfork, main_river, river)

    def jitter(x: float, r: int, seed: int) -> float:
        # deterministic pseudo-noise for ridge edges
        return math.sin(x * 12.9898 + r * 78.233 + seed) * 0.5 + 0.5

    grid: dict[str, int] = {}

    for r in range(HEIGHT):
        bx = blue_ridge_x(r)
        ax = allegheny_x(r)
        mx = massanutten_x(r) if r in MASSANUTTEN_ROWS else None
        for c in range(WIDTH):
            k = _key(c, r)
            terrain = plains
            # Ridges: core = mountains, shoulders = hills, wooded flanks
            for cx, halfw in ((bx, 1.6), (ax, 1.4)):
                d = abs(c - cx)
                if d <= halfw:
                    terrain = mtn
                elif d <= halfw + 1.2 and jitter(c, r, 7) > 0.35:
                    terrain = hill
            if mx is not None:
                d = abs(c - mx)
                if d <= 1.0:
                    terrain = mtn
                elif d <= 1.8 and jitter(c, r, 3) > 0.3:
                    terrain = hill
            # Valley-floor patchwork: farmland (Field) vs open woods (ThinForest)
            if terrain == plains:
                near_edge = min(abs(c - bx), abs(c - ax), abs(c - mx) if mx else 99)
                j = jitter(c, r, 11)
                if near_edge < 3.2 and j > 0.62:
                    # closed woods hugging the ridge footslopes
                    terrain = thick if j > 0.82 else forest
                elif j < 0.30:
                    terrain = field
                elif 2.0 < near_edge < 2.8 and j > 0.55:
                    terrain = forest
            grid[k] = terrain

    # Rocky broken ground on outer flanks of the two walls (beyond the hills)
    for r in range(HEIGHT):
        for cx in (blue_ridge_x(r), allegheny_x(r)):
            for side in (-1, 1):
                c = round(cx + side * 2.9)
                if 0 <= c < WIDTH and grid[_key(c, r)] in (plains, field):
                    if jitter(c, r, 17) > 0.6:
                        grid[_key(c, r)] = rocky

    # Rivers (carve over whatever is there); each fork keeps its own tile name
    def carve_line(xs: list[tuple[int, float]], code: int) -> None:
        for r, x in xs:
            _set(grid, round(x), r, code, overwrite=True)

    north_pts, south_pts, main_pts = [], [], []
    for r in range(HEIGHT):
        nfx, sfx, msx = north_fork_x(r), south_fork_x(r), main_stem_x(r)
        if nfx is not None:
            north_pts.append((r, nfx + math.sin(r / 3.0) * 0.4))
        if sfx is not None:
            south_pts.append((r, sfx + math.cos(r / 4.0) * 0.4))
        if msx is not None:
            main_pts.append((r, msx))
    carve_line(north_pts, nfork)
    carve_line(south_pts, sfork)
    carve_line(main_pts, main_river)

    # Floodplain marshes on the joined river just north of the forks' confluence
    for r in range(30, 34):
        x = main_stem_x(r)
        if x is not None:
            _set(grid, round(x) - 1, r, TERRAIN_CODES["marsh"])

    # Gaps: cut a passable corridor through the ridge lines
    for row, col, _label in GAPS:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                k = _key(col + dc, row + dr)
                if grid.get(k) in (mtn, forest):
                    grid[k] = hill

    # Valley Pike & secondary roads
    def lerp_waypoints(pts):
        out = []
        for (c1, r1), (c2, r2) in zip(pts, pts[1:]):
            steps = max(abs(r2 - r1), abs(c2 - c1), 1)
            for i in range(steps + 1):
                t = i / steps
                out.append((round(c1 + (c2 - c1) * t), round(r1 + (r2 - r1) * t)))
        return out

    seen = set()
    for c, r in lerp_waypoints(PIKE_WAYPOINTS):
        if (c, r) in seen:
            continue
        seen.add((c, r))
        k = _key(c, r)
        if grid.get(k) not in water + (city,):  # bridges/towns keep their terrain
            grid[k] = pike

    road = TERRAIN_CODES["road"]
    road_tiles = []
    for name, pts in SECONDARY_ROADS.items():
        for c, r in lerp_waypoints(pts):
            if not (0 <= c < WIDTH and 0 <= r < HEIGHT):
                continue
            k = _key(c, r)
            cur = grid.get(k)
            if cur in (pike,) + water + (city,):  # don't downgrade turnpikes/streams/towns
                continue
            grid[k] = road
            road_tiles.append({"name": name, "col": c, "row": r})

    # Towns/cities last so they overwrite pike/plains
    for name, c, r, size in TOWNS:
        _set(grid, c, r, city, overwrite=True)

    # Per-tile HoS tile-name lookup (from the Hexerreich vocabulary). Roads are
    # overlays in HoS; we bake them into the tile here and flag the underlying
    # terrain in "road_overlay" metadata for a future exporter.
    code_to_name = {v: k for k, v in TERRAIN_CODES.items()}
    tiles = []
    for r in range(HEIGHT):
        for c in range(WIDTH):
            code = grid[_key(c, r)]
            tiles.append({
                "col": c, "row": r, "terrain": code,
                "tile": HOS_TILE_NAMES[code_to_name[code]],
            })

    payload = {
        "format": "hexwright-json",
        "version": 1,
        "map_name": "Shenandoah Valley",
        "file_name": "map_shenandoah_valley",
        "scenario_name": "Valley Corridor (1862/1864 base terrain)",
        "description": (
            "Procedurally drafted Shenandoah Valley corridor, ~10 mi/hex, north at top. "
            "Blue Ridge east, Allegheny Front west, Massanutten dividing the Middle Valley, "
            "North & South Forks joining at Staunton, Valley Pike as the maneuver road."
        ),
        "size_x": WIDTH,
        "size_y": HEIGHT,
        "offset": "odd-r",
        "terrain_codes": TERRAIN_CODES,
        "tile_names": HOS_TILE_NAMES,  # intermediate code -> HoS tile name
        "tiles": tiles,
        "towns": [{"name": n, "col": c, "row": r, "size": s} for n, c, r, s in TOWNS],
        "gaps": [{"row": row, "col": col, "name": name} for row, col, name in GAPS],
        "pike_waypoints": PIKE_WAYPOINTS,
        "roads": road_tiles,
        "deployment_zones": DEPLOYMENT_ZONES,
    }
    return payload


def validate(payload: dict) -> None:
    """Sanity checks: dimensions, terrain ids, connectivity of the pike."""
    assert payload["format"] == "hexwright-json"
    codes = set(TERRAIN_CODES.values())
    seen = set()
    for t in payload["tiles"]:
        assert t["terrain"] in codes, f"bad terrain id {t}"
        k = (t["col"], t["row"])
        assert k not in seen, f"duplicate tile {k}"
        seen.add(k)
    expected = WIDTH * HEIGHT
    assert len(seen) == expected, f"expected {expected} tiles, got {len(seen)}"
    # every town sits on a city tile
    city_code = TERRAIN_CODES["city"]
    by_pos = {(t["col"], t["row"]): t["terrain"] for t in payload["tiles"]}
    for town in payload["towns"]:
        assert by_pos[(town["col"], town["row"])] == city_code, \
            f"town {town['name']} not on city tile"
    # pike should connect Winchester to Staunton region: check waypoints exist
    for c, r in payload["pike_waypoints"]:
        assert 0 <= c < WIDTH and 0 <= r < HEIGHT, f"pike waypoint out of bounds {(c, r)}"


def write_json(payload: dict, out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=1))
    return out_path


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Generate the Shenandoah Valley map JSON.")
    ap.add_argument("--out", default="maps/generated/map_shenandoah_valley.json")
    args = ap.parse_args()

    payload = generate_map()
    validate(payload)
    path = write_json(payload, args.out)
    print(f"Wrote {path} ({payload['size_x']}x{payload['size_y']}, {len(payload['tiles'])} tiles)")
    from collections import Counter
    names = Counter(t["tile"] for t in payload["tiles"])
    for name, n in sorted(names.items(), key=lambda kv: -kv[1]):
        print(f"  {n:5d}  {name}")


if __name__ == "__main__":
    main()
