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
    for k in ("valley_pike", "middle_road", "cedar_creek_grade"):
        add_path(roads, simplify_chain(G.trace(feats["roads"][k]["waypoints"])))
    for k in ("apple_valley_road", "stone_lane"):
        add_path(trails, simplify_chain(G.trace(feats["roads"][k]["waypoints"])))
    for k in ("opequon_creek", "hoge_run", "abrams_creek", "buffalo_lick"):
        add_path(rivers, simplify_chain(G.trace(feats["rivers"][k]["waypoints"])))
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
    return roads, rivers, trails, fences


# ---------------------------------------------------------------- objectives
# VP values are listed identically for both sides (as every stock file does).
# initialControl: 0 = Union (first side), 1 = Confederate (second side).
VP_SITES = [
    # name, lon, lat, vp, initialControl
    ("Winchester", -78.16444, 39.18389, 30, 0),
    ("Pritchard's Hill", -78.2025, 39.1548, 20, 0),
    ("Kernstown", -78.1978, 39.1425, 15, 0),
    ("Stone Wall", None, None, 15, 1),          # placed on the middle wall hex
    ("Bartonsville", -78.2100, 39.1160, 10, 1),
]
# Command points (Gettysburg pattern: non-VP hex, pp both sides, initialControl None).
CP_SITES = [
    ("Sandy Ridge crest", None, None, 2),          # ridge crest just south of the wall (artillery line)
    ("Pike & Cedar Creek Grade", None, None, 2),   # junction Tyler used to come onto the field
]


# ---------------------------------------------------------------- units
# (side, leader, unit, kind, CS, MP, range, lon, lat, standbyGroup)
# side 0 = Union (first), 1 = Confederate (second).  kind: inf/cav/art.
UNITS = [
    # --- Union: Shields' division (Kimball commanding on the field).  ~6,300 inf+cav+arty engaged.
    (0, "Kimball", "14 IN / 84 PA", "inf", 3, 4, 1, -78.2010, 39.1545, 0),
    (0, "Kimball", "8 OH / 67 OH", "inf", 3, 4, 1, -78.1975, 39.1500, 0),
    (0, "Jenks", "A 1 WV Lt Arty", "art", 1, 3, 2, -78.2040, 39.1560, 0),
    (0, "Clark", "E 4 US Arty", "art", 1, 3, 2, -78.2020, 39.1575, 0),
    (0, "Robinson", "L 1 OH Lt Arty", "art", 1, 3, 2, -78.1995, 39.1535, 0),
    (0, "Davey", "B 1 WV Lt Arty", "art", 1, 3, 2, -78.1925, 39.1470, 0),
    (0, "Brodhead", "1 MI Cav", "cav", 1, 6, 1, -78.2290, 39.1640, 0),
    (0, "Brodhead", "Ohio/Md/WV Cav", "cav", 1, 6, 1, -78.1850, 39.1420, 0),
    (0, "Sullivan", "13 IN / 5 OH", "inf", 3, 4, 1, -78.1880, 39.1480, 2),
    (0, "Sullivan", "62 OH", "inf", 2, 4, 1, -78.1840, 39.1520, 2),
    (0, "Tyler", "7 OH / 29 OH", "inf", 3, 4, 1, -78.1870, 39.1640, 1),
    (0, "Tyler", "7 IN / 1 WV", "inf", 3, 4, 1, -78.1835, 39.1675, 1),
    (0, "Tyler", "110 PA", "inf", 2, 4, 1, -78.1805, 39.1710, 1),
    (0, "Sullivan", "39 IL", "inf", 1, 4, 1, -78.1700, 39.1580, 3),
    (0, "Huntington", "H 1 OH Lt Arty", "art", 1, 3, 2, -78.1755, 39.1760, 3),
    # --- Confederate: Jackson's Valley District.  2,742 inf engaged, 290 cav, 18 of 27 guns.
    (1, "Ashby", "7 VA Cav", "cav", 1, 6, 1, -78.1880, 39.1340, 0),
    (1, "Chew", "Horse Arty", "art", 1, 3, 2, -78.1920, 39.1310, 0),
    (1, "Fulkerson", "23 / 37 VA", "inf", 2, 4, 1, -78.2150, 39.1300, 0),
    (1, "McLaughlin", "Rockbridge Arty", "art", 1, 3, 2, -78.2190, 39.1330, 0),
    (1, "Carpenter", "Alleghany Arty", "art", 1, 3, 2, -78.2120, 39.1340, 0),
    (1, "Garnett", "2 / 4 / 27 VA", "inf", 2, 4, 1, -78.2110, 39.1250, 0),
    (1, "Garnett", "5 / 33 VA", "inf", 2, 4, 1, -78.2070, 39.1220, 0),
    (1, "Waters", "W. Augusta Arty", "art", 1, 3, 2, -78.2050, 39.1260, 0),
    (1, "Burks", "21 VA / 1 VA Bn", "inf", 2, 4, 1, -78.2040, 39.1180, 0),
    (1, "Burks", "42 VA", "inf", 1, 4, 1, -78.2080, 39.1150, 0),
    (1, "Marye", "Hampden Arty", "art", 1, 3, 2, -78.2000, 39.1210, 0),
    (1, "Lanier", "Danville Arty", "art", 1, 3, 2, -78.1980, 39.1170, 0),
]

