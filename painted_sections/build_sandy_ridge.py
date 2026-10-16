"""Painted-texture rebuild of the Sandy Ridge test section (hex cols 10-25, rows 17-28).
Painting = texture/style source only; layout from data. Outputs test_sandy_ridge_final(.jpg|_grid.jpg)."""
import sys, json, math, os
sys.path.insert(0, 'scripts')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from scipy import ndimage as ndi
from sklearn.cluster import KMeans
from hex_grid import KERNSTOWN as G
Image.MAX_IMAGE_PIXELS = None
rng = np.random.default_rng(1862)
PAINT = '/cursor/stores/store-c1012374-62e4-4542-8256-a538f6d9c824/grok-bot/agents/755b30c1-08e9-4ee3-bb8c-637d39bd4be9/attachments/0c57fe998db5cd0153ec88426d6b7c3cb7816c58c06de9a11728b61b15b7e49e.jpg'
P = 0.55; BH, BW = 6723, 6635
FULL = os.environ.get('FULL') == '1'
BX = (0, 0, BW, BH) if FULL else (1016, 3067, 2794, 4658); W, H = BX[2]-BX[0], BX[3]-BX[1]
R = G.size_m * P; APO = R*math.sqrt(3)/2
SRC_SCALE = 1.0
OUT = 'painted_sections/'

def hexc(c, r):
    x, y = G.hex_to_xy_m(c, r); return x*P-BX[0], BH-y*P-BX[1]
def ll(lon, lat):
    x, y = G.lonlat_to_xy_m(lon, lat); return x*P-BX[0], BH-y*P-BX[1]
def hexpoly(c, r, s=1.0):
    cx, cy = hexc(c, r); return [(cx+s*R*math.cos(math.radians(60*k)), cy+s*R*math.sin(math.radians(60*k))) for k in range(6)]
