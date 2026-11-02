#!/usr/bin/env python3
"""Build a First Kernstown (23 March 1862) scenario for "Sekigahara 1600: Must Attack!" (Wargame Maker).

Inputs (all from the CivilWar1 repo, branch kernstown-map, unless noted):
  data/layers/kernstown_game.json        62x54 HoS terrain layer (250 yd, flat-top even-q)
  data/layers/painted_forest_fraction.json
  data/features/kernstown_features.json  lon/lat roads, creeks, stone wall, marsh, places
  data/dem/kernstown_3dep.tif            USGS 3DEP elevation
  data/assets/textures/*.png, sprites    painted tile art
  stock scenario (antietam1862.json)     only for the stock counter plates/icons and the city tile

Output: mKernstown1862_CW1.json  (compact JSON, UTF-8, no BOM, like the stock files)

Usage: python3 build_kernstown_ma.py --repo /path/to/CivilWar1 --stock /path/to/antietam1862.json --out out.json
"""
import argparse, base64, io, json, math, os, sys
from collections import Counter, defaultdict

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ma_grid import Grid, neighbor, edge_to  # noqa: E402

LANGS = ["ja", "en", "fr", "de", "es", "zh-Hans", "zh-Hant", "ko"]

# ---------------------------------------------------------------- board
# 300 m hexes, 32 x 36: Sandy Ridge / Middle Road (west) to Opequon Creek (east),
# Bartonsville (south) to Winchester (north).
WEST, NORTH, COLS, ROWS, HEX_M = -78.255, 39.192, 32, 36, 300.0
G = Grid(WEST, NORTH, COLS, ROWS, HEX_M)

# Stone wall: Ecelbarger and the ABT map put the wall Garnett held on the north crest of Sandy Ridge,
# running east from near the Glass farm.  The repo polyline is 1.5 km long; we keep the western
# eastern ~1 km, from the Glass farm to where the line meets the DEM ridge crest (ABT: Glass farm to the
# "target property"), i.e. 4 hexes at 300 m.
WALL_LON = (-78.2235, -78.2112)

# Woodland the HoS layer lacks: the wood on the north spur of Sandy Ridge that Tyler's brigade
# came through to reach the wall (ABT 2024 "19th-century woodline"; Hotchkiss H90).
EXTRA_WOODS = [
    [(-78.2335, 39.1500), (-78.2160, 39.1505), (-78.2120, 39.1560), (-78.2180, 39.1610),
     (-78.2330, 39.1600)],
]


