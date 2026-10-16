#!/usr/bin/env python3
"""Board-game-quality Kernstown map: continuous DEM relief + bold features, sliced to HoS hex tiles.

Engine strategy: HoS draws one sprite per hex, so continuous relief is achieved by giving
each hex its own tile (SV_K_<col>_<row>) cut from the continuous basemap with the stock
flat-top alpha mask. Neighboring sprites therefore match exactly at edges.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from hex_grid import KERNSTOWN as G

PX_PER_M = 0.40
FEAT = json.loads((ROOT / "data/features/kernstown_features.json").read_text())
mid = (G.south + G.north) / 2
m_lat, m_lon = G.meters_per_deg(mid)
W = int((G.east - G.west) * m_lon * PX_PER_M)
H = int((G.north - G.south) * m_lat * PX_PER_M)
rng = np.random.default_rng(7)

def ll2px(lon, lat):
    return ((lon - G.west) * m_lon * PX_PER_M, (G.north - lat) * m_lat * PX_PER_M)

def hexc(col, row):
    x, y = G.hex_to_xy_m(col, row)
    return x * PX_PER_M, H - y * PX_PER_M

R_PX = G.size_m * PX_PER_M

# ---------- relief ----------
dem = np.array(Image.open(ROOT / "data/dem/kernstown_3dep.tif"), np.float32)
dem = np.where(np.isfinite(dem), dem, np.nanmedian(dem))
demh = np.array(Image.fromarray(dem).resize((W, H), Image.Resampling.BICUBIC), np.float32)
from scipy.ndimage import gaussian_filter
demh = gaussian_filter(demh, sigma=1.2)
gy, gx = np.gradient(demh, 1 / PX_PER_M)
slope = np.arctan(np.hypot(gx, gy))
aspect = np.arctan2(-gx, gy)
az, alt = math.radians(315), math.radians(35)
hs = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
hs = np.clip(hs, 0, 1)
# exaggerate relief contrast
hs = hs ** 1.3
lo, hi = np.percentile(demh, 3), np.percentile(demh, 99)
t = np.clip((demh - lo) / (hi - lo), 0, 1)
stops = [(0.0, (214, 194, 146)), (0.30, (196, 168, 116)), (0.55, (170, 128, 84)),
         (0.75, (146, 98, 62)), (1.0, (118, 74, 46))]
hyp = np.zeros((H, W, 3), np.float32)
for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
    m = (t >= t0) & (t <= t1)
    f = ((t[m] - t0) / (t1 - t0))[:, None]
    hyp[m] = np.array(c0) * (1 - f) + np.array(c1) * f
shade = 0.35 + 0.85 * hs
img = np.clip(hyp * shade[..., None], 0, 255)
# field texture: plowed strips in lowland
noise = rng.random((H // 6 + 1, W // 6 + 1))
noise = np.array(Image.fromarray((noise * 255).astype(np.uint8)).resize((W, H), Image.Resampling.NEAREST), np.float32) / 255
img *= (0.94 + 0.10 * noise)[..., None]
base = Image.fromarray(img.astype(np.uint8)).convert("RGBA")
d = ImageDraw.Draw(base, "RGBA")

# plowed field parcels (brown) vs dormant straw
for _ in range(220):
    cx, cy = rng.uniform(0, W), rng.uniform(0, H)
    ix, iy = int(min(W - 1, cx)), int(min(H - 1, cy))
    if t[iy, ix] > 0.5:
        continue
    w, h = rng.uniform(30, 80), rng.uniform(20, 55)
    ang = rng.uniform(0, math.pi)
    corners = [(-w, -h), (w, -h), (w, h), (-w, h)]
    pts = [(cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)) for x, y in corners]
    col = (150, 112, 74, 70) if rng.random() < 0.55 else (220, 200, 150, 55)
    d.polygon(pts, fill=col)
    if col[0] == 150:  # furrows
        for k in range(-int(h), int(h), 5):
            a = (cx + (-w) * math.cos(ang) - k * math.sin(ang), cy + (-w) * math.sin(ang) + k * math.cos(ang))
            b = (cx + w * math.cos(ang) - k * math.sin(ang), cy + w * math.sin(ang) + k * math.cos(ang))
            d.line([a, b], fill=(120, 88, 58, 60), width=1)

# ---------- woods ----------
forest = np.zeros((H, W), bool)
yy, xx = np.mgrid[0:H, 0:W]
# ridge woods: Sandy Ridge corridor + steeper slopes
for lon, lat in FEAT["ridge_cores"]["sandy_ridge"]:
    px, py = ll2px(lon, lat)
    forest |= ((xx - px) ** 2 / (110 ** 2) + (yy - py) ** 2 / (260 ** 2)) < 1
forest |= (slope > math.radians(7)) & (t > 0.35)
for _ in range(45):
    cx, cy = rng.uniform(0, W), rng.uniform(0, H)
    rx, ry = rng.uniform(25, 90), rng.uniform(20, 70)
    forest |= ((xx - cx) ** 2 / rx ** 2 + (yy - cy) ** 2 / ry ** 2) < 1
# keep Pritchard's Hill open (artillery on cleared hill)
for lon, lat in FEAT["ridge_cores"]["pritchards_hill"]:
    px, py = ll2px(lon, lat)
    forest &= ((xx - px) ** 2 + (yy - py) ** 2) > 70 ** 2
# keep towns open
for p in FEAT["places"]:
    px, py = ll2px(p["lon"], p["lat"])
    forest &= ((xx - px) ** 2 + (yy - py) ** 2) > 45 ** 2
fm = Image.fromarray((forest * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))
shadow = Image.new("RGBA", (W, H), (70, 58, 44, 0))
shadow.putalpha(fm.point(lambda v: int(v * 0.35)))
base = Image.alpha_composite(base, shadow)
d = ImageDraw.Draw(base, "RGBA")
fy, fx = np.where(forest)
idx = rng.choice(len(fx), size=min(len(fx) // 55, 26000), replace=False)
order = idx[np.argsort(fy[idx])]
for i in order:
    x, y = float(fx[i]), float(fy[i])
    r = rng.uniform(3.5, 6.5)
    kind = rng.random()
    if kind < 0.10:   # redbud
        crown = (168, 86, 140, 235)
    elif kind < 0.17:  # dead
        d.line([(x, y + r), (x, y - r * 1.6)], fill=(96, 88, 78, 255), width=2)
        d.line([(x, y - r * 0.6), (x - r, y - r * 1.4)], fill=(96, 88, 78, 255), width=1)
        d.line([(x, y - r * 0.8), (x + r, y - r * 1.5)], fill=(96, 88, 78, 255), width=1)
        continue
    else:             # bare gray-brown crown
        g = rng.integers(-12, 12)
        crown = (118 + g, 104 + g, 88 + g, 230)
    d.ellipse((x - r + 2, y - r + 2, x + r + 2, y + r + 2), fill=(50, 40, 30, 90))
    d.ellipse((x - r, y - r, x + r, y + r), fill=crown, outline=(70, 58, 46, 200))
    d.line([(x - r * 0.5, y - r * 0.2), (x + r * 0.4, y + r * 0.3)], fill=(84, 72, 60, 160), width=1)

# orchards near Winchester / farms: regular rows
def orchard(lon, lat, n=6, m=5, sp=11):
    px, py = ll2px(lon, lat)
    for i in range(n):
        for j in range(m):
            x, y = px + i * sp, py + j * sp
            d.ellipse((x - 3.5, y - 3.5, x + 3.5, y + 3.5), fill=(132, 112, 90, 240), outline=(80, 66, 52, 220))
for lon, lat in [(-78.178, 39.176), (-78.185, 39.160), (-78.205, 39.128), (-78.150, 39.170)]:
    orchard(lon, lat)

# ---------- linework ----------
def pl(coords, widths_colors):
    pts = [ll2px(*c) for c in coords]
    for w, c in widths_colors:
        d.line(pts, fill=c, width=w, joint="curve")
        for p in (pts[0], pts[-1]):
            d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=c)

pl(FEAT["rivers"]["opequon_creek"]["waypoints"], [(17, (34, 62, 96, 255)), (12, (62, 118, 168, 255)), (4, (120, 170, 205, 255))])
for k in ("hoge_run", "abrams_creek"):
    pl(FEAT["rivers"][k]["waypoints"], [(10, (34, 62, 96, 255)), (6, (70, 128, 176, 255))])
for k, rd in FEAT["roads"].items():
    if rd.get("kind") != "pike":
        pl(rd["waypoints"], [(9, (70, 48, 30, 255)), (6, (136, 98, 62, 255))])
pl(FEAT["roads"]["valley_pike"]["waypoints"], [(19, (82, 72, 58, 255)), (15, (196, 188, 166, 255)), (9, (232, 226, 206, 255))])
# railroad
rr = [ll2px(*c) for c in FEAT["railroads"]["winchester_and_potomac"]["waypoints"]]
d.line(rr, fill=(150, 136, 116, 255), width=11)
dense = []
for a, b in zip(rr, rr[1:]):
    L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(L / 6))
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for i in range(n):
        f = i / n; dense.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, ang))
for x, y, ang in dense:
    nx, ny = -math.sin(ang), math.cos(ang)
    d.line([(x - nx * 7, y - ny * 7), (x + nx * 7, y + ny * 7)], fill=(92, 66, 42, 255), width=3)
for off in (-2.5, 2.5):
    pts = [(x - math.sin(a) * off, y + math.cos(a) * off) for x, y, a in dense]
    d.line(pts, fill=(30, 28, 26, 255), width=2)
# stone wall
sw = [ll2px(*c) for c in FEAT["stone_walls"]["glass_wall_sandy_ridge"]["waypoints"]]
d.line(sw, fill=(60, 56, 50, 255), width=8)
d.line(sw, fill=(178, 174, 162, 255), width=5)
for a, b in zip(sw, sw[1:]):
    n = int(math.hypot(b[0] - a[0], b[1] - a[1]) / 5)
    for i in range(n):
        f = i / n; x, y = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
        d.rectangle((x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=(120, 116, 106, 255))
# rail fences along lanes near farms (zigzag)
def zigzag(coords):
    pts = [ll2px(*c) for c in coords]
    for a, b in zip(pts, pts[1:]):
        n = int(math.hypot(b[0] - a[0], b[1] - a[1]) / 7)
        ang = math.atan2(b[1] - a[1], b[0] - a[0]); nx, ny = -math.sin(ang) * 9, math.cos(ang) * 9
        zz = [(a[0] + (b[0] - a[0]) * i / n + nx + (3 if i % 2 else -3) * -math.sin(ang),
               a[1] + (b[1] - a[1]) * i / n + ny + (3 if i % 2 else -3) * math.cos(ang)) for i in range(n + 1)]
        d.line(zz, fill=(104, 78, 50, 230), width=2)
zigzag(FEAT["roads"]["stone_lane"]["waypoints"])
zigzag(FEAT["roads"]["cedar_creek_grade"]["waypoints"])
# fords
for f in FEAT["fords"]:
    x, y = ll2px(f["lon"], f["lat"])
    for k in range(-2, 3):
        d.line([(x - 10, y + k * 3), (x + 10, y + k * 3)], fill=(225, 214, 180, 220), width=1)
    d.ellipse((x - 9, y - 9, x + 9, y + 9), outline=(30, 26, 22, 255), width=2)

# ---------- buildings ----------
def building(x, y, w, h, ang, wall, roof):
    c, s = math.cos(ang), math.sin(ang)
    def rot(px, py): return (x + px * c - py * s, y + px * s + py * c)
    sh = [rot(-w / 2 + 2, -h / 2 + 2), rot(w / 2 + 2, -h / 2 + 2), rot(w / 2 + 2, h / 2 + 2), rot(-w / 2 + 2, h / 2 + 2)]
    d.polygon(sh, fill=(40, 32, 24, 120))
    body = [rot(-w / 2, -h / 2), rot(w / 2, -h / 2), rot(w / 2, h / 2), rot(-w / 2, h / 2)]
    d.polygon(body, fill=roof, outline=(36, 28, 22, 255))
    d.line([rot(-w / 2, 0), rot(w / 2, 0)], fill=tuple(max(0, v - 30) for v in roof[:3]) + (255,), width=1)

BRICK = [(150, 82, 62, 255), (136, 72, 54, 255), (164, 96, 72, 255)]
STONE = [(170, 166, 154, 255), (150, 146, 136, 255)]
ROOF = [(96, 70, 52, 255), (84, 86, 92, 255), (110, 80, 58, 255)]

# Winchester street grid (1862 core: Loudoun/Market/Braddock N-S, Boscawen/Water/Piccadilly E-W)
wc = ll2px(-78.1633, 39.1857)
grid_ang = math.radians(-8)  # approx rotation of Winchester grid
ca, sa = math.cos(grid_ang), math.sin(grid_ang)
def wrot(u, v): return (wc[0] + u * ca - v * sa, wc[1] + u * sa + v * ca)
block = 46
streets_ns = range(-4, 5)
streets_ew = range(-6, 7)
for i in streets_ns:
    d.line([wrot(i * block, -6.5 * block), wrot(i * block, 6.5 * block)], fill=(120, 90, 60, 255), width=5)
for j in streets_ew:
    d.line([wrot(-4.5 * block, j * block), wrot(4.5 * block, j * block)], fill=(120, 90, 60, 255), width=4)
for i in range(-4, 4):
    for j in range(-6, 6):
        dist = math.hypot(i + 0.5, (j + 0.5) * 0.7)
        density = max(0.0, 1 - dist / 6.0)
        if density <= 0: continue
        for k in range(int(3 + density * 9)):
            u = (i + 0.12 + rng.random() * 0.76) * block
            v = (j + 0.12 + rng.random() * 0.76) * block
            if rng.random() > density + 0.2: continue
            x, y = wrot(u, v)
            wall = BRICK[rng.integers(3)] if rng.random() < 0.6 else STONE[rng.integers(2)]
            building(x, y, rng.uniform(7, 13), rng.uniform(6, 10), grid_ang, wall, wall if rng.random() < 0.3 else ROOF[rng.integers(3)])
# courthouse + churches
x, y = wrot(0, 0); building(x, y, 18, 14, grid_ang, STONE[0], (84, 86, 92, 255))
d.rectangle((x - 2, y - 14, x + 2, y - 7), fill=(200, 196, 184, 255), outline=(40, 32, 24, 255))

def village(lon, lat, n, spread=30):
    cx, cy = ll2px(lon, lat)
    for k in range(n):
        x, y = cx + rng.normal(0, spread * 0.5), cy + rng.normal(0, spread * 0.35)
        building(x, y, rng.uniform(7, 11), rng.uniform(6, 9), rng.uniform(-0.3, 0.3),
                 BRICK[rng.integers(3)], ROOF[rng.integers(3)])
village(-78.1967, 39.1437, 11, 34)        # Kernstown
village(-78.2100, 39.1160, 6, 24)         # Bartonsville
village(-78.1750, 39.1650, 5, 22)         # Milltown
for nm, lon, lat in [("Pritchard", -78.2010, 39.1410), ("Glass", -78.2160, 39.1470), ("Grim", -78.1990, 39.1375),
                     ("Barton", -78.2060, 39.1190), ("Hoge", -78.1860, 39.1430), ("Ramseur", -78.2250, 39.1510)]:
    cx, cy = ll2px(lon, lat)
    building(cx, cy, 11, 8, 0.2, (214, 204, 184, 255), (96, 70, 52, 255))  # farmhouse
    building(cx + 14, cy + 6, 14, 9, 0.2, (122, 92, 64, 255), (110, 80, 58, 255))  # barn
# Opequon Presbyterian Church (limestone, steeple)
cx, cy = ll2px(-78.1925, 39.1408)
building(cx, cy, 16, 11, 0.0, STONE[0], (84, 86, 92, 255))
d.rectangle((cx - 3, cy - 18, cx + 3, cy - 5), fill=(170, 166, 154, 255), outline=(30, 26, 22, 255))
d.polygon([(cx - 4, cy - 18), (cx, cy - 28), (cx + 4, cy - 18)], fill=(70, 72, 78, 255), outline=(30, 26, 22, 255))
d.line([(cx, cy - 33), (cx, cy - 28)], fill=(30, 26, 22, 255), width=2)
for k in range(5):  # graveyard stones
    d.rectangle((cx + 12 + k * 4, cy + 4, cx + 14 + k * 4, cy + 7), fill=(200, 196, 186, 255))

base.save(ROOT / "data/basemap_kernstown.png")
print("basemap", base.size, "R_px", R_PX)
json.dump({"W": W, "H": H, "px_per_m": PX_PER_M, "R_px": R_PX}, open(ROOT / "data/basemap_meta.json", "w"))
