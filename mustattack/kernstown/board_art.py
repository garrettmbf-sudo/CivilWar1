"""Painted board image for meta.boardArt, aligned to the Must Attack hex grid.

Geometry (checked against antietam1862.json, where the dotted fence marks in its board image fall
exactly on the fenced hexsides; see validate_kernstown_ma.py check_boardart_geometry):
  world centre of hex (q, r) = (sqrt(3)*R*(q + 0.5*(r & 1)), 1.5*R*r),  R = hexSize = 45
  image pixel              = (world - origin) * scale,  scale = 2
  origin                   = (-sqrt(3)*R/2 - 13.5, -R - 13.5)  (13.5 world units of padding)
  image size               = ((sqrt(3)*R*(W + 0.5) + 27) * scale, (R*(1.5*(H - 1) + 2) + 27) * scale)
Pixels outside the board's hex outline are transparent, as in the stock image.

Ground: the repo's own v0.4.2 painted basemap (data/basemap_painted_full.png, built by
painted_sections/build_full_map.py; gitignored, so pass its path), resampled to this grid, softened
and washed toward parchment so counters stay readable.  Over it, hex-exact layers drawn from the game
terrain so the art and the rules agree: woods, ridge hachures, stone wall on the fenced hexsides,
roads/creeks through the same hexes the game uses, farm and village buildings, and a few water/road
names.  Place names of hexes are NOT drawn here: the editor says a hex's name "is drawn on the game
map too", so drawing them again would double them.
"""
import hashlib, io, math, os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None

R = 45.0
SCALE = 2
PAD = 13.5
SQ3 = math.sqrt(3)
FONT_DIR = "/usr/share/fonts/truetype/sand-box/google"
F_ITAL = os.path.join(FONT_DIR, "IM Fell French Canon", "IMFellFrenchCanon-Italic.ttf")
F_CAPS = os.path.join(FONT_DIR, "IM Fell English SC", "IMFellEnglishSC-Regular.ttf")
PARCH = np.array([236, 226, 200], np.float32)


def geometry(cols, rows):
    ox, oy = -SQ3 * R / 2 - PAD, -R - PAD
    W = int(round((SQ3 * R * (cols + 0.5) + 2 * PAD) * SCALE))
    H = int(round((R * (1.5 * (rows - 1) + 2) + 2 * PAD) * SCALE))
    return ox, oy, W, H


def hex_px(q, r, ox, oy):
    return ((SQ3 * R * (q + 0.5 * (r & 1)) - ox) * SCALE, (1.5 * R * r - oy) * SCALE)


def corners(cx, cy, k=1.0):
    rr = R * SCALE * k
    return [(cx + rr * math.cos(math.radians(60 * i - 30)), cy + rr * math.sin(math.radians(60 * i - 30))) for i in range(6)]


def edge_pts(cx, cy, e):
    """Endpoints of hexside e (0=E 1=SE 2=SW 3=W 4=NW 5=NE) of a pointy-top hex."""
    c = corners(cx, cy)
    return c[e], c[(e + 1) % 6]


def chaikin(pts, it=3):
    for _ in range(it):
        if len(pts) < 3:
            return pts
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        out.append(pts[-1])
        pts = out
    return pts


def hex_mask(hexes, ox, oy, W, H, k=1.02):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for q, r in hexes:
        d.polygon(corners(*hex_px(q, r, ox, oy), k), fill=255)
    return np.asarray(m, np.float32) / 255.0


def blob(hexes, ox, oy, W, H, sigma=22):
    """Hex-union softened into a natural outline (still inside the hexes it stands for)."""
    if not hexes:
        return np.zeros((H, W), bool)
    m = hex_mask(hexes, ox, oy, W, H)
    s = ndimage.gaussian_filter(m, sigma)
    return s > 0.5