def b64png(im, mode=None):
    buf = io.BytesIO()
    if mode:
        im = im.convert(mode)
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def seg_intersect(p1, p2, p3, p4):
    def cross(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2 = cross(p3, p4, p1), cross(p3, p4, p2)
    d3, d4 = cross(p1, p2, p3), cross(p1, p2, p4)
    return (d1 > 0) != (d2 > 0) and (d3 > 0) != (d4 > 0)


# ---------------------------------------------------------------- terrain
def classify_terrain(repo):
    sys.path.insert(0, os.path.join(repo, "scripts"))
    from hex_grid import KERNSTOWN as K
    import rasterio

    game = json.load(open(os.path.join(repo, "data/layers/kernstown_game.json")))
    hos = {(h["col"], h["row"]): h for h in game["hexes"]}
    ffrac = {tuple(map(int, k.split(","))): v
             for k, v in json.load(open(os.path.join(repo, "data/layers/painted_forest_fraction.json"))).items()
             if k[0].isdigit()}
    feats = json.load(open(os.path.join(repo, "data/features/kernstown_features.json")))
    marsh_polys = [[G.lonlat_to_xy(*p) for p in m["polygon"]] for m in feats["marshes"].values()]
    woods_polys = [[G.lonlat_to_xy(*p) for p in w] for w in EXTRA_WOODS]
    ds = rasterio.open(os.path.join(repo, "data/dem/kernstown_3dep.tif"))
    dem = ds.read(1)

    # Fine 10 m raster of the board for elevation; smoothed (150 m) to drop modern road cuts and
    # embankments, then compared with a 1.8 km mean: a topographic-position index (TPI) that picks
    # out Sandy Ridge and the Pritchard's Hill knoll and ignores the regional rise to the west.
    from scipy import ndimage
    from rasterio.transform import rowcol
    step = 10.0
    bw, bh = COLS * HEX_M + HEX_M, ROWS * G.rp + HEX_M
    xs = np.arange(0, bw, step)
    ys = np.arange(0, bh, step)
    X, Y = np.meshgrid(xs, ys)
    LON, LAT = G.west + X / G.mlon, G.north - Y / G.mlat
    rr, cc = rowcol(ds.transform, LON.ravel(), LAT.ravel())
    rr = np.clip(np.array(rr), 0, dem.shape[0] - 1)
    cc = np.clip(np.array(cc), 0, dem.shape[1] - 1)
    Z = dem[rr, cc].reshape(X.shape).astype(float)
    Zs = ndimage.gaussian_filter(Z, 15)
    TPI = Zs - ndimage.uniform_filter(Zs, 181)

    elev = np.zeros((ROWS, COLS))
    tpi = np.zeros((ROWS, COLS))
    stats = {}
    for r in range(ROWS):
        for q in range(COLS):
            pts = G.sample_points(q, r, 3)
            n = len(pts)
            c = Counter()
            fr = 0.0
            ev, tv = [], []
            for x, y in pts:
                lon, lat = G.xy_to_lonlat(x, y)
                hh = K.lonlat_to_hex(lon, lat)
                h = hos.get(hh)
                tag = h["tag"] if h else "open"
                if "town" in tag or ("village" in tag and lat > 39.17):
                    c["city"] += 1
                elif "village" in tag:
                    c["village"] += 1
                if "hill" in tag:
                    c["hill"] += 1
                if "woods" in tag:
                    fr += 1.0
                else:
                    fr += ffrac.get(hh, 0.0)
                if any(point_in_poly(x, y, p) for p in woods_polys):
                    fr += 1.0
                if any(point_in_poly(x, y, p) for p in marsh_polys):
                    c["marsh"] += 1
                j, i = min(int(y / step), Z.shape[0] - 1), min(int(x / step), Z.shape[1] - 1)
                ev.append(Zs[j, i])
                tv.append(TPI[j, i])
            elev[r, q] = np.mean(ev)
            tpi[r, q] = np.mean(tv)
            stats[(q, r)] = {"city": c["city"] / n, "village": c["village"] / n, "hill": c["hill"] / n,
                             "marsh": c["marsh"] / n, "forest": min(1.0, fr / n)}

    # the modern quarry NW of Kernstown (deep pit + spoil banks) is not 1862 ground
    pit = {(q, r) for r in range(ROWS) for q in range(COLS) if tpi[r, q] <= -12}
    def near_pit(q, r):
        return any(math.dist(G.center_xy(q, r), G.center_xy(*p)) <= 2.1 * HEX_M for p in pit)

    terrain = {}
    for r in range(ROWS):
        for q in range(COLS):
            s = stats[(q, r)]
            high = (tpi[r, q] >= 6.0 and not near_pit(q, r)) or s["hill"] >= 0.35
            if s["city"] >= 0.3:
                t = "city"
            elif s["village"] >= 0.3:
                t = "wasteland"   # hamlet/farmstead art, plain-like stats
            elif s["marsh"] >= 0.45 and tpi[r, q] <= -2:
                t = "marsh"
            elif s["forest"] >= 0.40:
                t = "rough" if high else "forest"
            elif high:
                t = "mountain"
            else:
                t = "plain"
            terrain[(q, r)] = t
    # drop isolated single high-ground hexes (noise), keep anything in a cluster of 2+
    for (q, r), t in list(terrain.items()):
        if t in ("mountain", "rough"):
            if not any(terrain.get(neighbor(q, r, e)) in ("mountain", "rough") for e in range(6)):
                terrain[(q, r)] = "plain" if t == "mountain" else "forest"
    return terrain, elev, tpi, feats


# ---------------------------------------------------------------- linear features
def simplify_chain(chain):
    """Drop repeats, loops and one-hex detours (a-b-c where a,c adjacent)."""
    out = []
    for h in chain:
        if h in out:
            out = out[: out.index(h) + 1]
            continue
        out.append(h)
        while len(out) >= 3 and edge_to(out[-3], out[-1]) is not None:
            del out[-2]
    return out


def add_path(edges, chain):
    for a, b in zip(chain, chain[1:]):
        if not (G.inside(*a) and G.inside(*b)):
            continue
        e = edge_to(a, b)
        if e is None:
            continue
        edges[a].add(e)
        edges[b].add((e + 3) % 6)


def build_features(feats):
    roads, rivers, trails, fences = (defaultdict(set) for _ in range(4))
    chains = {"roads": [], "rivers": [], "trails": [], "labels": []}
    def onboard(c):
        return [h for h in c if G.inside(*h)]
    for k in ("valley_pike", "middle_road", "cedar_creek_grade"):
        c = simplify_chain(G.trace(feats["roads"][k]["waypoints"]))
        add_path(roads, c)
        chains["roads"].append((k, onboard(c)))
    for k in ("apple_valley_road", "stone_lane"):
        c = simplify_chain(G.trace(feats["roads"][k]["waypoints"]))
        add_path(trails, c)
        chains["trails"].append(onboard(c))
    for k in ("opequon_creek", "hoge_run", "abrams_creek", "buffalo_lick"):
        c = simplify_chain(G.trace(feats["rivers"][k]["waypoints"]))
        add_path(rivers, c)
        chains["rivers"].append(onboard(c))
    rc = dict(chains["roads"])
    rv = dict(zip(("opequon_creek", "hoge_run", "abrams_creek", "buffalo_lick"), chains["rivers"]))
    chains["labels"] = [
        ("Valley Turnpike", rc["valley_pike"], 0.30, 34, "road"),
        ("Valley Turnpike", rc["valley_pike"], 0.80, 34, "road"),
        ("Middle Road", rc["middle_road"], 0.55, 30, "road"),
        ("Cedar Creek Grade", rc["cedar_creek_grade"], 0.45, 30, "road"),
        ("Opequon Creek", rv["opequon_creek"], 0.45, 36, "water"),
        ("Hoge Run", rv["hoge_run"], 0.70, 32, "water"),
        ("Abrams Creek", rv["abrams_creek"], 0.55, 32, "water"),
        ("Buffalo Lick", rv["buffalo_lick"], 0.50, 32, "water"),
    ]
    # trails never duplicate a road on the same hexside
    for h in list(trails):
        trails[h] -= roads.get(h, set())
    # Stone wall -> one-sided fences on the hexes the wall runs through, on their north-facing
    # edges (NW=4, NE=5), the side Tyler attacked from.  Same pattern as Antietam's Bloody Lane
    # (fences 4/5 on the lane hexes, nothing on the attacker's hexes).
    wall = [p for p in feats["stone_walls"]["glass_wall_sandy_ridge"]["waypoints"] if WALL_LON[0] <= p[0] <= WALL_LON[1]]
    # the wall runs almost due E-W, so take one hex row (nearest the mean line) across its extent
    pxy = [G.lonlat_to_xy(*p) for p in wall]
    r0 = round((sum(y for _, y in pxy) / len(pxy) - HEX_M / 2) / G.rp)
    x0, x1 = min(x for x, _ in pxy), max(x for x, _ in pxy)
    chain = [(q, r0) for q in range(COLS) if x0 - HEX_M / 4 <= G.center_xy(q, r0)[0] <= x1 + HEX_M / 4]
    for h in chain:
        for e in (4, 5):
            if neighbor(*h, e) not in chain:
                fences[h].add(e)
    return roads, rivers, trails, fences, chains


# ---------------------------------------------------------------- objectives
# VP values are listed identically for both sides (as every stock file does).
# initialControl: 0 = Union (first side), 1 = Confederate (second side), None = neutral
# (secondbullrun1862 "Groveton" / chancellorsville1863 pattern: boxes[15] = 0).
# Wall hexes are numbered west to east along the single wall row (see build_features):
# W0 = Glass farm end ... W3 = east end on the ridge crest.
VP_SITES = [
    # name, where, vp, initialControl
    ("Winchester", (-78.16444, 39.18389), 30, 0),
    ("Pritchard's Hill", (-78.2025, 39.1548), 20, 0),
    ("Kernstown", (-78.1978, 39.1425), 15, 0),
    ("Stone Wall", "W2", 15, None),        # v1: Confederate-held 15 on the middle hex
    ("Glass Farm", "W0", 5, None),         # v2: west end of the wall, Fulkerson's flank (new)
    ("Bartonsville", (-78.2100, 39.1160), 10, 1),
]
# Command points.  The editor's own help (user screenshot): "CP = holding it changes how many
# units a side may move per turn ... A plus CP (+3) raises your own cap."  Non-VP hexes only, as in
# every stock file.  v1 had a "+2" on the Sandy Ridge crest behind the wall: the playtest AI parked
# Garnett on it instead of the wall, so it moves onto the wall itself.
CP_SITES = [
    ("Stone Wall West", "W1", 2),
    ("Pike & Cedar Creek Grade", "grade", 2),
]
# Named hexes without VP (Antietam "North Woods", Malvern "Willis Church" pattern: name + boxes[9]).
# Places are the repo's own (data/features/kernstown_features.json places/fords) or the ABT map.
NAMED_SITES = [
    ("Sandy Ridge", (10, 21)),                       # crest just behind the wall (the v1 CP hex)
    ("Stone Wall East", "W3"),
    ("Opequon Church", (-78.1915, 39.1392)),
    ("Pritchard Farm", (-78.2015, 39.1418)),
    ("Milltown", (-78.175, 39.165)),
    ("Hoge Run Ford", (-78.19977, 39.14140)),
    ("Opequon Ford", (-78.172, 39.146)),
    ("Middle Road", (-78.2330, 39.1350)),
    ("Frederick County Courthouse", None),           # same hex as Winchester VP: skipped
    # v3: farmhouses marked as 19th-century structures on the American Battlefield Trust map
    # (First Kernstown, Sept. 2024 edition, data/historic_maps/First-Kernstown-ABT-2024.pdf).  Placed
    # by their offset on that map from Glass, Pritchard and Kernstown, so +/- 1 hex.
    ("Marcauley Farm", (12, 21)),
    ("Mahaney House", (15, 22)),
    ("Triplett House", (17, 22)),
]


# ---------------------------------------------------------------- units
# (side, leader, unit (counter label), kind, CS, MP, range, hex, standbyGroup)
# side 0 = Union (first), 1 = Confederate (second).  kind: inf/cav/art.
# Positions are explicit hexes (v2): the Confederate line is laid out against the wall row and the
# guns against Pritchard's Hill at a 3-hex range, so they are given by hex, not lon/lat.
# Strengths: one point per ~300 men (infantry/cavalry).  Batteries: CS 2, the stock value for a
# full battery (antietam/gainesmill/sevenpines range-2 units); Chew's 3-gun horse battery CS 1 (as
# Antietam's Pelham horse artillery).  Range 3 for field guns: stock range 2 at 500-700 m hexes is
# 1.0-1.4 km; at 300 m hexes the same ground is 3 hexes (range 3 is itself stock: Malvern Hill
# Hunt's reserve, Second Bull Run S.D. Lee).
UNITS = [
    # --- Union: Shields' division (Kimball commanding on the field).  ~6,300 inf+cav+arty engaged.
    # v3: field commanders as their own counters, the stock pattern ("Lee Army N. Va." CS 2 MP 4 in
    # gainesmill1862, "Porter V Corps HQ" CS 1 in malvernhill1862).  CS 1: a headquarters and escort.
    # Both are in hold groups (turn 0 / chance 0) so the AI keeps them back; a human moves them freely.
    (0, "Kimball", "Shields' Div. HQ", "hq", 1, 4, 1, (13, 14), 3),
    (0, "Kimball", "14 IN/84 PA", "inf", 3, 4, 1, (12, 16), 0),
    (0, "Kimball", "8 OH/67 OH", "inf", 3, 4, 1, (14, 16), 0),
    (0, "Jenks", "A 1 WV Bty", "art", 2, 3, 3, (13, 17), 0),
    (0, "Clark", "E 4 US Bty", "art", 2, 3, 3, (13, 17), 0),
    (0, "Robinson", "L 1 OH Bty", "art", 2, 3, 3, (13, 16), 0),
    (0, "Davey", "B 1 WV Bty", "art", 2, 3, 3, (16, 17), 0),    # v3: was (17,18), 1 rear hex
    (0, "Brodhead", "1 MI Cav", "cav", 1, 6, 1, (6, 12), 0),    # v3: was (7,12), 1 rear hex
    (0, "Brodhead", "OH/MD Cav", "cav", 1, 6, 1, (19, 21), 0),
    (0, "Sullivan", "13 IN/5 OH", "inf", 3, 4, 1, (19, 18), 2),
    (0, "Sullivan", "62 OH", "inf", 2, 4, 1, (20, 16), 2),
    (0, "Tyler", "7 OH/29 OH", "inf", 3, 4, 1, (19, 12), 1),
    (0, "Tyler", "7 IN/1 WV", "inf", 3, 4, 1, (20, 10), 1),
    (0, "Tyler", "110 PA", "inf", 2, 4, 1, (21, 8), 1),
    (0, "Sullivan", "39 IL", "inf", 1, 4, 1, (24, 14), 3),
    (0, "Huntington", "H 1 OH Bty", "art", 2, 3, 3, (22, 6), 3),
    # --- Confederate: Jackson's Valley District.  2,742 inf engaged, 290 cav, 18 of 27 guns.
    (1, "Jackson", "Valley District HQ", "hq", 1, 4, 1, (12, 24), 5),
    (1, "Ashby", "7 VA Cav", "cav", 1, 6, 1, (20, 24), 5),
    (1, "Chew", "Horse Bty", "art", 1, 3, 3, (20, 24), 5),
    (1, "Fulkerson", "23/37 VA", "inf", 2, 4, 1, (9, 21), 0),
    (1, "McLaughlin", "Rockbridge Bty", "art", 2, 3, 3, (12, 20), 0),
    (1, "Carpenter", "Alleghany Bty", "art", 2, 3, 3, (12, 20), 0),
    (1, "Garnett", "2/4/27 VA", "inf", 2, 4, 1, (10, 23), 0),   # v3: was (10,22), 1 rear hex
    (1, "Garnett", "5/33 VA", "inf", 2, 4, 1, (11, 22), 0),
    (1, "Waters", "W. Augusta Bty", "art", 2, 3, 3, (11, 21), 0),
    (1, "Burks", "21 VA/1 VA Bn", "inf", 2, 4, 1, (13, 27), 4),
    (1, "Burks", "42 VA", "inf", 1, 4, 1, (13, 28), 4),
    (1, "Marye", "Hampden Bty", "art", 2, 3, 3, (14, 28), 4),
    (1, "Lanier", "Danville Bty", "art", 2, 3, 3, (14, 29), 4),
]

STANDBY = [  # standby_groups[n-1] for standbyGroup n; Antietam schema
    # 1: Tyler's brigade, halted on the pike north of the toll gate at 2 PM; Kimball sent it west
    #    against Jackson's flank about 3:30-4 PM (v1: turn 3 / 40 / 30).
    {"side": 0, "turn": 4, "chance": 50, "rise": 25, "guardHexes": 0, "guardCs": 0},
    # 2: Sullivan, watching Ashby east of the pike; his regiments went to Sandy Ridge only late.
    {"side": 0, "turn": 6, "chance": 30, "rise": 25, "guardHexes": 0, "guardCs": 0},
    # 3: 39 IL and Huntington's battery, held in reserve and never sent in (Antietam's V Corps
    #    pattern: turn 0, chance 0).
    {"side": 0, "turn": 0, "chance": 0, "rise": 0, "guardHexes": 0, "guardCs": 0},
    # 4 (new): Burks' brigade with Marye's and Lanier's guns, Jackson's reserve near Bartonsville;
    #    Jackson brought it up to the wall about 5 PM (Seven Pines / Second Bull Run use side-1 groups).
    {"side": 1, "turn": 5, "chance": 40, "rise": 30, "guardHexes": 0, "guardCs": 0},
    # 5 (new): Ashby and Chew screening east of the pike, as they did all afternoon against Sullivan;
    #    held in place (turn 0 / chance 0, Malvern Hill's side-1 hold-group pattern) so the AI cannot
    #    throw them forward alone into Kernstown as it did in playtest 1.
    {"side": 1, "turn": 0, "chance": 0, "rise": 0, "guardHexes": 0, "guardCs": 0},
]


def place_units(occupied_ok):
    placed, count = [], Counter()
    for u in UNITS:
        h = u[7]
        assert G.inside(*h) and occupied_ok(h, u[0]) and count[h] < 2, (u, h)
        count[h] += 1
        placed.append((u, h))
    return placed


# ---------------------------------------------------------------- art
def hex_mask(size=180):
    m = Image.new("L", (size, size), 0)
    R = size / 2
    cx = cy = size / 2
    pts = [(cx + R * math.cos(math.radians(90 + 60 * i)), cy + R * math.sin(math.radians(90 + 60 * i))) for i in range(6)]
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


def load_tex(path, size=180):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    s = min(w, h)
    return im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((size, size), Image.LANCZOS)


def hachure(im, color=(92, 70, 40), n=7, alpha=120):
    """Short downslope ticks, the period way of showing a ridge."""
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    W = im.size[0]
    rng = np.random.default_rng(7)
    for row in range(n):
        y0 = W * (0.18 + 0.66 * row / (n - 1))
        for k in range(9):
            x = W * (0.12 + 0.76 * k / 8) + rng.uniform(-4, 4)
            d.line([(x, y0), (x + rng.uniform(-2, 2), y0 + W * 0.07)], fill=color + (alpha,), width=3)
    out = im.convert("RGBA")
    out.alpha_composite(ov)
    return out.convert("RGB")


def sprite(im, path, xy, h):
    sp = Image.open(path).convert("RGBA")
    sp = sp.resize((int(sp.width * h / sp.height), h), Image.LANCZOS)
    base = im.convert("RGBA")
    base.alpha_composite(sp, (int(xy[0] - sp.width / 2), int(xy[1] - sp.height / 2)))
    return base.convert("RGB")


def pixel_data(im):
    small = im.convert("RGB").resize((16, 16), Image.BOX)
    a = np.array(small)
    return [["#%02x%02x%02x" % tuple(a[y, x]) for x in range(16)] for y in range(16)]


def make_terrains(repo, stock):
    tx = os.path.join(repo, "data/assets/textures")
    spr = os.path.join(repo, "data/assets/sprites")
    pasture = load_tex(os.path.join(tx, "pasture.png"))
    wood = load_tex(os.path.join(tx, "woodland.png"))
    marsh = load_tex(os.path.join(tx, "marsh.png"))
    plowed = load_tex(os.path.join(tx, "plowed.png"))
    high = hachure(ImageEnhance.Brightness(pasture).enhance(0.92))
    rough = hachure(ImageEnhance.Brightness(wood).enhance(0.85), color=(60, 45, 25))
    village = sprite(plowed, os.path.join(spr, "house_limestone_0.png"), (70, 80), 52)
    village = sprite(village, os.path.join(spr, "house_brick_2.png"), (112, 104), 48)
    mask = hex_mask()

    def rec(tid, im, move, dfn, custom=None):
        t = im.convert("RGBA")
        t.putalpha(mask)
        r = {"id": tid, "type": "image"}
        if custom is not None:
            r["customId"] = custom
        r.update({"pixelData": pixel_data(im), "imageUrl": b64png(t), "renderedUrl": None,
                  "moveCost": move, "defenseMultiplier": dfn})
        return r

    stock_city = next(t for t in stock["assets"]["terrains"] if t["id"] == "city")
    city = dict(stock_city)
    city["moveCost"], city["defenseMultiplier"] = 1, 2
    # key order follows the stock records: default terrains without customId; mountain carries
    # customId 4 as in gettysburg1863.json and the user's own export.
    terr = [
        rec("plain", pasture, 1, 1),
        rec("forest", wood, 3, 1),
        rec("mountain", high, 2, 2, custom=4),     # open ridge / hill crest: gentle, so cost 2 not 4
        rec("rough", rough, 3, 2),                 # wooded ridge
        rec("marsh", marsh, 3, 1),
        city,
        {**{k: v for k, v in rec("wasteland", village, 1, 1).items() if k != "renderedUrl"}, "renderedUrl": None},
    ]
    # wasteland key order in stock: id,type,pixelData,imageUrl,moveCost,defenseMultiplier,renderedUrl
    return terr


FONT = os.environ.get("MA_COUNTER_FONT", "/usr/share/fonts/truetype/sand-box/google/Playfair Display/PlayfairDisplay-VariableFont_wght.ttf")


def font(px, weight):
    f = ImageFont.truetype(FONT, int(px))
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def data_img(s):
    return Image.open(io.BytesIO(base64.b64decode(s.split(",", 1)[1]))).convert("RGBA")


def make_range_badge(rng=3):
    """Small plate in the stock emblem slot (img_emb_nato_A is 104x68): "R3" = fires 3 hexes."""
    W, H = 136, 68
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 2, W - 3, H - 3], 10, fill=(239, 236, 226, 255), outline=(30, 30, 30, 255), width=5)
    d.text((W / 2, 33), "R%d" % rng, font=font(58, 900), fill=(20, 20, 20, 255), anchor="mm")
    return im


