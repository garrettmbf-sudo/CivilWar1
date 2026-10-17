"""Valley Pike continuity across tile seams under the game's own placement (MapGO.cs:452-459).
Walks the painted Pike centreline (data/layers/painted_lines.json) every 2 basemap px. For each point: world position ->
owning tile (nearest MapGO centre) -> pixel in SV_K_c_r.png (330 px/unit, pivot 999.5). Reports
  * colour agreement tile-vs-master along the whole Pike (dE76),
  * at every seam crossing (owning tile changes), the colour of BOTH tiles at the crossing point (both cover it via the
    bleed): dE between them (a stagger error of half a row shows up here as a jump to field colour),
  * whether consecutive Pike hexes are game neighbours (Utils.GetAllTilesNeighbours).
Usage: python3 tools/validate/check_pike_continuity.py [tile_dir]
  PARITY_CONTROL=1 places tiles with the wrong (odd-raised) stagger as a negative control: it must FAIL."""
import sys, os, json, math
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from hex_grid import KERNSTOWN as G, game_xy, neighbors, TILE_PX_PER_UNIT as PPU, TILE_CENTER_PX as C0
Image.MAX_IMAGE_PIXELS = None
TD = sys.argv[1] if len(sys.argv) > 1 else 'mod/Graphics/Tiles/Summer'
if os.environ.get('PARITY_CONTROL') == '1':
    _gxy = game_xy
    def game_xy(c, r):
        gx, gy = _gxy(c, r); return gx, gy + (-2.55 if c % 2 == 0 else 2.55)   # odd columns raised instead (the v0.4.1 bug)
L = json.load(open('data/layers/painted_lines.json')); P, BH = L['px_per_m'], L['H']
base = np.asarray(Image.open('data/basemap_painted_full.png').convert('RGB'), np.float32)
def lab(c):
    c = np.asarray(c, np.float64) / 255.0; c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1, 1.08883]); f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)
cache = {}
def tile(c, r):
    if (c, r) not in cache:
        if len(cache) > 40: cache.clear()
        cache[(c, r)] = np.asarray(Image.open(f'{TD}/SV_K_{c}_{r}.png').convert('RGBA'), np.float32)
    return cache[(c, r)]
def bil(img, x, y):
    x0, y0 = int(math.floor(x)), int(math.floor(y)); fx, fy = x - x0, y - y0
    if not (0 <= x0 < img.shape[1] - 1 and 0 <= y0 < img.shape[0] - 1): return np.zeros(img.shape[2], np.float32)
    a, b, c, d = img[y0, x0], img[y0, x0 + 1], img[y0 + 1, x0], img[y0 + 1, x0 + 1]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy
def from_tile(c, r, wx, wy):
    gx, gy = game_xy(c, r); u, v = C0 + (wx - gx) * PPU, C0 - (wy - gy) * PPU
    return bil(tile(c, r), u, v)
pts = []
for v in L['roads'].values():
    if v['kind'] != 'pike': continue
    a = np.array(v['pts'], np.float64); s = np.r_[0, np.cumsum(np.hypot(*np.diff(a, axis=0).T))]
    t = np.arange(0, s[-1], 2.0); pts += list(zip(np.interp(t, s, a[:, 0]), np.interp(t, s, a[:, 1])))
along, seams, chain = [], [], []
prev = None; pprev = None
for bx, by in pts:
    if not (2 <= bx < base.shape[1] - 2 and 2 <= by < base.shape[0] - 2): continue
    xm, ym = bx / P, (BH - by) / P; wx, wy = G.xy_m_to_game(xm, ym); h = G.xy_m_to_hex(xm, ym)
    if not G.in_grid(*h): prev = None; continue
    ref = bil(base, bx, by); t = from_tile(*h, wx, wy)
    along.append(float(np.linalg.norm(lab(t[:3]) - lab(ref))))
    if prev is not None and prev != h:
        (ax, ay), (cx, cy) = pprev, (xm, ym)            # bisect to the cell boundary between the two samples
        for _ in range(16):
            mx, my = (ax + cx) / 2, (ay + cy) / 2
            if G.xy_m_to_hex(mx, my) == prev: ax, ay = mx, my
            else: cx, cy = mx, my
        bwx, bwy = G.xy_m_to_game(cx, cy); rb = bil(base, cx * P, BH - cy * P)
        a_ = from_tile(*prev, bwx, bwy); b_ = from_tile(*h, bwx, bwy)
        seams.append((prev, h, float(np.linalg.norm(lab(a_[:3]) - lab(b_[:3]))), float(min(a_[3], b_[3])),
                      float(np.linalg.norm(lab(b_[:3]) - lab(rb))), prev[0] != h[0]))
    if not chain or chain[-1] != h: chain.append(h)
    prev = h; pprev = (xm, ym)
along = np.array(along); sd = np.array([s[2] for s in seams]); col_seams = [s for s in seams if s[5]]
adj = sum(b in neighbors(*a) for a, b in zip(chain, chain[1:]))
summ = (f'pike samples={len(along)} tile_vs_master dE mean={along.mean():.2f} p99={np.percentile(along, 99):.2f} max={along.max():.2f} | '
        f'seam crossings={len(seams)} (column seams={len(col_seams)}) tileA_vs_tileB dE mean={sd.mean():.2f} max={sd.max():.2f} '
        f'min_alpha_at_crossing={min(s[3] for s in seams):.0f} crossings_dE>10={int((sd > 10).sum())} | '
        f'pike hexes={len(chain)} adjacent_steps={adj}/{len(chain) - 1}')
print(summ); open('previews/pike_continuity_summary.txt', 'w').write(summ + '\n')
for s_ in sorted(seams, key=lambda z: -z[2])[:3]: print('  worst crossing', s_[0], '->', s_[1], 'dE %.1f alpha %.0f' % (s_[2], s_[3]))
sys.exit(0 if (sd.max() <= 10 and min(s[3] for s in seams) >= 250 and adj == len(chain) - 1) else 1)