def ground(painted, grid, W, H, ox, oy, kgrid):
    """Resample the repo painting (HoS v0.4.2 geometry, 0.55 px/m) onto this board."""
    src = Image.open(painted).convert("RGB")
    sw, sh = src.size
    small = 4  # work at 1/4 then upsample: the softening we want anyway, and fast
    w4, h4 = W // small + 1, H // small + 1
    px, py = np.meshgrid((np.arange(w4) + 0.5) * small, (np.arange(h4) + 0.5) * small)
    xm = (px / SCALE + ox) * kgrid + grid.s / 2
    ym = (py / SCALE + oy) * kgrid + grid.s / 2
    lon = grid.west + xm / grid.mlon
    lat = grid.north - ym / grid.mlat
    # repo hex_grid.KERNSTOWN projection (scripts/hex_grid.py GridSpec.lonlat_to_xy_m)
    west, south, north = -78.260, 39.100, 39.210
    mlat = 111_132.0
    mlon = 111_132.0 * math.cos(math.radians((south + north) / 2))
    sx = (lon - west) * mlon * 0.55
    sy = sh - (lat - south) * mlat * 0.55
    a = np.asarray(src.filter(ImageFilter.BoxBlur(3)), np.float32)
    out = np.stack([ndimage.map_coordinates(a[..., c], [sy - 0.5, sx - 0.5], order=1, mode="nearest") for c in range(3)], -1)
    im = Image.fromarray(out.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    im = im.resize((W, H), Image.BICUBIC)
    g = np.asarray(im, np.float32)
    lum = g.mean(-1, keepdims=True)
    g = lum + (g - lum) * 0.75                     # a little less saturated
    g = g * 0.5 + PARCH * 0.5 + 18                 # wash toward parchment, lighten
    return g.clip(0, 255)


def flat_ground(W, H):
    rng = np.random.default_rng(1862)
    n = ndimage.zoom(rng.random((H // 64 + 2, W // 64 + 2)).astype(np.float32), 64, order=3)[:H, :W]
    g = np.empty((H, W, 3), np.float32)
    g[:] = PARCH
    g += (n[..., None] - 0.5) * 14
    return g


def paint(base, mask, rgb, alpha):
    base[mask] = base[mask] * (1 - alpha) + np.array(rgb, np.float32) * alpha


def make_board_art(grid, terrain, chains, fences, elev, painted=None, seed=1862):
    cols, rows = grid.cols, grid.rows
    ox, oy, W, H = geometry(cols, rows)
    kgrid = grid.s / (SQ3 * R)                     # metres per world unit
    rng = np.random.default_rng(seed)
    if painted and os.path.exists(painted):
        g = ground(painted, grid, W, H, ox, oy, kgrid)
        src = "painted"
    else:
        g = flat_ground(W, H)
        src = "flat"

    by = {}
    for h, t in terrain.items():
        by.setdefault(t, []).append(h)
    high = by.get("mountain", []) + by.get("rough", []) + by.get("fortress", [])
    woods = by.get("forest", []) + by.get("rough", [])

    # ridges: buff tint and hachures running downslope from the crest
    hb = blob(high, ox, oy, W, H, 26)
    paint(g, hb, (190, 158, 108), 0.40)
    woods_b = blob(woods, ox, oy, W, H, 18)
    paint(g, woods_b, (118, 128, 86), 0.42)
    paint(g, blob(by.get("city", []), ox, oy, W, H, 10), (200, 176, 150), 0.45)
    marsh_b = blob(by.get("marsh", []), ox, oy, W, H, 14)
    paint(g, marsh_b, (150, 175, 170), 0.35)

    im = Image.fromarray(g.astype(np.uint8)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # hachures: short strokes across the slope band of each ridge, pointing downhill (to its edge)
    if hb.any():
        dist = ndimage.distance_transform_edt(hb)
        sm = ndimage.gaussian_filter(dist, 5)
        gy, gx = np.gradient(sm)
        band = np.argwhere((dist > 4) & (dist < 40))
        rng.shuffle(band)
        taken = np.zeros((H // 14 + 1, W // 14 + 1), bool)
        for y, x in band[: len(band) // 3]:
            cy, cx = y // 14, x // 14
            if taken[cy, cx]:
                continue
            taken[cy, cx] = True
            vx, vy = -gx[y, x], -gy[y, x]
            n = math.hypot(vx, vy)
            if n < 1e-3:
                continue
            L = min(dist[y, x], rng.uniform(16, 26))
            d.line([(x, y), (x + vx / n * L, y + vy / n * L)], fill=(120, 88, 52, 170), width=3)
    # woods: tree crowns (bare March woods: olive-brown, Hotchkiss style)
    if woods_b.any():
        pts = np.argwhere(woods_b[::30, ::30]) * 30
        for y, x in pts:
            x += rng.uniform(-12, 12)
            y += rng.uniform(-12, 12)
            if not woods_b[min(int(y), H - 1), min(int(x), W - 1)]:
                continue
            rr = rng.uniform(8, 12)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(104, 114, 70, 150), outline=(60, 66, 38, 200), width=2)
    for q, r in by.get("marsh", []):
        cx, cy = hex_px(q, r, ox, oy)
        for _ in range(14):
            x, y = cx + rng.uniform(-55, 55), cy + rng.uniform(-55, 55)
            for k in (-6, 0, 6):
                d.line([(x + k, y), (x + k * 1.6, y - 9)], fill=(70, 110, 120, 200), width=2)

    # creeks and roads through the same hexes the game uses (smoothed hex-centre chains)
    def path(chain):
        return chaikin([hex_px(q, r, ox, oy) for q, r in chain])
    for chain in chains.get("rivers", []):
        p = path(chain)
        d.line(p, fill=(70, 105, 140, 255), width=11, joint="curve")
        d.line(p, fill=(140, 180, 205, 255), width=5, joint="curve")
    for name, chain in chains.get("roads", []):
        p = path(chain)
        wide = name == "valley_pike"
        d.line(p, fill=(70, 52, 34, 255), width=15 if wide else 11, joint="curve")
        d.line(p, fill=(232, 214, 170, 255), width=9 if wide else 5, joint="curve")
    for chain in chains.get("trails", []):
        p = path(chain)
        segs = []
        acc = 0.0
        for a, b in zip(p, p[1:]):
            L = math.dist(a, b)
            if (acc // 18) % 2 == 0:
                segs.append((a, b))
            acc += L
        for a, b in segs:
            d.line([a, b], fill=(95, 70, 45, 230), width=4)

    # buildings: hamlets / farms (wasteland) and Winchester (city)
    def house(x, y, w, h, ang, col=(128, 58, 44, 255)):
        c, s = math.cos(ang), math.sin(ang)
        pts = [(x + c * dx - s * dy, y + s * dx + c * dy) for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))]
        d.polygon(pts, fill=col, outline=(50, 30, 22, 255))
    for q, r in by.get("wasteland", []):
        cx, cy = hex_px(q, r, ox, oy)
        for _ in range(3):
            house(cx + rng.uniform(-40, 40), cy + rng.uniform(-40, 30), rng.uniform(9, 13), rng.uniform(6, 9), rng.uniform(-0.4, 0.4))
    for q, r in by.get("city", []):
        cx, cy = hex_px(q, r, ox, oy)
        for gx_ in (-28, 28):
            for gy_ in (-30, 26):
                x, y = cx + gx_ + rng.uniform(-4, 4), cy + gy_ + rng.uniform(-4, 4)
                d.rectangle([x - 24, y - 22, x + 24, y + 22], fill=(178, 120, 96, 235), outline=(100, 62, 48, 255), width=2)
                d.line([(x - 24, y), (x + 24, y)], fill=(120, 76, 58, 200), width=2)

    # stone wall on the fenced hexsides: a row of field stones (Antietam marks fences with dots)
    for (q, r), es in fences.items():
        cx, cy = hex_px(q, r, ox, oy)
        for e in es:
            (x0, y0), (x1, y1) = edge_pts(cx, cy, e)
            n = 13
            for i in range(n + 1):
                t = i / n
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                rr = rng.uniform(4.5, 6.5)
                d.ellipse([x - rr, y - rr * 0.8, x + rr, y + rr * 0.8], fill=(150, 146, 136, 255), outline=(40, 38, 34, 255), width=2)

    # names of water and roads (hex place names are drawn by the game itself)
    def label(txt, at, ang, size, col=(60, 45, 30, 255), font=F_ITAL):
        f = ImageFont.truetype(font, size)
        tw = int(d.textlength(txt, font=f)) + 20
        t = Image.new("RGBA", (tw, size * 2), (0, 0, 0, 0))
        td = ImageDraw.Draw(t)
        td.text((tw / 2, size), txt, font=f, anchor="mm", fill=col, stroke_width=3, stroke_fill=(240, 232, 210, 200))
        t = t.rotate(-math.degrees(ang), expand=True, resample=Image.BICUBIC)
        ov.alpha_composite(t, (int(at[0] - t.width / 2), int(at[1] - t.height / 2)))
    for txt, chain, frac, off, kind in chains.get("labels", []):
        p = path(chain)
        i = max(1, min(len(p) - 2, int(len(p) * frac)))
        (x0, y0), (x1, y1) = p[i - 1], p[i + 1]
        ang = math.atan2(y1 - y0, x1 - x0)
        if ang > math.pi / 2:
            ang -= math.pi
        elif ang < -math.pi / 2:
            ang += math.pi
        nx, ny = -math.sin(ang), math.cos(ang)
        at = (p[i][0] + nx * off, p[i][1] + ny * off)
        label(txt, at, ang, 40 if kind == "road" else 44, (50, 80, 110, 255) if kind == "water" else (70, 50, 32, 255))

    # cartouche, south-east corner
    cq, cr = cols - 4, rows - 2
    cx, cy = hex_px(cq, cr, ox, oy)
    f1, f2 = ImageFont.truetype(F_CAPS, 64), ImageFont.truetype(F_ITAL, 38)
    d.rounded_rectangle([cx - 300, cy - 90, cx + 300, cy + 90], 14, fill=(242, 234, 212, 215), outline=(80, 60, 40, 255), width=4)
    d.text((cx, cy - 26), "Kernstown", font=f1, anchor="mm", fill=(60, 42, 28, 255))
    d.text((cx, cy + 40), "Frederick County, Va., 23 March 1862", font=f2, anchor="mm", fill=(60, 42, 28, 255))
    ax, ay = cx - 360, cy
    d.polygon([(ax, ay - 70), (ax - 18, ay), (ax + 18, ay)], fill=(60, 42, 28, 255))
    d.text((ax, ay + 30), "N", font=f2, anchor="mm", fill=(60, 42, 28, 255))

    im.alpha_composite(ov)
    # clip to the board's hex outline, transparent outside (stock style)
    board = hex_mask([(q, r) for r in range(rows) for q in range(cols)], ox, oy, W, H, 1.0) > 0.5
    rgb = im.convert("RGB")
    pal = rgb.quantize(colors=96, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    a = np.asarray(pal).copy()
    a[~board] = 255
    out = Image.fromarray(a, "P")
    p = pal.getpalette()[:96 * 3] + [0, 0, 0] * (256 - 96)
    out.putpalette(p)
    out.info["transparency"] = 255
    buf = io.BytesIO()
    out.save(buf, "PNG", optimize=True, transparency=255)
    png = buf.getvalue()
    meta = {"version": 1, "style": "acw_b", "scale": SCALE, "hexSize": R, "originX": round(ox, 3), "originY": round(oy, 3),
            "grid": "#282828", "gridAlpha": 0.2, "hash": hashlib.sha1(png).hexdigest()}
    return out, png, meta, src