STANDBY = [  # standby_groups[n-1] for standbyGroup n (Antietam pattern, side 0 only)
    # 1: Tyler's brigade, halted on the pike north of the toll gate at 2 PM; Kimball sent it west
    #    against Jackson's flank about 3:30-4 PM.
    {"side": 0, "turn": 3, "chance": 40, "rise": 30, "guardHexes": 0, "guardCs": 0},
    # 2: Sullivan, watching Ashby east of the pike; his regiments went to Sandy Ridge only late.
    {"side": 0, "turn": 5, "chance": 30, "rise": 25, "guardHexes": 0, "guardCs": 0},
    # 3: 39 IL and Huntington's battery: never sent in (Antietam's V Corps pattern: turn 0, chance 0).
    {"side": 0, "turn": 0, "chance": 0, "rise": 0, "guardHexes": 0, "guardCs": 0},
]


def place_units(occupied_ok):
    placed, count = [], Counter()
    for u in UNITS:
        side, leader, uname, kind, cs, mp, rng, lon, lat, sb = u
        h = G.lonlat_to_hex(lon, lat)
        if count[h] >= 2 or not occupied_ok(h, side):
            # nearest legal hex
            best = None
            for rad in range(1, 4):
                cands = [(q, r) for q in range(h[0] - rad, h[0] + rad + 1) for r in range(h[1] - rad, h[1] + rad + 1)
                         if G.inside(q, r) and count[(q, r)] < 2 and occupied_ok((q, r), side)]
                if cands:
                    best = min(cands, key=lambda c: math.dist(G.center_xy(*c), G.center_xy(*h)))
                    break
            h = best
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


def make_range_badge():
    """Small plate in the stock emblem slot: NATO artillery box plus the range figure."""
    W, H = 168, 68
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 2, W - 3, H - 3], 8, fill=(239, 236, 226, 255), outline=(40, 40, 40, 255), width=4)
    d.rectangle([12, 14, 70, 54], outline=(30, 30, 30, 255), width=4)
    d.ellipse([33, 26, 49, 42], fill=(30, 30, 30, 255))
    f = font(50, 900)
    d.text((118, 34), "R2", font=f, fill=(30, 30, 30, 255), anchor="mm")
    return im


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
            # shrink long names to fit their half of the counter (the game may wrap or clip instead)
            px = sh["fontSize"] * k
            while ImageDraw.Draw(im).textlength(txt, font=f) > 0.46 * S and px > 12:
                px -= 1
                f = font(px, sh["fontWeight"])
            d = ImageDraw.Draw(im)
            d.text((S / 2 + sh["x"] * k, S / 2 + sh["y"] * k), txt, font=f, anchor="mm",
                   fill=sh["color"], stroke_width=max(1, round(sh["strokeWidth"] * k / 2)), stroke_fill=sh["strokeColor"])
    return b64png(im)


def template_shapes(side, kind):
    if side == 0:
        plate, col, scol, sw = "img_side_253a69_nonato", "#ffffff", "#000000", 0.6
    else:
        plate, col, scol, sw = "img_side_b5b0a1_nonato", "#1b1b1b", "#efece2", 0.35
    def txt(link, z, x, y, fs, fw):
        return {"type": "text", "link": link, "z": z, "x": x, "y": y, "fontSize": fs, "color": col,
                "fontFamily": "Playfair Display", "fontWeight": fw, "strokeWidth": sw, "strokeColor": scol}
    shapes = [{"type": "image", "z": 0, "x": 0, "y": 0, "w": 30, "h": 30, "imageRef": plate},
              txt("box3", 1, -8, -10, 3.0, 900), txt("box4", 2, 8, -10, 3.0, 700),
              txt("box5", 3, -10.3, 8.9, 7.0, 900), txt("box6", 4, 10.3, 8.9, 7.0, 900)]
    if kind == "art":
        shapes.append({"type": "image", "x": 0, "y": 9.14, "w": 7.4, "h": 3.0, "imageRef": "img_emb_range2"})
    icon = {"inf": "img_kind_musket", "art": "img_kind_cannons", "cav": "img_kind_sabre"}[kind]
    shapes.append({"type": "image", "x": 0, "y": -0.05, "w": 12.6, "h": 12.6, "imageRef": icon, "z": 5})
    return shapes


