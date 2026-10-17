"""v0.4 full 62x54 (game-native grid, v0.4.2) painted basemap (March 1862, First Kernstown + Winchester).
Stage A (cached): painting-quilted broom ground + DEM hillshade  -> painted_sections/v04_ground_cache.py
Stage B (this file): field parcels that flow across hexes, early-spring bare woods, thin muddy creeks,
graded roads, dry-stone wall, wider 1862 Winchester, landmarks (compose_painted_map sprites), W&P railroad.
Writes data/basemap_painted_full.png (+_labeled), data/layers/painted_buildings.json (+ _masks.npz),
data/layers/painted_lines.json (the exact road/Pike/rail/creek lines painted, for game-layer tracing), previews/v04_*.jpg
v0.4.2: hex grid = game convention (scripts/hex_grid.py); buildings are never pasted over roads, the Pike, the
railroad, town streets or water (nudged to the nearest clear spot; checked by tools/validate/check_buildings.py)."""
import os, sys, math, json, subprocess
sys.path.insert(0, 'scripts')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from hex_grid import KERNSTOWN as G
import compose_painted_map as CPM
Image.MAX_IMAGE_PIXELS = None
P = 0.55; BW, BH = 6635, 6723; W, H = BW, BH
R = G.size_m * P; APO = R * math.sqrt(3) / 2
CACHE = os.environ.get('V04_CACHE', '/workspace/cache')
if not os.path.exists(f'{CACHE}/ground.npy'):
    subprocess.check_call([sys.executable, 'painted_sections/v04_ground_cache.py'])
FE = CPM.FEAT
rng = np.random.default_rng(1862)

def hexc(c, r):
    x, y = G.hex_to_xy_m(c, r); return x * P, BH - y * P
def ll(lon, lat):
    x, y = G.lonlat_to_xy_m(lon, lat); return x * P, BH - y * P
