"""Edge-by-edge validator for SV_K tiles laid out exactly as Hex of Steel places them.
Game layout (MapGO.cs:452-459; scripts/hex_grid.py): tile SV_K_c_r is tile (PosX=c, PosY=r), centred at world
  (4.42*c, 5.1*r + 2.55 if c even); rows run NORTH, EVEN columns are raised; neighbours as Utils.GetAllTilesNeighbours.
  Tile sprites: 330 px per world unit (ModsManager.cs:1023-1026) -> row pitch 1683 px, column pitch 1458.6 px;
  the cell hex inside the 2000 px PNG has half-height 841.5 px and vertex half-width 972.4 px (screen y down).
For each unique edge (A, B) we sample 96 points along the shared edge, k px inside each tile (mirrored), and measure
  dE (CIE76 Lab) of A vs B, luminance-profile lag (linear feature offset along edge), alpha seam (aA+aB<250 on edge),
  and bleed (alpha of A and B >= 250 up to 20 px beyond the edge, i.e. +-20 px of placement error stays covered).
Usage: python3 tools/validate/validate_tile_edges.py <tile_dir> <out_csv> <out_heatmap_png>"""
import sys, os, csv, math
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from hex_grid import (KERNSTOWN as G, neighbor, game_xy, TILE_PX_PER_UNIT as PPU, TILE_CENTER_PX as C0,
                      TILE_ROW_PITCH_PX as RP, TILE_COL_PITCH_PX as CP, TILE_HEX_HALF_W_PX as HA, TILE_HEX_HALF_H_PX as HB)
COLS, ROWS = G.cols, G.rows
HW = 2 * HA
V = {'E': (HA, 0), 'NE': (HA/2, -HB), 'NW': (-HA/2, -HB), 'W': (-HA, 0), 'SW': (-HA/2, HB), 'SE': (HA/2, HB)}
DIRS = {'N': ((0, -RP), V['NW'], V['NE']), 'NE': ((CP, -RP/2), V['NE'], V['E']), 'SE': ((CP, RP/2), V['E'], V['SE'])}
T = np.linspace(0.08, 0.92, 96); KS = (6, 16, 18, -20)  # k=18 vs k=6 inside A = same 12px separation -> intrinsic texture noise floor
PARITY_CONTROL = os.environ.get('PARITY_CONTROL') == '1'   # negative control: odd-raised adjacency (the v0.4.1 bug)
def nb(c, r, d):
    if PARITY_CONTROL:
        c2, r2 = neighbor(c + 1, r, d); return c2 - 1, r2   # same offsets with column parity swapped
    return neighbor(c, r, d)          # game adjacency (Utils.GetAllTilesNeighbours)
def bil(img, x, y):
    h, w = img.shape[:2]; x = np.clip(x, 0, w-1.001); y = np.clip(y, 0, h-1.001)
    x0 = x.astype(int); y0 = y.astype(int); fx = (x-x0)[:, None]; fy = (y-y0)[:, None]
    a, b, c_, d = img[y0, x0], img[y0, x0+1], img[y0+1, x0], img[y0+1, x0+1]
    return a*(1-fx)*(1-fy)+b*fx*(1-fy)+c_*(1-fx)*fy+d*fx*fy
def pts(d, side):
    off, e1, e2 = DIRS[d]; off = np.array(off); e1 = np.array(e1); e2 = np.array(e2)
    P = e1[None]+(e2-e1)[None]*T[:, None]; n = -off/np.linalg.norm(off)   # inward normal for A
    if side == 'B': P = P-off; n = -n
    return P, n
def sample(path):
    img = np.asarray(Image.open(path).convert('RGBA'), np.float32)
    out = {}
    for d in DIRS:
        for side in 'AB':
            P, n = pts(d, side); res = []
            for k in (0,)+KS:
                q = P+n*k+C0; res.append(bil(img, q[:, 0], q[:, 1]))
            out[(d, side)] = np.stack(res)  # (len(KS)+1, 96, 4)
    return out
def lab(rgb):
    c = rgb/255.0; c = np.where(c > 0.04045, ((c+0.055)/1.055)**2.4, c/12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c@M.T/np.array([0.95047, 1, 1.08883]); f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787*xyz+16/116)
    return np.stack([116*f[..., 1]-16, 500*(f[..., 0]-f[..., 1]), 200*(f[..., 1]-f[..., 2])], -1)
def job(cr):
    c, r = cr
    return cr, sample(f'{TD}/SV_K_{c}_{r}.png')
def lag(a, b):
    a = a-np.convolve(a, np.ones(9)/9, 'same'); b = b-np.convolve(b, np.ones(9)/9, 'same')
    if a[8:-8].std() < 3 or b[8:-8].std() < 3: return 0, 0.0
    best = max(range(-12, 13), key=lambda s: np.dot(a[20+s:76+s], b[20:76]))
    return best, float(np.abs(a).max())
