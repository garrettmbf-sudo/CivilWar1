#!/usr/bin/env python3
"""Build Kernstown hex layers from DEM + digitized 1862 features."""
from __future__ import annotations
import csv, json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from hex_grid import KERNSTOWN, GridSpec

def load_dem(path: Path):
    im = Image.open(path)
    arr = np.array(im, dtype=np.float32)
    # replace nodata extremes
    arr = np.where(np.isfinite(arr), arr, np.nan)
    return arr

def dem_at(dem, grid: GridSpec, lon, lat):
    h, w = dem.shape
    u = (lon - grid.west) / (grid.east - grid.west)
    v = (grid.north - lat) / (grid.north - grid.south)  # image row 0 = north
    x = u * (w - 1)
    y = v * (h - 1)
    if x < 0 or y < 0 or x > w - 1 or y > h - 1:
        return np.nan
    x0, y0 = int(x), int(y)
    x1, y1 = min(x0 + 1, w - 1), min(y0 + 1, h - 1)
    fx, fy = x - x0, y - y0
    vals = [dem[y0, x0], dem[y0, x1], dem[y1, x0], dem[y1, x1]]
    if any(np.isnan(v) for v in vals):
        return float(np.nanmean(vals))
    return float(
        vals[0] * (1 - fx) * (1 - fy)
        + vals[1] * fx * (1 - fy)
        + vals[2] * (1 - fx) * fy
        + vals[3] * fx * fy
    )

def slope_at(dem, grid, lon, lat, delta=0.0004):
    e = dem_at(dem, grid, lon, lat)
    e2 = dem_at(dem, grid, lon + delta, lat)
    e3 = dem_at(dem, grid, lon, lat + delta)
    if any(np.isnan(v) for v in (e, e2, e3)):
        return 0.0
    mid = (grid.south + grid.north) / 2
    m_lat, m_lon = grid.meters_per_deg(mid)
    dx = delta * m_lon
    dy = delta * m_lat
    return math.degrees(math.atan(math.hypot((e2 - e) / dx, (e3 - e) / dy)))

# Hex math lives in hex_grid.py (game convention: rows north, EVEN columns raised, MapGO.cs:452-459).
# v0.4.2 fix: these helpers used an even-raised cube conversion while hex_grid used odd-raised, so traced
# lines bridged every odd/even step with an extra hex. They now delegate to the single shared implementation.
from hex_grid import cube_round as _cube_round, offset_to_cube, cube_to_offset, hex_line  # noqa: E402,F401

def cube_round(q, r, s):
    return _cube_round(q, r, s)

def trace_waypoints(grid, waypoints):
    """Hexes under a lon/lat polyline (dense sampling, exact cell membership, gap-free chain)."""
    return {h for h in grid.trace_lonlat(waypoints) if grid.in_grid(*h)}

def edge_variant(a, b):
    """Pick RiverN/RoadN variant from neighbor direction (legacy stock-tile path; unused by the SV_K pipeline)."""
    dc, dr = b[0] - a[0], b[1] - a[1]
    # map to 1..9 like stock tiles
    if dc == 0 and dr < 0:
        return 1  # N-S
    if dc == 0 and dr > 0:
        return 1
    if dc > 0 and dr == 0:
        return 2
    if dc < 0 and dr == 0:
        return 2
    if dc > 0 and dr < 0:
        return 4
    if dc > 0 and dr > 0:
        return 5
    if dc < 0 and dr > 0:
        return 6
    if dc < 0 and dr < 0:
        return 7
    return 1