def fnoise(shape, scale, seed):
    g = np.random.default_rng(seed).random((shape[0]//scale+3, shape[1]//scale+3)).astype(np.float32)
    z = ndi.zoom(g, scale, order=3)[:shape[0], :shape[1]]
    return (z-z.mean())/(z.std()+1e-6)
def fbm(shape, seed):
    return (fnoise(shape, 96, seed)+0.5*fnoise(shape, 32, seed+1)+0.25*fnoise(shape, 10, seed+2))/1.75

# ---------- 1. segment painting ----------
src = Image.open(PAINT).convert('RGB')
SK = src.width/1024*SRC_SCALE  # seeds are in 1024-wide coords
src = src.resize((int(src.width*SRC_SCALE), int(src.height*SRC_SCALE)), Image.Resampling.LANCZOS)
S = np.asarray(src, np.float32)
from skimage.color import rgb2lab
lab = rgb2lab(S/255.)
gray = S.mean(2)
tex = np.sqrt(np.maximum(ndi.uniform_filter(gray**2, 9)-ndi.uniform_filter(gray, 9)**2, 0))
tex2 = np.sqrt(np.maximum(ndi.uniform_filter(gray**2, 21)-ndi.uniform_filter(gray, 21)**2, 0))
# directional energy (furrows are strongly oriented; branches are not)
gx0, gy0 = ndi.sobel(gray, 1), ndi.sobel(gray, 0)
jxx, jyy, jxy = [ndi.uniform_filter(v, 15) for v in (gx0*gx0, gy0*gy0, gx0*gy0)]
coh = np.sqrt((jxx-jyy)**2+4*jxy**2)/(jxx+jyy+1e-3)
feat = np.dstack([ndi.uniform_filter(lab[..., i], 9) for i in range(3)]+[tex, tex2, coh*30]).reshape(-1, 6)
# colour/texture classification: seed rectangles hand-picked on the painting (1024x576 coords)
SEEDS = {'woods': [(50,0,200,50),(812,50,1000,150),(0,375,62,525),(412,25,525,75),(962,500,1020,570)],
         'broom': [(737,243,862,325),(200,137,287,187),(612,462,700,550),(287,487,400,550),(875,412,1000,475),(0,268,100,300)],
         'plow':  [(662,206,762,244),(625,312,737,375),(462,431,587,500),(256,187,312,237),(875,250,925,287)],
         'creek': [(50,219,125,237),(375,356,462,371),(650,419,725,431),(925,390,1000,402)]}
CLS = ['woods', 'broom', 'plow', 'creek']
from sklearn.ensemble import RandomForestClassifier
F = feat.reshape(S.shape[0], S.shape[1], -1); Xs, Ys = [], []
for ci, c in enumerate(CLS):
    for x0, y0, x1, y1 in SEEDS[c]:
        f_ = F[int(y0*SK):int(y1*SK), int(x0*SK):int(x1*SK)].reshape(-1, F.shape[2])
        f_ = f_[rng.choice(len(f_), min(len(f_), 1500), replace=False)]
        Xs.append(f_); Ys.append(np.full(len(f_), ci))
clf = RandomForestClassifier(60, max_depth=12, n_jobs=-1, random_state=0).fit(np.vstack(Xs), np.concatenate(Ys))
segmap = clf.predict(feat).reshape(S.shape[:2])
segmap = ndi.median_filter(segmap, 9)
viz = np.array([(70, 60, 50), (210, 190, 120), (120, 70, 40), (90, 130, 170)], np.uint8)[segmap]
Image.fromarray(viz).save(OUT+'debug_painting_segments.png')

# ---------- texture synthesis (patch quilting with feathered overlaps) ----------
PS, OV = 72, 20
def patch_pool(cls_idx, purity=0.92):
    m = (segmap == cls_idx).astype(np.float32)
    frac = ndi.uniform_filter(m, PS)
    ys, xs = np.where(frac[PS//2:-PS//2, PS//2:-PS//2] >= purity)
    return np.stack([ys, xs], 1) if len(ys) else None
FEATHER = None
def feather():
    w = np.ones(PS, np.float32); r = np.linspace(0, 1, OV+2)[1:-1]; w[:OV] = r; w[-OV:] = r[::-1]
    return np.outer(w, w)[..., None]
FEATHER = feather()
def quilt(pool, shape, seed, local=None):
    r = np.random.default_rng(seed); step = PS-OV
    acc = np.zeros(shape+(3,), np.float32); wsum = np.zeros(shape+(1,), np.float32)
    for y in range(-OV, shape[0], step):
        for x in range(-OV, shape[1], step):
            best = None
            cand = pool[r.integers(len(pool), size=12)]
            if local is not None: cand = local
            # pick candidate matching the already-placed left/top overlap best
            y0, x0 = max(y, 0), max(x, 0); y1, x1 = min(y+PS, shape[0]), min(x+PS, shape[1])
            for sy, sx in cand[:12] if local is None else local[r.integers(len(local), size=12)]:
                p = S[sy:sy+PS, sx:sx+PS][y0-y:y1-y, x0-x:x1-x]
                ws = wsum[y0:y1, x0:x1]
                if ws.sum() > 0:
                    e = (((acc[y0:y1, x0:x1]/np.maximum(ws, 1e-6))-p)**2*(ws > 0)).mean()
                else: e = r.random()
                if best is None or e < best[0]: best = (e, p)
            f = FEATHER[y0-y:y1-y, x0-x:x1-x]
            acc[y0:y1, x0:x1] += best[1]*f; wsum[y0:y1, x0:x1] += f
    return acc/np.maximum(wsum, 1e-6)

pools = {c: patch_pool(i) for i, c in enumerate(CLS)}
for c in CLS: print(c, 'patches', None if pools[c] is None else len(pools[c]))
if pools['creek'] is None: pools['creek'] = patch_pool(3, 0.25)

# ---------- 2. masks from data ----------
shape = (H, W)
ff = json.load(open('data/layers/painted_forest_fraction.json'))
tags = json.load(open('layers/kernstown_terrain_tags.json'))
marsh = {tuple(h) for h in tags['marsh_hexes']}
guide = np.asarray(Image.open('data/basemap_kernstown.png' if FULL else OUT+'guide_sandy_ridge_nogrid.jpg').convert('RGB'))
hexes = [(c, r) for c in range(G.cols) for r in range(G.rows)] if FULL else [(c, r) for c in range(8, 28) for r in range(15, 31)]
def hexmask(cset, s=1.0):
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    for h in cset: d.polygon(hexpoly(*h, s), fill=255)
    return np.asarray(im, np.float32)/255.
# forest field: per-hex fraction rasterised then blurred
forest = np.zeros(shape, np.float32)
im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
for h in hexes:
    v = ff.get(f'{h[0]},{h[1]}', 0.0)
    if v > 0: d.polygon(hexpoly(*h), fill=int(255*v))
forest = ndi.gaussian_filter(np.asarray(im, np.float32)/255., R*0.45)
woods_m = np.clip((forest + 0.22*fbm(shape, 11) - 0.33)/0.10, 0, 1)
# plowed hexes: take the existing basemap's plowed hex choices (dark furrow brown) for layout continuity
plow_hex = []
for h in hexes:
    cx, cy = hexc(*h)
    if not (0 <= cx < W and 0 <= cy < H): continue
    q = int(R*0.42); g = guide[max(int(cy)-q, 0):int(cy)+q, max(int(cx)-q, 0):int(cx)+q].reshape(-1, 3).astype(np.float32)
    if FULL and not (0 <= hexc(*h)[0] < W): continue
    rr, gg, bb = g[:, 0].mean(), g[:, 1].mean(), g[:, 2].mean()
    if rr > gg*1.35 and rr < 150 and bb < gg: plow_hex.append(h)
print('plow hexes', plow_hex)
plow_m = hexmask(plow_hex, 0.93)
plow_m = (ndi.gaussian_filter(plow_m, 10) > 0.02)*np.clip((ndi.gaussian_filter(plow_m, 14) + 0.22*fnoise(shape, 45, 5) + 0.08*fnoise(shape, 8, 6) - 0.5)/0.08, 0, 1)*(1-woods_m)
marsh_m = np.clip((ndi.gaussian_filter(hexmask(marsh), R*0.35)+0.25*fbm(shape, 21)-0.45)/0.15, 0, 1)
# creek ribbon
cr = json.load(open('data/hydro/creeks_flow_spline.json'))['rivers']['hoge_run']['waypoints']
crp = [ll(*p) for p in cr]
for _ in range(4):
    o_ = [crp[0]]
    for a, b in zip(crp, crp[1:]): o_ += [(0.75*a[0]+0.25*b[0], 0.75*a[1]+0.25*b[1]), (0.25*a[0]+0.75*b[0], 0.25*a[1]+0.75*b[1])]
    o_.append(crp[-1]); crp = o_
# resample at 2px and moving-average (k=31) to remove the DEM-snap stair steps
arr = np.array(crp); seg = np.r_[0, np.cumsum(np.hypot(*np.diff(arr, axis=0).T))]
t = np.arange(0, seg[-1], 2.0); arr = np.c_[np.interp(t, seg, arr[:, 0]), np.interp(t, seg, arr[:, 1])]
kk = 31; pad = np.r_[np.repeat(arr[:1], kk//2, 0), arr, np.repeat(arr[-1:], kk//2, 0)]
arr = np.c_[np.convolve(pad[:, 0], np.ones(kk)/kk, 'valid'), np.convolve(pad[:, 1], np.ones(kk)/kk, 'valid')]
crp = [tuple(p) for p in arr]
cim = Image.new('L', (W, H), 0)
if not FULL: ImageDraw.Draw(cim).line(crp, fill=255, width=12, joint='curve')
water = np.asarray(cim, np.float32)/255.
bank = np.clip(ndi.gaussian_filter(water, 6)*3+0.3*fnoise(shape, 6, 8), 0, 1)
riparian = np.clip(ndi.gaussian_filter(water, 18)*5-0.4+0.5*fnoise(shape, 14, 12), 0, 1)

# ---------- composite textures ----------
base = quilt(pools['broom'], shape, 1)
alt = quilt(pools['broom'], shape, 2)   # second broom variant for patchy fields
patch_v = np.clip((fbm(shape, 31)+0.3)/0.5, 0, 1)[..., None]
base = base*(1-patch_v*0.5)+alt*patch_v*0.5
# plowed: each field synthesised from a single local source region => coherent furrow direction
plow_layer = np.zeros_like(base)
pp = pools['plow']
for i, h in enumerate(plow_hex):
    cy0 = pp[rng.integers(len(pp))]
    near = pp[np.hypot(pp[:, 0]-cy0[0], pp[:, 1]-cy0[1]) < 40]
    cx, cy = hexc(*h); x0, y0 = int(max(cx-R*1.3, 0)), int(max(cy-R*1.3, 0)); x1, y1 = int(min(cx+R*1.3, W)), int(min(cy+R*1.3, H))
    if x1 <= x0 or y1 <= y0: continue
    t = quilt(pp, (y1-y0, x1-x0), 100+i, local=near if len(near) > 4 else None)
    plow_layer[y0:y1, x0:x1] = t
woods = quilt(pools['woods'], shape, 3)
creekt = quilt(pools['creek'], shape, 4) if (pools['creek'] is not None and not FULL) else np.full(shape+(3,), 110, np.float32)
img = base
pm = plow_m[..., None]; img = img*(1-pm)+plow_layer*pm
# marsh: darker, slightly olive wet broom
mm = marsh_m[..., None]*(1-woods_m[..., None])
img = img*(1-mm*0.55) + (img*np.array([0.78, 0.84, 0.80]))*mm*0.55
dk = np.clip(fbm(shape, 41)*0.5+0.1, 0, 1)[..., None]
img = img*(1-dk*0.28)+img*np.array([0.78, 0.70, 0.62])*dk*0.28
woods = woods*np.array([1.06, 1.0, 0.92])
wm = np.maximum(woods_m, riparian*0.85*(1-plow_m))[..., None]; img = img*(1-wm)+woods*wm
# woods edge darkening (soft shadow fringe)
edge = np.clip(ndi.gaussian_filter(woods_m, 7)-woods_m, 0, 1)[..., None]*1.6
img *= 1-edge*0.35

# ---------- 3. hillshade ----------
dem = np.asarray(Image.open('data/dem/kernstown_3dep.tif'), np.float32)
dem = np.where(np.isfinite(dem), dem, np.nanmedian(dem))
sy, sx = dem.shape[0]/BH, dem.shape[1]/BW
if FULL:
    dz = np.asarray(Image.fromarray(dem).resize((W, H), Image.Resampling.BICUBIC), np.float32)
else:
  dc = dem[int(BX[1]*sy)-2:int(BX[3]*sy)+3, int(BX[0]*sx)-2:int(BX[2]*sx)+3]
  dz = np.asarray(Image.fromarray(dc).resize((int(dc.shape[1]/sx), int(dc.shape[0]/sy)), Image.Resampling.BICUBIC), np.float32)
  o = (int(BX[1]*sy)-2)/sy; ox = (int(BX[0]*sx)-2)/sx
  dz = dz[int(BX[1]-o):int(BX[1]-o)+H, int(BX[0]-ox):int(BX[0]-ox)+W]
dz = ndi.gaussian_filter(dz, 28)
mpp = 1/P
gy, gx = np.gradient(dz*1.6, mpp)  # mild vertical exaggeration
az, alt_ = math.radians(315), math.radians(40)
sl = np.arctan(np.hypot(gx, gy)); asp = np.arctan2(-gx, gy)
hs = np.sin(alt_)*np.cos(sl)+np.cos(alt_)*np.sin(sl)*np.cos(az-asp)
hs = (hs - np.median(hs))
elev = (dz-dz.mean())/(dz.std()+1e-6)
shade = 1 + 0.9*hs + 0.035*elev      # higher ground a touch lighter
img *= np.clip(shade, 0.8, 1.15)[..., None]
img = np.clip(img, 0, 255)
# creek: stony bank then water texture from painting, tinted gray-blue
bk = bank[..., None]
stones = (fnoise(shape, 3, 77) > 0.9).astype(np.float32)[..., None]*bk
img = img*(1-bk*0.6)+np.array([150, 140, 125])*bk*0.6
img = img*(1-stones*0.6)+np.array([185, 180, 170])*stones*0.6
wt = ndi.gaussian_filter(water, 1.2)[..., None]
wtex = creekt*0.6+np.array([100, 118, 128])*0.4
img = img*(1-wt)+wtex*wt
canvas = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')

# ---------- roads ----------
FE = json.load(open('data/features/kernstown_features.json'))
def jitter(pts, amp=1.2, seed=0):
    r = np.random.default_rng(seed); return [(x+r.normal(0, amp), y+r.normal(0, amp)) for x, y in pts]
lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
for n, (k, v) in enumerate(FE['roads'].items()):
    pts = [ll(*p) for p in v['waypoints']]
    if not any(-50 < x < W+50 and -50 < y < H+50 for x, y in pts): continue
    pike = v.get('kind') == 'pike'
    wdt = 15 if pike else 11
    d.line(pts, fill=(95, 72, 50, 150), width=wdt+5, joint='curve')
    d.line(pts, fill=(196, 188, 170, 255) if pike else (148, 112, 78, 255), width=wdt, joint='curve')
    if not pike:
        for off in (-2.6, 2.6):
            # ruts: offset polyline
            q = []
            for i in range(len(pts)-1):
                (x0, y0), (x1, y1) = pts[i], pts[i+1]; L = math.hypot(x1-x0, y1-y0)+1e-6
                q.append((x0-(y1-y0)/L*off, y0+(x1-x0)/L*off))
            d.line(jitter(q, 0.4, n), fill=(105, 78, 52, 200), width=2)
lay = lay.filter(ImageFilter.GaussianBlur(0.9))
# roughen road surface with noise
an = np.asarray(lay, np.float32); nz = fnoise(shape, 4, 9)[..., None]*10
an[..., :3] = np.clip(an[..., :3]+nz, 0, 255)
canvas = Image.alpha_composite(canvas, Image.fromarray(an.astype(np.uint8)))

# ---------- split-rail fences on some field edges ----------
fl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(fl)
def rail(a, b, seed):
    r = np.random.default_rng(seed); L = math.hypot(b[0]-a[0], b[1]-a[1]); n = max(2, int(L/7))
    ux, uy = (b[0]-a[0])/L, (b[1]-a[1])/L; nx, ny = -uy, ux; pts = []
    for i in range(n+1):
        t = i/n; z = 2.0 if i % 2 else -2.0
        pts.append((a[0]+ux*L*t+nx*z, a[1]+uy*L*t+ny*z))
    d.line([(x+1.5, y+1.5) for x, y in pts], fill=(40, 30, 20, 90), width=3)
    d.line(pts, fill=(118, 100, 80, 235), width=2)
    for x, y in pts[::2]: d.ellipse((x-1.2, y-1.2, x+1.2, y+1.2), fill=(80, 65, 50, 255))
for i, h in enumerate(plow_hex):
    poly = hexpoly(*h, 0.97)
    for k in range(6):
        if rng.random() < 0.6: rail(poly[k], poly[(k+1) % 6], i*10+k)
# a few broom-field hedges/fence lines on open hexes
open_h = [h for h in hexes if h not in plow_hex and ff.get(f'{h[0]},{h[1]}', 0) < 0.2 and h not in marsh]
for i in rng.choice(len(open_h), size=min(18, len(open_h)), replace=False):
    poly = hexpoly(*open_h[i], 0.98); k = int(rng.integers(6))
    rail(poly[k], poly[(k+1) % 6], 500+i)
fl = fl.filter(ImageFilter.GaussianBlur(0.35))
canvas = Image.alpha_composite(canvas, fl)

# ---------- stone wall: one natural, nearly straight E-W dry-stone wall across the crest ----------
sw = json.load(open('data/features/stone_wall_hexsides.json'))
wh = sorted(tuple(h) for h in sw['confederate_hexes'])
# anchor: centre-to-north-third of each wall hex, then a straight least-squares line (no hexside zigzag)
ax_ = np.array([hexc(c, r)[0] for c, r in wh]); ay_ = np.array([hexc(c, r)[1]-0.38*APO for c, r in wh])
k_, b_ = np.polyfit(ax_, ay_, 1)
x0w, x1w = ax_.min()-0.75*R, ax_.max()+0.75*R
wr = np.random.default_rng(23)
xs_ = np.arange(x0w, x1w, 1.0)
wob = fnoise((1, len(xs_)+400), 140, 3)[0][:len(xs_)]*3.5 + fnoise((1, len(xs_)+100), 35, 4)[0][:len(xs_)]*0.9
dense = [(x, k_*x+b_+w) for x, w in zip(xs_, wob)]
th = 8.0
def along(i):
    j = min(len(dense)-1, i+1); (xa, ya), (xb, yb) = dense[max(i-1, 0)], dense[j]
    L = math.hypot(xb-xa, yb-ya)+1e-9; return (xb-xa)/L, (yb-ya)/L
# grass/brush at the base (both sides, heavier on the north/uphill edge of a wall that collects debris)
gb = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(gb)
for i in range(0, len(dense), 2):
    x, y = dense[i]
    if wr.random() < 0.35: continue
    ux, uy = along(i); nx, ny = -uy, ux
    for _ in range(2):
        o = wr.choice([-1, 1])*wr.uniform(th*0.45, th*1.3); rr = wr.uniform(1.0, 2.8)
        g_ = wr.uniform(0.7, 1.15); c = (int(98*g_), int(86*g_), int(58*g_), int(wr.uniform(70, 160)))
        px_, py_ = x+nx*o+wr.normal(0, 1), y+ny*o+wr.normal(0, 1); gd.ellipse((px_-rr, py_-rr, px_+rr, py_+rr), fill=c)
    if wr.random() < 0.035:  # brush clumps / small cedar-like shrubs
        o = wr.choice([-1, 1])*wr.uniform(th*0.6, th*1.6); rr = wr.uniform(3, 6)
        gd.ellipse((x+nx*o-rr, y+ny*o-rr, x+nx*o+rr, y+ny*o+rr), fill=(68, 60, 42, 200))
canvas = Image.alpha_composite(canvas, gb.filter(ImageFilter.GaussianBlur(0.8)))
# soft cast shadow to the south-east (painting is lit from upper-left)
sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).line([(x+2.5, y+4.0) for x, y in dense[::3]], fill=(38, 30, 22, 150), width=int(th*1.1))
canvas = Image.alpha_composite(canvas, sh.filter(ImageFilter.GaussianBlur(2.2)))
# individual irregular fieldstones, two loose courses, with tumbled gaps
lw = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lw)
gaps = []
gx = x0w
while gx < x1w:
    gx += wr.uniform(60, 160)
    gaps.append((gx, gx+wr.uniform(5, 14)))
def in_gap(x, y=None): return any(g0 < x < g1 for g0, g1 in gaps) or (y is not None and 0 <= int(y) < H and water[int(y), int(x)] > 0.05)
def stone(cx, cy, rx, ry, rot, base):
    n = int(wr.integers(5, 8)); pts = []
    for t in range(n):
        ang = 2*math.pi*t/n+wr.uniform(-0.3, 0.3); rf = wr.uniform(0.75, 1.1)
        dx, dy = math.cos(ang)*rx*rf, math.sin(ang)*ry*rf
        pts.append((cx+dx*math.cos(rot)-dy*math.sin(rot), cy+dx*math.sin(rot)+dy*math.cos(rot)))
    ld.polygon(pts, fill=tuple(int(v) for v in base)+(255,))
    # lit top-left facet, dark lower-right rim
    hl = tuple(int(min(255, v*1.18)) for v in base)+(210,); dk = tuple(int(v*0.62) for v in base)+(230,)
    m = len(pts)
    ld.line([pts[(m*5)//8 % m], pts[(m*6)//8 % m], pts[(m*7)//8 % m]], fill=hl, width=1)
    ld.line([pts[m//8], pts[(m*2)//8], pts[(m*3)//8]], fill=dk, width=1)
i = 0
while i < len(dense)-1:
    x, y = dense[i]; ux, uy = along(i); nx, ny = -uy, ux; rot = math.atan2(uy, ux)
    sl = wr.uniform(3.0, 5.5)
    if in_gap(x, y):
        if wr.random() < 0.5:  # tumbled stone lying off the line
            o = wr.uniform(th*0.6, th*1.5)*wr.choice([-1, 1]); g = wr.uniform(0.8, 1.0)
            stone(x+nx*o, y+ny*o, 2.0, 1.6, wr.uniform(0, 3), np.array([128, 120, 106])*g)
        i += int(sl)+2; continue
    for off in (th*0.2, -th*0.18):   # south course first, north (top) course over it
        g = wr.uniform(0.78, 1.1)
        tint = np.array([wr.choice([118, 112, 124, 106]), wr.choice([112, 108, 116]), wr.choice([98, 102, 106])])  # gray to brown limestone/sandstone
        stone(x+nx*off+wr.normal(0, 0.5), y+ny*off+wr.normal(0, 0.5), sl*0.55, th*wr.uniform(0.24, 0.34), rot+wr.normal(0, 0.25), tint*g)
    if wr.random() < 0.25:  # capstone
        stone(x, y-1, sl*0.4, th*0.22, rot, np.array([150, 144, 130])*wr.uniform(0.9, 1.05))
    i += max(2, int(sl))
lw = lw.filter(ImageFilter.GaussianBlur(0.35))
canvas = Image.alpha_composite(canvas, lw)
WALL_BOX = (int(x0w)-30, int(min(y for _, y in dense))-60, int(x1w)+30, int(max(y for _, y in dense))+60)

# ---------- sprites ----------
SP = 'data/assets/painted/sprites/'
def put(name, x, y, w):
    s = Image.open(SP+name).convert('RGBA'); s = s.resize((int(w), int(w*s.height/s.width)), Image.Resampling.LANCZOS)
    a = s.split()[3]; shd = Image.new('RGBA', s.size, (30, 22, 15, 0)); shd.putalpha(a.point(lambda v: v*0.45))
    global canvas
    canvas.alpha_composite(shd.filter(ImageFilter.GaussianBlur(3)), (int(x-s.width/2+5), int(y-s.height/2+6)))
    canvas.alpha_composite(s, (int(x-s.width/2), int(y-s.height/2)))
places = {p['id']: p for p in FE['places']}
gx_, gy_ = ll(places['glass_farm']['lon'], places['glass_farm']['lat'])
put('cgpt_stone_farm.png', gx_, gy_, 64); put('cgpt_bank_barn.png', gx_+58, gy_+28, 58); put('cgpt_smokehouse.png', gx_-34, gy_+30, 24)
# small farmsteads on open ground away from the wall
for (c, r), nm, w in (((12, 19), 'cgpt_log_cabin.png', 40), ((23, 19), 'cgpt_frame_farmhouse.png', 48), ((22, 28), 'cgpt_log_cabin_small.png', 34), ((24, 21), 'cgpt_corncrib.png', 26)):
    cx, cy = hexc(c, r); put(nm, cx+8, cy-6, w)

# subtle unifying grade: warm tan, lowered saturation, faint vignette
out = canvas.convert('RGB')
out = ImageEnhance.Color(out).enhance(0.9)
a = np.asarray(out, np.float32); a = a*0.94+np.array([150, 125, 90])*0.06
out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.UnsharpMask(1.2, 40, 2))
out.save(OUT+'test_sandy_ridge_final.jpg', quality=92)
# ---------- gridded ----------
gimg = out.convert('RGBA'); gl = Image.new('RGBA', gimg.size, (0, 0, 0, 0)); d = ImageDraw.Draw(gl)
for c in range(8, 28):
    for r in range(15, 31):
        p = hexpoly(c, r); d.line(p+[p[0]], fill=(25, 20, 15, 215), width=3)
Image.alpha_composite(gimg, gl).convert('RGB').save(OUT+'test_sandy_ridge_final_grid.jpg', quality=92)
print('done', out.size)
if '--debug' in sys.argv:
    mont = Image.new('RGB', (4*PS*4, PS*4))
    for ci, c in enumerate(CLS):
        pl = pools[c]
        for k in range(16):
            sy, sx = pl[rng.integers(len(pl))]
            mont.paste(Image.fromarray(S[sy:sy+PS, sx:sx+PS].astype(np.uint8)), (ci*PS*4+(k % 4)*PS, (k//4)*PS))
    mont.save(OUT+'debug_pools.png')

# 2x close-up of the wall
x0c, y0c, x1c, y1c = WALL_BOX; cw = (x1c-x0c)//2
for n_, xo in enumerate((x0c, x0c+cw)):
    out.crop((xo, y0c, xo+cw, y1c)).resize((cw*2, (y1c-y0c)*2), Image.Resampling.LANCZOS).save(OUT+f'closeup_wall_2x_{n_}.jpg', quality=92)