# NATO-style branch marks (APP-6 / FM 1-02): infantry = box with an X, cavalry = box with one
# diagonal, artillery = box with a filled dot; size mark above the box (III regiment(s), I battery).
# The format's template shapes are only "image" and "text" (all 2,368 image and 4,448 text shapes in
# the 8 stock files), so the marks are drawn into small images, like the stock img_emb_nato_A.
NATO_W, NATO_H = 312, 250
NATO_COLORS = {0: (244, 244, 240, 255), 1: (24, 24, 24, 255)}


def make_nato(kind, side):
    im = Image.new("RGBA", (NATO_W, NATO_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = NATO_COLORS[side]
    x0, y0, x1, y1 = 16, 56, NATO_W - 16, NATO_H - 10
    fill = (255, 255, 255, 40) if side == 0 else (255, 255, 255, 70)
    d.rectangle([x0, y0, x1, y1], fill=fill, outline=col, width=12)
    if kind in ("inf", "cav"):
        d.line([(x0 + 6, y1 - 6), (x1 - 6, y0 + 6)], fill=col, width=12)
    if kind == "inf":
        d.line([(x0 + 6, y0 + 6), (x1 - 6, y1 - 6)], fill=col, width=12)
    if kind == "art":
        cx, cy, rr = (x0 + x1) / 2, (y0 + y1) / 2, 34
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=col)
    ticks = 1 if kind == "art" else 3
    for i in range(ticks):
        x = NATO_W / 2 + (i - (ticks - 1) / 2) * 30
        d.rectangle([x - 6, 6, x + 6, 46], fill=col)
    return im


NATO_KEYS = {(k, s): "img_nato_%s_%s" % (k, "us" if s == 0 else "cs") for k in ("inf", "cav", "art") for s in (0, 1)}


def text_width_units(txt, fs, weight):
    k = 256 / 30.0
    f = font(fs * k, weight)
    return ImageDraw.Draw(Image.new("RGBA", (4, 4))).textlength(txt, font=f) / k


def render_counter(shapes, images, boxes):
    S = 256
    k = S / 30.0
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for sh in sorted(shapes, key=lambda s: s.get("z", 6)):
        if sh["type"] == "image":
            src = images[sh["imageRef"]]
            w, h = max(1, round(sh["w"] * k)), max(1, round(sh["h"] * k))
            sp = src.resize((w, h), Image.LANCZOS)
            im.alpha_composite(sp, (round(S / 2 + sh["x"] * k - w / 2), round(S / 2 + sh["y"] * k - h / 2)))
        else:
            txt = str(boxes[int(sh["link"][3:])])
            f = font(sh["fontSize"] * k, sh["fontWeight"])
            d = ImageDraw.Draw(im)
            d.text((S / 2 + sh["x"] * k, S / 2 + sh["y"] * k), txt, font=f, anchor="mm",
                   fill=sh["color"], stroke_width=max(1, round(sh["strokeWidth"] * k / 2)), stroke_fill=sh["strokeColor"])
    return b64png(im)


# ---------------------------------------------------------------- portraits (v3)
# Approved portraits from the repo's historical_data/portrait_manifest.csv (status PRESENT,
# audit_status approved_existing), read straight out of git (`git show <ref>:<path>`) so no portrait
# file is copied, renamed, overwritten or regenerated in the work tree.  Only a downscaled,
# head-and-shoulders crop is embedded in the scenario as a counter image layer.
PORTRAIT_REF = os.environ.get("MA_PORTRAIT_REF", "origin/main")
PORTRAITS = {  # counter leader (box3) -> (manifest officer, repo path on PORTRAIT_REF)
    "Jackson": ("Thomas J. Jackson", "mdl_CSA_TJJackson.png"),
    "Garnett": ("Richard B. Garnett", "mdl_CSA_RGarnett.png"),
    "Ashby": ("Turner Ashby", "mdl_CSA_TAshby.png"),
    "Kimball": ("Nathan Kimball", "reference/mdl_USA_NKimball.png"),
    "Tyler": ("Erastus B. Tyler", "reference/mdl_USA_EBTyler.png"),
    "Sullivan": ("Jeremiah C. Sullivan", "reference/mdl_USA_JCSullivan.png"),
}
# used only on the briefing maps (Shields was wounded on the 22nd and is not on the field)
MAP_PORTRAITS = {"Shields": ("James Shields", "reference/mdl_USA_JShields.png")}


def git_blob(repo, path, ref=PORTRAIT_REF):
    import subprocess
    raw = subprocess.run(["git", "-C", repo, "show", f"{ref}:{path}"], check=True, capture_output=True).stdout
    sha = subprocess.run(["git", "-C", repo, "rev-parse", f"{ref}:{path}"], check=True, capture_output=True,
                         text=True).stdout.strip()
    return Image.open(io.BytesIO(raw)).convert("RGBA"), sha


def portrait_crop(im, w=100, frame_col=(30, 26, 22, 255)):
    """Head and shoulders (top 200 of the 170x280 manifest portraits), framed, downscaled."""
    W0, H0 = im.size
    c = im.crop((0, 0, W0, min(H0, round(W0 * 200 / 170))))
    bg = Image.new("RGBA", c.size, (214, 204, 182, 255))
    bg.alpha_composite(c)
    h = round(w * bg.height / bg.width)
    out = bg.resize((w, h), Image.LANCZOS)
    ImageDraw.Draw(out).rectangle([0, 0, w - 1, h - 1], outline=frame_col, width=3)
    return out


def portrait_key(leader):
    return "img_portrait_" + leader.lower()


def template_shapes(side, kind, leader, uname, portrait=None):
    """v2 layout: commander (small, top), unit (large), NATO branch mark, CS bottom-left,
    MP bottom-right, range plate for guns.  Same plates, font and colours as the stock ACW counters.
    v3: HQ counters carry the commander's portrait in place of the branch mark; brigade counters of a
    commander with an approved portrait carry it small, left of a narrower branch mark."""
    if side == 0:
        plate, col, scol, sw = "img_side_253a69_nonato", "#ffffff", "#000000", 0.6
    else:
        plate, col, scol, sw = "img_side_b5b0a1_nonato", "#1b1b1b", "#efece2", 0.35
    def txt(link, z, x, y, fs, fw):
        return {"type": "text", "link": link, "z": z, "x": x, "y": y, "fontSize": fs, "color": col,
                "fontFamily": "Playfair Display", "fontWeight": fw, "strokeWidth": sw, "strokeColor": scol}
    fs_name = 4.6 if kind != "hq" else 3.6
    while fs_name > 3.0 and text_width_units(uname, fs_name, 900) > 26.0:
        fs_name = round(fs_name - 0.1, 1)
    fs_lead = 3.0 if kind != "hq" else 4.4
    while fs_lead > 2.4 and text_width_units(leader, fs_lead, 700) > 24.0:
        fs_lead = round(fs_lead - 0.1, 1)
    shapes = [{"type": "image", "z": 0, "x": 0, "y": 0, "w": 30, "h": 30, "imageRef": plate},
              txt("box3", 1, 0, -11.2, fs_lead, 700 if kind != "hq" else 900),
              txt("box4", 2, 0, -7.0 if kind != "hq" else -7.4, fs_name, 900 if kind != "hq" else 700),
              txt("box5", 3, -10.0, 9.4, 6.2, 900), txt("box6", 4, 10.0, 9.4, 6.2, 900)]
    if kind == "hq":
        shapes.append({"type": "image", "x": 0, "y": 2.4, "w": 10.6, "h": 12.4, "imageRef": portrait, "z": 5})
        return shapes
    if kind == "art":
        shapes.append({"type": "image", "x": 0, "y": 10.4, "w": 7.0, "h": 3.5, "imageRef": "img_emb_range3"})
    if portrait:
        shapes.append({"type": "image", "x": -8.4, "y": 1.6, "w": 7.8, "h": 9.2, "imageRef": portrait, "z": 6})
        shapes.append({"type": "image", "x": 4.0, "y": 1.6, "w": 11.0, "h": 8.8, "imageRef": NATO_KEYS[(kind, side)], "z": 5})
    else:
        shapes.append({"type": "image", "x": 0, "y": 1.6, "w": 12.0, "h": 9.6, "imageRef": NATO_KEYS[(kind, side)], "z": 5})
    return shapes


# ---------------------------------------------------------------- briefing maps (1000x640, stock style)
PAPER = (233, 221, 196)


def frame(d, W, H):
    d.rectangle([3, 3, W - 4, H - 4], outline=(90, 75, 55), width=3)
    d.rectangle([9, 9, W - 10, H - 10], outline=(90, 75, 55), width=1)
    d.line([(950, 70), (950, 25)], fill=(70, 55, 40), width=3)
    d.polygon([(944, 34), (956, 34), (950, 22)], fill=(70, 55, 40))


FELL = "/usr/share/fonts/truetype/sand-box/google/IM Fell English SC/IMFellEnglishSC-Regular.ttf"


def fell(px):
    try:
        return ImageFont.truetype(FELL, px)
    except OSError:
        return font(px, 700)


def period_finish(im, seed=7):
    """v3: aged paper, a faint grain and a darker rim, like the engraved maps of the period."""
    W, H = im.size
    rng = np.random.default_rng(seed)
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    a += rng.normal(0, 5.0, (H, W, 1))
    yy, xx = np.mgrid[0:H, 0:W]
    rim = np.clip((np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)) - 0.75) / 0.6, 0, 1)
    a *= (1 - 0.22 * rim)[..., None]
    a[..., 2] *= 0.97
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def medallion(im, repo, spec, xy, caption, sub, w=96):
    """Portrait copy (downscaled from the repo's approved file, read from git) with a caption."""
    officer, path = spec
    src, sha = git_blob(repo, path)
    p = portrait_crop(src, w, frame_col=(70, 55, 40, 255)).convert("RGB")
    d = ImageDraw.Draw(im)
    bw = max(p.width, d.textlength(caption, font=fell(17)), d.textlength(sub, font=fell(13))) + 16
    x0, y = xy                       # xy = top-left of the caption box
    x = round(x0 + (bw - p.width) / 2)
    d.rectangle([x0, y - 6, x0 + bw, y + p.height + 44], fill=(240, 231, 208), outline=(90, 75, 55), width=2)
    im.paste(p, (x, y))
    d.text((x0 + bw / 2, y + p.height + 13), caption, font=fell(17), fill=(50, 38, 26), anchor="mm")
    d.text((x0 + bw / 2, y + p.height + 31), sub, font=fell(13), fill=(80, 64, 46), anchor="mm")
    MAP_PORTRAIT_LOG.append({"officer": officer, "path": path, "ref": PORTRAIT_REF, "blob": sha, "where": caption})