def main():
    grid = KERNSTOWN
    feats = json.loads((ROOT / "data/features/kernstown_features.json").read_text())
    dem = load_dem(ROOT / "data/dem/kernstown_3dep.tif")

    # elevation + slope per hex
    elev = np.zeros((grid.rows, grid.cols), np.float32)
    slope = np.zeros((grid.rows, grid.cols), np.float32)
    for r in range(grid.rows):
        for c in range(grid.cols):
            lon, lat = grid.hex_to_lonlat(c, r)
            elev[r, c] = dem_at(dem, grid, lon, lat)
            slope[r, c] = slope_at(dem, grid, lon, lat)

    # fill nan with median
    med = float(np.nanmedian(elev))
    elev = np.where(np.isnan(elev), med, elev)

    # terrain classification from DEM
    # relative relief: local elev - neighborhood mean
    from numpy.lib.stride_tricks import sliding_window_view
    pad = np.pad(elev, 2, mode="edge")
    # simple blur
    ker = np.ones((5, 5), np.float32) / 25
    blur = np.zeros_like(elev)
    for r in range(grid.rows):
        for c in range(grid.cols):
            blur[r, c] = pad[r : r + 5, c : c + 5].mean()
    relief = elev - blur

    terrain = np.full((grid.rows, grid.cols), "SV_Plain", object)
    for r in range(grid.rows):
        for c in range(grid.cols):
            s, rel = slope[r, c], relief[r, c]
            if s >= 12 or rel >= 12:
                terrain[r, c] = "SV_HillForest" if (c * 17 + r * 13) % 5 < 2 else "SV_Hill"
            elif s >= 7 or rel >= 6:
                terrain[r, c] = "SV_Hill"
            elif s >= 3 and (c + r * 3) % 7 < 3:
                terrain[r, c] = "SV_ThinForest"
            elif (c * 11 + r * 19) % 11 == 0:
                terrain[r, c] = "SV_ThinForest2"
            else:
                terrain[r, c] = ["SV_Plain", "SV_Plain2", "SV_Plain3"][(c + r) % 3]

    # ridge overrides
    for name, wps in feats.get("ridge_cores", {}).items():
        hx = trace_waypoints(grid, wps)
        for c, r in hx:
            if name == "sandy_ridge":
                terrain[r, c] = "SV_SandyRidge"
            else:
                terrain[r, c] = "SV_PritchardsHill"

    # layers
    river = set()
    road = set()
    pike = set()
    rail = set()
    wall = set()
    for key, riv in feats["rivers"].items():
        river |= trace_waypoints(grid, riv["waypoints"])
    for key, rd in feats["roads"].items():
        hx = trace_waypoints(grid, rd["waypoints"])
        if rd.get("kind") == "pike":
            pike |= hx
        else:
            road |= hx
    for key, rr in feats["railroads"].items():
        rail |= trace_waypoints(grid, rr["waypoints"])
    for key, sw in feats.get("stone_walls", {}).items():
        wall |= trace_waypoints(grid, sw["waypoints"])

    # assign tile names with variants along paths
    tiles = [[terrain[r, c] for c in range(grid.cols)] for r in range(grid.rows)]
    tile_type = [["Plain"] * grid.cols for _ in range(grid.rows)]
    filter_type = [["FilterAll"] * grid.cols for _ in range(grid.rows)]
    flags = [[{} for _ in range(grid.cols)] for _ in range(grid.rows)]
    labels = [["" for _ in range(grid.cols)] for _ in range(grid.rows)]

    def set_path(hexes, waypoints, prefix, typ, filt, extra=None):
        pts = [grid.lonlat_to_hex(lon, lat) for lon, lat in waypoints]
        pts = [(c, r) for c, r in pts if 0 <= c < grid.cols and 0 <= r < grid.rows]
        path = []
        for a, b in zip(pts, pts[1:]):
            path.extend(hex_line(a, b))
        for i, (c, r) in enumerate(path):
            if not (0 <= c < grid.cols and 0 <= r < grid.rows):
                continue
            nxt = path[i + 1] if i + 1 < len(path) else path[i - 1] if i else (c, r)
            v = edge_variant((c, r), nxt)
            tiles[r][c] = f"{prefix}{v}"
            tile_type[r][c] = typ
            filter_type[r][c] = filt
            if extra:
                flags[r][c].update(extra)

    for riv in feats["rivers"].values():
        set_path(None, riv["waypoints"], "SV_River", "River", "FilterRiver")
    for rd in feats["roads"].values():
        if rd.get("kind") == "pike":
            set_path(None, rd["waypoints"], "SV_ValleyPike", "Road", "FilterRoad")
        else:
            set_path(None, rd["waypoints"], "SV_Road", "Road", "FilterRoad")
    for rr in feats["railroads"].values():
        set_path(None, rr["waypoints"], "SV_Railroad", "Plain", "FilterRailroad", {"Railroad": True})
    for sw in feats.get("stone_walls", {}).values():
        for c, r in trace_waypoints(grid, sw["waypoints"]):
            tiles[r][c] = "SV_StoneWall"
            tile_type[r][c] = "Hill"
            filter_type[r][c] = "FilterTerrain"

    # fords as bridges on river/road intersections near listed points
    for ford in feats.get("fords", []):
        c, r = grid.lonlat_to_hex(ford["lon"], ford["lat"])
        if 0 <= c < grid.cols and 0 <= r < grid.rows:
            tiles[r][c] = "SV_River6Bridge"
            tile_type[r][c] = "Plain"
            filter_type[r][c] = "FilterRoadBridge"
            flags[r][c] = {"Bridge": True, "IsBridgeDestroyed": False}

    # Winchester multi-hex
    for blk in feats["winchester_blocks"]:
        c, r = grid.lonlat_to_hex(blk["lon"], blk["lat"])
        if 0 <= c < grid.cols and 0 <= r < grid.rows:
            tiles[r][c] = blk["tile"]
            tile_type[r][c] = "City"
            filter_type[r][c] = "FilterVP"
            flags[r][c] = {"Capturable": True}
            labels[r][c] = "Winchester"

    # places
    for pl in feats["places"]:
        c, r = grid.lonlat_to_hex(pl["lon"], pl["lat"])
        if not (0 <= c < grid.cols and 0 <= r < grid.rows):
            continue
        if pl["kind"] == "city" and labels[r][c] == "Winchester":
            flags[r][c].update({"IsVictoryPoint": pl["vp"], "PrimaryObjective": pl.get("primary", False),
                                "OwnerName": pl.get("owner", ""), "CityName": pl["name"]})
            continue
        if pl["kind"] == "church":
            tiles[r][c] = "SV_Church"
        elif pl["kind"] == "village" and pl["id"] == "kernstown":
            tiles[r][c] = "SV_Kernstown"
        elif pl["kind"] == "village":
            tiles[r][c] = "SV_Village"
        elif pl["kind"] == "hill":
            tiles[r][c] = "SV_PritchardsHill"
        elif pl["kind"] == "ridge":
            tiles[r][c] = "SV_SandyRidge"
        if pl["kind"] in ("city", "village", "church"):
            tile_type[r][c] = "City"
            filter_type[r][c] = "FilterVP"
            flags[r][c] = {
                "Capturable": True,
                "IsVictoryPoint": pl.get("vp", False),
                "PrimaryObjective": pl.get("primary", False),
                "OwnerName": pl.get("owner", ""),
                "CityName": pl["name"],
            }
        labels[r][c] = pl["name"]

    # set terrain type/filter for remaining
    for r in range(grid.rows):
        for c in range(grid.cols):
            name = tiles[r][c]
            if name.startswith("SV_Plain"):
                tile_type[r][c], filter_type[r][c] = "Plain", "FilterAll"
            elif "Forest" in name and "Hill" not in name:
                tile_type[r][c], filter_type[r][c] = "ThinForest" if "Thin" in name else "ThickForest", "FilterForest"
            elif name in ("SV_Hill", "SV_Hill2", "SV_HillForest", "SV_SandyRidge", "SV_PritchardsHill"):
                tile_type[r][c], filter_type[r][c] = "Hill", "FilterTerrain"

    out_dir = ROOT / "data" / "layers"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows_out = []
    for r in range(grid.rows):
        for c in range(grid.cols):
            lon, lat = grid.hex_to_lonlat(c, r)
            rows_out.append({
                "col": c, "row": r, "lon": round(lon, 6), "lat": round(lat, 6),
                "elev_m": round(float(elev[r, c]), 2),
                "slope_deg": round(float(slope[r, c]), 2),
                "tile_name": tiles[r][c],
                "type": tile_type[r][c],
                "filter": filter_type[r][c],
                "label": labels[r][c],
                "flags": flags[r][c],
            })
    (out_dir / "kernstown_hexes.json").write_text(json.dumps({
        "grid": {
            "cols": grid.cols, "rows": grid.rows, "hex_yards": grid.hex_yards,
            "bbox": {"west": grid.west, "south": grid.south, "east": grid.east, "north": grid.north},
        },
        "hexes": rows_out,
        "counts": {
            "river": len(river), "road": len(road), "pike": len(pike),
            "rail": len(rail), "wall": len(wall),
        },
    }, indent=2))
    with (out_dir / "kernstown_hexes.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["col","row","lon","lat","elev_m","slope_deg","tile_name","type","filter","label"])
        w.writeheader()
        for row in rows_out:
            w.writerow({k: row[k] for k in w.fieldnames})

    # elev preview
    e = elev.copy()
    e = (e - e.min()) / max(1e-6, e.max() - e.min())
    Image.fromarray((e * 255).astype(np.uint8)).resize((grid.cols * 8, grid.rows * 8), Image.Resampling.NEAREST).save(
        ROOT / "previews" / "dem_hex_elev.png"
    )
    print(f"layers: {grid.cols}x{grid.rows}={grid.cols*grid.rows} hexes")
    print("counts", {"river": len(river), "road": len(road), "pike": len(pike), "rail": len(rail), "wall": len(wall)})
    print("wrote", out_dir / "kernstown_hexes.json")

if __name__ == "__main__":
    main()
