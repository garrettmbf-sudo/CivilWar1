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
NCOL = 128   # v3.2: was 96; the hillshade needs more steps to avoid banding
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
    g = g * 0.5 + PARCH * 0.5 + 8                  # wash toward parchment (v3.6: +8, was +18, so the grey plates stand out)
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


def hillshade(dem, grid, W, H, ox, oy, kgrid, small=4):
    """v3.2: the repo DEM (classify_terrain's 10 m grid, lightly smoothed) resampled onto the board at
    1/small resolution: elevation Z (m) and a NW-lit hillshade in 0..1."""
    Z, step = dem["Z"], dem["step"]
    w4, h4 = W // small + 1, H // small + 1
    px, py = np.meshgrid((np.arange(w4) + 0.5) * small, (np.arange(h4) + 0.5) * small)
    xm = (px / SCALE + ox) * kgrid + grid.s / 2
    ym = (py / SCALE + oy) * kgrid + grid.s / 2
    z = ndimage.map_coordinates(Z, [ym / step, xm / step], order=1, mode="nearest")
    cell = small / SCALE * kgrid                      # metres per low-res pixel
    gy, gx = np.gradient(z, cell)
    ex = 2.5                                          # vertical exaggeration (v3.6: 2.5, was 4): a gently rolling Valley
    nx, ny, nz = -gx * ex, -gy * ex, np.ones_like(z)
    n = np.sqrt(nx ** 2 + ny ** 2 + 1)
    lx, ly, lz = -0.5, -0.5, 0.707                    # light from the north-west, 45 degrees up
    sh = ((nx * lx + ny * ly + nz * lz) / n).clip(0, 1)
    return z, sh


def up(a, W, H, order=1):
    return np.asarray(Image.fromarray(a.astype(np.float32), "F").resize((W, H), Image.BILINEAR if order else Image.NEAREST))


INK = (58, 40, 26, 255)
PAPER = (244, 236, 214, 255)   # v3.6: opaque (Hotchkiss P10), no contours ghosting through


def town(d, ov, city, chains, path, ox, oy, W, H, rng):
    """v3.5: Winchester as a street grid laid on the line of the Valley Turnpike (its main street),
    blocks built up along their street fronts with yards behind, instead of v3.2's repeated squares
    that sat on top of the pike and the creek.  Nothing is drawn on a road or creek."""
    if not city:
        return
    cm = blob(city, ox, oy, W, H, 10)
    av = Image.new("L", (W, H), 0)
    ad = ImageDraw.Draw(av)
    for _, chain in chains.get("roads", []):
        ad.line(path(chain), fill=255, width=44)
    for chain in chains.get("rivers", []):
        ad.line(path(chain), fill=255, width=30)
    avoid = np.asarray(av) > 0
    pike = dict(chains.get("roads", [])).get("valley_pike", [])
    pk = [p for p in path(pike) if 0 <= p[0] < W and 0 <= p[1] < H and cm[int(p[1]), int(p[0])]]
    if len(pk) < 2:
        return
    ang = math.atan2(pk[-1][1] - pk[0][1], pk[-1][0] - pk[0][0])
    ux, uy, vx, vy = math.cos(ang), math.sin(ang), -math.sin(ang), math.cos(ang)
    o = pk[len(pk) // 2]
    BU, BV, S = 132, 120, 22                      # block length along the pike, across it, street width
    ext = int(max(W, H))
    def P(u, v):
        return (o[0] + u * ux + v * vx, o[1] + u * uy + v * vy)
    # streets: pale, clipped to the town and kept off the pike and creek
    st = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(st)
    for k in range(-14, 15):
        sd.line([P(-ext, (k + 0.5) * BV), P(ext, (k + 0.5) * BV)], fill=255, width=S)
        sd.line([P((k + 0.5) * BU, -ext), P((k + 0.5) * BU, ext)], fill=255, width=S)
    smask = (np.asarray(st) > 0) & ndimage.binary_dilation(cm, iterations=6) & ~avoid
    lay = np.zeros((H, W, 4), np.uint8)
    lay[smask] = (218, 204, 172, 235)
    ov.alpha_composite(Image.fromarray(lay, "RGBA"))
    HK_LOG["streets"] = smask                      # v3.8: for the overlap check
    def ok(x, y):
        xi, yi = int(x), int(y)
        return 0 <= xi < W and 0 <= yi < H and cm[yi, xi] and not avoid[yi, xi]
    cols = [(176, 112, 88, 255)] * 5 + [(232, 224, 206, 255)] * 3 + [(192, 182, 162, 255)] * 2
    # v3.8: hatch the built-up blocks (inset 6 px from the street), clear of streets, pike and creek
    blocks = []
    for i in range(-14, 14):
        for j in range(-14, 14):
            u0, u1 = (i + 0.5) * BU + S / 2 + 6, (i + 1.5) * BU - S / 2 - 6
            v0, v1 = (j + 0.5) * BV + S / 2 + 6, (j + 1.5) * BV - S / 2 - 6
            if ok(*P((u0 + u1) / 2, (v0 + v1) / 2)):
                blocks.append([P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)])
    hk_town_hatch(ov, blocks, cm & ~avoid & ~smask, W, H)
    for i in range(-14, 14):
        for j in range(-14, 14):
            u0, u1 = (i + 0.5) * BU + S / 2 + 2, (i + 1.5) * BU - S / 2 - 2
            v0, v1 = (j + 0.5) * BV + S / 2 + 2, (j + 1.5) * BV - S / 2 - 2
            if not ok(*P((u0 + u1) / 2, (v0 + v1) / 2)) and not ok(*P(u0 + 20, v0 + 14)) and not ok(*P(u1 - 20, v1 - 14)):
                continue
            # houses along both long street fronts, a gap now and then for a yard or lane
            for side, vv, dv in ((0, v0, 1), (1, v1, -1)):
                u = u0
                while u < u1 - 10:
                    w = rng.uniform(16, 30)
                    if u + w > u1:
                        w = u1 - u
                    if w >= 10 and rng.random() > 0.14:
                        dep = rng.uniform(22, 30)
                        quad = [P(u, vv), P(u + w, vv), P(u + w, vv + dv * dep), P(u, vv + dv * dep)]
                        if all(ok(x, y) for x, y in quad) and hk_clear_poly(quad):   # v3.8: whole footprint
                            d.polygon([(x + 3, y + 4) for x, y in quad], fill=(40, 30, 20, 80))
                            d.polygon(quad, fill=cols[int(rng.integers(0, len(cols)))], outline=(70, 46, 34, 255))
                            hk_register("town house", quad)          # v3.8
                            a, b = P(u + 2, vv + dv * dep / 2), P(u + w - 2, vv + dv * dep / 2)
                            d.line([a, b], fill=(96, 62, 46, 200), width=2)
                    u += w + rng.uniform(1, 7)
            # a garden tree or two in the yard between the rows
            for _ in range(int(rng.integers(0, 3))):
                x, y = P(rng.uniform(u0 + 15, u1 - 15), rng.uniform(v0 + 34, v1 - 34))
                if ok(x, y):
                    d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(104, 116, 66, 230), outline=(56, 64, 34, 230))


def _font(path, size):
    return ImageFont.truetype(path, size)