# ---------------------------------------------------------------- briefing maps (1000x640, stock style)
PAPER = (233, 221, 196)


def frame(d, W, H):
    d.rectangle([3, 3, W - 4, H - 4], outline=(90, 75, 55), width=3)
    d.rectangle([9, 9, W - 10, H - 10], outline=(90, 75, 55), width=1)
    d.line([(950, 70), (950, 25)], fill=(70, 55, 40), width=3)
    d.polygon([(944, 34), (956, 34), (950, 22)], fill=(70, 55, 40))


def region_map():
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
    frame(d, W, H)
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


def battle_map(terrain, roads, rivers, vp_hexes):
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
    arrow([(-78.205, 39.122), (-78.222, 39.135), (-78.222, 39.146)], (175, 85, 75))      # Jackson to the ridge
    arrow([(-78.186, 39.165), (-78.205, 39.160), (-78.219, 39.152)], (95, 120, 175))      # Tyler to the wall
    for h in vp_hexes:
        x, y = P(*h)
        d.rectangle([x - 6, y - 6, x + 6, y + 6], fill=(250, 246, 235), outline=(70, 55, 40), width=2)
    frame(d, W, H)
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
DESCRIPTION = """23 March 1862. Kernstown, Frederick County, Virginia, United States, four miles south of Winchester on the Valley Pike

Ashby's scouts report that only a rear guard of four regiments is left near Winchester. They are wrong by about 6,000 men.
Two o'clock on a cold Sunday afternoon. Jackson has driven his small army north in two days of hard marching to keep Banks from leaving the Valley. In fact James Shields' whole division is here; Shields was wounded the evening before, and Colonel Nathan Kimball commands on the field from Pritchard's Hill. Jackson will not wait for Monday. He sends Fulkerson, then Garnett's Stonewall Brigade, west onto Sandy Ridge to turn the Union right, and his guns go up the ridge to enfilade Pritchard's Hill.

The board runs from Sandy Ridge in the west to Opequon Creek, and from Bartonsville north to Winchester; each hex is about 300 m and each turn half an hour. The Confederates move first. Kimball's brigade and four batteries can move from the start. Tyler's brigade, just up from Winchester on the pike, is on standby from 3 PM; Sullivan's regiments east of the pike from 4 PM; the 39th Illinois and Huntington's battery were never committed and wake only if the enemy comes to them. Union command is slow at first and improves at 4 PM.

The stone wall on the north crest of Sandy Ridge is the key. Whoever reaches it first holds a ridge line with a wall in front. The Union starts in possession of Winchester, Pritchard's Hill and Kernstown; the Confederates of the stone wall and of Bartonsville behind them. Jackson cannot simply sit on the ridge: the Union is far stronger and only has to take the wall and hold its own ground to win, as Kimball did when the Stonewall Brigade ran out of ammunition at dusk. Sunset is at 6:15; the 7 PM turn is night.

Counters: name, combat strength (left) and movement (right). Batteries show "R2": they fire two hexes. Strengths are one point per ~300 men or ~5 guns, from the reports of Jackson, Shields and Kimball in the Official Records (Series I, Vol. 12, Part 1) and Ecelbarger's "We Are in for It!"."""


