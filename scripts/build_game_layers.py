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
marsh = {tuple(x) for x in tags["marsh_hexes"]}
WALL = [(14,23),(15,23),(16,23),(17,23),(18,23),(19,22),(20,23)]
PRIMARY = (42, 41); SECONDARY = {(27, 20): "Kernstown", (30, 19): "Opequon Church"}

def hd(a, b):
    def cube(c, r):
        x = c; z = r - (c - (c & 1)) // 2; return x, -x - z, z
    p, q = cube(*a), cube(*b); return max(abs(p[i] - q[i]) for i in range(3))
town = {(c, r) for c in range(G.cols) for r in range(G.rows) if hd((c, r), PRIMARY) <= 3 or hd((c, r), (27, 20)) <= 1}

out = []
for h in base["hexes"]:
    c, r = h["col"], h["row"]; key = (c, r)
    typ, filt, mp, dmg, tag = "Plain", "FilterAll", 2, 0, "open"
    if h["filter"] == "FilterTerrain": typ, filt, mp, dmg, tag = "Hill", "FilterTerrain", 3, 15, "hill"
    if ff.get(f"{c},{r}", 0) >= 0.35 or (not ff and h["filter"] == "FilterForest"):
        typ, filt, mp, dmg, tag = "Forest", "FilterForest", 3, 25, "woods"
    if key in marsh: typ, filt, mp, dmg, tag = "Plain", "FilterAll", 4, 5, "marsh"
    if h["filter"] == "FilterRiver": typ, filt, mp, dmg, tag = "River", "FilterRiver", 3, 0, "creek"
    if key in town: typ, filt, mp, dmg, tag = "Plain", "FilterAll", 2, 40, "town"
    if key in dirt: typ, filt, mp, tag = "Road", "FilterRoad", 1, tag + "+road"
    if key in pike: typ, filt, mp, tag = "Road", "FilterRoad", 1, tag + "+pike"
    fl = h.get("flags", {})
    rec = dict(col=c, row=r, tile_name=h["tile_name"], type=typ, filter=filt, mp=mp, dmg=dmg, tag=tag,
               city=fl.get("CityName", ""), owner=fl.get("OwnerName", ""), railroad=bool(fl.get("Railroad")),
               vp=False, primary=False, secondary=False, stone_wall=False)
    if key in WALL: rec.update(dmg=35, stone_wall=True, tag=tag + "+stone_wall")
    if key == PRIMARY: rec.update(vp=True, primary=True, city="Winchester (Courthouse)", owner="Union", type="City", filter="FilterVP", dmg=40, mp=1)
    if key in SECONDARY: rec.update(vp=True, secondary=True, city=SECONDARY[key], owner=rec["owner"] or "Union")
    out.append(rec)
assert len(out) == G.cols * G.rows
(ROOT / "data/layers/kernstown_game.json").write_text(json.dumps({"cols": G.cols, "rows": G.rows, "season": "Summer", "hexes": out}, indent=0))
print(Counter(x["tag"].split("+")[0] for x in out), "wall", sum(x["stone_wall"] for x in out), "vp", [(x["col"], x["row"], x["city"]) for x in out if x["vp"]])