def cartouche(d, x, y, lines):
    w = max(d.textlength(t, font=fell(fs)) for t, fs in lines) + 36
    h = sum(fs + 8 for _, fs in lines) + 18
    d.rectangle([x, y, x + w, y + h], fill=(240, 231, 208), outline=(90, 75, 55), width=3)
    d.rectangle([x + 5, y + 5, x + w - 5, y + h - 5], outline=(90, 75, 55), width=1)
    yy = y + 12
    for t, fs in lines:
        d.text((x + w / 2, yy + fs / 2), t, font=fell(fs), fill=(50, 38, 26), anchor="mm")
        yy += fs + 8


def region_map(repo=None):
    W, H = 1000, 640
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    # schematic, north up; Lower Shenandoah Valley, March 1862
    def ll(lon, lat):  # -78.6..-77.7, 38.85..39.45
        return ((lon + 78.65) / 0.95 * W, (39.45 - lat) / 0.62 * H)
    potomac = [(-78.65, 39.42), (-78.3, 39.44), (-78.0, 39.41), (-77.75, 39.33)]
    shen = [(-78.62, 38.9), (-78.35, 38.93), (-78.18, 38.98), (-78.05, 39.10), (-77.93, 39.25), (-77.75, 39.33)]
    d.line([ll(*p) for p in potomac], fill=(95, 135, 165), width=7)
    d.line([ll(*p) for p in shen], fill=(95, 135, 165), width=4)
    for lat in np.linspace(38.92, 39.30, 9):  # Blue Ridge
        x, y = ll(-77.86 + (lat - 39.1) * 0.25, lat)
        d.polygon([(x - 14, y + 12), (x + 14, y + 12), (x, y - 14)], fill=(160, 135, 105))
    for lat in np.linspace(38.86, 39.05, 5):  # Massanutten
        x, y = ll(-78.42 + (lat - 38.95) * 0.9, lat)
        d.polygon([(x - 12, y + 10), (x + 12, y + 10), (x, y - 12)], fill=(160, 135, 105))
    pike = [(-78.60, 38.86), (-78.36, 38.99), (-78.29, 39.04), (-78.20, 39.13), (-78.165, 39.185), (-78.03, 39.31), (-77.95, 39.40)]
    d.line([ll(*p) for p in pike], fill=(150, 115, 75), width=3)
    for lon, lat in [(-78.165, 39.185), (-78.36, 38.99), (-78.197, 39.14), (-77.74, 39.32), (-78.29, 39.04)]:
        x, y = ll(lon, lat)
        d.rectangle([x - 6, y - 6, x + 6, y + 6], fill=(250, 246, 235), outline=(70, 55, 40), width=2)
    # Jackson's approach from Strasburg; Banks' divisions leaving east for Manassas
    d.line([ll(-78.33, 39.0), ll(-78.215, 39.115)], fill=(175, 85, 75), width=5)
    x, y = ll(-78.215, 39.115)
    d.polygon([(x, y), (x - 18, y + 4), (x - 8, y + 16)], fill=(175, 85, 75))
    d.line([ll(-78.12, 39.20), ll(-77.80, 39.20)], fill=(95, 120, 175), width=5)
    x, y = ll(-77.80, 39.20)
    d.polygon([(x, y - 9), (x, y + 9), (x + 16, y)], fill=(95, 120, 175))
    im = period_finish(im, 11)
    d = ImageDraw.Draw(im)
    frame(d, W, H)
    cartouche(d, 24, 22, [("The Lower Valley", 26), ("Virginia, March 1862", 16)])
    if repo:
        medallion(im, repo, PORTRAITS["Jackson"], (22, 200), "Maj. Gen. T. J. Jackson", "Valley District")
        medallion(im, repo, MAP_PORTRAITS["Shields"], (600, 436), "Brig. Gen. J. Shields", "wounded 22 March")
    def fr(lon, lat):
        x, y = ll(lon, lat)
        return round(x / W, 4), round(y / H, 4)
    labels = [
        (fr(-78.215, 39.143), "battle", "KERNSTOWN"),
        (fr(-78.15, 39.20), "city", "Winchester (Banks' HQ until 22 March)"),
        (fr(-78.36, 38.975), "city", "Strasburg (Jackson, 22 March)"),
        (fr(-77.74, 39.30), "city", "Harpers Ferry"),
        (fr(-78.30, 39.06), "force", "Jackson, 36 miles in two days"),
        (fr(-77.95, 39.17), "force", "Williams' division, leaving for Manassas"),
        (fr(-78.15, 39.44), "force", "Potomac River"),
        (fr(-77.86, 39.05), "force", "Blue Ridge"),
        (fr(-78.45, 38.89), "force", "Massanutten"),
        (fr(-78.45, 39.15), "force", "Valley Pike"),
    ]
    return im, labels