# ---------------------------------------------------------------- assemble
def build(repo, stock_path, out_path, preview=None):
    stock = json.load(open(stock_path))
    terrain, elev, tpi, feats = classify_terrain(repo)
    roads, rivers, trails, fences = build_features(feats)

    # objectives
    wall_hexes = sorted(fences, key=lambda h: h[0])
    vp = {}
    for name, lon, lat, val, ctl in VP_SITES:
        if name == "Stone Wall":
            h = wall_hexes[len(wall_hexes) // 2]
        else:
            h = G.lonlat_to_hex(lon, lat)
            if name == "Pritchard's Hill":  # snap to the knoll top in the DEM (within one hex)
                h = max([h] + [neighbor(*h, e) for e in range(6)], key=lambda c: tpi[c[1], c[0]])
        vp[h] = (name, val, ctl)
    cp = {}
    ridge = [(q, r) for (q, r), t in terrain.items() if t in ("mountain", "rough")]
    for name, _, _, val in CP_SITES:
        if name == "Sandy Ridge crest":
            # crest of Sandy Ridge just south of the wall, where Jackson's guns stood
            lon0, lat0 = -78.2115, 39.1455
            cands = [h for h in ridge if h not in vp and h not in fences
                     and math.dist(G.center_xy(*h), G.lonlat_to_xy(lon0, lat0)) < 700]
            h = max(cands, key=lambda h: tpi[h[1], h[0]])
        else:
            pike_end = feats["roads"]["cedar_creek_grade"]["waypoints"][-1]
            h = G.lonlat_to_hex(*pike_end)
            if h in vp:
                h = next(n for n in (neighbor(*h, e) for e in range(6)) if n in roads and n not in vp)
        cp[h] = (name, val)

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
                boxes[9], boxes[10], boxes[11], boxes[15] = name, vpv, vpv, ctl + 1
            if h in cp:
                name = cp[h][0]
                boxes[9], boxes[16], boxes[17] = name, "+%d" % ppv, "+%d" % ppv
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
    badge = make_range_badge()
    images_raw["img_emb_range2"] = badge
    used_imgs = ["img_side_253a69_nonato", "img_side_b5b0a1_nonato", "img_kind_musket", "img_kind_cannons",
                 "img_kind_sabre", "img_emb_range2"]
    images = {k: (stock["assets"]["images"][k] if k in stock["assets"]["images"] else b64png(images_raw[k]))
              for k in used_imgs}

    bad = {"city"} if False else set()
    placed = place_units(lambda h, side: G.inside(*h) and terrain[h] not in bad)
    units, templates = [], []
    for i, ((side, leader, uname, kind, cs, mp, rng, lon, lat, sb), (q, r)) in enumerate(placed, 1):
        full = f"{leader} {uname}"
        boxes = [side, 0, i, leader, uname, cs, mp, rng] + [0] * 12
        tid = f"local_{i}"
        shapes = template_shapes(side, kind)
        templates.append({"id": tid, "name": full, "isLocal": True,
                          "visuals": {"shapes": shapes, "renderedUrl": render_counter(shapes, images_raw, boxes)}})
        units.append({"id": i, "q": q, "r": r, "side": side, "combatStrength": cs, "movePoints": mp, "range": rng,
                      "name": full, "boxId": 0, "entryHex": "", "entryTurn": 0, "betrayalTurn": 0,
                      "betrayalChance": 0, "betrayalRise": 0, "suddenDeathUnit": False, "standbyGroup": sb,
                      "eliteUnit": False, "exitPoints": 0, "boxes": boxes, "templateId": tid})

    rmap, rlabels = region_map()
    bmap, blabels = battle_map(terrain, roads, rivers, list(vp))
    desc = DESCRIPTION
    sides_en = ["Union (Shields' Division, Kimball)", "Confederate (Jackson's Valley District)"]

    scenario = {
        "doctrine": {"blue": "def", "red": "off"},
        "meta": {
            "version": "2.0",
            "exportedAt": "2026-11-01T00:00:00.000Z",
            "description": {l: desc for l in LANGS},
            "briefingImage": "",
            "scaleMeters": 300, "scaleMinutes": 30, "scaleMen": 300,
            "scenarioName": "Kernstown 1862 (CivilWar1)",
            "gameId": "mustattack",
            "regionMap": {"image": b64png(rmap.convert("P", palette=Image.ADAPTIVE, colors=64)), "labels": labels_json(rlabels)},
            "battleMap": {"image": b64png(bmap.convert("P", palette=Image.ADAPTIVE, colors=64)), "labels": labels_json(blabels)},
        },
        "scenario": {
            "name": "Kernstown 1862 (CivilWar1)",
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
            },
            "map": {"width": COLS, "height": ROWS, "hexes": hexes},
            "units": units,
        },
        "victoryCondition": {"winLine": 45, "tacticalThreshold": 10, "operationalThreshold": 72, "strategicThreshold": 144},
        "assets": {"terrains": make_terrains(repo, stock), "images": images, "unitTemplates": templates},
    }
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(scenario, f, ensure_ascii=False, separators=(",", ":"))
    if preview:
        np.save(preview + ".elev.npy", elev)
    return scenario


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
    ap.add_argument("--stock", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "ref", "antietam1862.json"),
                    help="stock Antietam scenario exported from the game (not committed)")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "mKernstown1862_CW1.json"))
    a = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    s = build(a.repo, a.stock, a.out)
    t = Counter(h["terrainId"] for h in s["scenario"]["map"]["hexes"])
    print("wrote", a.out, os.path.getsize(a.out), "bytes;", dict(t))
