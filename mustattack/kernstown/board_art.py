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
    ex = 4.0                                          # vertical exaggeration: the ridges are 20-40 m
    nx, ny, nz = -gx * ex, -gy * ex, np.ones_like(z)
    n = np.sqrt(nx ** 2 + ny ** 2 + 1)
    lx, ly, lz = -0.5, -0.5, 0.707                    # light from the north-west, 45 degrees up
    sh = ((nx * lx + ny * ly + nz * lz) / n).clip(0, 1)
    return z, sh


def up(a, W, H, order=1):
    return np.asarray(Image.fromarray(a.astype(np.float32), "F").resize((W, H), Image.BILINEAR if order else Image.NEAREST))


def make_board_art(grid, terrain, chains, fences, elev, painted=None, seed=1862, dem=None, sites=()):
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
    tints = np.array([(196, 180, 120), (170, 140, 100), (178, 182, 128), (210, 196, 150), (186, 160, 112)], np.float32)
    pick = rng.integers(0, len(tints), len(seeds))
    field_rgb = tints[pick][lab]
    open_m = hex_mask(list(open_ground), ox, oy, W, H, 1.0)
    open_small = ndimage.zoom(open_m, 1 / small, order=1)[:h4, :w4]
    open_small = np.pad(open_small, ((0, max(0, h4 - open_small.shape[0])), (0, max(0, w4 - open_small.shape[1]))))
    alpha = ndimage.gaussian_filter(open_small, 3) * 0.22
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
        g *= (1 + 0.55 * (shade - base))[..., None]
        ci = 5.0
        lev = np.floor(z / ci)
        e = np.zeros_like(lev, bool)
        e[:, 1:] |= lev[:, 1:] != lev[:, :-1]
        e[1:, :] |= lev[1:, :] != lev[:-1, :]
        idx = e & (np.mod(np.maximum(lev, np.roll(lev, 1, 0)), 4) == 0)
        cl = up(ndimage.gaussian_filter(e.astype(np.float32), 0.6), W, H)
        ci_ = up(ndimage.gaussian_filter(idx.astype(np.float32), 0.6), W, H)
        paint(g, cl > 0.30, (128, 94, 60), 0.16)
        paint(g, ci_ > 0.30, (110, 76, 46), 0.22)
    # game high ground (defence x2): a warm buff tint so it reads as a rule, not only as relief
    soft = ndimage.gaussian_filter(hb.astype(np.float32), 10)
    g = g * (1 - soft[..., None] * 0.30) + np.array((196, 160, 104), np.float32) * soft[..., None] * 0.30
    woods_b = blob(woods, ox, oy, W, H, 18)
    paint(g, woods_b, (126, 132, 90), 0.34)
    paint(g, blob(by.get("city", []), ox, oy, W, H, 10), (200, 176, 150), 0.45)
    marsh_b = blob(by.get("marsh", []), ox, oy, W, H, 14)
    paint(g, marsh_b, (150, 175, 170), 0.35)
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
        n = max(2, int(L / 9))
        ux, uy = (xb - xa) / L, (yb - ya) / L
        pts = [(xa + (xb - xa) * k / n + (-uy) * (3.5 if k % 2 else -3.5), ya + (yb - ya) * k / n + ux * (3.5 if k % 2 else -3.5))
               for k in range(n + 1)]
        d.line(pts, fill=(98, 76, 52, 190), width=2)

    # hachures on the game's high ground: short strokes running downslope from the crest
    if hb.any():
        dist = ndimage.distance_transform_edt(hb)
        sm = ndimage.gaussian_filter(dist, 5)
        gy, gx = np.gradient(sm)
        band = np.argwhere((dist > 3) & (dist < 34))
        rng.shuffle(band)
        taken = np.zeros((H // 12 + 1, W // 12 + 1), bool)
        for y, x in band[: len(band) // 3]:
            cy, cx = y // 12, x // 12
            if taken[cy, cx]:
                continue
            taken[cy, cx] = True
            vx_, vy_ = -gx[y, x], -gy[y, x]
            n = math.hypot(vx_, vy_)
            if n < 1e-3:
                continue
            L = min(dist[y, x], rng.uniform(12, 22))
            d.line([(x, y), (x + vx_ / n * L, y + vy_ / n * L)], fill=(112, 78, 44, 150), width=2)

    # woods: shadowed tree crowns (bare March woods: olive-brown, Hotchkiss style)
    if woods_b.any():
        sh_l = Image.new("L", (W, H), 0)
        sd = ImageDraw.Draw(sh_l)
        crowns = []
        for y, x in np.argwhere(woods_b[::24, ::24]) * 24:
            x += rng.uniform(-10, 10)
            y += rng.uniform(-10, 10)
            if not woods_b[min(int(y), H - 1), min(int(x), W - 1)]:
                continue
            rr = rng.uniform(8, 13)
            crowns.append((x, y, rr))
            sd.ellipse([x - rr + 5, y - rr + 6, x + rr + 5, y + rr + 6], fill=150)
        sh_l = sh_l.filter(ImageFilter.GaussianBlur(3))
        shadow = Image.new("RGBA", (W, H), (46, 40, 24, 0))
        shadow.putalpha(sh_l.point(lambda v: v * 0.6))
        im.alpha_composite(shadow)
        tones = [(98, 108, 64), (110, 116, 70), (90, 98, 58), (120, 112, 72)]
        for x, y, rr in crowns:
            c = tones[int(rng.integers(0, len(tones)))]
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=c + (235,), outline=(52, 56, 32, 230), width=2)
            d.arc([x - rr * 0.6, y - rr * 0.7, x + rr * 0.3, y + rr * 0.2], 190, 290, fill=(168, 168, 116, 200), width=2)
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
            d.line(p, fill=(58, 46, 34, 255), width=19, joint="curve")
            d.line(p, fill=(226, 220, 204, 255), width=12, joint="curve")
            d.line(p, fill=(196, 188, 170, 255), width=2, joint="curve")
        else:
            d.line(p, fill=(80, 58, 36, 255), width=12, joint="curve")
            d.line(p, fill=(222, 198, 150, 255), width=6, joint="curve")
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

    # v3.2 farmsteads at the named farm / house / church hexes: house, barn, outbuilding, an orchard
    def bldg(x, y, w, h, ang, col, roof=True):
        c, s_ = math.cos(ang), math.sin(ang)
        rot = lambda pts: [(x + c * dx - s_ * dy, y + s_ * dx + c * dy) for dx, dy in pts]
        d.polygon(rot([(-w + 4, -h + 5), (w + 4, -h + 5), (w + 4, h + 5), (-w + 4, h + 5)]), fill=(40, 30, 20, 90))
        d.polygon(rot([(-w, -h), (w, -h), (w, h), (-w, h)]), fill=col, outline=(46, 30, 22, 255))
        if roof:
            d.line(rot([(-w, 0), (w, 0)]), fill=(60, 40, 30, 220), width=2)
    for (q, r), kind in sites:
        cx, cy = hex_px(q, r, ox, oy)
        a0 = rng.uniform(-0.3, 0.3)
        if kind == "church":
            bldg(cx - 6, cy + 8, 16, 11, a0, (226, 218, 200, 255))
            d.line([(cx - 6, cy - 18), (cx - 6, cy - 4)], fill=(50, 34, 24, 255), width=3)
            d.line([(cx - 12, cy - 13), (cx, cy - 13)], fill=(50, 34, 24, 255), width=3)
            continue
        bldg(cx - 18, cy + 10, 13, 9, a0, (232, 224, 206, 255))            # house (whitewashed)
        if kind == "farm":
            bldg(cx + 20, cy + 6, 17, 10, a0 + 0.1, (150, 62, 44, 255))    # bank barn
            bldg(cx + 2, cy + 34, 7, 5, a0, (170, 120, 90, 255), False)    # outbuilding
            for i in range(3):                                            # orchard rows
                for j in range(4):
                    x = cx - 44 + j * 13 + (i % 2) * 6
                    y = cy - 34 + i * 12
                    d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(96, 112, 60, 230), outline=(56, 64, 34, 230))
        else:
            bldg(cx + 14, cy + 18, 7, 5, a0, (170, 120, 90, 255), False)

    # buildings: hamlets / farms (wasteland) and Winchester (city)
    for q, r in by.get("wasteland", []):
        if (q, r) in site_hex:
            continue
        cx, cy = hex_px(q, r, ox, oy)
        for i in range(3):
            bldg(cx + rng.uniform(-40, 40), cy + rng.uniform(-40, 30), rng.uniform(9, 13), rng.uniform(6, 9),
                 rng.uniform(-0.4, 0.4), [(232, 224, 206, 255), (150, 62, 44, 255), (170, 120, 90, 255)][i])
    for q, r in by.get("city", []):
        cx, cy = hex_px(q, r, ox, oy)
        for gx_ in (-28, 28):
            for gy_ in (-30, 26):
                x, y = cx + gx_ + rng.uniform(-4, 4), cy + gy_ + rng.uniform(-4, 4)
                d.rectangle([x - 24, y - 22, x + 24, y + 22], fill=(178, 120, 96, 235), outline=(100, 62, 48, 255), width=2)
                d.line([(x - 24, y), (x + 24, y)], fill=(120, 76, 58, 200), width=2)

    # stone wall on the fenced hexsides: a row of field stones (Antietam marks fences with dots)
    # v3.2: heavier, two courses of stones on a dark footing, with a cast shadow
    for (q, r), es in fences.items():
        cx, cy = hex_px(q, r, ox, oy)
        for e in es:
            (x0, y0), (x1, y1) = edge_pts(cx, cy, e)
            d.line([(x0 + 4, y0 + 6), (x1 + 4, y1 + 6)], fill=(30, 26, 20, 120), width=16)
            d.line([(x0, y0), (x1, y1)], fill=(54, 50, 44, 255), width=13)
            n = 14
            for course, off in ((0, -2.5), (1, 2.5)):
                for i in range(n + 1):
                    t = (i + 0.5 * course) / n
                    if t > 1:
                        continue
                    x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + off
                    rr = rng.uniform(4.5, 6.5)
                    tone = int(rng.integers(140, 178))
                    d.ellipse([x - rr, y - rr * 0.75, x + rr, y + rr * 0.75], fill=(tone, tone - 4, tone - 14, 255),
                              outline=(36, 34, 30, 255), width=2)

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
    # v3.2: median cut drops small, saturated details (the barns came out grey-green), so the palette
    # is median cut for NCOL - len(KEEP) colours plus the drawing colours of the small features.
    KEEP = [(150, 62, 44), (232, 224, 206), (226, 218, 200), (226, 220, 204), (170, 120, 90), (46, 30, 22),
            (96, 112, 60), (140, 180, 205), (70, 105, 140), (222, 198, 150), (54, 50, 44), (160, 156, 146)]
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