def battle_map(terrain, roads, rivers, vp_hexes, repo=None, wall=()):
    W, H = 1000, 640
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    bw, bh = G.cols * HEX_M + HEX_M / 2, G.rows * G.rp + HEX_M / 2
    sc = min((W - 40) / bw, (H - 40) / bh)
    ox, oy = (W - bw * sc) / 2, (H - bh * sc) / 2
    def P(q, r):
        x, y = G.center_xy(q, r)
        return ox + x * sc, oy + y * sc
    for (q, r), t in terrain.items():
        x, y = P(q, r)
        rad = HEX_M * sc * 0.62
        if t in ("forest", "rough"):
            d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=(150, 168, 120))
        elif t == "mountain":
            d.ellipse([x - rad * 0.7, y - rad * 0.7, x + rad * 0.7, y + rad * 0.7], fill=(205, 185, 150))
        elif t == "city":
            d.rectangle([x - rad * .5, y - rad * .5, x + rad * .5, y + rad * .5], fill=(250, 246, 235), outline=(70, 55, 40))
    for edges, col, w in ((rivers, (95, 135, 165), 4), (roads, (150, 115, 75), 3)):
        for h, es in edges.items():
            for e in es:
                d.line([P(*h), P(*neighbor(*h, e))], fill=col, width=w)
    def arrow(pts, col):
        pts = [P(*G.lonlat_to_hex(*p)) for p in pts]
        d.line(pts, fill=col, width=5)
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        a = math.atan2(y1 - y0, x1 - x0)
        d.polygon([(x1 + 12 * math.cos(a), y1 + 12 * math.sin(a)),
                   (x1 + 10 * math.cos(a + 2.4), y1 + 10 * math.sin(a + 2.4)),
                   (x1 + 10 * math.cos(a - 2.4), y1 + 10 * math.sin(a - 2.4))], fill=col)
    if wall:  # the stone wall, drawn heavy along the north side of its hexes
        pts = [P(*h) for h in wall]
        off = HEX_M * sc * 0.45
        pts = [(x, y - off) for x, y in pts]
        d.line(pts, fill=(60, 48, 38), width=7)
        for x, y in pts:
            d.line([(x - 4, y - 5), (x + 4, y + 5)], fill=(240, 231, 208), width=2)
    arrow([(-78.205, 39.122), (-78.222, 39.135), (-78.222, 39.146)], (175, 85, 75))      # Jackson to the ridge
    arrow([(-78.186, 39.165), (-78.205, 39.160), (-78.219, 39.152)], (95, 120, 175))      # Tyler to the wall
    for h in vp_hexes:
        x, y = P(*h)
        d.rectangle([x - 6, y - 6, x + 6, y + 6], fill=(250, 246, 235), outline=(70, 55, 40), width=2)
    im = period_finish(im, 13)
    d = ImageDraw.Draw(im)
    frame(d, W, H)
    cartouche(d, 20, 22, [("Kernstown", 26), ("23 March 1862", 16)])
    if repo:
        medallion(im, repo, PORTRAITS["Kimball"], (812, 140), "Col. N. Kimball", "commanding on the field")
        medallion(im, repo, PORTRAITS["Garnett"], (24, 400), "Brig. Gen. R. B. Garnett", "Stonewall Brigade")
    def fr(lon, lat):
        x, y = P(*G.lonlat_to_hex(lon, lat))
        return round(x / W, 4), round(y / H, 4)
    labels = [
        (fr(-78.166, 39.188), "city", "Winchester"),
        (fr(-78.190, 39.1395), "city", "Kernstown"),
        (fr(-78.196, 39.158), "battle", "Pritchard's Hill (Union guns)"),
        (fr(-78.232, 39.146), "battle", "The stone wall"),
        (fr(-78.228, 39.128), "force", "Sandy Ridge"),
        (fr(-78.18, 39.17), "force", "Tyler (arrives 2 PM)"),
        (fr(-78.21, 39.112), "force", "Jackson"),
        (fr(-78.18, 39.135), "force", "Ashby (east of the pike)"),
        (fr(-78.150, 39.15), "force", "Opequon Creek"),
    ]
    return im, labels