if __name__ == '__main__':
    TD, OUT, HEAT = sys.argv[1:4]
    S = {}
    with Pool(6) as p:
        for cr, s in p.imap_unordered(job, [(c, r) for c in range(COLS) for r in range(ROWS)], chunksize=4): S[cr] = s
    rows = []; step = (HW*(T[1]-T[0]))/2  # px along edge per sample on N edge (approx)
    for (c, r), sa in S.items():
        for d in DIRS:
            c2, r2 = nb(c, r, d)
            if (c2, r2) not in S: continue
            A, B = sa[(d, 'A')], S[(c2, r2)][(d, 'B')]
            seam = float(np.mean(A[0, :, 3]+B[0, :, 3] < 250))
            gapA = float(np.mean(A[1, :, 3] < 250)); gapB = float(np.mean(B[1, :, 3] < 250))
            dE = [float(np.mean(np.linalg.norm(lab(A[i, :, :3])-lab(B[i, :, :3]), axis=1))) for i in (1, 2)]
            floor = float(np.mean(np.linalg.norm(lab(A[1, :, :3])-lab(A[3, :, :3]), axis=1)))
            LA = A[1, :, :3]@[.299, .587, .114]; LB = B[1, :, :3]@[.299, .587, .114]
            lg, amp = lag(LA, LB)
            bleedA = float(np.mean(A[4, :, 3] >= 250)); bleedB = float(np.mean(B[4, :, 3] >= 250))
            L_edge = float(np.hypot(*np.subtract(DIRS[d][2], DIRS[d][1])))
            rows.append(dict(col=c, row=r, dir=d, ncol=c2, nrow=r2, dE_k6=round(dE[0], 2), dE_k16=round(dE[1], 2), dE_floor_same_tile=round(floor, 2),
                             feature_lag_px=round(lg*L_edge*(T[1]-T[0]), 1), feature_amp=round(amp, 1),
                             alpha_seam_frac=round(seam, 3), alpha_gap_frac=round(max(gapA, gapB), 3), bleed20_frac=round(min(bleedA, bleedB), 3),
                             bad=int(dE[0] > 5 or abs(lg) >= 2 and amp > 15 or seam > 0.02 or min(bleedA, bleedB) < 0.98)))
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, rows[0].keys()); w.writeheader(); w.writerows(rows)
    dE = np.array([x['dE_k6'] for x in rows]); bad = sum(x['bad'] for x in rows)
    feat = [x for x in rows if x['feature_amp'] > 15]; fbad = sum(abs(x['feature_lag_px']) >= 30 for x in feat)
    seams = sum(x['alpha_seam_frac'] > 0.02 for x in rows); bleed_bad = sum(x['bleed20_frac'] < 0.98 for x in rows)
    fl = np.mean([x['dE_floor_same_tile'] for x in rows])
    summ = (f'edges={len(rows)} mean_dE={dE.mean():.2f} median_dE={np.median(dE):.2f} p95_dE={np.percentile(dE,95):.2f} texture_floor_dE={fl:.2f} '
            f'dE>5={int((dE>5).sum())} feature_edges={len(feat)} feature_misaligned(>=30px)={fbad} '
            f'alpha_seam_edges={seams} bleed20_short_edges={bleed_bad} bad_edges={bad}')
    print(summ); open(OUT.replace('.csv', '_summary.txt'), 'w').write(summ+'\n')
    s = 0.012; Wd = int(COLS*CP*s+HW*s)+20; Hd = int((ROWS+1)*RP*s+20); YMAX = game_xy(0, ROWS)[1]
    im = Image.new('RGB', (Wd, Hd+40), (20, 20, 20)); dr = ImageDraw.Draw(im)
    def ctr(c, r):
        gx, gy = game_xy(c, r); return (10+HA*s+gx*PPU*s, 10+(YMAX-gy)*PPU*s)   # MapGO placement, north up
    for x in rows:
        cx, cy = ctr(x['col'], x['row']); off, e1, e2 = DIRS[x['dir']]
        v = min(x['dE_k6']/10, 1); col = (int(255*v), int(255*(1-v)), 40)
        if x['alpha_seam_frac'] > 0.02 or (x['feature_amp'] > 15 and abs(x['feature_lag_px']) >= 30): col = (255, 0, 255) if v < .5 else col
        dr.line([(cx+e1[0]*s, cy+e1[1]*s), (cx+e2[0]*s, cy+e2[1]*s)], fill=col, width=3)
    dr.text((10, Hd+5), summ[:150], fill=(255, 255, 255)); dr.text((10, Hd+20), 'green dE0 -> red dE>=10; magenta=seam/feature offset; north up', fill=(200, 200, 200))
    im.save(HEAT)
