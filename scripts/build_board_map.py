#!/usr/bin/env python3
"""Board-game-quality First Kernstown basemap + bold-grid previews + HoS hex tiles.

Visual target: Avalon Hill Stonewall in the Valley / MMP Stonewall Jackson's Way —
continuous hypsometric DEM relief, bold edge-matched features, early-spring 1862
palette (tan fields, bare woods + redbud, pale limestone pike). Hex grid is a
SEPARATE preview overlay; never baked into tile PNGs.
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

PX_PER_M = 0.55  # sharper features for board-map look
FEAT = json.loads((ROOT / "data/features/kernstown_features.json").read_text())
mid = (G.south + G.north) / 2
m_lat, m_lon = G.meters_per_deg(mid)
W = int((G.east - G.west) * m_lon * PX_PER_M)
H = int((G.north - G.south) * m_lat * PX_PER_M)
rng = np.random.default_rng(11)
R_PX = G.size_m * PX_PER_M
OUT_PREV = ROOT / "previews"
OUT_PREV.mkdir(exist_ok=True)
TILE_SUMMER = ROOT / "mod/Graphics/Tiles/Summer"
TILE_SPRING = ROOT / "mod/Graphics/Tiles/Spring"
TILE_SUMMER.mkdir(parents=True, exist_ok=True)
TILE_SPRING.mkdir(parents=True, exist_ok=True)

def ll2px(lon, lat):
    return ((lon - G.west) * m_lon * PX_PER_M, (G.north - lat) * m_lat * PX_PER_M)

def hexc(col, row):
    x, y = G.hex_to_xy_m(col, row)
    return x * PX_PER_M, H - y * PX_PER_M

def load_font(size, bold=False):
    cands = [
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ]
    for p in cands:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def build_basemap() -> Image.Image:
    dem = np.array(Image.open(ROOT / "data/dem/kernstown_3dep.tif"), np.float32)
    dem = np.where(np.isfinite(dem), dem, np.nanmedian(dem))
    # Upsample + gentle smooth (preserve ridges, kill DEM speckles)
    demh = np.array(Image.fromarray(dem).resize((W, H), Image.Resampling.BICUBIC), np.float32)
    demh = gaussian_filter(demh, sigma=1.8)

    gy, gx = np.gradient(demh, 1.0 / PX_PER_M)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, alt = math.radians(315), math.radians(38)
    hs = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    hs = np.clip(hs, 0, 1)
    # Dramatic board-map relief (AH ridges are dark, valleys parchment)
    hs = np.power(hs, 1.15)

    lo, hi = np.percentile(demh, 2), np.percentile(demh, 98.5)
    t = np.clip((demh - lo) / (hi - lo + 1e-6), 0, 1)
    # Hypsometric: parchment → straw → ochre → sienna → umber (early spring, NOT green)
    stops = [
        (0.00, (232, 214, 168)),
        (0.22, (214, 190, 138)),
        (0.42, (196, 158, 104)),
        (0.62, (168, 118, 72)),
        (0.80, (138, 88, 52)),
        (1.00, (102, 62, 38)),
    ]
    hyp = np.zeros((H, W, 3), np.float32)
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        m = (t >= t0) & (t <= t1)
        f = ((t[m] - t0) / (t1 - t0 + 1e-9))[:, None]
        hyp[m] = np.array(c0, np.float32) * (1 - f) + np.array(c1, np.float32) * f

    # Strong shade multiply — continuous 3D ridges
    shade = 0.28 + 0.92 * hs
    # Slight ambient occlusion from slope
    shade *= 1.0 - 0.22 * np.clip(slope / math.radians(25), 0, 1)
    img = np.clip(hyp * shade[..., None], 0, 255)

    # Subtle parchment grain (not noisy bumps)
    grain = rng.normal(0, 1, (H // 4 + 1, W // 4 + 1)).astype(np.float32)
    grain = np.array(Image.fromarray(((grain - grain.min()) / (np.ptp(grain) + 1e-6) * 255).astype(np.uint8))
                     .resize((W, H), Image.Resampling.BILINEAR), np.float32) / 255.0
    img = np.clip(img * (0.97 + 0.06 * grain[..., None]), 0, 255)

    base = Image.fromarray(img.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(base, "RGBA")

    # Plowed / fallow parcels in lowland (AH open-ground variation)
    for _ in range(160):
        cx, cy = rng.uniform(0, W), rng.uniform(0, H)
        ix, iy = int(min(W - 1, cx)), int(min(H - 1, cy))
        if t[iy, ix] > 0.48:
            continue
        ww, hh = rng.uniform(40, 110), rng.uniform(28, 70)
        ang = rng.uniform(0, math.pi)
        c, s = math.cos(ang), math.sin(ang)
        corners = [(-ww, -hh), (ww, -hh), (ww, hh), (-ww, hh)]
        pts = [(cx + x * c - y * s, cy + x * s + y * c) for x, y in corners]
        if rng.random() < 0.5:
            d.polygon(pts, fill=(148, 108, 70, 55))
            for k in range(-int(hh), int(hh), 6):
                a = (cx + (-ww) * c - k * s, cy + (-ww) * s + k * c)
                b = (cx + ww * c - k * s, cy + ww * s + k * c)
                d.line([a, b], fill=(118, 86, 54, 50), width=1)
        else:
            d.polygon(pts, fill=(228, 210, 158, 45))

    # ---------- Woods: AH-style canopy mass + sparse large tree symbols ----------
    yy, xx = np.mgrid[0:H, 0:W]
    forest = np.zeros((H, W), bool)
    for lon, lat in FEAT["ridge_cores"]["sandy_ridge"]:
        px, py = ll2px(lon, lat)
        forest |= ((xx - px) ** 2 / (140 ** 2) + (yy - py) ** 2 / (320 ** 2)) < 1
    forest |= (slope > math.radians(6.5)) & (t > 0.32)
    # Extra woodlots
    for _ in range(28):
        cx, cy = rng.uniform(0, W), rng.uniform(0, H)
        rx, ry = rng.uniform(45, 130), rng.uniform(35, 100)
        forest |= ((xx - cx) ** 2 / rx ** 2 + (yy - cy) ** 2 / ry ** 2) < 1
    for lon, lat in FEAT["ridge_cores"]["pritchards_hill"]:
        px, py = ll2px(lon, lat)
        forest &= ((xx - px) ** 2 + (yy - py) ** 2) > 95 ** 2
    for p in FEAT["places"]:
        px, py = ll2px(p["lon"], p["lat"])
        rad = 70 if p.get("kind") == "city" else 40
        forest &= ((xx - px) ** 2 + (yy - py) ** 2) > rad ** 2
    # Soft canopy underlay (dark olive-brown mass — early spring bare woods)
    fm = Image.fromarray((forest.astype(np.uint8) * 255)).filter(ImageFilter.GaussianBlur(10))
    canopy = Image.new("RGBA", (W, H), (78, 68, 48, 0))
    canopy.putalpha(fm.point(lambda v: int(v * 0.55)))
    base = Image.alpha_composite(base, canopy)
    # Second darker pass for dense interior
    canopy2 = Image.new("RGBA", (W, H), (58, 50, 36, 0))
    fm2 = fm.filter(ImageFilter.GaussianBlur(4))
    canopy2.putalpha(fm2.point(lambda v: int(max(0, v - 60) * 0.45)))
    base = Image.alpha_composite(base, canopy2)
    d = ImageDraw.Draw(base, "RGBA")

    # Tree clumps (larger, fewer — board-map style)
    fy, fx = np.where(forest)
    if len(fx):
        n_trees = min(len(fx) // 140, 5500)
        idx = rng.choice(len(fx), size=n_trees, replace=False)
        order = idx[np.argsort(fy[idx])]
        for i in order:
            x, y = float(fx[i]), float(fy[i])
            r = rng.uniform(7.0, 12.0)
            kind = rng.random()
            if kind < 0.08:  # redbud bloom
                crown = (176, 92, 132, 240)
            elif kind < 0.14:  # dead snag
                d.line([(x, y + r), (x, y - r * 1.7)], fill=(90, 82, 72, 255), width=2)
                d.line([(x, y - r * 0.5), (x - r * 0.9, y - r * 1.3)], fill=(90, 82, 72, 255), width=1)
                d.line([(x, y - r * 0.7), (x + r, y - r * 1.4)], fill=(90, 82, 72, 255), width=1)
                continue
            else:
                g = int(rng.integers(-10, 10))
                crown = (108 + g, 96 + g, 78 + g, 235)
            d.ellipse((x - r + 2, y - r + 2, x + r + 2, y + r + 2), fill=(40, 32, 24, 70))
            d.ellipse((x - r, y - r, x + r, y + r), fill=crown, outline=(62, 52, 40, 180))
            # small companion blobs for clump look
            if rng.random() < 0.45:
                ox, oy = rng.uniform(-r, r), rng.uniform(-r * 0.4, r * 0.4)
                rr = r * 0.55
                d.ellipse((x + ox - rr, y + oy - rr, x + ox + rr, y + oy + rr), fill=crown)

    def orchard(lon, lat, n=7, m=5, sp=14):
        px, py = ll2px(lon, lat)
        for i in range(n):
            for j in range(m):
                x, y = px + i * sp, py + j * sp
                d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(124, 106, 84, 240), outline=(72, 58, 44, 220))
    for lon, lat in [(-78.178, 39.176), (-78.185, 39.160), (-78.205, 39.128), (-78.150, 39.170)]:
        orchard(lon, lat)

    # ---------- Linework (AH/MMP bold style) ----------
    def pl(coords, layers):
        pts = [ll2px(*c) for c in coords]
        for w, c in layers:
            d.line(pts, fill=c, width=w, joint="curve")
            for p in (pts[0], pts[-1]):
                d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=c)

    # Creeks — bright blue, dark casing (highly visible on board maps)
    pl(FEAT["rivers"]["opequon_creek"]["waypoints"], [
        (22, (28, 52, 88, 255)), (16, (48, 108, 168, 255)), (8, (140, 188, 220, 255))])
    for k in ("hoge_run", "abrams_creek"):
        pl(FEAT["rivers"][k]["waypoints"], [
            (14, (28, 52, 88, 255)), (9, (58, 120, 176, 255)), (4, (130, 178, 210, 255))])

    # Dirt roads first (under pike)
    for k, rd in FEAT["roads"].items():
        if rd.get("kind") == "pike":
            continue
        pl(rd["waypoints"], [(11, (72, 48, 28, 255)), (7, (148, 108, 68, 255))])

    # Valley Pike — pale crushed limestone with brown casing (NOT neon white)
    pl(FEAT["roads"]["valley_pike"]["waypoints"], [
        (24, (86, 70, 50, 255)), (18, (176, 164, 136, 255)), (12, (204, 192, 162, 255))])

    # W&P RR — period single-track wooden ties
    rr = [ll2px(*c) for c in FEAT["railroads"]["winchester_and_potomac"]["waypoints"]]
    d.line(rr, fill=(168, 152, 128, 255), width=14)
    dense = []
    for a, b in zip(rr, rr[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / 7))
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for i in range(n):
            f = i / n
            dense.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, ang))
    for x, y, ang in dense:
        nx, ny = -math.sin(ang), math.cos(ang)
        d.line([(x - nx * 9, y - ny * 9), (x + nx * 9, y + ny * 9)], fill=(98, 70, 44, 255), width=3)
    for off in (-3.0, 3.0):
        pts = [(x - math.sin(a) * off, y + math.cos(a) * off) for x, y, a in dense]
        d.line(pts, fill=(24, 22, 20, 255), width=2)

    # Glass stone wall on Sandy Ridge
    sw = [ll2px(*c) for c in FEAT["stone_walls"]["glass_wall_sandy_ridge"]["waypoints"]]
    d.line(sw, fill=(48, 44, 40, 255), width=10)
    d.line(sw, fill=(186, 180, 166, 255), width=6)
    for a, b in zip(sw, sw[1:]):
        n = int(math.hypot(b[0] - a[0], b[1] - a[1]) / 6)
        for i in range(n):
            f = i / n
            x, y = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
            d.rectangle((x - 2, y - 2, x + 2, y + 2), fill=(128, 122, 110, 255))

    def zigzag(coords):
        pts = [ll2px(*c) for c in coords]
        for a, b in zip(pts, pts[1:]):
            n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 8))
            ang = math.atan2(b[1] - a[1], b[0] - a[0])
            nx, ny = -math.sin(ang) * 10, math.cos(ang) * 10
            zz = []
            for i in range(n + 1):
                f = i / n
                side = 4 if i % 2 else -4
                zz.append((a[0] + (b[0] - a[0]) * f + nx + side * -math.sin(ang),
                           a[1] + (b[1] - a[1]) * f + ny + side * math.cos(ang)))
            d.line(zz, fill=(110, 82, 52, 230), width=2)
    zigzag(FEAT["roads"]["stone_lane"]["waypoints"])
    zigzag(FEAT["roads"]["cedar_creek_grade"]["waypoints"])

    for f in FEAT["fords"]:
        x, y = ll2px(f["lon"], f["lat"])
        for k in range(-3, 4):
            d.line([(x - 14, y + k * 3.5), (x + 14, y + k * 3.5)], fill=(228, 216, 178, 230), width=2)
        d.ellipse((x - 12, y - 12, x + 12, y + 12), outline=(32, 26, 20, 255), width=2)

    # ---------- Buildings ----------
    def building(x, y, w, h, ang, wall, roof):
        c, s = math.cos(ang), math.sin(ang)
        def rot(px, py):
            return (x + px * c - py * s, y + px * s + py * c)
        sh = [rot(-w / 2 + 2, -h / 2 + 2), rot(w / 2 + 2, -h / 2 + 2),
              rot(w / 2 + 2, h / 2 + 2), rot(-w / 2 + 2, h / 2 + 2)]
        d.polygon(sh, fill=(40, 32, 24, 110))
        body = [rot(-w / 2, -h / 2), rot(w / 2, -h / 2), rot(w / 2, h / 2), rot(-w / 2, h / 2)]
        d.polygon(body, fill=roof, outline=(36, 28, 22, 255))
        d.line([rot(-w / 2, 0), rot(w / 2, 0)],
               fill=tuple(max(0, v - 28) for v in roof[:3]) + (255,), width=1)

    BRICK = [(152, 84, 64, 255), (138, 74, 56, 255), (166, 98, 74, 255)]
    STONE = [(174, 170, 158, 255), (152, 148, 138, 255)]
    ROOF = [(98, 72, 54, 255), (86, 88, 94, 255), (112, 82, 60, 255)]

    wc = ll2px(-78.1633, 39.1857)
    grid_ang = math.radians(-8)
    ca, sa = math.cos(grid_ang), math.sin(grid_ang)
    def wrot(u, v):
        return (wc[0] + u * ca - v * sa, wc[1] + u * sa + v * ca)
    block = 52
    for i in range(-4, 5):
        d.line([wrot(i * block, -6.5 * block), wrot(i * block, 6.5 * block)],
               fill=(128, 98, 68, 255), width=6)
    for j in range(-6, 7):
        d.line([wrot(-4.5 * block, j * block), wrot(4.5 * block, j * block)],
               fill=(128, 98, 68, 255), width=5)
    # town fill tone
    for i in range(-4, 4):
        for j in range(-6, 6):
            pts = [wrot(i * block + 4, j * block + 4), wrot((i + 1) * block - 4, j * block + 4),
                   wrot((i + 1) * block - 4, (j + 1) * block - 4), wrot(i * block + 4, (j + 1) * block - 4)]
            d.polygon(pts, fill=(198, 186, 164, 70))
    for i in range(-4, 4):
        for j in range(-6, 6):
            dist = math.hypot(i + 0.5, (j + 0.5) * 0.7)
            density = max(0.0, 1 - dist / 6.0)
            if density <= 0:
                continue
            for _k in range(int(4 + density * 10)):
                u = (i + 0.12 + rng.random() * 0.76) * block
                v = (j + 0.12 + rng.random() * 0.76) * block
                if rng.random() > density + 0.15:
                    continue
                x, y = wrot(u, v)
                wall = BRICK[rng.integers(3)] if rng.random() < 0.62 else STONE[rng.integers(2)]
                building(x, y, rng.uniform(8, 14), rng.uniform(7, 11), grid_ang, wall,
                         wall if rng.random() < 0.28 else ROOF[rng.integers(3)])
    x, y = wrot(0, 0)
    building(x, y, 20, 15, grid_ang, STONE[0], (84, 86, 92, 255))
    d.rectangle((x - 2, y - 16, x + 2, y - 8), fill=(200, 196, 184, 255), outline=(40, 32, 24, 255))

    def village(lon, lat, n, spread=34):
        cx, cy = ll2px(lon, lat)
        for _k in range(n):
            x, y = cx + rng.normal(0, spread * 0.5), cy + rng.normal(0, spread * 0.35)
            building(x, y, rng.uniform(8, 12), rng.uniform(7, 10), rng.uniform(-0.3, 0.3),
                     BRICK[rng.integers(3)], ROOF[rng.integers(3)])
    village(-78.1967, 39.1437, 14, 38)
    village(-78.2100, 39.1160, 7, 26)
    village(-78.1750, 39.1650, 6, 24)
    for lon, lat in [(-78.2010, 39.1410), (-78.2160, 39.1470), (-78.1990, 39.1375),
                    (-78.2060, 39.1190), (-78.1860, 39.1430), (-78.2250, 39.1510)]:
        cx, cy = ll2px(lon, lat)
        building(cx, cy, 12, 9, 0.2, (216, 206, 186, 255), (98, 72, 54, 255))
        building(cx + 16, cy + 7, 16, 10, 0.2, (124, 94, 66, 255), (112, 82, 60, 255))

    cx, cy = ll2px(-78.1925, 39.1408)
    building(cx, cy, 18, 12, 0.0, STONE[0], (84, 86, 92, 255))
    d.rectangle((cx - 3, cy - 20, cx + 3, cy - 6), fill=(170, 166, 154, 255), outline=(30, 26, 22, 255))
    d.polygon([(cx - 5, cy - 20), (cx, cy - 32), (cx + 5, cy - 20)], fill=(70, 72, 78, 255), outline=(30, 26, 22, 255))
    d.line([(cx, cy - 38), (cx, cy - 32)], fill=(30, 26, 22, 255), width=2)
    for k in range(5):
        d.rectangle((cx + 14 + k * 5, cy + 4, cx + 16 + k * 5, cy + 8), fill=(200, 196, 186, 255))

    base = ImageEnhance.Contrast(base).enhance(1.08)
    base = ImageEnhance.Color(base).enhance(0.92)  # slightly desaturated board-print feel
    return base, t, demh

def draw_bold_hex_grid(draw, w, h, width=3, color=(32, 26, 20, 210)):
    """Flat-top even-q hex outlines matching G — SEPARATE overlay layer."""
    for col in range(G.cols):
        for row in range(G.rows):
            cx, cy = hexc(col, row)
            if cx < -R_PX or cy < -R_PX or cx > w + R_PX or cy > h + R_PX:
                continue
            pts = []
            for i in range(6):
                ang = math.radians(60 * i)  # flat-top: 0° = east vertex
                pts.append((cx + R_PX * math.cos(ang), cy + R_PX * math.sin(ang)))
            draw.line(pts + [pts[0]], fill=color, width=width)

def draw_labels(draw, scale=1.0):
    font_major = load_font(int(28 * scale), bold=True)
    font_feat = load_font(int(20 * scale), bold=True)
    font_farm = load_font(int(14 * scale), bold=False)
    majors = [
        ("WINCHESTER", -78.1633, 39.1885, font_major, 22, -20, 3),
        ("Kernstown", -78.1967, 39.1437, font_feat, 16, 14, 2),
        ("Opequon Church", -78.1925, 39.1408, font_feat, 18, -16, 2),
        ("Sandy Ridge", -78.2180, 39.1480, font_feat, -40, -12, 2),
        ("Pritchard's Hill", -78.2050, 39.1365, font_feat, 14, 16, 2),
        ("Valley Pike", -78.1750, 39.1700, font_feat, 26, 2, 2),
        ("Middle Road", -78.2380, 39.1600, font_feat, -44, 0, 2),
        ("Opequon Creek", -78.1480, 39.1550, font_feat, 16, 10, 2),
        ("W&P RR", -78.1450, 39.1950, font_feat, 12, -14, 2),
        ("Bartonsville", -78.2100, 39.1160, font_feat, 10, 12, 2),
    ]
    farms = [
        ("Pritchard", -78.2010, 39.1410, 8, 10),
        ("Glass", -78.2160, 39.1465, -8, 10),
        ("Hoge", -78.1860, 39.1430, 8, -8),
        ("Grim", -78.1990, 39.1375, 8, 8),
    ]
    for name, lon, lat, font, dx, dy, stroke in majors:
        x, y = ll2px(lon, lat)
        draw.text((x + dx, y + dy), name, font=font, fill=(28, 22, 16, 245),
                  stroke_width=stroke, stroke_fill=(236, 228, 206, 210))
    for name, lon, lat, dx, dy in farms:
        x, y = ll2px(lon, lat)
        draw.text((x + dx, y + dy), name, font=font_farm, fill=(60, 48, 36, 190),
                  stroke_width=1, stroke_fill=(230, 220, 196, 140))

def render_previews(base: Image.Image):
    """Full + closeups with BOLD separate hex grid + labels."""
    # Full
    full = base.copy()
    g = Image.new("RGBA", full.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g, "RGBA")
    draw_bold_hex_grid(gd, *full.size, width=max(3, int(R_PX * 0.055)), color=(24, 18, 12, 230))
    full = Image.alpha_composite(full, g)
    ld = Image.new("RGBA", full.size, (0, 0, 0, 0))
    draw_labels(ImageDraw.Draw(ld, "RGBA"), scale=1.0)
    full = Image.alpha_composite(full, ld)
    rgb = full.convert("RGB")
    # Downscale for manageable preview while keeping detail
    max_side = 3200
    if max(rgb.size) > max_side:
        s = max_side / max(rgb.size)
        rgb = rgb.resize((int(rgb.size[0] * s), int(rgb.size[1] * s)), Image.Resampling.LANCZOS)
    rgb.save(OUT_PREV / "kernstown_full.jpg", quality=92, optimize=True)
    # No-grid version
    base.convert("RGB").resize(rgb.size, Image.Resampling.LANCZOS).save(
        OUT_PREV / "kernstown_full_nogrid.jpg", quality=90, optimize=True)

    def crop_save(lon0, lat0, lon1, lat1, name, label_scale=1.3, grid_w=3):
        x0, y1 = ll2px(lon0, lat0)
        x1, y0 = ll2px(lon1, lat1)
        box = (int(min(x0, x1)), int(min(y0, y1)), int(max(x0, x1)), int(max(y0, y1)))
        crop = base.crop(box)
        g = Image.new("RGBA", crop.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(g, "RGBA")
        # local hex grid: shift hexc into crop coords
        for col in range(G.cols):
            for row in range(G.rows):
                cx, cy = hexc(col, row)
                cx -= box[0]; cy -= box[1]
                if cx < -R_PX or cy < -R_PX or cx > crop.size[0] + R_PX or cy > crop.size[1] + R_PX:
                    continue
                pts = [(cx + R_PX * math.cos(math.radians(60 * i)),
                        cy + R_PX * math.sin(math.radians(60 * i))) for i in range(6)]
                gd.line(pts + [pts[0]], fill=(28, 22, 16, 220), width=grid_w)
        crop = Image.alpha_composite(crop, g)
        # labels in crop space
        lab = Image.new("RGBA", crop.size, (0, 0, 0, 0))
        dd = ImageDraw.Draw(lab, "RGBA")
        # reuse draw_labels but offset — inline simplified
        font_major = load_font(int(32 * label_scale), bold=True)
        font_feat = load_font(int(22 * label_scale), bold=True)
        font_farm = load_font(int(15 * label_scale), bold=False)
        items = [
            ("WINCHESTER", -78.1633, 39.1885, font_major, 18, -18, 3),
            ("Kernstown", -78.1967, 39.1437, font_feat, 14, 12, 2),
            ("Opequon Church", -78.1925, 39.1408, font_feat, 14, -14, 2),
            ("Sandy Ridge", -78.2180, 39.1480, font_feat, -36, -10, 2),
            ("Pritchard's Hill", -78.2050, 39.1365, font_feat, 12, 14, 2),
            ("Valley Pike", -78.1980, 39.1500, font_feat, 20, 0, 2),
            ("stone wall", -78.2180, 39.1450, font_farm, 8, 8, 1),
            ("Pritchard", -78.2010, 39.1410, font_farm, 8, 8, 1),
            ("Glass", -78.2160, 39.1465, font_farm, -6, 8, 1),
        ]
        for name_l, lon, lat, font, dx, dy, stroke in items:
            x, y = ll2px(lon, lat)
            x -= box[0]; y -= box[1]
            if -40 < x < crop.size[0] + 40 and -40 < y < crop.size[1] + 40:
                dd.text((x + dx, y + dy), name_l, font=font, fill=(28, 22, 16, 245),
                        stroke_width=stroke, stroke_fill=(236, 228, 206, 210))
        crop = Image.alpha_composite(crop, lab).convert("RGB")
        # Upscale if small for readability
        if max(crop.size) < 1400:
            s = 1400 / max(crop.size)
            crop = crop.resize((int(crop.size[0] * s), int(crop.size[1] * s)), Image.Resampling.LANCZOS)
        crop.save(OUT_PREV / name, quality=93, optimize=True)
        print("wrote", name, crop.size)

    crop_save(-78.235, 39.122, -78.165, 39.162, "closeup_kernstown_sandy_ridge.jpg")
    crop_save(-78.195, 39.168, -78.135, 39.205, "closeup_winchester.jpg")
    crop_save(-78.230, 39.130, -78.185, 39.158, "closeup_pritchards_hill.jpg", label_scale=1.5, grid_w=4)
    # Medium overview
    med = full.convert("RGB")
    med = med.resize((1800, int(1800 * med.size[1] / med.size[0])), Image.Resampling.LANCZOS)
    med.save(OUT_PREV / "kernstown_medium.jpg", quality=92, optimize=True)
    print("previews written")

def slice_tiles(base: Image.Image, limit=None):
    """Cut unique SV_K_col_row 2000×2000 flat-top hex tiles from continuous basemap."""
    mask = Image.open(ROOT / "data/hex_mask.png").convert("L")
    if mask.size != (2000, 2000):
        mask = mask.resize((2000, 2000), Image.Resampling.NEAREST)
    # Half-width of hex in basemap px = R_PX; tile covers 2*R_PX square mapped to 2000
    half = R_PX  # distance center→vertex
    # Stock tiles: opaque hex inscribed in 2000×2000; flat-top width = 2000, height = 2000*√3/2
    # Our mask is L; use it as alpha.
    names = []
    n = 0
    total = G.cols * G.rows
    for col in range(G.cols):
        for row in range(G.rows):
            if limit is not None and n >= limit:
                break
            cx, cy = hexc(col, row)
            # Crop square covering the hex (flat-top: width 2*R_PX, height √3*R_PX)
            # Use square of side 2*R_PX centered on hex, then resize to 2000 and multiply mask
            side = 2.0 * R_PX
            left, top = cx - side / 2, cy - side / 2
            # Paste onto transparent canvas if near edge
            tile_src = Image.new("RGBA", (int(side) + 2, int(side) + 2), (0, 0, 0, 0))
            src_box = (int(left), int(top), int(left + side), int(top + side))
            # Clamp paste
            region = Image.new("RGBA", (int(side), int(side)), (210, 190, 150, 255))
            # Copy overlapping basemap
            bx0, by0 = max(0, src_box[0]), max(0, src_box[1])
            bx1, by1 = min(base.size[0], src_box[2]), min(base.size[1], src_box[3])
            if bx1 > bx0 and by1 > by0:
                piece = base.crop((bx0, by0, bx1, by1))
                region.paste(piece, (bx0 - src_box[0], by0 - src_box[1]))
            region = region.resize((2000, 2000), Image.Resampling.LANCZOS)
            r, g, b, _a = region.split()
            out = Image.merge("RGBA", (r, g, b, mask))
            name = f"SV_K_{col}_{row}"
            out.save(TILE_SUMMER / f"{name}.png", compress_level=3)
            # Spring alias: hardlink or copy lightweight
            spring_path = TILE_SPRING / f"{name}.png"
            if not spring_path.exists():
                try:
                    spring_path.hardlink_to(TILE_SUMMER / f"{name}.png")
                except Exception:
                    out.save(spring_path, compress_level=3)
            names.append({"col": col, "row": row, "tile_name": name})
            n += 1
            if n % 200 == 0:
                print(f"  tiles {n}/{total}")
        if limit is not None and n >= limit:
            break
    print(f"sliced {n} tiles")
    return names

def write_layers(hexes):
    # Enrich with terrain hints from features for .sav builder
    layers = {
        "grid": {
            "cols": G.cols, "rows": G.rows, "hex_yards": G.hex_yards,
            "orientation": "flat-top even-q",
            "bbox": {"west": G.west, "south": G.south, "east": G.east, "north": G.north},
            "neighbor_m": G.hex_m, "size_m": G.size_m,
        },
        "hexes": hexes,
        "season": "Summer",
        "notes": "Unique per-hex tiles sliced from continuous DEM basemap for edge-matched relief.",
    }
    out = ROOT / "data/layers"
    out.mkdir(parents=True, exist_ok=True)
    (out / "kernstown_hexes.json").write_text(json.dumps(layers))
    # CSV
    import csv
    with open(out / "kernstown_hexes.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["col", "row", "tile_name"])
        w.writeheader()
        w.writerows(hexes)
    print("layers written", len(hexes))

def contact_sheet(hexes, n=24):
    """Sample tiles contact sheet for QA."""
    cols = 6
    rows = (n + cols - 1) // cols
    cell = 220
    sheet = Image.new("RGB", (cols * cell, rows * cell), (40, 36, 32))
    pick = hexes[:: max(1, len(hexes) // n)][:n]
    for i, h in enumerate(pick):
        p = TILE_SUMMER / f"{h['tile_name']}.png"
        if not p.exists():
            continue
        im = Image.open(p).convert("RGBA").resize((cell - 8, cell - 8), Image.Resampling.LANCZOS)
        bg = Image.new("RGBA", (cell - 8, cell - 8), (210, 190, 150, 255))
        bg = Image.alpha_composite(bg, im)
        r, c = divmod(i, cols)
        sheet.paste(bg.convert("RGB"), (c * cell + 4, r * cell + 4))
    sheet.save(OUT_PREV / "tile_contact_board.jpg", quality=90)
    print("contact sheet")

def main():
    print(f"basemap target {W}x{H}, R_px={R_PX:.2f}, grid {G.cols}x{G.rows}")
    base, t, demh = build_basemap()
    base.save(ROOT / "data/basemap_kernstown.png", compress_level=3)
    json.dump({"W": W, "H": H, "px_per_m": PX_PER_M, "R_px": R_PX,
               "cols": G.cols, "rows": G.rows}, open(ROOT / "data/basemap_meta.json", "w"))
    print("basemap saved", base.size)
    render_previews(base)
    # Full unique tile set for continuous in-engine relief
    hexes = slice_tiles(base, limit=None)
    write_layers(hexes)
    contact_sheet(hexes)
    print("DONE")

if __name__ == "__main__":
    main()