def labels_json(labels):
    return [{"x": x, "y": y, "kind": k, "text": {l: t for l in LANGS}} for (x, y), k, t in labels]


# ---------------------------------------------------------------- description
DESCRIPTION = """23 March 1862, a cold Sunday afternoon. Kernstown, Frederick County, Virginia, four miles south of Winchester on the Valley Turnpike.

Turner Ashby's troopers have watched Winchester all week. On Saturday evening they skirmished with what they took to be a rear guard, and Ashby sent word to Jackson: four regiments left, the rest of Banks' army gone east. Jackson has marched his 3,000 infantry thirty-six miles in two days to keep those troops in the Valley. Ashby is wrong by about 6,000 men. James Shields' whole division is still here. Shields himself was struck by a shell fragment in that Saturday skirmish, his arm broken, and lies in Winchester; Colonel Nathan Kimball, an Indiana doctor, fights the battle for him from Pritchard's Hill.

[If you command the Union: Kimball] You hold the high ground and you have the numbers: your own brigade and four batteries are up, Tyler's brigade is halted on the pike behind you, and Sullivan's regiments watch Ashby east of the road. Jackson has seen only part of your force. When his guns appear on Sandy Ridge he is trying to turn your right. Send Tyler west along the ridge to the stone wall, as Kimball did about 4 PM, and feed in what you can spare. Do not strip the pike: Winchester and Pritchard's Hill are worth more than the wall.

[If you command the Confederates: Jackson] You attack because you believe the enemy is weak, and by the time you learn otherwise you are committed. Fulkerson's small brigade leads onto Sandy Ridge, Garnett's Stonewall Brigade follows, and your guns on the ridge duel with Pritchard's Hill. The stone wall along the north crest is the place to stand. You cannot win by pushing straight up the pike into the Union guns; you score by holding the wall and Glass Farm and costing Kimball men. Burks' brigade is your only reserve. Keep a line of retreat open behind every regiment: when Garnett's men ran out of ammunition at dusk he pulled them back without orders, and Jackson never forgave him, but the brigade lived to fight again.

[The afternoon] Each turn is half an hour. Turn 1, 2:00 PM: Fulkerson and the guns on Sandy Ridge. Turn 4, 3:30 PM: a computer-run Tyler may start west. Turn 5, 4:00 PM: historically the Stonewall Brigade reached the wall about now; a computer-run Burks may come up, and the Union gains two moves a turn. Turn 6, 4:30 PM: a computer-run Sullivan may join. Turn 9, 6:00 PM: historically Garnett's line gave way about now. Sunset is at 6:15; turn 11, 7:00 PM, is night.

[How to win] The dividing line is Union +55, the score if nothing changes hands. The stone wall (15) and Glass Farm (5) start neutral; Pritchard's Hill (20), Kernstown (15) and Winchester (30) are Union, Bartonsville (10) Confederate. Holding the wall's west hex, and the junction of the pike and the Cedar Creek Grade, gives the holder two more moves a turn.

[Combat] This board uses its own combat table, gentler than the default. Between 1:2 and 2:1, the odds most Kernstown attacks were made at, a bad roll repulses the attacker (AR), a middling one is a stand-off (C) and a good one drives the defender back (DR). A unit is destroyed outright only at 5:1 or better on the best rolls, or attacking at 1:3 on a 1. A unit that must retreat and has no open hex behind it (enemy units, their zone of control, a full stack) is lost, so most losses come from being surrounded, not from the die. The wall hexes are high ground (defence x2) and can be held, but a beaten defender falls back from them instead of dying in place.

[Order of battle] Union, Shields' division, Col. Nathan Kimball. Kimball's brigade: 14th Indiana (Lt. Col. Harrow), 84th Pennsylvania (Col. Murray, killed), 8th Ohio (Col. Carroll), 67th Ohio (Lt. Col. Voris). Tyler's brigade, Col. Erastus Tyler: 7th and 29th Ohio, 7th Indiana, 1st West Virginia (Col. Thoburn), 110th Pennsylvania. Sullivan's brigade, Col. Jeremiah Sullivan: 13th Indiana, 5th Ohio, 62nd Ohio, 39th Illinois (not engaged). Brodhead's cavalry: 1st Michigan, Ohio and Maryland companies. Batteries: Jenks (A, 1st West Virginia), Clark (E, 4th U.S.), Robinson (L, 1st Ohio), Davey (B, 1st West Virginia), Huntington (H, 1st Ohio).
Confederate, Valley District, Maj. Gen. Thomas J. Jackson. Stonewall Brigade, Brig. Gen. Richard Garnett: 2nd (Col. Allen), 4th (Lt. Col. Ronald), 5th (Col. Harman), 27th (Col. Echols, wounded) and 33rd (Col. Cummings) Virginia, with McLaughlin's Rockbridge, Waters' West Augusta and Carpenter's Alleghany batteries. Burks' brigade, Col. Jesse Burks: 21st Virginia (Lt. Col. Patton), 42nd Virginia (Lt. Col. Langhorne), 1st Virginia Battalion (Irish), Marye's Hampden battery. Fulkerson's brigade, Col. Samuel Fulkerson: 23rd and 37th Virginia, Lanier's Danville battery. Ashby's 7th Virginia Cavalry and Chew's horse battery. Kimball and Jackson appear as headquarters counters (strength 1) with their portraits; they stand back unless a player moves them.

[Counters] Commander on top, unit in large type, the commander's portrait where one exists, the NATO branch mark (X infantry, / cavalry, dot artillery; III regiments, I battery), combat strength bottom left, movement bottom right. Batteries carry a RANGE 3 plate: they fire three hexes. One strength point is about 300 men; a full battery is 2. The board is about 300 m a hex, from Sandy Ridge in the west to Opequon Creek, and from Bartonsville north to Winchester. Sources: the reports of Jackson, Shields and Kimball in the Official Records (Series I, Vol. 12, Part 1); Gary Ecelbarger, "We Are in for It!"; the American Battlefield Trust map of First Kernstown (2024)."""