def cartouche(ov, cx, cy, px_per_m):
    """Period title block: double ruled frame with corner rosettes, title, place and date, and
    two scale bars (yards above, meters below) drawn at the board's own scale.
    v3.6 (Hotchkiss P10): 840 x 560 (was 1000 x 660), every offset and font x 0.85."""
    f = 0.85
    W_, H_ = 840, 560
    lay = Image.new("RGBA", (W_ + 40, H_ + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = 20, 20, 20 + W_, 20 + H_
    d.rectangle([x0 + 8, y0 + 10, x1 + 8, y1 + 10], fill=(40, 30, 20, 70))          # cast shadow
    d.rectangle([x0, y0, x1, y1], fill=PAPER, outline=INK, width=6)
    d.rectangle([x0 + 14, y0 + 14, x1 - 14, y1 - 14], outline=INK, width=2)
    # a fine rope of short ticks between the rules
    for t in range(0, 2 * (W_ + H_), 12):
        if t < W_:
            pts = [(x0 + t, y0 + 7), (x0 + t + 6, y0 + 7)], [(x0 + t, y1 - 7), (x0 + t + 6, y1 - 7)]
        elif t < W_ + H_:
            k = t - W_
            pts = [(x0 + 7, y0 + k), (x0 + 7, y0 + k + 6)], [(x1 - 7, y0 + k), (x1 - 7, y0 + k + 6)]
        else:
            continue
        for p in pts:
            d.line(p, fill=(120, 92, 62, 255), width=3)
    for x, y in ((x0 + 14, y0 + 14), (x1 - 14, y0 + 14), (x0 + 14, y1 - 14), (x1 - 14, y1 - 14)):
        d.ellipse([x - 19, y - 19, x + 19, y + 19], fill=PAPER, outline=INK, width=3)
        d.polygon([(x, y - 13), (x + 5, y), (x, y + 13), (x - 5, y)], fill=INK)
        d.polygon([(x - 13, y), (x, y - 5), (x + 13, y), (x, y + 5)], fill=(120, 92, 62, 255))
    mx = (x0 + x1) / 2
    Y = lambda v: y0 + v * f
    F = lambda path, size: _font(path, round(size * f))
    d.text((mx, Y(68)), "Map of the Battle of", font=F(F_ITAL, 46), anchor="mm", fill=INK)
    d.text((mx, Y(160)), "KERNSTOWN", font=F(F_CAPS, 128), anchor="mm", fill=INK)
    d.text((mx, Y(252)), "Frederick County, Virginia", font=F(F_ITAL, 50), anchor="mm", fill=INK)
    d.text((mx, Y(312)), "Sunday, 23 March 1862", font=F(F_ITAL, 50), anchor="mm", fill=INK)
    # flourish rule
    ry = Y(362)
    d.line([(mx - 280, ry), (mx - 20, ry)], fill=INK, width=3)
    d.line([(mx + 20, ry), (mx + 280, ry)], fill=INK, width=3)
    d.polygon([(mx, ry - 10), (mx + 14, ry), (mx, ry + 10), (mx - 14, ry)], fill=INK)
    for sx in (-1, 1):
        d.ellipse([mx + sx * 290 - 5, ry - 5, mx + sx * 290 + 5, ry + 5], fill=INK)
    # scale bars, 0-1,000 in alternately filled 200-unit cells; length from px_per_m, never hard-coded
    fl, fs = F(F_CAPS, 34), F(F_ITAL, 30)
    def bar(y, unit_m, label, total=1000, step=200):
        Lpx = total * unit_m * px_per_m
        bx = mx - Lpx / 2
        d.text((bx - 16, y + 8), label, font=fl, anchor="rm", fill=INK)
        d.rectangle([bx, y, bx + Lpx, y + 16], outline=INK, width=2)
        n = total // step
        for k in range(n):
            a, b = bx + Lpx * k / n, bx + Lpx * (k + 1) / n
            if k % 2 == 0:
                d.rectangle([a, y, b, y + 16], fill=INK)
            d.line([(a, y - 5), (a, y + 21)], fill=INK, width=2)
        d.line([(bx + Lpx, y - 5), (bx + Lpx, y + 21)], fill=INK, width=2)
        for k in range(n + 1):
            v = k * step
            d.text((bx + Lpx * k / n, y + 38), f"{v:,}", font=fs, anchor="mm", fill=INK)
    bar(Y(410), 0.9144, "Yards")
    bar(Y(500), 1.0, "Meters")
    d.text((mx, Y(612)), "One hex, 300 meters (328 yards) from side to side; one turn, half an hour",
           font=F(F_ITAL, 31), anchor="mm", fill=INK)
    ov.alpha_composite(lay, (int(cx - W_ / 2 - 20), int(cy - H_ / 2 - 20)))


def compass_rose(ov, cx, cy, rr):
    """An 8-point compass rose with a ring of degree ticks and a red north point (v3.6: the 16
    intercardinal half-points are dropped, Hotchkiss P11)."""
    S = int(rr * 2 + 200)
    lay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = S / 2
    LIGHT, DARK, MID = (246, 238, 216, 255), INK, (150, 64, 46, 255)
    d.ellipse([c - rr - 6 + 6, c - rr - 6 + 8, c + rr + 6 + 6, c + rr + 6 + 8], fill=(40, 30, 20, 50))
    d.ellipse([c - rr - 6, c - rr - 6, c + rr + 6, c + rr + 6], fill=(244, 236, 214, 255), outline=DARK, width=4)
    d.ellipse([c - rr + 18, c - rr + 18, c + rr - 18, c + rr - 18], outline=DARK, width=2)
    for k in range(72):
        a = math.radians(k * 5)
        r0 = rr - (14 if k % 2 else 4)
        d.line([(c + r0 * math.sin(a), c - r0 * math.cos(a)), (c + (rr + 2) * math.sin(a), c - (rr + 2) * math.cos(a))],
               fill=DARK, width=2 if k % 2 else 3)
    def point(deg, length, half, colours):
        a = math.radians(deg)
        tip = (c + length * math.sin(a), c - length * math.cos(a))
        l = (c + half * math.sin(a - math.pi / 2), c - half * math.cos(a - math.pi / 2))
        r = (c + half * math.sin(a + math.pi / 2), c - half * math.cos(a + math.pi / 2))
        d.polygon([(c, c), l, tip], fill=colours[0], outline=DARK)
        d.polygon([(c, c), r, tip], fill=colours[1], outline=DARK)
    for deg in range(45, 360, 90):
        point(deg, rr * 0.66, rr * 0.10, (DARK, LIGHT))
    for deg in (90, 180, 270):
        point(deg, rr * 0.88, rr * 0.14, (LIGHT, DARK))
    point(0, rr * 0.88, rr * 0.14, (MID, DARK))
    d.ellipse([c - 12, c - 12, c + 12, c + 12], fill=LIGHT, outline=DARK, width=3)
    f = _font(F_CAPS, 44)                          # v3.6: 44, was 58 (Hotchkiss P11)
    for txt, deg in (("N", 0), ("E", 90), ("S", 180), ("W", 270)):
        a = math.radians(deg)
        rl = rr + 30
        d.text((c + rl * math.sin(a), c - rl * math.cos(a)), txt, font=f, anchor="mm", fill=DARK,
               stroke_width=4, stroke_fill=(244, 236, 214, 230))
    ov.alpha_composite(lay, (int(cx - c), int(cy - c)))


def make_board_art(grid, terrain, chains, fences, elev, painted=None, seed=1862, dem=None, sites=()):
    cols, rows = grid.cols, grid.rows
    ox, oy, W, H = geometry(cols, rows)
    kgrid = grid.s / (SQ3 * R)                     # metres per world unit
    rng = np.random.default_rng(seed)
    HK_LOG.update(objects=[], lines=None, streets=None, exit_zone=None)   # v3.8
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
    open_ground = set(by.get("plain", []))
    site_hex = {h for h, _ in sites}

    # v3.2 field patchwork: Voronoi fields over open ground, each a slightly different tint (stubble,
    # plough, pasture), so the plain is not one flat wash.  Low-res, then upsampled.
    from scipy.spatial import cKDTree
    small = 4
    w4, h4 = W // small + 1, H // small + 1
    seeds = []
    for (q, r) in open_ground:
        cx, cy = hex_px(q, r, ox, oy)
        for _ in range(2 if any(math.dist((q, r), sh) <= 2.5 for sh in site_hex) else 1):
            seeds.append((cx + rng.uniform(-70, 70), cy + rng.uniform(-70, 70)))
    seeds = np.array(seeds) / small
    yy, xx = np.mgrid[0:h4, 0:w4]
    tree = cKDTree(seeds)
    _, lab = tree.query(np.stack([xx.ravel(), yy.ravel()], -1))
    lab = lab.reshape(h4, w4)
    # v3.6 (Hotchkiss P5): March tan and pale green, so the grey Confederate plate separates by hue
    tints = np.array([(206, 190, 138), (196, 176, 128), (190, 198, 146), (214, 202, 160), (182, 192, 140)], np.float32)
    pick = rng.integers(0, len(tints), len(seeds))
    field_rgb = tints[pick][lab]
    open_m = hex_mask(list(open_ground), ox, oy, W, H, 1.0)
    open_small = ndimage.zoom(open_m, 1 / small, order=1)[:h4, :w4]
    open_small = np.pad(open_small, ((0, max(0, h4 - open_small.shape[0])), (0, max(0, w4 - open_small.shape[1]))))
    alpha = ndimage.gaussian_filter(open_small, 3) * 0.32
    fr = np.stack([up(field_rgb[..., c], W, H) for c in range(3)], -1)
    al = up(alpha, W, H)[..., None]
    g = g * (1 - al) + fr * al
    edges_f = (lab[:, 1:] != lab[:, :-1])[:-1, :] | (lab[1:, :] != lab[:-1, :])[:, :-1]

    # v3.2 relief: hillshade and 5 m form lines from the DEM, strongest on the high ground
    hb = blob(high, ox, oy, W, H, 30)
    if dem:
        z, sh = hillshade(dem, grid, W, H, ox, oy, kgrid, small)
        shade = up(sh, W, H)
        base = np.median(shade)
        g *= (1 + 0.40 * (shade - base))[..., None]          # v3.6: 0.40, was 0.55
        ci = 5.0
        lev = np.floor(z / ci)
        e = np.zeros_like(lev, bool)
        e[:, 1:] |= lev[:, 1:] != lev[:, :-1]
        e[1:, :] |= lev[1:, :] != lev[:-1, :]
        idx = e & (np.mod(np.maximum(lev, np.roll(lev, 1, 0)), 4) == 0)
        cl = up(ndimage.gaussian_filter(e.astype(np.float32), 0.6), W, H)
        ci_ = up(ndimage.gaussian_filter(idx.astype(np.float32), 0.6), W, H)
        paint(g, cl > 0.30, (128, 94, 60), 0.12)
        paint(g, ci_ > 0.30, (110, 76, 46), 0.22)
    # game high ground (defence x2): a warm buff tint so it reads as a rule, not only as relief
    soft = ndimage.gaussian_filter(hb.astype(np.float32), 10)
    g = g * (1 - soft[..., None] * 0.18) + np.array((204, 178, 128), np.float32) * soft[..., None] * 0.18   # v3.6: 0.18, was 0.30
    woods_b = blob(woods, ox, oy, W, H, 18)
    paint(g, woods_b, (150, 138, 114), 0.22)            # v3.6: leafless grey-brown woodlot wash
    paint(g, blob(by.get("city", []), ox, oy, W, H, 10), (200, 176, 150), 0.45)
    marsh_b = blob(by.get("marsh", []), ox, oy, W, H, 14)
    paint(g, marsh_b, (176, 186, 150), 0.28)            # v3.6: a wet meadow, not a pond
    # paper grain and a faint darkening toward the board edge
    grain = ndimage.zoom(rng.random((H // 10 + 2, W // 10 + 2)).astype(np.float32), 10, order=1)[:H, :W]
    g += (grain[..., None] - 0.5) * 8
    vy, vx = np.ogrid[0:H, 0:W]
    vig = 1 - 0.07 * (((vx - W / 2) / (W / 2)) ** 4 + ((vy - H / 2) / (H / 2)) ** 4)
    g *= vig[..., None]
    g = g.clip(0, 255)

    im = Image.fromarray(g.astype(np.uint8)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # worm (rail) fences along the field edges around the farms: thin zigzag lines, plainly unlike
    # the heavy stone wall that the game treats as a fence
    from scipy.spatial import Voronoi
    vor = Voronoi(seeds * small)
    hk_fences = []                                 # v3.8: drawn by hk_fence_runs() after the buildings
    site_px = [hex_px(*sh, ox, oy) for sh in site_hex]
    for (i, j), rv in zip(vor.ridge_points, vor.ridge_vertices):
        if -1 in rv:
            continue
        (xa, ya), (xb, yb) = vor.vertices[rv[0]], vor.vertices[rv[1]]
        mx, my = (xa + xb) / 2, (ya + yb) / 2
        if not site_px or min(math.dist((mx, my), sp) for sp in site_px) > 200:
            continue
        L = math.dist((xa, ya), (xb, yb))
        if L < 20 or L > 400 or not (0 <= mx < W and 0 <= my < H) or open_m[int(my), int(mx)] < 0.5:
            continue
        if not all(0 <= v < lim and open_m[int(min(v2, H - 1)), int(min(v1, W - 1))] > 0.5
                   for v, lim, v1, v2 in ((xa, W, xa, ya), (ya, H, xa, ya), (xb, W, xb, yb), (yb, H, xb, yb))):
            continue
        n = max(2, int(L / 12))                   # v3.6: amplitude 2.5, step 12, opaque (Hotchkiss P12)
        ux, uy = (xb - xa) / L, (yb - ya) / L
        pts = [(xa + (xb - xa) * k / n + (-uy) * (2.5 if k % 2 else -2.5), ya + (yb - ya) * k / n + ux * (2.5 if k % 2 else -2.5))
               for k in range(n + 1)]
        hk_fences.append(pts)

    # hachures on the game's high ground: short strokes running downslope from the crest
    if hb.any():
        dist = ndimage.distance_transform_edt(hb)
        sm = ndimage.gaussian_filter(dist, 5)
        gy, gx = np.gradient(sm)
        band = np.argwhere((dist > 6) & (dist < 26))       # v3.6: a narrower, sparser fringe
        rng.shuffle(band)
        taken = np.zeros((H // 18 + 1, W // 18 + 1), bool)
        for y, x in band[: len(band) // 3]:
            cy, cx = y // 18, x // 18
            if taken[cy, cx]:
                continue
            taken[cy, cx] = True
            vx_, vy_ = -gx[y, x], -gy[y, x]
            n = math.hypot(vx_, vy_)
            if n < 1e-3:
                continue
            L = min(dist[y, x], rng.uniform(8, 14))
            d.line([(x, y), (x + vx_ / n * L, y + vy_ / n * L)], fill=(128, 98, 66, 255), width=1)

    # woods: v3.8 drawn tree by tree by hk_woods(), after the roads and creeks are known
    for q, r in by.get("marsh", []):
        cx, cy = hex_px(q, r, ox, oy)
        for _ in range(8):
            x, y = cx + rng.uniform(-55, 55), cy + rng.uniform(-55, 55)
            for k in (-6, 0, 6):
                d.line([(x + k, y), (x + k * 1.6, y - 9)], fill=(92, 120, 104, 255), width=1)
            d.line([(x - 8, y + 3), (x + 8, y + 3)], fill=(92, 120, 104, 255), width=1)

    # creeks and roads through the same hexes the game uses (smoothed hex-centre chains)
    # v3.6 (Hotchkiss P6): a chain that ends on the board's edge row/column runs on one more hex so
    # it leaves the board instead of stopping short (the final clip hides the overhang); the Valley
    # Turnpike gets a light moving average (each centre moves at most 0.35 hex) and more smoothing.
    pike_chain = dict(chains.get("roads", [])).get("valley_pike")
    def on_edge(q, r):
        return q in (0, cols - 1) or r in (0, rows - 1)
    def path(chain):
        pts = [hex_px(q, r, ox, oy) for q, r in chain]
        if len(pts) >= 2:
            if on_edge(*chain[0]):
                pts = [(2 * pts[0][0] - pts[1][0], 2 * pts[0][1] - pts[1][1])] + pts
            if on_edge(*chain[-1]):
                pts = pts + [(2 * pts[-1][0] - pts[-2][0], 2 * pts[-1][1] - pts[-2][1])]
        if chain is pike_chain and len(pts) >= 3:
            lim = 0.35 * SQ3 * R * SCALE
            sm = [pts[0]]
            for a, b, c in zip(pts, pts[1:], pts[2:]):
                mx, my = (a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3
                dx, dy = mx - b[0], my - b[1]
                k = min(1.0, lim / max(1e-6, math.hypot(dx, dy)))
                sm.append((b[0] + dx * k, b[1] + dy * k))
            pts = sm + [pts[-1]]
            return chaikin(pts, 5)
        return chaikin(pts)
    # v3.6 (Hotchkiss P7): Opequon Creek at stream weight, the runs as a single thin line, and
    # Buffalo Lick Run carried on to its confluence with the Opequon
    river_names = ("opequon_creek", "hoge_run", "abrams_creek", "buffalo_lick")
    rpaths = {k: path(c) for k, c in zip(river_names, chains.get("rivers", []))}
    if "buffalo_lick" in rpaths and "opequon_creek" in rpaths:
        bl, oq = rpaths["buffalo_lick"], rpaths["opequon_creek"]
        for end in (0, -1):
            near = min(oq, key=lambda p: math.dist(p, bl[end]))
            if math.dist(near, bl[end]) < 90:
                rpaths["buffalo_lick"] = ([near] + bl) if end == 0 else (bl + [near])
                break
    # v3.8 (engraved pass): meandering, tapering creeks; the mask of every drawn line; the woods
    # drawn tree by tree clear of it, with a clearing round each farmstead
    rpaths = hk_meander(rpaths, seed)
    hk_streams(d, rpaths)
    hk_ctx = hk_lines(W, H, chains, path, rpaths)
    hk_woods(im, d, woods_b, hk_ctx, seed, clearings=site_px)
    rs = Image.new("L", (W, H), 0)
    rsd = ImageDraw.Draw(rs)
    for name, chain in chains.get("roads", []):
        p = [(x + 4, y + 5) for x, y in path(chain)]
        rsd.line(p, fill=110, width=19 if name == "valley_pike" else 13, joint="curve")
    road_shadow = Image.new("RGBA", (W, H), (40, 30, 18, 0))
    road_shadow.putalpha(rs.filter(ImageFilter.GaussianBlur(3)))
    ov.alpha_composite(road_shadow)
    for name, chain in chains.get("roads", []):
        p = path(chain)
        if name == "valley_pike":   # the macadamised Valley Turnpike: wide, pale stone surface
            hk_pike(d, p)                          # v3.8: double-line macadam
        else:
            hk_road(d, p)
    for chain in chains.get("trails", []):
        p = path(chain)
        segs = []
        acc = 0.0
        for a, b in zip(p, p[1:]):
            L = math.dist(a, b)
            if acc % 24 < 14:                     # v3.6: 14 px dash, 10 px gap, 3 px, opaque (lanes)
                segs.append((a, b))
            acc += L
        for a, b in segs:
            d.line([a, b], fill=(95, 70, 45, 255), width=3)

    # v3.6 (Hotchkiss V1): nothing stands on a road, creek or trail.  The same kind of avoid mask
    # town() uses (roads 44 px, creeks 30 px, trails 20 px wide); a building whose footprint (with a
    # few px of margin) touches it moves to the first clear spot on rings of 30/45/60 px around the
    # hex centre, or is left out; an orchard tree that touches it is left out.
    av = Image.new("L", (W, H), 0)
    avd = ImageDraw.Draw(av)
    for _, chain in chains.get("roads", []):
        avd.line(path(chain), fill=255, width=44)
    for p in rpaths.values():
        avd.line(p, fill=255, width=30)
    for chain in chains.get("trails", []):
        avd.line(path(chain), fill=255, width=20)
    avoid = np.asarray(av) > 0
    taken_b = Image.new("L", (W, H), 0)
    tbd = ImageDraw.Draw(taken_b)
    def clear(pts):
        tb = np.asarray(taken_b)
        return all(0 <= x < W and 0 <= y < H and not avoid[int(y), int(x)] and not tb[int(y), int(x)] for x, y in pts)
    def quad(x, y, w, h, ang, m=0):
        c, s_ = math.cos(ang), math.sin(ang)
        return [(x + c * dx - s_ * dy, y + s_ * dx + c * dy) for dx, dy in
                ((-w - m, -h - m), (w + m, -h - m), (w + m, h + m), (-w - m, h + m), (0, 0), (-w - m, 0), (w + m, 0), (0, -h - m), (0, h + m))]
    def bldg(x, y, w, h, ang, col, roof=True, home=None):
        if not clear(quad(x, y, w, h, ang, 3)):
            hx, hy = home if home else (x, y)
            for rad in (30, 45, 60):
                for k in range(8):
                    a = k * math.pi / 4 + 0.3
                    x2, y2 = hx + rad * math.cos(a), hy + rad * math.sin(a)
                    if clear(quad(x2, y2, w, h, ang, 3)):
                        x, y = x2, y2
                        break
                else:
                    continue
                break
            else:
                return False
        c, s_ = math.cos(ang), math.sin(ang)
        rot = lambda pts: [(x + c * dx - s_ * dy, y + s_ * dx + c * dy) for dx, dy in pts]
        hk_building(d, rot, w, h, ang, col, roof)    # v3.8: shaded roof, chimney
        tbd.polygon(rot([(-w - 2, -h - 2), (w + 2, -h - 2), (w + 2, h + 2), (-w - 2, h + 2)]), fill=255)
        return (x, y)
    # v3.2 farmsteads at the named farm / house / church hexes: house, barn, outbuilding, an orchard
    for (q, r), kind in sites:
        cx, cy = hex_px(q, r, ox, oy)
        a0 = rng.uniform(-0.3, 0.3)
        if kind == "church":
            at = bldg(cx - 6, cy + 8, 16, 11, a0, (226, 218, 200, 255), home=(cx, cy))
            if at:                                 # v3.8: cross and dotted churchyard, where it stands
                hk_church(d, at[0], at[1], 16, 11, a0, lambda pts: clear(pts) and hk_ctx is not None
                          and all(not hk_ctx["grown"][int(y), int(x)] for x, y in pts))
            continue
        bldg(cx - 18, cy + 10, 13, 9, a0, (232, 224, 206, 255), home=(cx, cy))            # house (whitewashed)
        if kind == "farm":
            bldg(cx + 20, cy + 6, 17, 10, a0 + 0.1, (150, 62, 44, 255), home=(cx, cy))    # bank barn
            bldg(cx + 2, cy + 34, 7, 5, a0, (170, 120, 90, 255), False, home=(cx, cy))    # outbuilding
            hk_orchard(d, cx, cy, a0, lambda pts: clear(pts) and all(not hk_ctx["grown"][int(y), int(x)] for x, y in pts))  # v3.8
        else:
            bldg(cx + 14, cy + 18, 7, 5, a0, (170, 120, 90, 255), False, home=(cx, cy))

    # buildings: hamlets / farms (wasteland) and Winchester (city).  v3.6 (Hotchkiss P12): set square
    # to the nearest road, within +-0.1 rad, so Kernstown reads as a roadside hamlet.
    road_segs = [(a, b) for _, chain in chains.get("roads", []) for a, b in zip(path(chain), path(chain)[1:])]
    def road_angle(x, y):
        if not road_segs:
            return 0.0
        def dist(seg):
            (ax, ay), (bx, by) = seg
            L2 = (bx - ax) ** 2 + (by - ay) ** 2 or 1e-9
            t = max(0, min(1, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / L2))
            return math.dist((x, y), (ax + t * (bx - ax), ay + t * (by - ay)))
        (ax, ay), (bx, by) = min(road_segs, key=dist)
        a = math.atan2(by - ay, bx - ax)
        while a > math.pi / 2:
            a -= math.pi
        while a < -math.pi / 2:
            a += math.pi
        return a
    for q, r in by.get("wasteland", []):
        if (q, r) in site_hex:
            continue
        cx, cy = hex_px(q, r, ox, oy)
        for i in range(3):
            x, y = cx + rng.uniform(-40, 40), cy + rng.uniform(-40, 30)
            bldg(x, y, rng.uniform(9, 13), rng.uniform(6, 9), road_angle(x, y) + rng.uniform(-0.1, 0.1),
                 [(232, 224, 206, 255), (150, 62, 44, 255), (170, 120, 90, 255)][i], home=(cx, cy))
    town(d, ov, by.get("city", []), chains, path, ox, oy, W, H, rng)
    # v3.8: worm fences (field edges, and along the roads and lanes near the farms), meadow tufts
    # and springs, all clear of every line and building
    tb = np.asarray(taken_b) > 0
    for pts in hk_fences:
        hk_fence_runs(d, pts, hk_ctx, tb, step=12, min_len=3)
    hk_lane_fences(d, chains, path, hk_ctx, tb, open_m, woods_b, site_px)
    hk_meadow(d, grid, ox, oy, hk_ctx, tb, woods_b, seed, keep_off=site_px)
    hk_springs(d, grid, ox, oy, hk_ctx, tb)

    # stone wall on the fenced hexsides.  v3.6 (Hotchkiss P2): a thin, light limestone line instead of
    # v3.2's heavy dark sawtooth.  The fenced hexsides are joined where they share a corner and
    # smoothed (chaikin x2 keeps every point within ~12 px of a hexside), with a faint shadow, a mortar
    # edge and stone dots.  The validator checks the line still lies on every fenced hexside.
    segs = []
    for (q, r), es in fences.items():
        cx, cy = hex_px(q, r, ox, oy)
        for e in es:
            a, b = edge_pts(cx, cy, e)
            segs.append((tuple(round(v, 1) for v in a), tuple(round(v, 1) for v in b)))
    def key(p):
        return (round(p[0]), round(p[1]))
    lines_ = []
    left = segs[:]
    while left:
        a, b = left.pop(0)
        line = [a, b]
        grown = True
        while grown:
            grown = False
            for i, (c, e) in enumerate(left):
                if key(c) == key(line[-1]):
                    line.append(e)
                elif key(e) == key(line[-1]):
                    line.append(c)
                elif key(e) == key(line[0]):
                    line.insert(0, c)
                elif key(c) == key(line[0]):
                    line.insert(0, e)
                else:
                    continue
                left.pop(i)
                grown = True
                break
        lines_.append(line)
    for line in lines_:
        p = chaikin(line, 2)
        d.line([(x + 2, y + 3) for x, y in p], fill=(60, 52, 40, 70), width=7, joint="curve")
        d.line(p, fill=(150, 146, 136, 255), width=6, joint="curve")
        d.line(p, fill=(226, 224, 216, 255), width=3, joint="curve")
        acc = 0.0
        for a, b in zip(p, p[1:]):
            L = math.dist(a, b)
            t = (9 - acc % 9) if acc % 9 else 0
            while t <= L:
                x, y = a[0] + (b[0] - a[0]) * t / L, a[1] + (b[1] - a[1]) * t / L
                d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(196, 192, 182, 255))
                t += 9
            acc += L

    # names of water and roads (hex place names are drawn by the game itself)
    def label(txt, at, ang, size, col=(60, 45, 30, 255), font=F_ITAL):
        f = ImageFont.truetype(font, size)
        tw = int(d.textlength(txt, font=f)) + 20
        t = Image.new("RGBA", (tw, size * 2), (0, 0, 0, 0))
        td = ImageDraw.Draw(t)
        td.text((tw / 2, size), txt, font=f, anchor="mm", fill=col, stroke_width=3, stroke_fill=(240, 232, 210, 255))
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

    # v3.7: the Confederate exits.  A small period-style arrow pointing off the south edge beside the
    # road (east of it), one row in from the edge, with an italic legend to its right; neither touches the exit
    # row itself, so the exit hexes stay clear.
    for txt, (q, r) in chains.get("exits", []):
        # the road crosses row r-1 in the hex north-east of its exit hex (both roads run SSW here)
        rx, ry = hex_px(q + 1, r - 1, ox, oy)
        ax = rx + 70
        y0, y1 = ry - 34, ry + 40
        d.line([(ax, y0), (ax, y1 - 14)], fill=(70, 50, 32, 255), width=4)
        d.polygon([(ax - 11, y1 - 18), (ax + 11, y1 - 18), (ax, y1)], fill=(70, 50, 32, 255))
        d.line([(ax - 8, y0), (ax + 8, y0)], fill=(70, 50, 32, 255), width=3)
        f = ImageFont.truetype(F_ITAL, 30)
        tw = d.textlength(txt, font=f)
        tx = min(ax + 18, W - 30 - tw)
        if tx < ax + 18:                       # too close to the east edge: put the legend on the left
            tx = ax - 18 - tw
        d.text((tx, (y0 + y1) / 2), txt, font=f, anchor="lm", fill=(70, 50, 32, 255),
               stroke_width=3, stroke_fill=(240, 232, 210, 255))

    # v3.5: title cartouche with scale bars, and a compass rose, in the empty south-east corner (east
    # of the pike, south of Buffalo Lick Run: no objective, name or start hex within 5 hexes)
    px_per_m = SQ3 * R * SCALE / grid.s           # hex centre to centre = grid.s metres (300)
    # v3.6 (Hotchkiss P10/P11): a smaller cartouche, a plain 8-point rose just west of it
    cartouche(ov, 4280, 4560, px_per_m)
    compass_rose(ov, 3670, 4600, 120)

    hk_neatline(ov, cols, rows, ox, oy, W, H)      # v3.8: engraved neatline
    im.alpha_composite(ov)
    # clip to the board's hex outline, transparent outside (stock style)
    board = hex_mask([(q, r) for r in range(rows) for q in range(cols)], ox, oy, W, H, 1.0) > 0.5
    rgb = im.convert("RGB")
    # v3.2: median cut drops small, saturated details (the barns came out grey-green), so the palette
    # is median cut for NCOL - len(KEEP) colours plus the drawing colours of the small features.
    KEEP = [(150, 62, 44), (232, 224, 206), (226, 218, 200), (226, 220, 204), (170, 120, 90), (46, 30, 22),
            (96, 112, 60), (140, 180, 205), (70, 105, 140), (222, 198, 150), (54, 50, 44), (160, 156, 146)]
    # v3.6 (Hotchkiss P1-P3, P7): woods, wall, trail/hachure brown, ink, label and paper colours,
    # creeks, so the quantiser does not pull them to olive
    KEEP += [(128, 114, 92), (116, 104, 86), (138, 124, 100), (122, 112, 96), (84, 72, 58),
             (150, 146, 136), (226, 224, 216), (196, 192, 182), (95, 70, 45), (128, 98, 66), (58, 40, 26),
             (70, 50, 32), (244, 236, 214), (80, 116, 146), (150, 186, 206), (50, 80, 110)]
    KEEP += [c for c in HK_KEEP if c not in KEEP]  # v3.8: engraved-pass inks
    base_pal = rgb.quantize(colors=NCOL - len(KEEP), method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    flat = base_pal.getpalette()[:(NCOL - len(KEEP)) * 3] + [v for c in KEEP for v in c]
    pimg = Image.new("P", (1, 1))
    pimg.putpalette(flat + flat[:3] * (256 - NCOL))   # pad with a used colour: index 255 is transparency
    pal = rgb.quantize(palette=pimg, dither=Image.Dither.NONE)
    a = np.asarray(pal).copy()
    a[~board] = 255
    out = Image.fromarray(a, "P")
    p = pal.getpalette()[:NCOL * 3] + [0, 0, 0] * (256 - NCOL)
    out.putpalette(p)
    out.info["transparency"] = 255
    buf = io.BytesIO()
    out.save(buf, "PNG", optimize=True, transparency=255)
    png = buf.getvalue()
    meta = {"version": 1, "style": "acw_b", "scale": SCALE, "hexSize": R, "originX": round(ox, 3), "originY": round(oy, 3),
            "grid": "#282828", "gridAlpha": 0.2, "hash": hashlib.sha1(png).hexdigest()}
    return out, png, meta, src


# ================================================================ v3.8 engraved detail pass (Hotchkiss)
# Everything below is called from make_board_art() through short hooks marked "v3.8".  The look is
# Jed. Hotchkiss's manuscript map of the battle (LOC g3884w.cwh00090, "H90", in the repo at
# data/historic_maps/hotchkiss_h90_hi.png) and the Official Records atlas: fine ink line work, double-
# line roads, zigzag worm fences along the roads, small shaded buildings, a church with a cross in a
# dotted churchyard, orchards in rows, leafless trees drawn one by one, and meadow tufts.
# Only features in the repo's data are drawn: the pritchard_sandy_meadow polygon and the two springs
# are from data/features/kernstown_features.json (copied here with their source, as the build does
# not pass that file in).  No mill, toll gate, milestone or rail is drawn (see the staff note).
# HK_LOG records every object drawn, and the lines it must stay off, for the 0-overlap check.

HK_INK = (72, 56, 40)
HK_TREE = [(188, 176, 150), (176, 164, 138), (196, 184, 158)]       # pale leafless crowns
HK_TREE_DARK, HK_TREE_LIT, HK_STIPPLE = (92, 80, 64), (150, 136, 112), (110, 98, 80)
HK_MEADOW, HK_MEADOW_BASE = (78, 92, 66), (96, 124, 140)
HK_FENCE = (128, 98, 66)
HK_HATCH = (166, 140, 112)
HK_KEEP = [*HK_TREE, HK_TREE_DARK, HK_TREE_LIT, HK_STIPPLE, HK_MEADOW, HK_MEADOW_BASE, HK_HATCH, HK_INK,
           (118, 48, 36), (196, 186, 166), (140, 96, 72), (184, 176, 158), (196, 188, 170), (90, 70, 50),
           (176, 172, 160)]
# data/features/kernstown_features.json: springs[], marshes.pritchard_sandy_meadow.polygon (lon, lat)
HK_SPRINGS = [("Spring near Hoge", -78.212, 39.144), ("Spring E of Pike", -78.19, 39.146)]
HK_MEADOW_POLY = [(-78.218, 39.1505), (-78.2135, 39.1528), (-78.2085, 39.1545), (-78.205, 39.1548),
                  (-78.2035, 39.1525), (-78.2055, 39.1498), (-78.21, 39.1482), (-78.2145, 39.1485),
                  (-78.2175, 39.1495)]
HK_LOG = {"objects": [], "lines": None, "streets": None, "exit_zone": None}


def hk_register(kind, pts, width=0):
    """Record a drawn object: a polygon (width 0) or a polyline of the given width."""
    HK_LOG["objects"].append((kind, [(float(x), float(y)) for x, y in pts], width))


def hk_lonlat_px(grid, ox, oy, lon, lat):
    xm, ym = grid.lonlat_to_xy(lon, lat)
    k = grid.s / (SQ3 * R)
    return ((xm - grid.s / 2) / k - ox) * SCALE, ((ym - grid.s / 2) / k - oy) * SCALE


def _resample(p, step):
    out = [p[0]]
    acc = 0.0
    for a, b in zip(p, p[1:]):
        L = math.dist(a, b)
        t = step - acc
        while t <= L:
            out.append((a[0] + (b[0] - a[0]) * t / L, a[1] + (b[1] - a[1]) * t / L))
            t += step
        acc = (acc + L) % step
    if math.dist(out[-1], p[-1]) > 1:
        out.append(p[-1])
    return out


def _normals(p):
    n = []
    for i in range(len(p)):
        a, b = p[max(0, i - 1)], p[min(len(p) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        n.append((-dy / L, dx / L))
    return n


def hk_meander(rpaths, seed=1862):
    """Creeks that wiggle: two summed sines across the line (<= 5 px), fading out at both ends so the
    confluences and board-edge exits stay where they were."""
    rng = np.random.default_rng(seed + 38)
    out = {}
    for k, p in rpaths.items():
        q = _resample(p, 5)
        n = _normals(q)
        f1, f2 = rng.uniform(0, 6.3, 2)
        amp = 2.4 if k == "opequon_creek" else 3.2
        tot = 5.0 * (len(q) - 1)
        res = []
        for i, ((x, y), (nx, ny)) in enumerate(zip(q, n)):
            s = 5.0 * i
            fade = min(1.0, s / 60, (tot - s) / 60)
            o = fade * (amp * math.sin(2 * math.pi * s / 74 + f1) + 0.6 * amp * math.sin(2 * math.pi * s / 29 + f2))
            res.append((x + nx * o, y + ny * o))
        out[k] = res
    return out


def hk_streams(d, rpaths):
    """Creeks taper from source to mouth.  The mouth of a run is the end nearer the Opequon; the
    Opequon flows north.  The Opequon gets a fine water line either side (OR atlas style)."""
    oq = rpaths.get("opequon_creek", [])
    def mouth_last(k, p):
        if k == "opequon_creek" or not oq:
            return p[-1][1] < p[0][1]
        da = min(math.dist(p[0], o) for o in oq[::4])
        db = min(math.dist(p[-1], o) for o in oq[::4])
        return db < da
    def taper(p, w0, w1, col):
        cum = [0.0]
        for a, b in zip(p, p[1:]):
            cum.append(cum[-1] + math.dist(a, b))
        L = cum[-1] or 1.0
        for i, (a, b) in enumerate(zip(p, p[1:])):
            w = w0 + (w1 - w0) * (cum[i] / L) ** 0.8
            d.line([a, b], fill=col, width=max(1, round(w)))
            if w >= 2.5:
                r_ = w / 2 - 0.3
                d.ellipse([b[0] - r_, b[1] - r_, b[0] + r_, b[1] + r_], fill=col)
    for k, p in rpaths.items():
        p = p if mouth_last(k, p) else p[::-1]
        if k == "opequon_creek":
            for side in (-1, 1):
                n = _normals(p)
                lp = [(x + nx * side * 9, y + ny * side * 9) for (x, y), (nx, ny) in zip(p, n)]
                d.line(lp, fill=(150, 186, 206, 255), width=1)
            taper(p, 5.5, 9.0, (70, 105, 140, 255))
            taper(p, 1.5, 3.5, (150, 186, 206, 255))
        else:
            taper(p, 1.6, 5.2, (80, 116, 146, 255))


def hk_lines(W, H, chains, path, rpaths):
    """Mask of every drawn road, lane and creek at its drawn width (the strict check), and a copy
    grown by a few px (what new objects keep off)."""
    m = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(m)
    for name, chain in chains.get("roads", []):
        md.line(path(chain), fill=255, width=19 if name == "valley_pike" else 12, joint="curve")
    for chain in chains.get("trails", []):
        md.line(path(chain), fill=255, width=4)
    for k, p in rpaths.items():
        md.line(p, fill=255, width=28 if k == "opequon_creek" else 6, joint="curve")   # Opequon incl. its water lines
    strict = np.asarray(m) > 0
    HK_LOG["lines"] = strict
    grown = ndimage.binary_dilation(strict, iterations=5)
    grown |= hk_exit_zone(W, H, chains)
    return {"strict": strict, "grown": grown, "W": W, "H": H}


def hk_exit_zone(W, H, chains, ox=None, oy=None):
    """The v3.7 exit hexes, and the arrow and legend v3.7 draws one row in, kept free of every
    object this pass adds."""
    if ox is None:
        ox, oy = -SQ3 * R / 2 - PAD, -R - PAD
    m = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(m)
    f = ImageFont.truetype(F_ITAL, 30)
    for txt, (q, r) in chains.get("exits", []):
        for dq in (-1, 0, 1):
            md.polygon(corners(*hex_px(q + dq, r, ox, oy), 1.02), fill=255)
        rx, ry = hex_px(q + 1, r - 1, ox, oy)
        ax = rx + 70
        tw = md.textlength(txt, font=f)
        tx = min(ax + 18, W - 30 - tw)
        if tx < ax + 18:
            tx = ax - 18 - tw
        md.rectangle([min(ax - 24, tx - 12), ry - 50, max(ax + 24, tx + tw + 12), ry + 56], fill=255)
    z = np.asarray(m) > 0
    HK_LOG["exit_zone"] = z
    return z


def _free(ctx, pts, taken=None):
    g, W, H = ctx["grown"], ctx["W"], ctx["H"]
    for x, y in pts:
        xi, yi = int(x), int(y)
        if not (0 <= xi < W and 0 <= yi < H) or g[yi, xi] or (taken is not None and taken[yi, xi]):
            return False
    return True


def hk_tree(d, x, y, rr, rng):
    """One leafless tree: a pale crown with a scalloped outline, dark on the shaded south-east side
    and light on the lit north-west side, three stipple dots of twig, and a trunk tick."""
    pts = []
    ph = rng.uniform(0, 6.3)
    for i in range(19):
        t = 2 * math.pi * i / 18
        rad = rr * (1 + 0.13 * math.sin(6 * t + ph))
        pts.append((x + rad * math.cos(t), y + rad * math.sin(t)))
    d.polygon(pts, fill=HK_TREE[int(rng.integers(0, len(HK_TREE)))] + (255,))
    for (a, b) in zip(pts, pts[1:]):
        mxp, myp = (a[0] + b[0]) / 2 - x, (a[1] + b[1]) / 2 - y
        shaded = mxp + myp > -rr * 0.3                  # facing away from a north-west light
        d.line([a, b], fill=(HK_TREE_DARK if shaded else HK_TREE_LIT) + (255,), width=2 if shaded else 1)
    for _ in range(3):
        sx, sy = x + rng.uniform(-rr * 0.5, rr * 0.5), y + rng.uniform(-rr * 0.5, rr * 0.5)
        d.point([(sx, sy), (sx + 1, sy)], fill=HK_STIPPLE + (255,))
    d.line([(x + 1, y + rr * 0.95), (x + 1, y + rr * 0.95 + 3)], fill=HK_TREE_DARK + (255,), width=1)


def hk_woods(im, d, woods_b, ctx, seed, clearings=()):
    """Woodlots as individual leafless trees (H90 draws its woods tree by tree), on a jittered
    22 px lattice with glades, kept off every road, lane and creek, with a clearing round each farm."""
    if not woods_b.any():
        return
    rng = np.random.default_rng(seed + 11)
    H, W = woods_b.shape
    crowns = []
    for y, x in np.argwhere(woods_b[::22, ::22]) * 22:
        if rng.random() < 0.18:
            continue
        x, y = x + rng.uniform(-8, 8), y + rng.uniform(-8, 8)
        rr = rng.uniform(5.0, 8.0)
        if not woods_b[min(int(y), H - 1), min(int(x), W - 1)]:
            continue
        if any(math.dist((x, y), c) < 75 for c in clearings):
            continue
        ring = [(x + (rr + 3) * math.cos(a), y + (rr + 4) * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 9)] + [(x, y)]
        if not _free(ctx, ring):
            continue
        crowns.append((x, y, rr))
    sh = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(sh)
    for x, y, rr in crowns:
        sd.ellipse([x - rr + 3, y - rr + 4, x + rr + 3, y + rr + 4], fill=90)
    sh = sh.filter(ImageFilter.GaussianBlur(2.5))
    shadow = Image.new("RGBA", (W, H), (46, 40, 24, 0))
    shadow.putalpha(sh)
    im.alpha_composite(shadow)
    crowns.sort(key=lambda c: c[1])                    # back to front
    for x, y, rr in crowns:
        hk_tree(d, x, y, rr, rng)
        hk_register("tree", [(x - rr, y - rr), (x + rr, y - rr), (x + rr, y + rr + 3), (x - rr, y + rr + 3)])


def _zigzag(run, amp=2.5):
    n = _normals(run)
    return [(x + nx * (amp if i % 2 else -amp), y + ny * (amp if i % 2 else -amp)) for i, ((x, y), (nx, ny)) in enumerate(zip(run, n))]


def hk_fence_runs(d, pts, ctx, taken, step=10, min_len=4):
    """Draw a worm fence along pts, only where it is clear of every line and building."""
    q = _resample(pts, step) if len(pts) >= 2 else pts
    run = []
    def flush():
        if len(run) >= min_len:
            z = _zigzag(run)
            d.line(z, fill=HK_FENCE + (255,), width=1)
            d.line([(x, y + 1) for x, y in z], fill=HK_FENCE + (110,), width=1)   # a hair of shadow
            hk_register("fence", z, 2)
        run.clear()
    for p in q:
        if _free(ctx, [p, (p[0] + 4, p[1] + 4), (p[0] - 4, p[1] - 4), (p[0] + 4, p[1] - 4), (p[0] - 4, p[1] + 4)], taken):
            run.append(p)
        else:
            flush()
    flush()


def hk_lane_fences(d, chains, path, ctx, taken, open_m, woods_b, site_px, off=30):
    """Worm fences along both sides of the roads and lanes near the farms, as H90 draws them."""
    lines = [path(c) for _, c in chains.get("roads", [])] + [path(c) for c in chains.get("trails", [])]
    H, W = woods_b.shape
    for p in lines:
        q = _resample(p, 10)
        n = _normals(q)
        for side in (-1, 1):
            run = []
            for (x, y), (nx, ny) in zip(q, n):
                fx, fy = x + nx * side * off, y + ny * side * off
                ok = (0 <= fx < W and 0 <= fy < H and open_m[int(fy), int(fx)] > 0.5 and not woods_b[int(fy), int(fx)]
                      and site_px and min(math.dist((fx, fy), s) for s in site_px) < 330)
                if ok:
                    run.append((fx, fy))
                elif run:
                    hk_fence_runs(d, run, ctx, taken)
                    run = []
            if run:
                hk_fence_runs(d, run, ctx, taken)


def hk_meadow(d, grid, ox, oy, ctx, taken, woods_b, seed, keep_off=()):
    """Tufts of rough grass in the wet meadow between Sandy Ridge and Pritchard's Hill
    (kernstown_features.json marshes.pritchard_sandy_meadow)."""
    poly = [hk_lonlat_px(grid, ox, oy, lon, lat) for lon, lat in HK_MEADOW_POLY]
    H, W = woods_b.shape
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    m = np.asarray(m) > 0
    rng = np.random.default_rng(seed + 23)
    ys, xs = np.where(m[::30, ::34])
    for y, x in zip(ys * 30, xs * 34):
        x += 17 * ((y // 30) % 2)                  # staggered rows, as engraved marsh signs are set
        if rng.random() < 0.22:                    # open water-meadow between the clumps
            continue
        x, y = x + rng.uniform(-12, 12), y + rng.uniform(-9, 9)
        xi, yi = int(x), int(y)
        if not (0 <= xi < W and 0 <= yi < H) or not m[yi, xi] or woods_b[yi, xi]:
            continue
        if any(math.dist((x, y), k) < 70 for k in keep_off):
            continue
        box = [(x - 10, y - 11), (x + 10, y - 11), (x + 10, y + 5), (x - 10, y + 5)]
        if not _free(ctx, box, taken):
            continue
        # the period marsh sign: a tuft over short ruled water lines
        d.line([(x - 9, y + 1), (x + 9, y + 1)], fill=HK_MEADOW_BASE + (255,), width=1)
        d.line([(x - 5, y + 4), (x + 6, y + 4)], fill=HK_MEADOW_BASE + (255,), width=1)
        L = rng.uniform(6, 9)
        for dx in (-5, -2.5, 0, 2.5, 5):
            d.line([(x + dx * 0.4, y), (x + dx, y - L * (1 - abs(dx) / 14))], fill=HK_MEADOW + (255,), width=1)
        hk_register("meadow tuft", box)


def hk_springs(d, grid, ox, oy, ctx, taken):
    """The two springs in kernstown_features.json: a small ring with a dot, the period sign.  If the
    data point falls on a line it moves to the nearest clear spot within 40 px."""
    for name, lon, lat in HK_SPRINGS:
        x0, y0 = hk_lonlat_px(grid, ox, oy, lon, lat)
        for rad in (0, 12, 24, 40):
            for k in range(8 if rad else 1):
                x, y = x0 + rad * math.cos(k * math.pi / 4), y0 + rad * math.sin(k * math.pi / 4)
                box = [(x - 8, y - 8), (x + 8, y - 8), (x + 8, y + 8), (x - 8, y + 8), (x, y)]
                if _free(ctx, box, taken):
                    d.ellipse([x - 6, y - 6, x + 6, y + 6], outline=(70, 105, 140, 255), width=2)
                    d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(70, 105, 140, 255))
                    hk_register("spring", box[:4])
                    break
            else:
                continue
            break


def hk_pike(d, p):
    """The macadamised Valley Turnpike as a double-line road: two fine ink edges, a pale metalled
    surface and a light stipple of broken stone."""
    d.line(p, fill=(58, 46, 34, 255), width=19, joint="curve")
    d.line(p, fill=(226, 220, 204, 255), width=15, joint="curve")
    q = _resample(p, 11)
    n = _normals(q)
    for i, ((x, y), (nx, ny)) in enumerate(zip(q, n)):
        o = (2.5 if i % 2 else -2.5) + (1.5 if i % 3 == 0 else 0)
        d.point([(x + nx * o, y + ny * o)], fill=(184, 176, 158, 255))


def hk_road(d, p):
    """A common road: double fine edges, pale earth between."""
    d.line(p, fill=(80, 58, 36, 255), width=12, joint="curve")
    d.line(p, fill=(222, 198, 150, 255), width=8, joint="curve")


def _shade(col, k=0.78):
    return tuple(int(c * k) for c in col[:3]) + (255,)


def hk_building(d, rot, w, h, ang, col, roof=True):
    """A small building drawn as H90/OR atlas do: cast shadow, wall outline, a ridged roof with the
    half away from the north-west light shaded, and (for a house) a chimney at one gable."""
    d.polygon(rot([(-w + 4, -h + 5), (w + 4, -h + 5), (w + 4, h + 5), (-w + 4, h + 5)]), fill=(40, 30, 20, 90))
    long_x = w >= h
    if long_x:
        a_half, b_half = [(-w, -h), (w, -h), (w, 0), (-w, 0)], [(-w, 0), (w, 0), (w, h), (-w, h)]
        nrm = (-math.sin(ang), math.cos(ang))          # outward normal of the +y half
    else:
        a_half, b_half = [(-w, -h), (0, -h), (0, h), (-w, h)], [(0, -h), (w, -h), (w, h), (0, h)]
        nrm = (math.cos(ang), math.sin(ang))
    b_lit = (nrm[0] + nrm[1]) < 0                       # faces the north-west light
    col = tuple(col[:3]) + (255,)
    d.polygon(rot(a_half), fill=col if b_lit is False else _shade(col))
    d.polygon(rot(b_half), fill=col if b_lit else _shade(col))
    if roof:
        d.line(rot([(-w, 0), (w, 0)] if long_x else [(0, -h), (0, h)]), fill=(60, 40, 30, 255), width=1)
        if long_x:   # hipped ends
            for sx in (-1, 1):
                d.line(rot([(sx * w, -h), (sx * (w - min(h, w / 3)), 0), (sx * w, h)]), fill=(60, 40, 30, 255), width=1)
    d.polygon(rot([(-w, -h), (w, -h), (w, h), (-w, h)]), outline=(46, 30, 22, 255))
    if roof and col[:3] == (232, 224, 206) and long_x:
        cx_, cy_ = rot([(-w + 3, 0)])[0]
        d.rectangle([cx_ - 2, cy_ - 2, cx_ + 2, cy_ + 2], fill=(90, 70, 50, 255))
    hk_register("building", rot([(-w, -h), (w, -h), (w, h), (-w, h)]))


def hk_church(d, x, y, w, h, ang, clear):
    """Opequon Church: an upright cross over the gable, and the dotted churchyard enclosure H90
    draws round the church by Kernstown (only the dots that are clear of every line)."""
    c, s_ = math.cos(ang), math.sin(ang)
    rot = lambda pts: [(x + c * dx - s_ * dy, y + s_ * dx + c * dy) for dx, dy in pts]
    gx, gy = rot([(-w * 0.55, 0)])[0]
    d.line([(gx, gy - 6), (gx, gy - 20)], fill=(50, 34, 24, 255), width=3)
    d.line([(gx - 5, gy - 15), (gx + 5, gy - 15)], fill=(50, 34, 24, 255), width=3)
    hk_register("cross", [(gx - 6, gy - 21), (gx + 6, gy - 21), (gx + 6, gy - 5), (gx - 6, gy - 5)])
    yard = rot([(-w - 16, -h - 14), (w + 16, -h - 14), (w + 16, h + 14), (-w - 16, h + 14), (-w - 16, -h - 14)])
    for a, b in zip(yard, yard[1:]):
        L = math.dist(a, b)
        for k in range(int(L // 8) + 1):
            px_, py_ = a[0] + (b[0] - a[0]) * k * 8 / L, a[1] + (b[1] - a[1]) * k * 8 / L
            box = [(px_ - 2, py_ - 2), (px_ + 2, py_ - 2), (px_ + 2, py_ + 2), (px_ - 2, py_ + 2)]
            if clear(box):
                d.ellipse([px_ - 1.6, py_ - 1.6, px_ + 1.6, py_ + 1.6], fill=(90, 70, 50, 255))
                hk_register("churchyard dot", box)


def hk_orchard(d, hx, hy, ang, clear):
    """An orchard in neat rows: 4 rows of 5 small trees, square to the farmstead, north-west of the
    house; a tree that is not clear of roads, creeks, lanes and buildings is left out."""
    c, s_ = math.cos(ang), math.sin(ang)
    for i in range(4):
        for j in range(5):
            dx, dy = -66 + j * 11, -50 + i * 11
            x, y = hx + c * dx - s_ * dy, hy + s_ * dx + c * dy
            box = [(x - 4, y - 4), (x + 4, y - 4), (x + 4, y + 4), (x - 4, y + 4), (x, y)]
            if clear(box):
                d.ellipse([x - 3.2, y - 3.2, x + 3.2, y + 3.2], fill=(176, 172, 160, 255), outline=HK_TREE_DARK + (255,), width=1)
                d.point([(x, y)], fill=HK_TREE_DARK + (255,))
                hk_register("orchard tree", box[:4])


def hk_town_hatch(ov, blocks, keep, W, H):
    """Winchester's built-up blocks hatched at 45 degrees, as the OR atlas fills a town."""
    if not blocks:
        return
    bm = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(bm)
    for quad in blocks:
        bd.polygon(quad, fill=255)
    yy, xx = np.ogrid[0:H, 0:W]
    hatch = ((xx + yy) % 7) == 0
    m = (np.asarray(bm) > 0) & hatch & keep
    lay = np.zeros((H, W, 4), np.uint8)
    lay[m] = HK_HATCH + (255,)
    ov.alpha_composite(Image.fromarray(lay, "RGBA"))


def hk_neatline(ov, cols, rows, ox, oy, W, H):
    """A fine engraved neatline just inside the board's hex outline: a 3 px rule and a hairline 6 px
    inside it."""
    b = hex_mask([(q, r) for r in range(rows) for q in range(cols)], ox, oy, W, H, 1.0) > 0.5
    e2 = ndimage.binary_erosion(b, iterations=2)
    e5 = ndimage.binary_erosion(e2, iterations=3)
    e11 = ndimage.binary_erosion(e5, iterations=6)
    e12 = ndimage.binary_erosion(e11, iterations=1)
    lay = np.zeros((H, W, 4), np.uint8)
    gap = HK_LOG.get("exit_zone")
    gap = np.zeros((H, W), bool) if gap is None else gap
    lay[e2 & ~e5 & ~gap] = INK
    lay[e11 & ~e12 & ~gap] = INK
    ov.alpha_composite(Image.fromarray(lay, "RGBA"))


def hk_clear_poly(poly, pad=3):
    """True when a footprint, grown by pad px, touches no road, lane, creek or street at drawn width."""
    L = HK_LOG["lines"]
    if L is None:
        return True
    H, W = L.shape
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    x0, y0 = max(int(min(xs)) - pad - 1, 0), max(int(min(ys)) - pad - 1, 0)
    x1, y1 = min(int(max(xs)) + pad + 2, W), min(int(max(ys)) + pad + 2, H)
    if x1 <= x0 or y1 <= y0:
        return True
    m = Image.new("L", (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(m).polygon([(x - x0, y - y0) for x, y in poly], fill=255, outline=255, width=1 + 2 * pad)
    grown = np.asarray(m) > 0
    if grown[L[y0:y1, x0:x1]].any():
        return False
    if HK_LOG["streets"] is None:
        return True
    m = Image.new("L", (x1 - x0, y1 - y0), 0)       # the houses front the streets: test the bare footprint
    ImageDraw.Draw(m).polygon([(x - x0, y - y0) for x, y in poly], fill=255)
    return not (np.asarray(m) > 0)[HK_LOG["streets"][y0:y1, x0:x1]].any()