def fnoise(shape, scale, seed):
    g = np.random.default_rng(seed).random((shape[0] // scale + 3, shape[1] // scale + 3)).astype(np.float32)
    z = ndi.zoom(g, scale, order=3)[:shape[0], :shape[1]]
    return (z - z.mean()) / (z.std() + 1e-6)
def fbm(shape, seed):
    return (fnoise(shape, 96, seed) + 0.5 * fnoise(shape, 32, seed + 1) + 0.25 * fnoise(shape, 10, seed + 2)) / 1.75
def offset_line(pts, off):
    q = []
    for i in range(len(pts)):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) + 1e-9
        q.append((pts[i][0] - (b[1] - a[1]) / L * off, pts[i][1] + (b[0] - a[0]) / L * off))
    return q
def chaikin(pts, it=2):
    for _ in range(it):
        o = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            o += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        o.append(pts[-1]); pts = o
    return pts
def resample(pts, step=2.0, smooth=0):
    a = np.array(pts, np.float64); s = np.r_[0, np.cumsum(np.hypot(*np.diff(a, axis=0).T))]
    if s[-1] < step: return [tuple(p) for p in a]
    t = np.arange(0, s[-1], step); a = np.c_[np.interp(t, s, a[:, 0]), np.interp(t, s, a[:, 1])]
    if smooth > 1 and len(a) > smooth:
        k = smooth; pad = np.r_[np.repeat(a[:1], k // 2, 0), a, np.repeat(a[-1:], k // 2, 0)]
        a = np.c_[np.convolve(pad[:, 0], np.ones(k) / k, 'valid'), np.convolve(pad[:, 1], np.ones(k) / k, 'valid')][:len(t)]
    return [tuple(p) for p in a]

shape = (H, W)
img = np.load(f'{CACHE}/ground.npy').astype(np.float32)
shade = np.load(f'{CACHE}/shade.npy').astype(np.float32)
forest = np.load(f'{CACHE}/forest.npy').astype(np.float32)
# calm the broom quilt: pull very dark specks (painting's woods/shadow bits) toward local mean -> no stray dark blobs
lum = img.mean(2); locm = ndi.uniform_filter(lum, 41)
dark = np.clip((locm - lum - 18) / 30, 0, 1)[..., None]
img = img * (1 - 0.6 * dark) + img * (locm / np.maximum(lum, 1))[..., None] * 0.6 * dark
img = img * 0.9 + np.array([162, 136, 98], np.float32) * 0.1     # warm March broom-sedge tan

# ---------- zones ----------
C_LL = (-78.16444, 39.18389)            # Frederick County Courthouse
wcx, wcy = ll(*C_LL)
yy, xx = np.ogrid[0:H, 0:W]
town_rx, town_ry = 560.0, 520.0          # Winchester built-up ellipse (px), wider E-W than v0.3
town_d = np.sqrt(((xx - wcx) / town_rx) ** 2 + ((yy - wcy) / town_ry) ** 2).astype(np.float32)
kx, ky = ll(-78.1978, 39.1425)
kern_d = (np.sqrt((xx - kx) ** 2 + (yy - ky) ** 2) / 170.0).astype(np.float32)
town_m = np.clip((1.05 - np.minimum(town_d, kern_d)) / 0.2, 0, 1)
woods_m = np.clip((forest + 0.25 * fbm(shape, 11) - 0.30) / 0.16, 0, 1)   # feathered, noisy edge
lot_density = np.clip(0.62 + 0.45 * fnoise(shape, 220, 13), 0.25, 1.0)    # open woodland <-> dense hardwood

# ---------- 1. field parcels (Voronoi in a slowly rotating, anisotropic frame) ----------
S2 = 2; h2, w2 = H // S2 + 1, W // S2 + 1
theta = (0.30 + 0.45 * fnoise((h2, w2), 700, 51)).astype(np.float32)     # local field orientation (rad)
gy2, gx2 = np.mgrid[0:h2, 0:w2].astype(np.float32)
# farm districts: each has one field orientation; seeds on a rotated, slightly jittered lattice -> rectangular-ish fields
nd = 70
dc = np.c_[rng.uniform(0, w2, nd), rng.uniform(0, h2, nd)]; dth = rng.uniform(-0.5, 0.5, nd) + 0.25
dkd = cKDTree(dc); seeds = []; th_l = []
for di in range(nd):
    c_, s_ = math.cos(dth[di]), math.sin(dth[di]); a_ = rng.uniform(95, 130); b_ = rng.uniform(55, 75)   # field length / width (half-res px)
    for u_ in np.arange(-1500, 1500, a_):
        for v_ in np.arange(-1500, 1500, b_):
            uu = u_ + rng.uniform(-0.22, 0.22) * a_; vv = v_ + rng.uniform(-0.15, 0.15) * b_
            x_, y_ = dc[di, 0] + uu * c_ - vv * s_, dc[di, 1] + uu * s_ + vv * c_
            if -60 < x_ < w2 + 60 and -60 < y_ < h2 + 60 and dkd.query((x_, y_))[1] == di:
                seeds.append((x_, y_)); th_l.append(dth[di])
seeds = np.array(seeds, np.float32); th_s = np.array(th_l, np.float32)
# anisotropic Voronoi: each seed measures distance in its own rotated frame (long axis along th_s)
tree = cKDTree(seeds); cs_, sn_ = np.cos(th_s), np.sin(th_s)
pts_all = np.c_[gx2.ravel(), gy2.ravel()]; label = np.empty(len(pts_all), np.int32)
for i0 in range(0, len(pts_all), 2_000_000):
    pp = pts_all[i0:i0 + 2_000_000]; _, nn = tree.query(pp, k=8, workers=-1)
    dx = pp[:, 0, None] - seeds[nn, 0]; dy = pp[:, 1, None] - seeds[nn, 1]
    du = dx * cs_[nn] + dy * sn_[nn]; dv = (-dx * sn_[nn] + dy * cs_[nn]) * 1.75
    label[i0:i0 + 2_000_000] = nn[np.arange(len(pp)), np.argmin(du * du + dv * dv, 1)]
label = label.reshape(h2, w2); del pts_all
NL = len(seeds)
# per-cell openness
open2 = ((1 - woods_m[::S2, ::S2]) * (1 - town_m[::S2, ::S2]))[:h2, :w2]
cnt = np.bincount(label.ravel(), minlength=NL).astype(np.float32)
openf = np.bincount(label.ravel(), weights=open2.ravel(), minlength=NL) / np.maximum(cnt, 1)
KINDS = ['broom', 'plowed', 'pasture', 'stubble', 'fallow']
kind = np.zeros(NL, np.int32)
farm_n = fnoise((h2, w2), 300, 57)[np.clip(seeds[:, 1].astype(int), 0, h2 - 1), np.clip(seeds[:, 0].astype(int), 0, w2 - 1)]
seed_full = seeds * S2
sw_zone = (seed_full[:, 0] < kx + 250) | (seed_full[:, 1] > ky - 150)   # south & west of Kernstown (y down = south)
for i in range(NL):
    if openf[i] < 0.85: continue
    p_field = (0.29 if sw_zone[i] else 0.19) * float(np.clip(1 + 0.6 * farm_n[i], 0.3, 1.7))
    if rng.random() < p_field:
        pw = [0.48, 0.2, 0.16, 0.16] if sw_zone[i] else [0.26, 0.28, 0.24, 0.22]
        kind[i] = 1 + rng.choice(4, p=pw)
cell_ang = th_s + np.where(rng.random(NL) < 0.3, math.pi / 2, 0) + rng.normal(0, 0.03, NL)
cell_tone = rng.uniform(0.94, 1.05, NL).astype(np.float32)
lab_full = np.repeat(np.repeat(label, S2, 0), S2, 1)[:H, :W]
k_full = kind[lab_full]
openfull = (1 - woods_m) * (1 - town_m)
fmask = {}
for ki in range(1, 5):
    m = (k_full == ki).astype(np.float32)
    fmask[ki] = ndi.gaussian_filter(m, 1.6) * openfull
# boundary distance (for headlands)
bnd2 = (label != np.roll(label, 1, 0)) | (label != np.roll(label, 1, 1))
dist_b = ndi.distance_transform_edt(~bnd2) * S2
dist_b = np.repeat(np.repeat(dist_b, S2, 0), S2, 1)[:H, :W].astype(np.float32)
detail = (img / np.maximum(img.mean(2, keepdims=True), 1)) * 0.5 + 0.5      # keep painterly grain
lumn = (img.mean(2) / 140.0)[..., None]
grain = fnoise(shape, 3, 61)[..., None]
TINT = {2: (124, 120, 86), 3: (166, 148, 108), 4: (138, 122, 102)}         # olive pasture, gold stubble, gray-brown fallow
for ki, tint in TINT.items():
    t = np.array(tint, np.float32) * (0.75 + 0.25 * lumn) * detail * cell_tone[lab_full][..., None]
    if ki == 3:  # faint stubble rows
        ang = cell_ang[lab_full]
        st = np.sin((xx * np.cos(ang) + yy * np.sin(ang)) * (2 * math.pi / 4.0))
        t *= (1 + 0.035 * st)[..., None]
    a = (fmask[ki] * 0.66)[..., None]
    img = img * (1 - a) + t * a
# plowed: dark-brown furrows following each field's own direction, unplowed headland at the edge
ang = cell_ang[lab_full]
u = xx * np.cos(ang) + yy * np.sin(ang) + 2.5 * fnoise(shape, 40, 71)
fur = 0.5 + 0.5 * np.sin(u * (2 * math.pi / 6.0))
pl = np.array([98, 76, 55], np.float32) * (1 - fur[..., None]) + np.array([122, 98, 74], np.float32) * fur[..., None]
pl = pl * (0.85 + 0.15 * detail) * (1 + 0.04 * grain) * cell_tone[lab_full][..., None]
head = np.clip((dist_b - 4) / 5, 0, 1)
a = (fmask[1] * 0.8 * (0.25 + 0.75 * head))[..., None]
img = img * (1 - a) + pl * a
del u, fur, pl, ang, detail
# gentle per-parcel tonal drift on the plain broom fields too (reads as separate farms, not hex stamps)
drift = (cell_tone[lab_full] - 1.0) * 0.8
img *= (1 + drift * (k_full == 0) * openfull)[..., None]

# ---------- 2. woods floor (leaf litter) ----------
wl = (woods_m * (0.35 + 0.35 * lot_density))[..., None]
img = img * (1 - wl) + (img * np.array([0.85, 0.80, 0.75])) * wl
# hillshade
img *= np.clip(shade, 0.8, 1.15)[..., None]
canvas = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
del img, lumn, grain, drift

# ---------- 3. fences & hedgerows along parcel boundaries ----------
lab_u = np.roll(label, 1, 0); lab_l = np.roll(label, 1, 1)
def pair_rand(a, b, salt):
    k = np.minimum(a, b).astype(np.float64) * 7919 + np.maximum(a, b) + salt
    return np.modf(np.sin(k * 12.9898) * 43758.5453)[0] % 1.0
fence2 = np.zeros((h2, w2), bool); hedge2 = np.zeros((h2, w2), bool)
for nb in (lab_u, lab_l):
    e = label != nb
    fld = (kind[label] > 0) | (kind[nb] > 0)
    r_ = pair_rand(label, nb, 0)
    fence2 |= e & ((fld & (r_ < 0.62)) | (~fld & (r_ < 0.14)))
    hedge2 |= e & fld & (r_ >= 0.62) & (r_ < 0.80)
def up(m):
    return np.repeat(np.repeat(m, S2, 0), S2, 1)[:H, :W]
okm = openfull > 0.6
fence = up(fence2) & okm; hedge = ndi.binary_dilation(up(hedge2), iterations=2) & okm
fl = np.zeros((H, W, 4), np.uint8)
post = fnoise(shape, 2, 81) > 0.7
fl[fence] = (96, 78, 58, 80); fl[fence & post] = (72, 56, 40, 130)
brush = hedge & (fnoise(shape, 2, 83) > -0.2)
bud = fnoise(shape, 5, 85) > 0.9
fl[brush] = (104, 90, 70, 130); fl[brush & bud] = (116, 116, 84, 120)
canvas = Image.alpha_composite(canvas, Image.fromarray(fl).filter(ImageFilter.GaussianBlur(0.6)))
del fl, post, brush, bud

# ---------- 4. creeks: thin, muddy, meandering ----------
def creek_path(wps, seed, amp=2.2):
    pts = resample([ll(*c) for c in wps], 3.0, smooth=15)
    pts = chaikin(pts, 1); pts = resample(pts, 2.0)
    out = []; dist = 0.0; ph = seed * 0.37
    for i in range(len(pts)):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) + 1e-9; nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
        dist += 2.0
        off = amp * math.sin(dist / 46 * 2 * math.pi + ph) + 0.5 * amp * math.sin(dist / 17 * 2 * math.pi + 1.7 * ph)
        out.append((pts[i][0] + nx * off, pts[i][1] + ny * off))
    return out
WIN_BB = (-78.172, 39.173, -78.155, 39.193)
creeks = []; CREEK_NAMES = []
for name, ww, seed in (('opequon_creek', 4, 0), ('hoge_run', 3, 11), ('abrams_creek', 3, 5), ('buffalo_lick', 2, 7), ('town_run', 2, 3)):
    if name not in FE['rivers']: continue
    wps = FE['rivers'][name]['waypoints']; runs = [[]]
    for lon, lat in wps:
        if name == 'abrams_creek' and WIN_BB[0] < lon < WIN_BB[2] and WIN_BB[1] < lat < WIN_BB[3]:
            if runs[-1]: runs.append([])
            continue
        runs[-1].append((lon, lat))
    for rr_ in runs:
        if len(rr_) >= 2: creeks.append((creek_path(rr_, seed), ww)); CREEK_NAMES.append(name)
cl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(cl)
for pts, ww in creeks:   # dead grass fringe, muddy bank, water
    cd.line(pts, fill=(160, 142, 100, 70), width=ww + 16, joint='curve')
for pts, ww in creeks:
    cd.line(pts, fill=(104, 84, 62, 210), width=ww + 5, joint='curve')
for pts, ww in creeks:
    cd.line(pts, fill=(84, 92, 90, 255), width=ww, joint='curve')
    cd.line(offset_line(pts, -ww * 0.25), fill=(118, 126, 120, 120), width=1)
cl = cl.filter(ImageFilter.GaussianBlur(0.7))
canvas = Image.alpha_composite(canvas, cl); del cl
water = np.zeros(shape, bool)
wim = Image.new('L', (W, H), 0); wd_ = ImageDraw.Draw(wim)
for pts, ww in creeks: wd_.line(pts, fill=255, width=ww + 4)
water = np.asarray(wim) > 0; del wim

# ---------- 5. roads ----------
rl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(rl)
road_pts = {}
for k, v in FE['roads'].items():
    road_pts[k] = resample([ll(*p) for p in v['waypoints']], 3.0, smooth=9)
for k, pts in road_pts.items():
    if k in ('apple_valley_road', 'stone_lane'):     # farm lanes: faint tracks
        rd.line(pts, fill=(118, 96, 70, 95), width=6, joint='curve')
        for off in (-1.6, 1.6): rd.line(offset_line(pts, off), fill=(96, 76, 54, 120), width=1)
for k, pts in road_pts.items():
    if FE['roads'][k].get('kind') != 'pike' and k not in ('apple_valley_road', 'stone_lane'):   # dirt roads
        rd.line(pts, fill=(88, 68, 48, 120), width=12, joint='curve')
        rd.line(pts, fill=(128, 100, 72, 255), width=8, joint='curve')
        for off in (-2.0, 2.0): rd.line(offset_line(pts, off), fill=(100, 78, 54, 200), width=1)
for k, pts in road_pts.items():
    if FE['roads'][k].get('kind') == 'pike':           # Valley Pike: macadam, crowned
        rd.line(pts, fill=(96, 82, 62, 150), width=19, joint='curve')
        rd.line(pts, fill=(156, 144, 120, 255), width=14, joint='curve')
        rd.line(pts, fill=(168, 158, 136, 255), width=7, joint='curve')
        rd.line(pts, fill=(172, 164, 146, 170), width=3, joint='curve')
rl = rl.filter(ImageFilter.GaussianBlur(0.8))
an = np.asarray(rl, np.float32).copy(); an[..., :3] = np.clip(an[..., :3] + fnoise(shape, 3, 9)[..., None] * 7, 0, 255)
canvas = Image.alpha_composite(canvas, Image.fromarray(an.astype(np.uint8))); del an, rl
roadm = np.zeros(shape, bool)
rim = Image.new('L', (W, H), 0); rdm = ImageDraw.Draw(rim)
for k, pts in road_pts.items(): rdm.line(pts, fill=255, width=16)
roadm = np.asarray(rim) > 0; del rim

# ---------- 6. W&P railroad (1862: Winchester depot northward only; the line south of town is post-war) ----------
RR_MIN_LAT = 39.1885
rr_ll = [p for p in FE['railroads']['winchester_and_potomac']['waypoints'] if p[1] >= RR_MIN_LAT]
rr = resample([ll(*p) for p in rr_ll], 2.0, smooth=11)
tl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); td = ImageDraw.Draw(tl)
td.line(rr, fill=(118, 108, 94, 220), width=8, joint='curve')
for i in range(0, len(rr) - 1, 3):
    (x0, y0), (x1, y1) = rr[i], rr[i + 1]; L = math.hypot(x1 - x0, y1 - y0) + 1e-9; nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    td.line([(x0 - nx * 4.5, y0 - ny * 4.5), (x0 + nx * 4.5, y0 + ny * 4.5)], fill=(72, 58, 44, 230), width=2)
for off in (-1.8, 1.8): td.line(offset_line(rr, off), fill=(62, 60, 58, 240), width=1)
canvas = Image.alpha_composite(canvas, tl.filter(ImageFilter.GaussianBlur(0.4))); del tl

# ---------- 7. dry-stone wall on the Sandy Ridge crest ----------
sw = json.load(open('data/features/stone_wall_hexsides.json'))
wh = sorted(tuple(h) for h in sw['confederate_hexes'])
ax_ = np.array([hexc(c, r)[0] for c, r in wh]); ay_ = np.array([hexc(c, r)[1] - 0.38 * APO for c, r in wh])
cf = np.polyfit(ax_, ay_, 2)
x0w, x1w = ax_.min() - 0.8 * R, ax_.max() + 0.8 * R
xs_ = np.arange(x0w, x1w, 1.0)
wob = fnoise((1, len(xs_) + 600), 180, 3)[0][:len(xs_)] * 5.0 + fnoise((1, len(xs_) + 100), 40, 4)[0][:len(xs_)] * 1.2
wall = resample([(x, np.polyval(cf, x) + w) for x, w in zip(xs_, wob)], 1.0, smooth=25)
wr = np.random.default_rng(23)
tr = Image.new('RGBA', (W, H), (0, 0, 0, 0)); trd = ImageDraw.Draw(tr)
trd.line(wall, fill=(132, 110, 82, 150), width=22, joint='curve')
trd.line(wall, fill=(122, 100, 74, 120), width=12, joint='curve')
tr = tr.filter(ImageFilter.GaussianBlur(3))
ta = np.asarray(tr, np.float32).copy(); ta[..., 3] *= np.clip(0.75 + 0.4 * fnoise(shape, 5, 91), 0, 1)
canvas = Image.alpha_composite(canvas, Image.fromarray(ta.astype(np.uint8))); del ta, tr
sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).line([(x + 1.5, y + 2.5) for x, y in wall[::2]], fill=(40, 32, 24, 130), width=6)
canvas = Image.alpha_composite(canvas, sh.filter(ImageFilter.GaussianBlur(1.6))); del sh
lw = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lw)
def stone(cx, cy, rx, ry, rot, base):
    n = int(wr.integers(5, 8)); pts = []
    for t in range(n):
        a_ = 2 * math.pi * t / n + wr.uniform(-0.3, 0.3); rf = wr.uniform(0.75, 1.1)
        dx, dy = math.cos(a_) * rx * rf, math.sin(a_) * ry * rf
        pts.append((cx + dx * math.cos(rot) - dy * math.sin(rot), cy + dx * math.sin(rot) + dy * math.cos(rot)))
    ld.polygon(pts, fill=tuple(int(v) for v in base) + (255,))
    m = len(pts)
    ld.line([pts[(m * 5) // 8 % m], pts[(m * 6) // 8 % m]], fill=tuple(int(min(255, v * 1.15)) for v in base) + (200,), width=1)
    ld.line([pts[m // 8], pts[(m * 3) // 8]], fill=tuple(int(v * 0.62) for v in base) + (220,), width=1)
th = 5.0; i = 0
GLASS = ll(-78.2248, 39.1470)   # farmyard gap in the wall
while i < len(wall) - 2:
    x, y = wall[i]; (xa, ya), (xb, yb) = wall[max(i - 1, 0)], wall[i + 1]
    L = math.hypot(xb - xa, yb - ya) + 1e-9; ux, uy = (xb - xa) / L, (yb - ya) / L; nx, ny = -uy, ux; rot = math.atan2(uy, ux)
    sl = wr.uniform(2.6, 4.2)
    if not (0 <= int(y) < H and water[int(y), int(x)]) and math.hypot(x - GLASS[0], y - GLASS[1]) > 42:
        for off in (th * 0.22, -th * 0.2):
            g = wr.uniform(0.82, 1.08)
            tint = np.array([wr.choice([142, 136, 148, 130]), wr.choice([134, 130, 138]), wr.choice([120, 124, 114])])
            stone(x + nx * off + wr.normal(0, 0.4), y + ny * off + wr.normal(0, 0.4), sl * 0.55, th * wr.uniform(0.24, 0.32), rot + wr.normal(0, 0.25), tint * g)
        if wr.random() < 0.2: stone(x, y - 0.8, sl * 0.4, th * 0.2, rot, np.array([156, 152, 142]) * wr.uniform(0.9, 1.04))
    i += max(2, int(sl))
canvas = Image.alpha_composite(canvas, lw.filter(ImageFilter.GaussianBlur(0.3))); del lw
_wi = int(len(wall) * 0.58); FE.setdefault('_runtime', {})['stone_wall_label_xy'] = (wall[_wi][0] + 30, wall[_wi][1] + 40)   # just south of the wall line
WALL_BOX = (int(x0w), int(min(y for _, y in wall)), int(x1w), int(max(y for _, y in wall)))

# ---------- 8. bare early-spring trees (woodlots, hedgerows, creeks, yards) ----------
def make_tree(r, seed, bud):
    t_ = np.random.default_rng(seed); s = int(r * 2 + 8); c = s / 2
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((c - r * 0.95, c - r * 0.9, c + r * 0.95, c + r * 0.9), fill=(130, 110, 86, 95))
    if bud: d.ellipse((c - r * 0.8, c - r * 0.75, c + r * 0.8, c + r * 0.75), fill=(124, 128, 80, 70))
    for k in range(int(t_.integers(6, 10))):
        a_ = 2 * math.pi * k / 8 + t_.uniform(-0.4, 0.4); L = r * t_.uniform(0.6, 0.95)
        ex, ey = c + math.cos(a_) * L, c + math.sin(a_) * L * 0.9
        d.line([(c, c), (ex, ey)], fill=(92, 76, 60, 190), width=1)
        for f in (0.55, 0.8):
            b = a_ + t_.choice([-1, 1]) * t_.uniform(0.4, 0.8); mx, my = c + math.cos(a_) * L * f, c + math.sin(a_) * L * f * 0.9
            d.line([(mx, my), (mx + math.cos(b) * L * 0.35, my + math.sin(b) * L * 0.32)], fill=(106, 90, 72, 140), width=1)
    d.ellipse((c - 0.9, c - 0.9, c + 0.9, c + 0.9), fill=(80, 66, 52, 220))
    hl = Image.new('RGBA', (s, s), (0, 0, 0, 0)); ImageDraw.Draw(hl).ellipse((c - r * 0.8, c - r * 0.85, c + r * 0.1, c - r * 0.0), fill=(170, 156, 132, 38))
    return Image.alpha_composite(im.filter(ImageFilter.GaussianBlur(0.35)), hl.filter(ImageFilter.GaussianBlur(2)))
def make_shadow(r):
    s = int(r * 2 + 8); im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((s / 2 - r * 0.85, s / 2 - r * 0.7, s / 2 + r * 0.85, s / 2 + r * 0.7), fill=(50, 38, 26, 62))
    return im.filter(ImageFilter.GaussianBlur(2.2))
TREES = {}
for r in (5, 6, 7, 8, 9, 10, 11):
    TREES[r] = ([make_tree(r, r * 100 + k, False) for k in range(6)], [make_tree(r, r * 1000 + k, True) for k in range(4)], make_shadow(r))
tl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); shl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
def put_tree(x, y, r):
    lst, bud, shd = TREES[int(np.clip(r, 5, 11))]
    s = lst[int(wr.integers(len(lst)))] if wr.random() > 0.3 else bud[int(wr.integers(len(bud)))]
    shl.alpha_composite(shd, (int(x - shd.width / 2 + 3), int(y - shd.height / 2 + 4)))
    tl.alpha_composite(s, (int(x - s.width / 2), int(y - s.height / 2)))
ntree = 0
step = 8
for gy in range(4, H - 4, step):
    for gx in range(4, W - 4, step):
        x = gx + wr.uniform(-3.5, 3.5); y = gy + wr.uniform(-3.5, 3.5)
        xi, yi = int(x), int(y)
        wm = woods_m[yi, xi]
        if wm < 0.03 or town_m[yi, xi] > 0.5 or roadm[yi, xi] or water[yi, xi]: continue
        dens = lot_density[yi, xi]
        p = (wm ** 1.3) * (0.2 + 0.6 * dens)
        if wr.random() < p:
            put_tree(x, y, wr.uniform(6, 8) + 3 * dens * wm); ntree += 1
# riparian bare trees along creeks (overhanging banks)
for pts, ww in creeks:
    for j in range(0, len(pts) - 1, 7):
        if wr.random() < 0.45: continue
        (x0, y0), (x1, y1) = pts[j], pts[j + 1]; L = math.hypot(x1 - x0, y1 - y0) + 1e-9; nx, ny = -(y1 - y0) / L, (x1 - x0) / L
        o = wr.choice([-1, 1]) * wr.uniform(ww / 2 + 2, ww / 2 + 7)
        x, y = x0 + nx * o, y0 + ny * o
        if 0 <= int(y) < H and 0 <= int(x) < W and town_m[int(y), int(x)] < 0.5 and not roadm[int(y), int(x)]:
            put_tree(x, y, wr.uniform(5, 8)); ntree += 1
# hedgerow trees + lone field trees
hy_, hx_ = np.where(hedge[::6, ::6])
for y, x in zip(hy_ * 6, hx_ * 6):
    if wr.random() < 0.08 and not roadm[y, x]: put_tree(x, y, wr.uniform(5, 7)); ntree += 1
canvas = Image.alpha_composite(canvas, shl); canvas = Image.alpha_composite(canvas, tl); del tl, shl
print('trees', ntree)

# ---------- 9. buildings: landmarks (logged) + wider 1862 Winchester ----------
lib = CPM.build_sprite_library()
# ---------- 9a. no-build mask (v0.4.2): roads, the Pike, the railroad, water; town streets added in place_winchester ----------
NOBUILD_DILATE = 2
LINES = {'px_per_m': P, 'H': BH, 'W': BW, 'dilate_px': NOBUILD_DILATE, 'roads': {}, 'creeks': [], 'rail': None, 'streets': []}
def _lw(k):
    return 20 if FE['roads'][k].get('kind') == 'pike' else (7 if k in ('apple_valley_road', 'stone_lane') else 13)
fim = Image.new('L', (W, H), 0); fd = ImageDraw.Draw(fim)
for k, pts in road_pts.items():
    fd.line(pts, fill=255, width=_lw(k), joint='curve')
    LINES['roads'][k] = {'kind': FE['roads'][k].get('kind', 'road'), 'width_px': _lw(k), 'pts': [[round(x, 1), round(y, 1)] for x, y in pts]}
fd.line(rr, fill=255, width=11, joint='curve'); LINES['rail'] = {'width_px': 11, 'pts': [[round(x, 1), round(y, 1)] for x, y in rr]}
for (pts, ww), nm in zip(creeks, CREEK_NAMES):
    fd.line(pts, fill=255, width=ww + 6, joint='curve')
    LINES['creeks'].append({'name': nm, 'width_px': ww + 6, 'pts': [[round(x, 1), round(y, 1)] for x, y in pts]})
FORBID = ndi.binary_dilation(np.asarray(fim) > 0, iterations=NOBUILD_DILATE); del fim
NUDGED, SKIPPED, FOOT, FOOT_MASKS = [], [], [], []
CHECK = {'on': True}
EXEMPT = {id(lib['bridge'])} if lib.get('bridge') is not None else set()     # a bridge belongs on the water/road
def _box(sprite, x, y, anchor):
    sw_, sh_ = sprite.size
    if anchor == 'foot': return int(x - sw_ / 2), int(y - sh_ + 4)
    if anchor == 'center': return int(x - sw_ / 2), int(y - sh_ / 2)
    return int(x), int(y)
def _hits(am, px, py):
    h_, w_ = am.shape; x0, y0, x1, y1 = max(px, 0), max(py, 0), min(px + w_, W), min(py + h_, H)
    if x1 <= x0 or y1 <= y0: return False
    return bool((FORBID[y0:y1, x0:x1] & am[y0 - py:y1 - py, x0 - px:x1 - px]).any())
BUILDINGS = []
_orig_paste = CPM.paste_sprite
def logged_paste(base, sprite, x, y, anchor='foot'):
    if CHECK['on'] and id(sprite) not in EXEMPT:
        am = np.asarray(sprite.convert('RGBA'))[..., 3] > 64
        px, py = _box(sprite, x, y, anchor)
        if _hits(am, px, py):
            found = None
            for rad in range(3, 91, 3):
                for k_ in range(24):
                    a_ = 2 * math.pi * k_ / 24; dx, dy = round(rad * math.cos(a_)), round(rad * math.sin(a_))
                    if not _hits(am, px + dx, py + dy): found = (dx, dy); break
                if found: break
            if found is None:
                SKIPPED.append((float(x), float(y))); return None
            NUDGED.append(math.hypot(*found)); x, y = x + found[0], y + found[1]; px, py = px + found[0], py + found[1]
        FOOT.append([px, py, am.shape[1], am.shape[0]]); FOOT_MASKS.append(np.packbits(am, axis=1))
    BUILDINGS.append((float(x), float(y), int(sprite.size[0] * sprite.size[1])))
    return _orig_paste(base, sprite, x, y, anchor)
CPM.paste_sprite = logged_paste
CHECK['on'] = False; canvas = CPM.place_fords(canvas, lib); del BUILDINGS[:]; CHECK['on'] = True   # fords sit on the water by design
canvas = CPM.place_landmarks(canvas, lib)

def place_winchester(base):
    loud = -78.1645
    NS = {'Stewart': -78.1712, 'Washington': -78.1692, 'Braddock': -78.1672, 'Loudoun': loud,
          'Cameron': -78.1624, 'Kent': -78.1604, 'East': -78.1584, 'Liberty': -78.1564}
    EW = {'Fairfax': 39.1905, 'Peyton': 39.1888, 'Piccadilly': 39.1870, 'Boscawen': 39.1852,
          'Water': 39.1834, 'Amherst': 39.1816, 'Cork': 39.1796, 'Germain': 39.1776, 'South': 39.1760}
    ns_span = {'Stewart': (39.1834, 39.1870), 'Washington': (39.1796, 39.1888), 'Braddock': (39.1776, 39.1905),
               'Loudoun': (39.1745, 39.1925), 'Cameron': (39.1776, 39.1905), 'Kent': (39.1796, 39.1888),
               'East': (39.1816, 39.1870), 'Liberty': (39.1834, 39.1852)}
    ew_span = {'Fairfax': (-78.1672, -78.1624), 'Peyton': (-78.1692, -78.1604), 'Piccadilly': (-78.1728, -78.1584),
               'Boscawen': (-78.1740, -78.1560), 'Water': (-78.1735, -78.1565), 'Amherst': (-78.1728, -78.1584),
               'Cork': (-78.1692, -78.1604), 'Germain': (-78.1672, -78.1624), 'South': (-78.1660, -78.1630)}
    sl = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(sl)
    segs = [((NS[n], a), (NS[n], b), n == 'Loudoun') for n, (a, b) in ns_span.items()] + \
           [((a, EW[n]), (b, EW[n]), False) for n, (a, b) in ew_span.items()]
    for (lo0, la0), (lo1, la1), main in segs:
        p0, p1 = ll(lo0, la0), ll(lo1, la1); wd = 13 if main else 8
        d.line([p0, p1], fill=(100, 82, 60, 90), width=wd + 3)
        d.line([p0, p1], fill=(150, 138, 114, 255) if main else (130, 106, 80, 225), width=wd)
    stm = Image.new('L', base.size, 0); smd = ImageDraw.Draw(stm)
    for (lo0, la0), (lo1, la1), main in segs:
        p0, p1 = ll(lo0, la0), ll(lo1, la1); wd = (13 if main else 8) + 2
        smd.line([p0, p1], fill=255, width=wd); LINES['streets'].append({'width_px': wd, 'pts': [[round(p0[0], 1), round(p0[1], 1)], [round(p1[0], 1), round(p1[1], 1)]]})
    np.logical_or(FORBID, ndi.binary_dilation(np.asarray(stm) > 0, iterations=NOBUILD_DILATE), out=FORBID); del stm
    canvas_ = Image.alpha_composite(base, sl.filter(ImageFilter.GaussianBlur(0.9)))
    tr = np.random.default_rng(41)
    rows_ = lib['townhouse_rows'] + lib['shop_rows']; bricks = lib['brick_houses']; houses = lib['houses']; outs = lib['outbuildings']
    def scl(s_, f):
        return s_.resize((max(6, int(s_.size[0] * f)), max(6, int(s_.size[1] * f))), Image.Resampling.LANCZOS)
    SC = {id(s_): s_ for s_ in []}
    small_rows = [scl(s_, 0.40) for s_ in rows_]; small_bricks = [scl(s_, 0.48) for s_ in bricks]
    small_houses = [scl(s_, 0.44) for s_ in houses]; small_outs = [scl(s_, 0.42) for s_ in outs]
    yard = Image.new('RGBA', base.size, (0, 0, 0, 0)); yd = ImageDraw.Draw(yard)
    placed = []
    def put(spr, lon, lat, dx=0, dy=0):
        x, y = ll(lon, lat); x += dx; y += dy
        for px, py in placed:
            if abs(px - x) < spr.size[0] * 0.75 and abs(py - y) < spr.size[1] * 0.55: return False
        placed.append((x, y)); CPM.paste_sprite(canvas_, spr, x, y); return True
    cx_, cy_ = ll(*C_LL)
    def core(lon, lat):     # commercial core: Braddock..Cameron (3-4 blocks wide at the courthouse), Piccadilly..Cork
        return -78.1680 <= lon <= -78.1616 and 39.1800 <= lat <= 39.1866
    lots = []
    for n, (a, b) in ns_span.items():
        for lat in np.arange(a + 0.0004, b - 0.0002, 0.00055):
            for sgn in (-1, 1): lots.append((NS[n] + sgn * 0.00028, lat, 'ns'))
    for n, (a, b) in ew_span.items():
        for lon in np.arange(a + 0.0004, b - 0.0002, 0.00062):
            for sgn in (-1, 1): lots.append((lon, EW[n] + sgn * 0.00022, 'ew'))
    tr.shuffle(lots)
    lots.sort(key=lambda l: (not core(l[0], l[1]), math.hypot(*(np.subtract(ll(l[0], l[1]), (cx_, cy_))))))
    for lon, lat, o in lots:
        x, y = ll(lon, lat); dn = math.hypot((x - cx_) / 520, (y - cy_) / 470)
        if abs(lat - C_LL[1]) < 0.0006 and abs(lon - C_LL[0]) < 0.0009: continue    # courthouse square
        if core(lon, lat):
            if tr.random() < 0.75: put(small_rows[int(tr.integers(len(small_rows)))] if tr.random() < 0.7 else small_bricks[int(tr.integers(len(small_bricks)))], lon, lat)
            continue
        p = np.clip(1.0 - dn * 0.95, 0.12, 0.8)
        if tr.random() > p: continue
        spr = small_bricks[int(tr.integers(len(small_bricks)))] if dn < 0.55 and tr.random() < 0.5 else small_houses[int(tr.integers(len(small_houses)))]
        if put(spr, lon, lat):
            yd.ellipse((x - 16, y - 8, x + 16, y + 10), fill=(150, 150, 112, 50))
            if tr.random() < 0.45 and outs: put(small_outs[int(tr.integers(len(small_outs)))], lon, lat, dx=tr.uniform(-14, 14), dy=-12)
            if tr.random() < 0.35: put_tree_town.append((x + tr.uniform(-18, 18), y + tr.uniform(-16, 4)))
    canvas_ = Image.alpha_composite(canvas_, yard.filter(ImageFilter.GaussianBlur(3)))
    # landmarks
    ch = lib['courthouse']; ch = scl(ch, 0.85)
    CPM.paste_sprite(canvas_, ch, cx_ + 2, cy_ + 10); FE.setdefault('_runtime', {})['courthouse_ll'] = list(C_LL)
    t_lon, t_lat = loud + 0.00028, 39.1856
    CPM.paste_sprite(canvas_, scl(lib['townhouse_rows'][0], 0.55), *ll(t_lon, t_lat)); FE['_runtime']['taylor_hotel_ll'] = [t_lon, t_lat]
    for spr, lon, lat, f in ((lib['church'], -78.1682, EW['Boscawen'] + 0.0002, 0.6),            # Christ Episcopal
                             (lib['steepled_church'], NS['Kent'] + 0.0003, EW['Boscawen'] + 0.0001, 0.6),  # Kent St Presbyterian
                             (lib['steepled_church'], loud + 0.0003, 39.1866, 0.55),               # Loudoun St Presbyterian
                             (lib['church'], NS['Cameron'] + 0.0002, EW['Amherst'] + 0.0002, 0.55),
                             (lib['steepled_church'], NS['Braddock'] - 0.0003, EW['Cork'] + 0.0001, 0.5)):
        CPM.paste_sprite(canvas_, scl(spr, f), *ll(lon, lat))
    # ordinary frame cottage on North Braddock (unlabeled)
    CPM.paste_sprite(canvas_, small_houses[3 % len(small_houses)], *ll(NS['Braddock'] - 0.00028, 39.1888))
    # depot at the south end of the 1862 W&P line
    CPM.paste_sprite(canvas_, scl(lib['depot'], 0.6), *rr[0])
    FE['_runtime']['depot_ll'] = list(rr_ll[0])
    CPM.paste_sprite = _orig_paste                     # earthworks are not buildings (not tallied)
    canvas_ = CPM.draw_earthworks(canvas_, lib)     # Fort Collier, Fort Alabama
    CPM.paste_sprite = logged_paste
    print('winchester buildings', len(placed))
    return canvas_
put_tree_town = []
canvas = place_winchester(canvas)
CPM.paste_sprite = _orig_paste
tl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); shl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
for x, y in put_tree_town: put_tree(x, y, wr.uniform(5, 7))
canvas = Image.alpha_composite(Image.alpha_composite(canvas, shl), tl); del tl, shl

# ---------- grade + outputs ----------
out = canvas.convert('RGB')
out = ImageEnhance.Color(out).enhance(0.88)
a = np.asarray(out, np.float32); a = a * 0.95 + np.array([150, 126, 92]) * 0.05
out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.UnsharpMask(1.0, 30, 2)); del a
out.save('data/basemap_painted_full.png', compress_level=3)
# per-hex building tally (game-data check: town hexes must match the art)
cnt_hex = {}; area_hex = {}
cells = [(c, r) for c in range(G.cols) for r in range(G.rows)]
cxy = np.array([hexc(c, r) for c, r in cells]); kd = cKDTree(cxy)
for x, y, area in BUILDINGS:
    j = kd.query((x, y - 6))[1]; k = f'{cells[j][0]},{cells[j][1]}'; cnt_hex[k] = cnt_hex.get(k, 0) + 1; area_hex[k] = area_hex.get(k, 0) + area
np.savez_compressed('data/layers/painted_buildings_masks.npz', **{f'm{i}': mk for i, mk in enumerate(FOOT_MASKS)})
json.dump({'note': 'buildings painted per hex (build_full_map.py, game-convention grid); used by build_game_layers.py for town hexes',
           'grid': 'game-native (scripts/hex_grid.py)', 'counts': cnt_hex, 'sprite_area_px': area_hex,
           'footprints_px': FOOT, 'footprint_masks': 'data/layers/painted_buildings_masks.npz (packbits axis=1, alpha>64)',
           'nudged_off_roads_water': len(NUDGED), 'nudge_px_max': round(max(NUDGED), 1) if NUDGED else 0, 'skipped': SKIPPED},
          open('data/layers/painted_buildings.json', 'w'), indent=0)
json.dump(LINES, open('data/layers/painted_lines.json', 'w'))
print('buildings', len(FOOT), 'nudged off roads/rail/water', len(NUDGED), 'max', max(NUDGED) if NUDGED else 0, 'skipped', len(SKIPPED))
fieldfrac = {KINDS[k]: float((k_full == k)[openfull > 0.6].mean()) for k in range(5)}
print('field fractions of open ground', fieldfrac)
lab = CPM.draw_labels(out.convert('RGBA'), scale=1.15).convert('RGB')
lab.save('data/basemap_painted_full_labeled.png', compress_level=3)
os.makedirs('previews', exist_ok=True)
s_ = 3000 / max(lab.size); lab.resize((int(lab.width * s_), int(lab.height * s_)), Image.Resampling.LANCZOS).save('previews/v04_full.jpg', quality=90)
def crop(x0, y0, x1, y1, name):
    lab.crop((int(x0), int(y0), int(x1), int(y1))).save('previews/' + name, quality=90)
crop(wcx - 900, wcy - 820, wcx + 900, wcy + 760, 'v04_closeup_winchester.jpg')
x0k, y1k = ll(-78.240, 39.135); x1k, y0k = ll(-78.192, 39.162)
crop(x0k, y0k, x1k, y1k, 'v04_closeup_kernstown_wall.jpg')
fx, fy = hexc(14, 11)   # legacy (14,12)
crop(fx - 700, fy - 500, fx + 700, fy + 500, 'v04_closeup_fields.jpg')
print('FULL DONE', out.size)
