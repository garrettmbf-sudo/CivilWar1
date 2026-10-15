"""Hex of Steel Valley map *preflight* (not a game-save writer).

Keep geographical features as independent networks until a native tile can render
all required exits. This avoids pretending a nearest-looking sprite joins its
neighbours. The coordinate system matches the existing PowerShell EVEN-Q grid.

IMPORTANT: coordinates in the current PowerShell builder are provisional. A
passing topology audit does not certify the historical geography or .sav file.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable

# Direction 0..5: top, upper-right, lower-right, bottom, lower-left, upper-left.
EVEN = ((0, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0))
ODD = ((0, -1), (1, -1), (1, 0), (0, 1), (-1, 0), (-1, -1))

# Physically inspected from original civilhex assets; NOT a guessed universal
# shared index. Railroad6..9 have a DIFFERENT numbering from River6..9.
RIVER_PORTS = {
    (0, 3): 1, (1, 4): 2, (2, 5): 3, (1, 5): 4,
    (2, 4): 5, (0, 4): 6, (0, 2): 7, (1, 3): 8,
    (3, 5): 9, (1, 3, 5): 10, (0, 2, 4): 11,
    (0, 1, 3): 12,
}
RAIL_PORTS = {
    (0, 3): 1, (1, 4): 2, (2, 5): 3, (1, 5): 4,
    (2, 4): 5, (0, 2): 6, (1, 3): 7, (3, 5): 8,
    (0, 4): 9,
}
# Verified road variants require a native game/actual PNG edge-port inventory;
# the provided custom asset set does not contain Road1...Road9 files.


def neighbor(cell: tuple[int, int], direction: int) -> tuple[int, int]:
    """Adjacent hex; use the same even-q layout as the PowerShell builder."""
    if not 0 <= direction < 6:
        raise ValueError(f"invalid hex direction: {direction}")
    x, y = cell
    dx, dy = (EVEN if x % 2 == 0 else ODD)[direction]
    return x + dx, y + dy


def port_to(a: tuple[int, int], b: tuple[int, int]) -> int:
    for direction in range(6):
        if neighbor(a, direction) == b:
            return direction
    raise ValueError(f"nonadjacent hexes {a} -> {b}")


def offset_to_cube(cell: tuple[int, int]) -> tuple[int, int, int]:
    col, row = cell
    q = col
    r = row - (col + (col & 1)) // 2
    return q, r, -q - r


def cube_to_offset(q: int, r: int) -> tuple[int, int]:
    return q, r + (q + (q & 1)) // 2


def cube_round(q: float, r: float, s: float) -> tuple[int, int, int]:
    qi, ri, si = round(q), round(r), round(s)
    dq, dr, ds = abs(qi - q), abs(ri - r), abs(si - s)
    if dq > dr and dq > ds:
        qi = -ri - si
    elif dr > ds:
        ri = -qi - si
    else:
        si = -qi - ri
    return qi, ri, si


def hex_line(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    aq, ar, as_ = offset_to_cube(a)
    bq, br, bs = offset_to_cube(b)
    steps = max(abs(aq - bq), abs(ar - br), abs(as_ - bs))
    if steps == 0:
        return [a]
    out = []
    for i in range(steps + 1):
        t = i / steps
        q, r, _ = cube_round(aq + (bq - aq) * t,
                             ar + (br - ar) * t,
                             as_ + (bs - as_) * t)
        cell = cube_to_offset(q, r)
        if not out or out[-1] != cell:
            out.append(cell)
    for left, right in zip(out, out[1:]):
        port_to(left, right)  # construction invariant
    return out


def trace_waypoints(points: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    points = list(points)
    if not points:
        return []
    result = [points[0]]
    for a, b in zip(points, points[1:]):
        result.extend(hex_line(a, b)[1:])
    return result


def parse_ps_paths(script: str) -> dict[str, dict[str, list[tuple[int, int]]]]:
    """Read literal integer waypoints, never execute untrusted PowerShell.

    Names/coordinates are source-script approximations, NOT georeferenced truth.
    """
    paths: dict[str, dict[str, list[tuple[int, int]]]] = {
        "river": {}, "road": {}, "rail": {}
    }
    pattern = re.compile(r'^\s*\$(river\w+|valleyPike|rd\w+|rr\w+)\s*=\s*@\(([^)]*)\)', re.M)
    for match in pattern.finditer(script):
        name, contents = match.groups()
        if not re.fullmatch(r'[\d,\s+-]+', contents):
            raise ValueError(f"unexpected expression in ${name}; inspect manually")
        coords = [int(n) for n in contents.split(',') if n.strip()]
        if len(coords) < 4 or len(coords) % 2:
            raise ValueError(f"invalid polyline ${name}")
        kind = ("river" if name.startswith("river") else
                "rail" if name.startswith("rr") else "road")
        paths[kind][name] = list(zip(coords[0::2], coords[1::2]))
    return paths


def build_networks(paths: dict, width: int, height: int) -> dict:
    """Preserve path edge identities; neighboring parallel routes aren't linked.

    Each output port is a requirement on actual artwork and navigation, not a
    claim that an installed sprite supports it.
    """
    grids = {k: defaultdict(set) for k in ("river", "road", "rail")}
    occupancy = {k: defaultdict(set) for k in grids}
    defects = []
    for kind, named in paths.items():
        for name, waypoints in named.items():
            traced = trace_waypoints(waypoints)
            for cell in traced:
                if not (0 <= cell[0] < width and 0 <= cell[1] < height):
                    defects.append({"type": "out_of_bounds", "feature": name, "hex": cell})
                    continue
                occupancy[kind][cell].add(name)
            for a, b in zip(traced, traced[1:]):
                if a == b:
                    continue
                if not all(0 <= c[0] < width and 0 <= c[1] < height for c in (a, b)):
                    continue
                d = port_to(a, b)
                grids[kind][a].add(d)
                grids[kind][b].add((d + 3) % 6)
    return {"grids": grids, "occupancy": occupancy, "defects": defects}


def variant(kind: str, ports: Iterable[int]) -> str | None:
    """Exact match ONLY; never substitute a visually incompatible bend."""
    key = tuple(sorted(set(ports)))
    table = RIVER_PORTS if kind == "river" else RAIL_PORTS if kind == "rail" else {}
    n = table.get(key)
    return f"{'River' if kind == 'river' else 'Railroad'}{n}" if n is not None else None


def asset_duplicates(directory: Path) -> list[list[str]]:
    """Identify identical PNGs masquerading as different track/river variants."""
    fingerprints: dict[str, list[str]] = defaultdict(list)
    for path in sorted(directory.glob("*.png")):
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        fingerprints[h].append(path.name)
    return [items for items in fingerprints.values() if len(items) > 1]


def create_report(script: str, width: int = 125, height: int = 130,
                  assets: Path | None = None) -> dict:
    paths = parse_ps_paths(script)
    networks = build_networks(paths, width, height)
    report = {
        "status": "PREFLIGHT_ONLY_NOT_GAME_TESTED",
        "coordinate_provenance": "UNVERIFIED_approximate_PowerShell_v4_waypoints",
        "size": [width, height],
        "feature_counts": {k: len(v) for k, v in paths.items()},
        "network_hex_counts": {k: len(networks["occupancy"][k]) for k in paths},
        "defects": networks["defects"],
        "unsupported_visual_ports": [],
        "river_route_crossings": [],
        "rail_road_shared_hexes": [],
        "duplicate_asset_groups": [],
    }
    for kind in ("river", "rail"):
        for cell, ports in sorted(networks["grids"][kind].items()):
            if variant(kind, ports) is None:
                report["unsupported_visual_ports"].append({
                    "kind": kind, "hex": list(cell), "ports": sorted(ports),
                    "reason": "no visually verified sprite for exact set of exits",
                })
    water = networks["occupancy"]["river"]
    for kind in ("road", "rail"):
        for cell in sorted(set(water) & set(networks["occupancy"][kind])):
            report["river_route_crossings"].append({
                "hex": list(cell), "route": kind,
                "rivers": sorted(water[cell]),
                "routes": sorted(networks["occupancy"][kind][cell]),
                "crossing_status": "UNVERIFIED_NO_AUTOMATIC_BRIDGE",
            })
    for cell in sorted(set(networks["occupancy"]["road"]) &
                       set(networks["occupancy"]["rail"])):
        report["rail_road_shared_hexes"].append(list(cell))
    if assets is not None:
        report["duplicate_asset_groups"] = asset_duplicates(assets)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe, read-only Valley hex connectivity preflight")
    parser.add_argument("script", type=Path, help="v4 build_valley_map.ps1 input (never executed)")
    parser.add_argument("--assets", type=Path, help="directory of unpacked user-owned PNG tiles")
    parser.add_argument("--output", type=Path, help="write JSON report")
    parser.add_argument("--width", type=int, default=125)
    parser.add_argument("--height", type=int, default=130)
    args = parser.parse_args()
    result = create_report(args.script.read_text(encoding="utf-8-sig"), args.width,
                           args.height, args.assets)
    report = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n", encoding="utf-8")
        print(f"Wrote preflight report: {args.output}")
    else:
        print(report)
    print(f"Unsupported sprite connections: {len(result['unsupported_visual_ports'])}; "
          f"crossings awaiting verification: {len(result['river_route_crossings'])}; "
          f"invalid route points: {len(result['defects'])}")
    # A single unresolved required sprite means the map is not certified.
    return 1 if result["defects"] or result["unsupported_visual_ports"] or result["river_route_crossings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

