#!/usr/bin/env python3
"""Per-hex gameplay table for the .sav builder -> data/layers/kernstown_game.json
Sources: data/layers/kernstown_hexes.json (slice output), layers/kernstown_terrain_tags.json,
data/layers/painted_forest_fraction.json (what the art actually shows as woods)."""
import json, sys
from pathlib import Path
from collections import Counter
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from hex_grid import KERNSTOWN as G
from build_kernstown_layers import trace_waypoints

base = json.loads((ROOT / "data/layers/kernstown_hexes.json").read_text())
tags = json.loads((ROOT / "layers/kernstown_terrain_tags.json").read_text())
ff_path = ROOT / "data/layers/painted_forest_fraction.json"
ff = json.loads(ff_path.read_text()) if ff_path.exists() else {}
FEAT = json.loads((ROOT / "data/features/kernstown_features.json").read_text())
pike = trace_waypoints(G, FEAT["roads"]["valley_pike"]["waypoints"])
dirt = set()
for k, rd in FEAT["roads"].items():
    if rd.get("kind") != "pike": dirt |= trace_waypoints(G, rd["waypoints"])
# v0.4: the 23 "marsh_hexes" (cols 18-25, rows 23-27, between the stone wall and Pritchard's Hill) are NOT wet ground:
# DEM 3DEP means 247-276 m, at/above their neighbourhood and higher than the 25 FilterTerrain hills (230-250 m).
# They were the only dmg:5 hexes. They are the Sandy Ridge / Pritchard's Hill upland -> stock Hill (dmg 15, mp 3).
upland = {tuple(x) for x in tags["marsh_hexes"]}
marsh = set()
# W&P Railroad in March 1862 ran north from the Winchester depot only (the line south of town is post-war);
# railroad flag = hexes under the painted track (same waypoints/cut-off as build_full_map.py)
RR_MIN_LAT = 39.1885
rail = trace_waypoints(G, [p for p in FEAT["railroads"]["winchester_and_potomac"]["waypoints"] if p[1] >= RR_MIN_LAT])
# town hexes from what the art actually shows (data/layers/painted_buildings.json written by build_full_map.py)
PB = json.loads((ROOT / "data/layers/painted_buildings.json").read_text())
bcnt = {tuple(map(int, k.split(","))): v for k, v in PB["counts"].items()}
barea = {tuple(map(int, k.split(","))): v for k, v in PB["sprite_area_px"].items()}
WALL = [(14,23),(15,23),(16,23),(17,23),(18,23),(19,22),(20,23)]
PRIMARY = (42, 41); SECONDARY = {(27, 20): "Kernstown", (30, 19): "Opequon Church"}

def hd(a, b):
    def cube(c, r):
        x = c; z = r - (c - (c & 1)) // 2; return x, -x - z, z
    p, q = cube(*a), cube(*b); return max(abs(p[i] - q[i]) for i in range(3))
win = {k for k in bcnt if hd(k, PRIMARY) <= 4}
town = {k for k in win if barea.get(k, 0) >= 12000} | {PRIMARY}                       # dense core (4-6 hexes)
village = {k for k in win if bcnt[k] >= 3 and k not in town} | {k for k in bcnt if hd(k, (27, 20)) <= 1 and bcnt[k] >= 2}

out = []
for h in base["hexes"]:
    c, r = h["col"], h["row"]; key = (c, r)
    typ, filt, mp, dmg, tag = "Plain", "FilterAll", 2, 0, "open"
    if h["filter"] == "FilterTerrain" or key in upland: typ, filt, mp, dmg, tag = "Hill", "FilterTerrain", 3, 15, "hill"
    if ff.get(f"{c},{r}", 0) >= 0.35 or (not ff and h["filter"] == "FilterForest"):
        typ, filt, mp, dmg, tag = "Forest", "FilterForest", 3, 25, "woods"
    if key in marsh: typ, filt, mp, dmg, tag = "Plain", "FilterAll", 4, 5, "marsh"
    if h["filter"] == "FilterRiver": typ, filt, mp, dmg, tag = "River", "FilterRiver", 3, 0, "creek"
    if key in village: typ, filt, mp, dmg, tag = "Plain", "FilterAll", 2, 20, "village"
    if key in town: typ, filt, mp, dmg, tag = "Plain", "FilterAll", 2, 40, "town"
    if key in dirt: typ, filt, mp, tag = "Road", "FilterRoad", 1, tag + "+road"
    if key in pike: typ, filt, mp, tag = "Road", "FilterRoad", 1, tag + "+pike"
    fl = h.get("flags", {})
    rec = dict(col=c, row=r, tile_name=h["tile_name"], type=typ, filter=filt, mp=mp, dmg=dmg, tag=tag,
               city=fl.get("CityName", ""), owner=fl.get("OwnerName", ""), railroad=key in rail,
               vp=False, primary=False, secondary=False, stone_wall=False)
    if key in WALL: rec.update(dmg=35, stone_wall=True, tag=tag + "+stone_wall")
    if key == PRIMARY: rec.update(vp=True, primary=True, city="Winchester (Courthouse)", owner="Union", type="City", filter="FilterVP", dmg=40, mp=1)
    if key in SECONDARY: rec.update(vp=True, secondary=True, city=SECONDARY[key], owner=rec["owner"] or "Union")
    out.append(rec)
assert len(out) == G.cols * G.rows
(ROOT / "data/layers/kernstown_game.json").write_text(json.dumps({"cols": G.cols, "rows": G.rows, "season": "Summer", "hexes": out}, indent=0))
print("town", sorted(town), "village", sorted(village), "rail", sorted(rail))
print(Counter(x["tag"].split("+")[0] for x in out), "wall", sum(x["stone_wall"] for x in out), "vp", [(x["col"], x["row"], x["city"]) for x in out if x["vp"]])
