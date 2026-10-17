#!/usr/bin/env python3
"""One-time migration (v0.4.2): re-index every hex-keyed Kernstown data file from the legacy grid
(<= v0.4.1: odd columns raised, 62x55) to the game's own convention (scripts/hex_grid.py: even columns
raised, rows north, 62x54). Hex centres on the ground do not move (<= 9 m, from the 4.42:5.1 pitch);
only the indices change: odd columns keep their row, even columns go down one row
(hex_grid.legacy_oddq_to_game). Legacy even row 0 and odd row 54 (half / fully off the painted map,
all open ground, no units) have no counterpart and are dropped.
Idempotent: files already carrying "grid_convention" == CONV are skipped."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from hex_grid import KERNSTOWN as G, legacy_oddq_to_game as L2G
CONV = "game-native: flat-top, rows north, even columns raised, 4.42:5.1 (v0.4.2)"
dropped = []

def m(h):
    n = L2G(int(h[0]), int(h[1]))
    if n is None: dropped.append(tuple(h))
    return None if n is None else [n[0], n[1]]
def mlist(lst): return [x for x in (m(h) for h in lst) if x is not None]
def mdict(d):
    n = L2G(int(d["col"]), int(d["row"]))
    if n is None: dropped.append((d["col"], d["row"])); return None
    d = dict(d); d["col"], d["row"] = n
    if "tile_name" in d: d["tile_name"] = f"SV_K_{n[0]}_{n[1]}"
    return d
def load(p): return json.loads((ROOT / p).read_text())
def save(p, obj, indent=None): (ROOT / p).write_text(json.dumps(obj, indent=indent) + ("\n" if indent else ""))

# 1. layers/kernstown_terrain_tags.json (user terrain decisions: upland "marsh_hexes" -> Hill, stone wall)
p = "layers/kernstown_terrain_tags.json"; t = load(p)
if t.get("grid_convention") != CONV:
    for k in ("marsh_hexes", "stone_wall_hexes", "stone_wall_confederate_hexes"): t[k] = mlist(t[k])
    t["stone_wall_hexsides"] = [x for x in (mdict(d) for d in t["stone_wall_hexsides"]) if x]
    t["stone_wall_hex_sides"] = [[m(a), m(b)] for a, b in t["stone_wall_hex_sides"] if m(a) and m(b)]
    ms = t.get("measurements", {})
    if "wall_hexes" in ms: ms["wall_hexes"] = mlist(ms["wall_hexes"])
    if "pritchard_hex" in ms: ms["pritchard_hex"] = m(ms["pritchard_hex"])
    t["winchester_courthouse_vp"]["hex"] = m(t["winchester_courthouse_vp"]["hex"])
    t["grid_convention"] = CONV; save(p, t, 2)
# 2. data/features/stone_wall_hexsides.json
p = "data/features/stone_wall_hexsides.json"; s = load(p)
if s.get("grid_convention") != CONV:
    s["hexsides"] = [x for x in (mdict(d) for d in s["hexsides"]) if x]
    s["confederate_hexes"] = mlist(s["confederate_hexes"]); s["grid_convention"] = CONV; save(p, s, 2)
# 3. data/layers/painted_forest_fraction.json  {"c,r": frac}
p = "data/layers/painted_forest_fraction.json"; f = load(p)
if f.get("_grid_convention") != CONV:
    out = {}
    for k, v in f.items():
        if k.startswith("_"): continue
        n = m(list(map(int, k.split(","))))
        if n: out[f"{n[0]},{n[1]}"] = v
    out["_grid_convention"] = CONV; save(p, out)
# 4. data/layers/kernstown_hexes.json (per-hex base table: hills, place flags)
p = "data/layers/kernstown_hexes.json"; b = load(p)
if b["grid"].get("convention") != CONV:
    b["hexes"] = sorted((x for x in (mdict(h) for h in b["hexes"]) if x), key=lambda h: (h["col"], h["row"]))
    b["grid"].update(cols=G.cols, rows=G.rows, orientation="flat-top, rows north, EVEN columns raised (game MapGO)",
                     convention=CONV, col_pitch_m=G.col_pitch_m, row_pitch_m=G.row_pitch_m, y0_m=G.y0_m)
    assert len(b["hexes"]) == G.cols * G.rows, len(b["hexes"])
    save(p, b)
# 5. layers/kernstown_hexes.json (legacy terrain-tag table) and data/basemap_meta.json measurements
p = "layers/kernstown_hexes.json"; lh = load(p)
if lh.get("grid_convention") != CONV:
    hx = {}
    for k, v in lh["hexes"].items():
        n = mdict(v)
        if n: hx[f"{n['col']},{n['row']}"] = n
    lh.update(cols=G.cols, rows=G.rows, hexes=hx, grid_convention=CONV); save(p, lh)
p = "data/basemap_meta.json"; bm = load(p)
if bm.get("grid_convention") != CONV:
    ms = bm.get("measurements", {})
    if "wall_hexes" in ms: ms["wall_hexes"] = mlist(ms["wall_hexes"])
    if "pritchard_hex" in ms: ms["pritchard_hex"] = m(ms["pritchard_hex"])
    bm["grid_convention"] = CONV; save(p, bm, 2)
print("migrated; dropped legacy hexes referenced:", sorted(set(dropped)))