def thresholds(units, vp_values):
    """Fits all six stock scenarios exactly (inferred, not documented):
    operational = 0.2 * sum(CS of all units) + 0.4 * sum(VP), tactical = op / 8, strategic = 2 * op."""
    op = round(0.2 * sum(u["combatStrength"] for u in units) + 0.4 * sum(vp_values))
    return round(op / 8), op, 2 * op


# ---------------------------------------------------------------- assemble
def build(repo, stock_path, out_path, painted=None, art=True, art_png=None):
    stock = json.load(open(stock_path))
    terrain, elev, tpi, feats = classify_terrain(repo)
    roads, rivers, trails, fences, chains = build_features(feats)

    # the stone wall.  v2 made its hexes the stock "fortress" terrain; playtest 2 showed that a unit in
    # a fortress hex never retreats: all three logged results that differ from the CRT are DR or AR
    # turned into C for the unit standing in the wall hex (11,19).  So the only way out of the wall
    # was elimination (DE), the opposite of what happened at Kernstown, where Garnett fell back.
    # v3: the wall hexes are the ridge's own "mountain" terrain (defence x2, as fortress), keeping the
    # fences on their NW/NE edges, so DR/AR push units back off the wall instead of killing them.
    wall_hexes = sorted(fences, key=lambda h: h[0])
    for h in wall_hexes:
        terrain[h] = WALL_TERRAIN
    W = {f"W{i}": h for i, h in enumerate(wall_hexes)}

    def where(spec):
        if isinstance(spec, str) and spec in W:
            return W[spec]
        if spec == "grade":
            h = G.lonlat_to_hex(*feats["roads"]["cedar_creek_grade"]["waypoints"][-1])
            if h in vp:
                h = next(n for n in (neighbor(*h, e) for e in range(6)) if n in roads and n not in vp)
            return h
        if all(isinstance(v, int) for v in spec):
            return tuple(spec)
        return G.lonlat_to_hex(*spec)

    vp = {}
    for name, spec, val, ctl in VP_SITES:
        h = where(spec)
        if name == "Pritchard's Hill":  # snap to the knoll top in the DEM (within one hex)
            h = max([h] + [neighbor(*h, e) for e in range(6)], key=lambda c: tpi[c[1], c[0]])
        vp[h] = (name, val, ctl)
    cp = {}
    for name, spec, val in CP_SITES:
        h = where(spec)
        assert h not in vp, name
        cp[h] = (name, val)
    named = {}
    for name, spec in NAMED_SITES:
        if spec is None:
            continue
        h = where(spec)
        if h in vp or h in cp or h in named or not G.inside(*h):
            continue
        named[h] = name

    hexes = []
    for r in range(ROWS):
        for q in range(COLS):
            h = (q, r)
            boxes = [0] * 20
            name = ""
            isvp = h in vp
            vpv = vp[h][1] if isvp else 0
            ctl = vp[h][2] if isvp else None
            ppv = cp[h][1] if h in cp else 0
            if isvp:
                name = vp[h][0]
                boxes[9], boxes[10], boxes[11], boxes[15] = name, vpv, vpv, (0 if ctl is None else ctl + 1)
            elif h in cp:
                name = cp[h][0]
                boxes[9], boxes[16], boxes[17] = name, "+%d" % ppv, "+%d" % ppv
            elif h in named:
                name = named[h]
                boxes[9] = name
            rd, rv, tr, fe = (sorted(x.get(h, ())) for x in (roads, rivers, trails, fences))
            hexes.append({
                "id": f"{q}-{r}", "q": q, "r": r, "terrainId": terrain[h],
                "hasRiver": bool(rv), "hasRoad": bool(rd), "rivers": rv, "roads": rd, "trails": tr,
                "majorRivers": [], "fences": fe, "isVPLocation": isvp,
                "vp": {"first": vpv, "second": vpv}, "pp": {"first": ppv, "second": ppv},
                "suddenDeath": {"first": False, "second": False, "both": False},
                "exitHex": {"first": False, "second": False}, "initialControl": ctl,
                "name": name, "boxes": boxes})

    # units & templates
    images_raw = {k: data_img(v) for k, v in stock["assets"]["images"].items()}
    images_raw["img_emb_range3"] = make_range_badge(3)
    for (kind, side), key in NATO_KEYS.items():
        images_raw[key] = make_nato(kind, side)
    used_imgs = ["img_side_253a69_nonato", "img_side_b5b0a1_nonato", "img_emb_range3"] + sorted(NATO_KEYS.values())
    PORTRAIT_LOG.clear()
    MAP_PORTRAIT_LOG.clear()
    leaders_used = {u[1] for u in UNITS}
    for leader, (officer, path) in sorted(PORTRAITS.items()):
        if leader not in leaders_used:
            continue
        src, sha = git_blob(repo, path)
        key = portrait_key(leader)
        images_raw[key] = portrait_crop(src)
        used_imgs.append(key)
        PORTRAIT_LOG[leader] = {"officer": officer, "path": path, "ref": PORTRAIT_REF, "blob": sha,
                                "imageRef": key, "size": images_raw[key].size, "units": []}
    images = {k: (stock["assets"]["images"][k] if k in stock["assets"]["images"] else b64png(images_raw[k]))
              for k in used_imgs}

    placed = place_units(lambda h, side: G.inside(*h))
    units, templates = [], []
    for i, ((side, leader, uname, kind, cs, mp, rng, _h, sb), (q, r)) in enumerate(placed, 1):
        full = f"{leader} {uname}"
        boxes = [side, 0, i, leader, uname, cs, mp, rng] + [0] * 12
        tid = f"local_{i}"
        pk = portrait_key(leader) if leader in PORTRAIT_LOG else None
        if pk:
            PORTRAIT_LOG[leader]["units"].append(full)
        shapes = template_shapes(side, kind, leader, uname, pk)
        templates.append({"id": tid, "name": full, "isLocal": True,
                          "visuals": {"shapes": shapes, "renderedUrl": render_counter(shapes, images_raw, boxes)}})
        units.append({"id": i, "q": q, "r": r, "side": side, "combatStrength": cs, "movePoints": mp, "range": rng,
                      "name": full, "boxId": 0, "entryHex": "", "entryTurn": 0, "betrayalTurn": 0,
                      "betrayalChance": 0, "betrayalRise": 0, "suddenDeathUnit": False, "standbyGroup": sb,
                      "eliteUnit": False, "exitPoints": 0, "boxes": boxes, "templateId": tid})

    rmap, rlabels = region_map(repo)
    bmap, blabels = battle_map(terrain, roads, rivers, list(vp), repo, wall_hexes)
    sides_en = ["Union (Shields' Division, Kimball)", "Confederate (Jackson's Valley District)"]
    tac, op, strat = thresholds(units, [v[1] for v in vp.values()])

    meta = {
        "version": "2.0",
        "exportedAt": "2026-11-02T00:00:00.000Z",
        "description": {l: DESCRIPTION for l in LANGS},
        "briefingImage": "",
        "scaleMeters": 300, "scaleMinutes": 30, "scaleMen": 300,
        "scenarioName": "Kernstown 1862 (CivilWar1)" if art else "Kernstown 1862 (CivilWar1, no art)",
        "gameId": "mustattack",
        "regionMap": {"image": b64png(rmap.convert("P", palette=Image.ADAPTIVE, colors=64)), "labels": labels_json(rlabels)},
        "battleMap": {"image": b64png(bmap.convert("P", palette=Image.ADAPTIVE, colors=64)), "labels": labels_json(blabels)},
    }
    art_info = None
    if art:
        from board_art import make_board_art
        im, png, bmeta, src = make_board_art(G, terrain, chains, fences, elev, painted)
        meta["boardArt"] = {**bmeta, "image": "data:image/png;base64," + base64.b64encode(png).decode()}
        if art_png:
            open(art_png, "wb").write(png)
        art_info = (src, im.size, len(png))

    scenario = {
        # Antietam's pair (Union attacking a held line with fences: "line" vs "brk").  v1 used
        # def/off; "off" sent the Confederates into 1:2 attacks in playtest 1.  Meanings inferred.
        "doctrine": {"blue": "line", "red": "brk"},
        "meta": meta,
        "scenario": {
            "name": meta["scenarioName"],
            "sideNames": ["Union", "Confederate"],
            "sideNamesByLang": {l: sides_en for l in LANGS},
            "sideColors": ["#253A69", "#B5B0A1"],
            "firstMove": "second",
            "maxTurns": 11,
            "turnClock": [{"turn": 1, "date": "3/23", "time": "14:00"}],
            "rules": {
                "fix_rules": False, "retreat_control": 0, "retreat_distance": 1, "stacking_limit": 2,
                "max_advance_units": 2, "zoc_exit_allowed": False, "full_move_entry_allowed": False,
                "activation_limit": {"first": 5, "second": 6},
                "activation_steps": {"first": [{"turn": 5, "add": 2}], "second": []},
                "replacement": False,
                "night_turns": [11],
                "standby_groups": STANDBY,
                "crt": CRT,
            },
            "map": {"width": COLS, "height": ROWS, "hexes": hexes},
            "units": units,
        },
        "victoryCondition": {"winLine": WIN_LINE, "tacticalThreshold": tac, "operationalThreshold": op,
                             "strategicThreshold": strat},
        "assets": {"terrains": make_terrains(repo, stock), "images": images, "unitTemplates": templates},
    }
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(scenario, f, ensure_ascii=False, separators=(",", ":"))
    return scenario, art_info


