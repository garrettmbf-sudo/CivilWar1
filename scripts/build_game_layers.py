#!/usr/bin/env python3
"""Per-hex gameplay table for the .sav builder -> data/layers/kernstown_game.json
Sources: data/layers/kernstown_hexes.json (slice output), layers/kernstown_terrain_tags.json,
data/layers/painted_forest_fraction.json (what the art actually shows as woods),
data/layers/painted_lines.json (the exact Pike/road/rail/creek lines painted by build_full_map.py).
v0.4.2: hexes are the game's own (PosX, PosY) (scripts/hex_grid.py: rows north, EVEN columns raised);
Road / River / Rail sets are traced from the painted lines, so they follow the art."""
import json, sys
from pathlib import Path
from collections import Counter
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from hex_grid import KERNSTOWN as G, hex_distance, neighbors

base = json.loads((ROOT / "data/layers/kernstown_hexes.json").read_text())
tags = json.loads((ROOT / "layers/kernstown_terrain_tags.json").read_text())
ff_path = ROOT / "data/layers/painted_forest_fraction.json"
ff = json.loads(ff_path.read_text()) if ff_path.exists() else {}
FEAT = json.loads((ROOT / "data/features/kernstown_features.json").read_text())
LINES = json.loads((ROOT / "data/layers/painted_lines.json").read_text())
STEP = 2.0
def trace_art(pts_px, min_frac=0.15):
    """Hex chain under a painted line (basemap px -> metres). A hex the line only clips (< min_frac of a row of
    line inside it) is dropped when its neighbours in the chain are adjacent anyway, so the set stays connected."""
    P_, H_ = LINES["px_per_m"], LINES["H"]
    pts = [(x / P_, (H_ - y) / P_) for x, y in pts_px]
    chain, cnt = [], Counter()
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / STEP))
        for i in range(n):
            cnt[G.xy_m_to_hex(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n)] += 1
    chain = [h for h in G.trace_xy_m(pts, STEP) if G.in_grid(*h)]
    seq = [h for i, h in enumerate(chain) if i == 0 or chain[i - 1] != h]
    keep = []
    for i, h in enumerate(seq):
        a = keep[-1] if keep else None; b = seq[i + 1] if i + 1 < len(seq) else None
        short = cnt[h] * STEP < min_frac * G.hex_m
        if short and a is not None and b is not None and (b in neighbors(*a) or b == a): continue
        keep.append(h)
    return keep
def chain_ok(ch): return all(b in neighbors(*a) for a, b in zip(ch, ch[1:]))
PIKE_CHAINS = [trace_art(v["pts"]) for v in LINES["roads"].values() if v["kind"] == "pike"]
pike = set().union(*PIKE_CHAINS)
dirt = set()
for k, v in LINES["roads"].items():
    if v["kind"] != "pike": dirt |= set(trace_art(v["pts"]))
river = set()
for c_ in LINES["creeks"]: river |= set(trace_art(c_["pts"]))
# v0.4: the 23 "marsh_hexes" (cols 18-25, rows 23-27, between the stone wall and Pritchard's Hill) are NOT wet ground:
# DEM 3DEP means 247-276 m, at/above their neighbourhood and higher than the 25 FilterTerrain hills (230-250 m).
# They were the only dmg:5 hexes. They are the Sandy Ridge / Pritchard's Hill upland -> stock Hill (dmg 15, mp 3).
upland = {tuple(x) for x in tags["marsh_hexes"]}
marsh = set()
# W&P Railroad in March 1862 ran north from the Winchester depot only (the line south of town is post-war);
# railroad flag = hexes under the painted track (same waypoints/cut-off as build_full_map.py)
rail = set(trace_art(LINES["rail"]["pts"]))      # painted line already starts at the depot (RR_MIN_LAT in build_full_map.py)
# town hexes from what the art actually shows (data/layers/painted_buildings.json written by build_full_map.py)
PB = json.loads((ROOT / "data/layers/painted_buildings.json").read_text())
bcnt = {tuple(map(int, k.split(","))): v for k, v in PB["counts"].items()}
barea = {tuple(map(int, k.split(","))): v for k, v in PB["sprite_area_px"].items()}
# user-chosen hexes (legacy (14,23)..(20,23), (42,41), (27,20), (30,19) re-indexed by migrate_legacy_oddq_to_game.py)
WALL = [tuple(h) for h in tags["stone_wall_confederate_hexes"]]
PRIMARY = tuple(tags["winchester_courthouse_vp"]["hex"]); SECONDARY = {(27, 20): "Kernstown", (30, 18): "Opequon Church"}
hd = hex_distance
win = {k for k in bcnt if hd(k, PRIMARY) <= 4}
town = {k for k in win if barea.get(k, 0) >= 12000} | {PRIMARY}                       # dense core (4-6 hexes)
village = {k for k in win if bcnt[k] >= 3 and k not in town} | {k for k in bcnt if hd(k, (27, 20)) <= 1 and bcnt[k] >= 2}
# v0.4.2: buildings are kept off the Pike, so the Kernstown VP hex (the Pike runs through it) may hold only 1 painted
# building; a secondary-VP hex with any painted building stays a village (as in v0.4.1)
village |= {k for k in SECONDARY if bcnt.get(k, 0) >= 1 and k not in town}

out = []
for h in base["hexes"]:
    c, r = h["col"], h["row"]; key = (c, r)
    typ, filt, mp, dmg, tag = "Plain", "FilterAll", 2, 0, "open"
    if h["filter"] == "FilterTerrain" or key in upland: typ, filt, mp, dmg, tag = "Hill", "FilterTerrain", 3, 15, "hill"
    if ff.get(f"{c},{r}", 0) >= 0.35 or (not ff and h["filter"] == "FilterForest"):
        typ, filt, mp, dmg, tag = "Forest", "FilterForest", 3, 25, "woods"
    if key in marsh: typ, filt, mp, dmg, tag = "Plain", "FilterAll", 4, 5, "marsh"
    if key in river: typ, filt, mp, dmg, tag = "River", "FilterRiver", 3, 0, "creek"
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
print("pike chains", [len(c) for c in PIKE_CHAINS], "continuous", all(chain_ok(c) for c in PIKE_CHAINS),
      "| hexes: pike", len(pike), "road", len(dirt - pike), "river", len(river), "rail", len(rail))
print(Counter(x["tag"].split("+")[0] for x in out), "wall", sum(x["stone_wall"] for x in out), "vp", [(x["col"], x["row"], x["city"]) for x in out if x["vp"]])
