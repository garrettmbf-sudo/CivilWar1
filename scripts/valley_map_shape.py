"""Hex counts, basemap size and per-scale 1862 mechanics for the Valley map polygon.

Uses the game's native flat-top even-q convention (src/hex_utils.py, MapGO pitch 4.42:5.1). Hex size is measured across
the flats, which equals the centre-to-centre spacing.
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import hex_utils as hu  # noqa: E402

DATA = ROOT / "scenarios" / "valley_campaign_1862" / "data"
YD = 0.9144
M_PER_DEG = 111_132.0
DETAIL_PX_PER_HEX = 145  # real painted detail across the flats (Kernstown bot recommendation)


def load_polygon(path: Path = DATA / "map_shape.json") -> list[tuple[float, float]]:
    return [tuple(p) for p in json.loads(path.read_text())["polygon"]]


def point_in_polygon(lon: float, lat: float, poly) -> bool:
    inside = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > lat) != (y2 > lat) and lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


class Frame:
    """Equirectangular frame about the polygon mid-latitude (as kernstown-map GridSpec)."""

    def __init__(self, poly):
        self.west = min(p[0] for p in poly); self.east = max(p[0] for p in poly)
        self.south = min(p[1] for p in poly); self.north = max(p[1] for p in poly)
        mid = (self.south + self.north) / 2
        self.m_lon = M_PER_DEG * math.cos(math.radians(mid))

    def to_xy(self, lon, lat):
        return (lon - self.west) * self.m_lon, (lat - self.south) * M_PER_DEG

    def to_lonlat(self, x, y):
        return self.west + x / self.m_lon, self.south + y / M_PER_DEG

    @property
    def size_m(self):
        return (self.east - self.west) * self.m_lon, (self.north - self.south) * M_PER_DEG


def grid_counts(poly, hex_yd: float) -> dict:
    f = Frame(poly)
    s = hex_yd * YD
    w, h = f.size_m
    cols = math.ceil(w / (s * hu.COL_PITCH_RATIO)) + 1
    rows = math.ceil(h / s) + 1
    inside = 0
    for c in range(cols):
        for r in range(rows):
            x, y = hu.hex_center(c, r, s)
            if point_in_polygon(*f.to_lonlat(x, y), poly):
                inside += 1
    px_scale = DETAIL_PX_PER_HEX / s
    return {"hex_yd": hex_yd, "cols": cols, "rows": rows, "rect_hexes": cols * rows, "playable_hexes": inside,
            "basemap_px": (math.ceil(w * px_scale), math.ceil(h * px_scale))}


def town_coords() -> dict[str, tuple[float, float]]:
    text = (ROOT / "tools" / "powershell" / "valley_map_data.ps1").read_text()
    pat = re.compile(r'Name="([^"]+)";\s*Lat=([0-9.]+);\s*Lon=([0-9.]+)')
    return {m.group(1): (-float(m.group(3)), float(m.group(2))) for m in pat.finditer(text)}


def feature_points() -> dict[str, tuple[float, float]]:
    pts = {}
    for row in csv.DictReader((DATA / "blue_ridge_passes.csv").open()):
        pts[row["feature_id"]] = (float(row["longitude"]), float(row["latitude"]))
    for row in csv.DictReader((DATA / "east_exit_edges.csv").open()):
        pts[row["exit_id"]] = (float(row["approx_exit_lon"]), float(row["approx_exit_lat"]))
    for row in csv.DictReader((DATA / "western_roads.csv").open()):
        for i, wp in enumerate(row["waypoints_lat_lon"].split(";")):
            lat, lon = [float(v) for v in re.findall(r"-?\d+\.\d+", wp)[:2]]
            pts[f"{row['route_id']}#{i}"] = (lon, lat)
    return pts


# 1862 ranges (yd). Typical figures from standard references; see docs/valley-map-build-plan.md.
RANGES = {"smoothbore_effective": 100, "rifle_musket_effective": 250, "canister": 400,
          "napoleon_max": 1600, "rifled_gun_max": 1900}


def mechanics(hex_yd: float, turn_h: float) -> dict:
    road_mph, cav_mph, offroad_cost = 2.5, 4.0, 2  # column incl. halts; walk/trot mix; HoS plain=2 MP
    hexes_per_mile = 1760 / hex_yd
    return {
        "musket_hexes": round(RANGES["rifle_musket_effective"] / hex_yd, 2),
        "canister_hexes": round(RANGES["canister"] / hex_yd, 2),
        "napoleon_range": max(1, round(RANGES["napoleon_max"] / hex_yd)),
        "rifled_range": max(1, round(RANGES["rifled_gun_max"] / hex_yd)),
        "vis_inf_yd": hex_yd, "vis_recon_yd": 2 * hex_yd,
        "brigade_hexes_400_800yd": (round(400 / hex_yd, 1), round(800 / hex_yd, 1)),
        "inf_road_mp": round(road_mph * turn_h * hexes_per_mile, 1),
        "cav_road_mp": round(cav_mph * turn_h * hexes_per_mile, 1),
        "march_20mi_hexes": round(20 * hexes_per_mile),
        "offroad_hexes_per_turn": round(road_mph * turn_h * hexes_per_mile / offroad_cost, 1),
    }


def main():
    poly = load_polygon()
    out = {"scales": [grid_counts(poly, yd) for yd in (250, 400, 500, 750, 1000)]}
    pts = {**{k: v for k, v in town_coords().items()}, **feature_points()}
    out["outside_polygon"] = [k for k, (lon, lat) in pts.items() if not point_in_polygon(lon, lat, poly)]
    out["mechanics"] = {f"{yd}yd_{t}h": mechanics(yd, t) for yd in (250, 400, 500, 750, 1000) for t in (1, 2)}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