# Score at the start if nothing changes hands (Union VP held - Confederate VP held): 65 - 10 = 55.
# winLine is author-set in every stock file near the historical result; Kimball's win was holding
# his ground and taking the wall, so a Union side that keeps what it has and wins the wall scores
# ~75 (tactical win) and a Jackson who holds wall + Glass Farm until dark scores ~35.
WIN_LINE = 55
WALL_TERRAIN = "mountain"
PORTRAIT_LOG = {}
MAP_PORTRAIT_LOG = []

# ---------------------------------------------------------------- combat results table (v3)
# rules.crt: 8 rows x 6 columns, the shape of the only two stock tables (gettysburg1863 and
# chancellorsville1863, identical).  Orientation, from the four saves we have (40 logged combats,
# playtest 1 and 2, Gaines' Mill, Waterloo; none of those scenarios has its own crt): every logged
# result equals stock_crt[odds_row][die - 1] with rows 1:3, 1:2, 1:1, 2:1, 3:1, 4:1, 5:1, 6:1 and
# columns die 1..6 (37 of 37 combats outside a fortress hex; the 3 others are the fortress C cases).
# So the stock table is also the built-in default, and a high die is good for the attacker.
# Default: 3 AE, 15 DE cells.  This table: 1 AE (1:3, die 1), 3 DE (5:1 die 6, 6:1 die 5-6);
# at 1:2 to 2:1, the odds a Kernstown attack is fought at, a bad roll is a repulse (AR), a middling
# one a stand-off (C) and a good one drives the defender back (DR), never an outright kill.
CRT = [
    ["AE", "AR", "AR", "AR", "AR", "C"],    # 1:3
    ["AR", "AR", "AR", "C", "C", "DR"],     # 1:2
    ["AR", "AR", "C", "C", "DR", "DR"],     # 1:1
    ["AR", "C", "C", "DR", "DR", "DR"],     # 2:1
    ["C", "C", "DR", "DR", "DR", "DR"],     # 3:1
    ["C", "DR", "DR", "DR", "DR", "DR"],    # 4:1
    ["DR", "DR", "DR", "DR", "DR", "DE"],   # 5:1
    ["DR", "DR", "DR", "DR", "DE", "DE"],   # 6:1
]

DEFAULT_PAINTED = os.environ.get("KERNSTOWN_BASEMAP", "/workspace/CivilWar1-work/data/basemap_painted_full.png")

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.abspath(os.path.join(here, "..", "..")))
    ap.add_argument("--stock", default=os.path.join(here, "ref", "antietam1862.json"),
                    help="stock Antietam scenario exported from the game (not committed)")
    ap.add_argument("--basemap", default=DEFAULT_PAINTED,
                    help="repo painted basemap (data/basemap_painted_full.png, gitignored; built by "
                         "painted_sections/build_full_map.py). Missing -> plain parchment ground.")
    ap.add_argument("--out", default=os.path.join(here, "mKernstown1862_CW1.json"))
    ap.add_argument("--out-noart", default=os.path.join(here, "mKernstown1862_CW1_noart.json"))
    ap.add_argument("--art-png", default=os.path.join(here, "board_art.png"))
    a = ap.parse_args()
    for out, art in ((a.out, True), (a.out_noart, False)):
        s, info = build(a.repo, a.stock, out, a.basemap, art, a.art_png if art else None)
        t = Counter(h["terrainId"] for h in s["scenario"]["map"]["hexes"])
        print("wrote", out, os.path.getsize(out), "bytes;", dict(t), "art:", info, s["victoryCondition"])
