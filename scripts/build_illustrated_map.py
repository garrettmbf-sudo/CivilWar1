#!/usr/bin/env python3
"""Illustrated board-map basemap: hand-drawn bare trees (NO dots), meandering features,
rich fields, crisp ink linework, paper tint. Continuous DEM relief; bold hex grid
is preview-only. Tiles stay 2000×2000 (HoS stock/docs) with strong PNG compression.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from hex_grid import KERNSTOWN as G

PX_PER_M = 0.52
FEAT = json.loads((ROOT / "data/features/kernstown_features.json").read_text())
mid = (G.south + G.north) / 2
m_lat, m_lon = G.meters_per_deg(mid)
W = int((G.east - G.west) * m_lon * PX_PER_M)
H = int((G.north - G.south) * m_lat * PX_PER_M)
rng = np.random.default_rng(19)
R_PX = G.size_m * PX_PER_M
OUT_PREV = ROOT / "previews"
OUT_PREV.mkdir(exist_ok=True)

def ll2px(lon, lat):
    return ((lon - G.west) * m_lon * PX_PER_M, (G.north - lat) * m_lat * PX_PER_M)

def hexc(col, row):
    x, y = G.hex_to_xy_m(col, row)
    return x * PX_PER_M, H - y * PX_PER_M

def load_font(size, bold=False):
    for p in [
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

# ---------- hand-drawn tree (bare crown + branching) — NEVER a filled dot ----------
def draw_bare_tree(d, x, y, scale=1.0, kind="bare"):
    """Hand-drawn winter tree: ink trunk + bare branching only. NO crown dots/ellipses."""
    s = scale
    # soft oval ground shadow only (ground plane, not foliage)
    trunk_w = max(1, int(1.8 * s))
    ink = (46, 38, 30, 255)
    twig = (58, 50, 40, 230)
    if kind == "snag":
        d.line([(x, y + 4*s), (x - 0.8*s, y - 16*s)], fill=(68, 60, 50, 255), width=trunk_w + 1)
        d.line([(x - 0.8*s, y - 7*s), (x - 8*s, y - 13*s)], fill=(68, 60, 50, 255), width=1)
        d.line([(x - 0.8*s, y - 10*s), (x + 7*s, y - 15*s)], fill=(64, 56, 46, 255), width=1)
        d.line([(x - 0.8*s, y - 5*s), (x + 6*s, y - 1*s)], fill=(66, 58, 48, 200), width=1)
        return
    # trunk with slight lean
    d.line([(x, y + 5*s), (x + 0.3*s, y - 5*s)], fill=ink, width=trunk_w)
    # primary scaffold — fan of bare limbs
    branches = [
        (0.3, -5, -9, -15), (0.3, -5, 8, -14), (0.3, -8, -5, -20), (0.3, -8, 6, -19),
        (0.3, -3, -11, -9), (0.3, -3, 10, -8), (-2, -11, -10, -17), (3, -11, 9, -17),
        (-4, -14, -1, -21), (5, -13, 3, -21), (-6, -10, -12, -12), (7, -10, 12, -11),
    ]
    for x0, y0, x1, y1 in branches:
        d.line([(x + x0*s, y + y0*s), (x + x1*s, y + y1*s)], fill=ink, width=max(1, int(1.15*s)))
    # fine twigs (branching texture)
    twigs = [
        (-9, -15, -13, -18), (-9, -15, -7, -19), (8, -14, 12, -17), (8, -14, 6, -18),
        (-5, -20, -8, -23), (6, -19, 9, -23), (-11, -9, -14, -11), (10, -8, 13, -11),
        (-10, -17, -14, -16), (9, -17, 13, -16), (-1, -21, -3, -24), (3, -21, 5, -24),
        (-12, -12, -15, -14), (12, -11, 15, -13),
    ]
    for x0, y0, x1, y1 in twigs:
        d.line([(x + x0*s, y + y0*s), (x + x1*s, y + y1*s)], fill=twig, width=1)
    # Redbud: same bare tree + long thin dusty-magenta tip strokes (reads as bloom on twigs, not dots)
    if kind == "redbud":
        bloom_ink = (132, 72, 108, 230)
        tips = [(-9,-15,-14,-20),(-5,-20,-8,-26),(6,-19,10,-25),(8,-14,13,-19),
                (-1,-21,-3,-27),(3,-21,6,-27),(-10,-17,-15,-21),(9,-17,14,-21)]
        for x0,y0,x1,y1 in tips:
            d.line([(x+x0*s, y+y0*s), (x+x1*s, y+y1*s)], fill=bloom_ink, width=1)

def draw_bare_tree_pass2(d, x, y, scale=1.0, kind="bare"):
    """Second pass: redraw key branches over wash so structure reads as drawn tree."""
    if kind == "snag":
        return
    s = scale
    ink = (44, 36, 28, 255)
    for x0, y0, x1, y1 in [(0, -4, -8, -14), (0, -4, 7, -13), (0, -7, -4, -18), (0, -7, 5, -17)]:
        d.line([(x + x0*s, y + y0*s), (x + x1*s, y + y1*s)], fill=ink, width=max(1, int(1.1*s)))
    d.line([(x, y + 5*s), (x, y - 4*s)], fill=(48, 38, 30, 255), width=max(1, int(1.5*s)))

def pl(d, coords, layers):
    pts = [ll2px(*c) for c in coords]
    if len(pts) < 2:
        return
    for w, c in layers:
        d.line(pts, fill=c, width=w, joint="curve")

def building(d, x, y, w, h, ang, wall, roof):
    c, s = math.cos(ang), math.sin(ang)
    def rot(px, py):
        return (x + px * c - py * s, y + px * s + py * c)
    sh = [rot(-w/2+2, -h/2+2), rot(w/2+2, -h/2+2), rot(w/2+2, h/2+2), rot(-w/2+2, h/2+2)]
    d.polygon(sh, fill=(40, 32, 24, 100))
    body = [rot(-w/2, -h/2), rot(w/2, -h/2), rot(w/2, h/2), rot(-w/2, h/2)]
    d.polygon(body, fill=wall, outline=(32, 24, 18, 255))
    # roof ridge
    d.polygon([rot(-w/2, -h/2), rot(0, -h/2 - 3), rot(w/2, -h/2), rot(w/2, -h/4), rot(-w/2, -h/4)],
              fill=roof, outline=(28, 22, 16, 255))

def worm_fence(d, coords, amp=9):
    pts = [ll2px(*c) for c in coords]
    for a, b in zip(pts, pts[1:]):
        n = max(2, int(math.hypot(b[0]-a[0], b[1]-a[1]) / 9))
        ang = math.atan2(b[1]-a[1], b[0]-a[0])
        nx, ny = -math.sin(ang), math.cos(ang)
        zz = []
        for i in range(n + 1):
            f = i / n
            side = amp if i % 2 else -amp
            zz.append((a[0] + (b[0]-a[0])*f + nx*side*0.15 + side*0.15*nx,
                       a[1] + (b[1]-a[1])*f + ny*side*0.15))
            # classic worm: alternate V
            zz[-1] = (a[0] + (b[0]-a[0])*f + nx * (amp if i % 2 else -amp) * 0.5,
                      a[1] + (b[1]-a[1])*f + ny * (amp if i % 2 else -amp) * 0.5)
        d.line(zz, fill=(40, 30, 22, 255), width=1)
        d.line(zz, fill=(110, 82, 52, 220), width=1)

def build_basemap():
    dem = np.array(Image.open(ROOT / "data/dem/kernstown_3dep.tif"), np.float32)
    dem = np.where(np.isfinite(dem), dem, np.nanmedian(dem))
    demh = np.array(Image.fromarray(dem).resize((W, H), Image.Resampling.BICUBIC), np.float32)
    demh = gaussian_filter(demh, sigma=1.5)

    # Exaggerated DEM for plastic/oblique ridge relief (landforms read as raised 3D)
    vex = 4.0  # vertical exaggeration for shading only
    gy, gx = np.gradient(demh * vex, 1.0 / PX_PER_M)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, alt = math.radians(315), math.radians(32)  # NW light
    hs = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    hs = np.clip(hs, 0, 1)
    hs = np.power(hs, 0.85)  # deepen shadows on steep faces

    lo, hi = np.percentile(demh, 2), np.percentile(demh, 98.5)
    t = np.clip((demh - lo) / (hi - lo + 1e-6), 0, 1)
    # Richer hypsometric — parchment → straw → ochre → sienna → deep umber
    stops = [
        (0.00, (236, 220, 178)),
        (0.18, (220, 198, 148)),
        (0.38, (198, 162, 108)),
        (0.58, (168, 120, 74)),
        (0.78, (132, 84, 50)),
        (1.00, (92, 56, 34)),
    ]
    hyp = np.zeros((H, W, 3), np.float32)
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        m = (t >= t0) & (t <= t1)
        f = ((t[m] - t0) / (t1 - t0 + 1e-9))[:, None]
        hyp[m] = np.array(c0, np.float32) * (1 - f) + np.array(c1, np.float32) * f

    shade = 0.18 + 1.05 * hs
    # Extra darkening on SE faces of ridges (oblique raised-landform cue)
    shade *= 1.0 - 0.38 * np.clip(slope / math.radians(18), 0, 1)
    # Soft north-facing highlight strip on high ground
    north_lit = np.clip((-gy) / (np.abs(gy).max() + 1e-6), 0, 1)
    shade += 0.06 * north_lit * (t > 0.4)
    img = np.clip(hyp * shade[..., None], 0, 255)

    # Paper grain / hand-tint feel
    grain = rng.normal(0, 1, (H // 5 + 1, W // 5 + 1)).astype(np.float32)
    grain = (grain - grain.min()) / (np.ptp(grain) + 1e-6)
    grain = np.array(Image.fromarray((grain * 255).astype(np.uint8)).resize((W, H), Image.Resampling.BILINEAR), np.float32) / 255
    img = np.clip(img * (0.96 + 0.08 * grain[..., None]) + (grain[..., None] - 0.5) * 6, 0, 255)

    base = Image.fromarray(img.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(base, "RGBA")

    # Varied open land: plowed / fallow straw / pasture — strong harmonious contrast
    field_palette = [
        ((148, 108, 68, 75), True),   # plowed brown + furrows
        ((158, 118, 76, 70), True),
        ((226, 206, 150, 80), False), # straw fallow
        ((214, 192, 138, 70), False),
        ((188, 168, 118, 65), False), # pasture
        ((170, 148, 98, 60), False),
        ((200, 156, 108, 55), False), # warmer tilled
    ]
    for _ in range(120):
        cx, cy = rng.uniform(0, W), rng.uniform(0, H)
        ix, iy = int(min(W - 1, cx)), int(min(H - 1, cy))
        if t[iy, ix] > 0.55:
            continue
        ww, hh = rng.uniform(90, 220), rng.uniform(60, 150)  # large parcels crossing many hexes
        ang = rng.uniform(0, math.pi)
        c, s = math.cos(ang), math.sin(ang)
        corners = [(-ww, -hh), (ww, -hh), (ww, hh), (-ww, hh)]
        pts = [(cx + x*c - y*s, cy + x*s + y*c) for x, y in corners]
        col, furrowed = field_palette[int(rng.integers(len(field_palette)))]
        d.polygon(pts, fill=col)
        # ink field edge
        d.line(pts + [pts[0]], fill=(70, 55, 38, 90), width=1)
        if furrowed:
            for k in range(-int(hh), int(hh), 5):
                a = (cx + (-ww)*c - k*s, cy + (-ww)*s + k*c)
                b = (cx + ww*c - k*s, cy + ww*s + k*c)
                d.line([a, b], fill=(110, 78, 48, 70), width=1)

    # Forest mask — canopy wash only (no tree dots here)
    yy, xx = np.mgrid[0:H, 0:W]
    forest = np.zeros((H, W), bool)
    for lon, lat in FEAT["ridge_cores"]["sandy_ridge"]:
        px, py = ll2px(lon, lat)
        forest |= ((xx - px)**2 / (150**2) + (yy - py)**2 / (340**2)) < 1
    forest |= (slope > math.radians(6.0)) & (t > 0.30)
    for _ in range(22):
        cx, cy = rng.uniform(0, W), rng.uniform(0, H)
        rx, ry = rng.uniform(50, 140), rng.uniform(40, 110)
        forest |= ((xx - cx)**2 / rx**2 + (yy - cy)**2 / ry**2) < 1
    for lon, lat in FEAT["ridge_cores"]["pritchards_hill"]:
        px, py = ll2px(lon, lat)
        forest &= ((xx - px)**2 + (yy - py)**2) > 110**2
    for p in FEAT["places"]:
        px, py = ll2px(p["lon"], p["lat"])
        rad = 85 if p.get("kind") == "city" else 48
        forest &= ((xx - px)**2 + (yy - py)**2) > rad**2

    # Soft wood wash + clear organic edge (darker interior)
    fm = Image.fromarray((forest.astype(np.uint8) * 255)).filter(ImageFilter.GaussianBlur(14))
    wash = Image.new("RGBA", (W, H), (86, 74, 54, 0))
    wash.putalpha(fm.point(lambda v: int(v * 0.50)))
    base = Image.alpha_composite(base, wash)
    wash2 = Image.new("RGBA", (W, H), (62, 52, 38, 0))
    wash2.putalpha(fm.point(lambda v: int(max(0, v - 50) * 0.40)))
    base = Image.alpha_composite(base, wash2)
    d = ImageDraw.Draw(base, "RGBA")

    # Forest mass = continuous canopy wash only (no per-hex stamp trees).
    # Sparse character trees added later by oblique_objects (modest height, off-center).

    # Orchards
    # Orchards — ordered bare trees (drawn, not dots)
    def orchard(lon, lat, n=5, m=3, sp=18):
        px, py = ll2px(lon, lat)
        for i in range(n):
            for j in range(m):
                draw_bare_tree(d, px + i*sp, py + j*sp, scale=0.95, kind="bare")
                draw_bare_tree_pass2(d, px + i*sp, py + j*sp, scale=0.95, kind="bare")
    for lon, lat in [(-78.178, 39.176), (-78.185, 39.160), (-78.205, 39.128), (-78.150, 39.170)]:
        orchard(lon, lat)

    # ---------- Hydro: banks + ink + fill (meandering features) ----------
    # Gentle banks first
    pl(d, FEAT["rivers"]["opequon_creek"]["waypoints"], [
        (28, (120, 130, 100, 90)), (22, (90, 110, 80, 70))])
    for k in ("hoge_run", "abrams_creek", "buffalo_lick"):
        if k in FEAT["rivers"]:
            pl(d, FEAT["rivers"][k]["waypoints"], [(16, (120, 130, 100, 70))])
    # Water fill + crisp ink casing
    pl(d, FEAT["rivers"]["opequon_creek"]["waypoints"], [
        (18, (28, 48, 78, 255)), (13, (52, 112, 168, 255)), (7, (140, 186, 218, 255))])
    for k in ("hoge_run", "abrams_creek", "buffalo_lick"):
        if k in FEAT["rivers"]:
            pl(d, FEAT["rivers"][k]["waypoints"], [
                (11, (28, 48, 78, 255)), (7, (58, 120, 176, 255)), (3, (150, 190, 220, 255))])

    # Dirt roads — soft edges, wheel ruts, ink outline
    for k, rd in FEAT["roads"].items():
        if rd.get("kind") == "pike":
            continue
        pl(d, rd["waypoints"], [
            (12, (48, 34, 22, 255)), (9, (128, 92, 58, 255)), (5, (158, 118, 76, 255))])
        # wheel ruts
        pts = [ll2px(*c) for c in rd["waypoints"]]
        for off in (-1.8, 1.8):
            rut = []
            for i in range(len(pts)-1):
                a, b = pts[i], pts[i+1]
                ang = math.atan2(b[1]-a[1], b[0]-a[0])
                rut.append((a[0] - math.sin(ang)*off, a[1] + math.cos(ang)*off))
            if len(rut) > 1:
                d.line(rut, fill=(70, 48, 30, 140), width=1)

    # Valley Pike — pale macadam + stone edging + ink
    pl(d, FEAT["roads"]["valley_pike"]["waypoints"], [
        (22, (42, 34, 26, 255)), (17, (138, 124, 98, 255)), (12, (188, 174, 142, 255)), (7, (206, 194, 164, 255))])
    # stone edging ticks
    vp = [ll2px(*c) for c in FEAT["roads"]["valley_pike"]["waypoints"]]
    for i in range(0, len(vp)-1, 4):
        a, b = vp[i], vp[i+1]
        ang = math.atan2(b[1]-a[1], b[0]-a[0])
        nx, ny = -math.sin(ang), math.cos(ang)
        for side in (-7, 7):
            d.line([(a[0]+nx*side, a[1]+ny*side), (a[0]+nx*(side+1.5), a[1]+ny*(side+1.5))],
                   fill=(120, 112, 98, 220), width=2)

    # RR
    rr = [ll2px(*c) for c in FEAT["railroads"]["winchester_and_potomac"]["waypoints"]]
    d.line(rr, fill=(40, 34, 28, 255), width=3)
    d.line(rr, fill=(168, 152, 128, 255), width=10)
    dense = []
    for a, b in zip(rr, rr[1:]):
        L = math.hypot(b[0]-a[0], b[1]-a[1]); n = max(1, int(L/8))
        ang = math.atan2(b[1]-a[1], b[0]-a[0])
        for i in range(n):
            f = i/n
            dense.append((a[0]+(b[0]-a[0])*f, a[1]+(b[1]-a[1])*f, ang))
    for x, y, ang in dense[::1]:
        nx, ny = -math.sin(ang), math.cos(ang)
        d.line([(x-nx*8, y-ny*8), (x+nx*8, y+ny*8)], fill=(88, 62, 40, 255), width=2)
    for off in (-2.8, 2.8):
        pts = [(x - math.sin(a)*off, y + math.cos(a)*off) for x, y, a in dense]
        d.line(pts, fill=(22, 20, 18, 255), width=2)

    # Stone wall — ink + limestone blocks
    sw = [ll2px(*c) for c in FEAT["stone_walls"]["glass_wall_sandy_ridge"]["waypoints"]]
    d.line(sw, fill=(32, 28, 24, 255), width=9)
    d.line(sw, fill=(178, 172, 158, 255), width=5)
    for a, b in zip(sw, sw[1:]):
        n = int(math.hypot(b[0]-a[0], b[1]-a[1]) / 5)
        for i in range(n):
            f = i/n; x, y = a[0]+(b[0]-a[0])*f, a[1]+(b[1]-a[1])*f
            d.rectangle((x-2, y-2, x+2, y+2), fill=(130, 124, 112, 255), outline=(50, 46, 40, 200))

    # Worm rail fences on field edges / lanes
    worm_fence(d, FEAT["roads"]["stone_lane"]["waypoints"])
    worm_fence(d, FEAT["roads"]["cedar_creek_grade"]["waypoints"], amp=8)
    worm_fence(d, FEAT["roads"]["apple_valley_road"]["waypoints"], amp=8)
    # extra farm fence segments near farms
    for lon0, lat0, lon1, lat1 in [
        (-78.203, 39.143, -78.199, 39.140), (-78.226, 39.148, -78.222, 39.145),
        (-78.210, 39.138, -78.205, 39.136), (-78.188, 39.145, -78.184, 39.143),
    ]:
        worm_fence(d, [[lon0, lat0], [lon1, lat1]], amp=7)

    # Fords
    for f in FEAT["fords"]:
        x, y = ll2px(f["lon"], f["lat"])
        for k in range(-3, 4):
            d.line([(x-14, y+k*3.5), (x+14, y+k*3.5)], fill=(228, 216, 178, 230), width=2)
        d.ellipse((x-11, y-11, x+11, y+11), outline=(32, 26, 20, 255), width=2)

    # Springs
    for sp in FEAT.get("springs", []):
        x, y = ll2px(sp["lon"], sp["lat"])
        d.line([(x-4, y), (x+4, y)], fill=(40, 80, 120, 220), width=1)
        d.line([(x, y-4), (x, y+4)], fill=(40, 80, 120, 220), width=1)

    BRICK = [(152, 84, 64, 255), (138, 74, 56, 255), (166, 98, 74, 255)]
    STONE = [(174, 170, 158, 255), (152, 148, 138, 255)]
    ROOF = [(98, 72, 54, 255), (86, 88, 94, 255), (112, 82, 60, 255)]
    WOOD = [(122, 92, 64, 255), (214, 204, 184, 255)]

    # Winchester street grid
    wc = ll2px(-78.1633, 39.1857)
    grid_ang = math.radians(-8)
    ca, sa = math.cos(grid_ang), math.sin(grid_ang)
    def wrot(u, v):
        return (wc[0] + u*ca - v*sa, wc[1] + u*sa + v*ca)
    block = 50
    for i in range(-4, 5):
        d.line([wrot(i*block, -6.5*block), wrot(i*block, 6.5*block)], fill=(48, 36, 24, 255), width=2)
        d.line([wrot(i*block, -6.5*block), wrot(i*block, 6.5*block)], fill=(140, 108, 74, 255), width=5)
    for j in range(-6, 7):
        d.line([wrot(-4.5*block, j*block), wrot(4.5*block, j*block)], fill=(48, 36, 24, 255), width=2)
        d.line([wrot(-4.5*block, j*block), wrot(4.5*block, j*block)], fill=(140, 108, 74, 255), width=4)
    for i in range(-4, 4):
        for j in range(-6, 6):
            pts = [wrot(i*block+3, j*block+3), wrot((i+1)*block-3, j*block+3),
                   wrot((i+1)*block-3, (j+1)*block-3), wrot(i*block+3, (j+1)*block-3)]
            d.polygon(pts, fill=(198, 186, 164, 65))
            dist = math.hypot(i+0.5, (j+0.5)*0.7)
            density = max(0.0, 1 - dist/6.0)
            for _k in range(int(3 + density*9)):
                if rng.random() > density + 0.15:
                    continue
                u = (i + 0.12 + rng.random()*0.76)*block
                v = (j + 0.12 + rng.random()*0.76)*block
                x, y = wrot(u, v)
                wall = BRICK[rng.integers(3)] if rng.random() < 0.62 else STONE[rng.integers(2)]
                building(d, x, y, rng.uniform(8, 14), rng.uniform(7, 11), grid_ang, wall,
                         wall if rng.random() < 0.25 else ROOF[rng.integers(3)])
    x, y = wrot(0, 0)
    building(d, x, y, 20, 15, grid_ang, STONE[0], (84, 86, 92, 255))

    def village(lon, lat, n, spread=34):
        cx, cy = ll2px(lon, lat)
        for _k in range(n):
            x, y = cx + rng.normal(0, spread*0.5), cy + rng.normal(0, spread*0.35)
            building(d, x, y, rng.uniform(8, 12), rng.uniform(7, 10), rng.uniform(-0.3, 0.3),
                     BRICK[rng.integers(3)], ROOF[rng.integers(3)])

    village(-78.1978, 39.1425, 14, 36)
    village(-78.2100, 39.1160, 7, 26)
    village(-78.1750, 39.1650, 6, 24)

    # Farmsteads: house + barn + small orchard
    farms = [
        (-78.2015, 39.1418), (-78.2248, 39.1470), (-78.1990, 39.1375),
        (-78.2060, 39.1190), (-78.1860, 39.1430), (-78.2250, 39.1510),
    ]
    for lon, lat in farms:
        cx, cy = ll2px(lon, lat)
        building(d, cx, cy, 13, 10, 0.15, WOOD[1], ROOF[0])
        building(d, cx+18, cy+8, 18, 12, 0.15, WOOD[0], ROOF[2])
        for i in range(4):
            for j in range(3):
                draw_bare_tree(d, cx - 22 + i*14, cy + 18 + j*13, scale=0.9, kind="bare")

    # Opequon Church
    cx, cy = ll2px(-78.1915, 39.1392)
    building(d, cx, cy, 18, 12, 0.0, STONE[0], (84, 86, 92, 255))
    d.rectangle((cx-3, cy-20, cx+3, cy-6), fill=(170, 166, 154, 255), outline=(30, 26, 22, 255))
    d.polygon([(cx-5, cy-20), (cx, cy-32), (cx+5, cy-20)], fill=(70, 72, 78, 255), outline=(30, 26, 22, 255))
    d.line([(cx, cy-38), (cx, cy-32)], fill=(30, 26, 22, 255), width=2)
    for k in range(5):
        d.rectangle((cx+14+k*5, cy+4, cx+16+k*5, cy+8), fill=(200, 196, 186, 255))

    # Slight paper desaturation + contrast
    base = ImageEnhance.Contrast(base).enhance(1.12)
    base = ImageEnhance.Color(base).enhance(0.88)
    return base, t

def draw_bold_hex_grid(draw, w, h, width=3, color=(24, 18, 12, 230)):
    for col in range(G.cols):
        for row in range(G.rows):
            cx, cy = hexc(col, row)
            if cx < -R_PX or cy < -R_PX or cx > w + R_PX or cy > h + R_PX:
                continue
            pts = [(cx + R_PX * math.cos(math.radians(60*i)),
                    cy + R_PX * math.sin(math.radians(60*i))) for i in range(6)]
            draw.line(pts + [pts[0]], fill=color, width=width)

def draw_labels_on(draw, ox=0, oy=0, scale=1.0):
    font_major = load_font(int(28*scale), bold=True)
    font_feat = load_font(int(20*scale), bold=True)
    font_farm = load_font(int(14*scale), bold=False)
    # Pritchard's Hill label ON the hill itself (small offset only)
    majors = [
        ("WINCHESTER", -78.1633, 39.1885, font_major, 22, -20, 3),
        ("Kernstown", -78.1978, 39.1425, font_feat, 14, 14, 2),
        ("Opequon Church", -78.1915, 39.1392, font_feat, 16, -16, 2),
        ("Sandy Ridge", -78.2185, 39.1455, font_feat, -36, -12, 2),
        ("Pritchard's Hill", -78.2072, 39.1408, font_feat, -10, -18, 2),
        ("Valley Pike", -78.190, 39.165, font_feat, 20, 2, 2),
        ("Middle Road", -78.236, 39.155, font_feat, -40, 0, 2),
        ("Opequon Creek", -78.148, 39.155, font_feat, 14, 8, 2),
        ("Hoge Run", -78.200, 39.1415, font_feat, 8, 16, 2),
        ("W&P RR", -78.160, 39.190, font_feat, 10, -12, 2),
        ("Bartonsville", -78.210, 39.116, font_feat, 10, 12, 2),
    ]
    farms = [
        ("Pritchard", -78.2015, 39.1418, 8, 10),
        ("Glass", -78.2248, 39.1470, -8, 10),
        ("stone wall", -78.2190, 39.146, 6, 10),
    ]
    for name, lon, lat, font, dx, dy, stroke in majors:
        x, y = ll2px(lon, lat)
        draw.text((x - ox + dx, y - oy + dy), name, font=font, fill=(28, 22, 16, 245),
                  stroke_width=stroke, stroke_fill=(236, 228, 206, 210))
    for name, lon, lat, dx, dy in farms:
        x, y = ll2px(lon, lat)
        draw.text((x - ox + dx, y - oy + dy), name, font=font_farm, fill=(60, 48, 36, 200),
                  stroke_width=1, stroke_fill=(230, 220, 196, 140))

def render_previews(base: Image.Image):
    full = base.copy()
    g = Image.new("RGBA", full.size, (0, 0, 0, 0))
    draw_bold_hex_grid(ImageDraw.Draw(g, "RGBA"), *full.size, width=max(3, int(R_PX*0.05)))
    full = Image.alpha_composite(full, g)
    lab = Image.new("RGBA", full.size, (0, 0, 0, 0))
    draw_labels_on(ImageDraw.Draw(lab, "RGBA"))
    full = Image.alpha_composite(full, lab)
    rgb = full.convert("RGB")
    max_side = 3200
    if max(rgb.size) > max_side:
        s = max_side / max(rgb.size)
        rgb = rgb.resize((int(rgb.size[0]*s), int(rgb.size[1]*s)), Image.Resampling.LANCZOS)
    rgb.save(OUT_PREV / "kernstown_full.jpg", quality=92, optimize=True)
    base.convert("RGB").resize(rgb.size, Image.Resampling.LANCZOS).save(
        OUT_PREV / "kernstown_full_nogrid.jpg", quality=90, optimize=True)

    def crop_save(lon0, lat0, lon1, lat1, name, label_scale=1.35, grid_w=3):
        x0, y1 = ll2px(lon0, lat0); x1, y0 = ll2px(lon1, lat1)
        box = (int(min(x0,x1)), int(min(y0,y1)), int(max(x0,x1)), int(max(y0,y1)))
        crop = base.crop(box)
        g = Image.new("RGBA", crop.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(g, "RGBA")
        for col in range(G.cols):
            for row in range(G.rows):
                cx, cy = hexc(col, row)
                cx -= box[0]; cy -= box[1]
                if cx < -R_PX or cy < -R_PX or cx > crop.size[0]+R_PX or cy > crop.size[1]+R_PX:
                    continue
                pts = [(cx + R_PX*math.cos(math.radians(60*i)),
                        cy + R_PX*math.sin(math.radians(60*i))) for i in range(6)]
                gd.line(pts+[pts[0]], fill=(24, 18, 12, 230), width=grid_w)
        crop = Image.alpha_composite(crop, g)
        lab = Image.new("RGBA", crop.size, (0, 0, 0, 0))
        draw_labels_on(ImageDraw.Draw(lab, "RGBA"), ox=box[0], oy=box[1], scale=label_scale)
        crop = Image.alpha_composite(crop, lab).convert("RGB")
        if max(crop.size) < 1400:
            s = 1400 / max(crop.size)
            crop = crop.resize((int(crop.size[0]*s), int(crop.size[1]*s)), Image.Resampling.LANCZOS)
        crop.save(OUT_PREV / name, quality=93, optimize=True)
        print("wrote", name, crop.size)

    crop_save(-78.235, 39.122, -78.165, 39.162, "closeup_kernstown_sandy_ridge.jpg")
    crop_save(-78.195, 39.168, -78.135, 39.205, "closeup_winchester.jpg")
    crop_save(-78.228, 39.128, -78.180, 39.156, "closeup_pritchards_hill.jpg", label_scale=1.5, grid_w=4)
    med = full.convert("RGB")
    med = med.resize((1800, int(1800*med.size[1]/med.size[0])), Image.Resampling.LANCZOS)
    med.save(OUT_PREV / "kernstown_medium.jpg", quality=92, optimize=True)
    print("previews done")

def main():
    print(f"illustrated basemap {W}x{H} R_px={R_PX:.1f}")
    base, t = build_basemap()
    base.save(ROOT / "data/basemap_kernstown.png", compress_level=4)
    json.dump({"W": W, "H": H, "px_per_m": PX_PER_M, "R_px": R_PX,
               "cols": G.cols, "rows": G.rows, "style": "illustrated-hand-drawn"},
              open(ROOT / "data/basemap_meta.json", "w"))
    print("basemap saved", base.size)
    render_previews(base)
    # QA thumb
    base.convert("RGB").resize((1000, int(1000*base.size[1]/base.size[0])), Image.Resampling.LANCZOS).save(
        OUT_PREV / "basemap_qa.jpg", quality=88)
    return base

if __name__ == "__main__":
    main()
