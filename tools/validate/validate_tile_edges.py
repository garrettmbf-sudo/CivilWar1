"""Edge-by-edge validator for SV_K tiles as Hex of Steel lays them out.
Game layout model (matches data/layers/kernstown_game.json + scripts/hex_grid.py, tile SV_K_c_r -> hex (c,r)):
  flat-top, odd-q, rows increase NORTH, odd columns shifted half a row north.
  The game abuts tiles by their stock alpha hex (data/hex_mask.png): hex W=1910px, H=1672px inside the 2000px PNG,
  so col pitch = 0.75*1910 = 1432.5 px, row pitch = 1672 px (screen y down => north = -y).
For each unique edge (A, B) we sample 96 points along the shared edge, k px inside each tile (mirrored), and measure
  dE (CIE76 Lab) of A vs B, luminance-profile lag (linear feature offset along edge), alpha seam (aA+aB<250 on edge).
Usage: python3 tools/validate/validate_tile_edges.py <tile_dir> <out_csv> <out_heatmap_png>"""
import sys, os, csv, math
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw
COLS, ROWS = 62, 55
HW, HH = 1910.0, 1672.0; C0 = 999.5
CP, RP = 0.75*HW, HH
V = {'E': (HW/2, 0), 'NE': (HW/4, -HH/2), 'NW': (-HW/4, -HH/2), 'W': (-HW/2, 0), 'SW': (-HW/4, HH/2), 'SE': (HW/4, HH/2)}
DIRS = {'N': ((0, -RP), V['NW'], V['NE']), 'NE': ((CP, -RP/2), V['NE'], V['E']), 'SE': ((CP, RP/2), V['E'], V['SE'])}
T = np.linspace(0.08, 0.92, 96); KS = (6, 16, 18)  # k=18 vs k=6 inside A = same 12px separation -> intrinsic texture noise floor
def nb(c, r, d):
    up = c & 1  # odd col sits half row north
    if d == 'N': return c, r+1
    if d == 'NE': return c+1, (r+1 if up else r)
    if d == 'SE': return c+1, (r if up else r-1)
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
            rows.append(dict(col=c, row=r, dir=d, ncol=c2, nrow=r2, dE_k6=round(dE[0], 2), dE_k16=round(dE[1], 2), dE_floor_same_tile=round(floor, 2),
                             feature_lag_px=round(lg*HW*(T[1]-T[0])*(1 if d == 'N' else 1), 1), feature_amp=round(amp, 1),
                             alpha_seam_frac=round(seam, 3), alpha_gap_frac=round(max(gapA, gapB), 3),
                             bad=int(dE[0] > 5 or abs(lg) >= 2 and amp > 15 or seam > 0.02)))
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, rows[0].keys()); w.writeheader(); w.writerows(rows)
    dE = np.array([x['dE_k6'] for x in rows]); bad = sum(x['bad'] for x in rows)
    feat = [x for x in rows if x['feature_amp'] > 15]; fbad = sum(abs(x['feature_lag_px']) >= 30 for x in feat)
    seams = sum(x['alpha_seam_frac'] > 0.02 for x in rows)
    fl = np.mean([x['dE_floor_same_tile'] for x in rows])
    summ = (f'edges={len(rows)} mean_dE={dE.mean():.2f} median_dE={np.median(dE):.2f} p95_dE={np.percentile(dE,95):.2f} texture_floor_dE={fl:.2f} '
            f'dE>5={int((dE>5).sum())} feature_edges={len(feat)} feature_misaligned(>=30px)={fbad} '
            f'alpha_seam_edges={seams} bad_edges={bad}')
    print(summ); open(OUT.replace('.csv', '_summary.txt'), 'w').write(summ+'\n')
    s = 0.012; Wd = int(COLS*CP*s+HW*s)+20; Hd = int((ROWS+1)*RP*s+20)
    im = Image.new('RGB', (Wd, Hd+40), (20, 20, 20)); dr = ImageDraw.Draw(im)
    def ctr(c, r): return (10+HW/2*s+c*CP*s, 10+Hd-20-(r+0.5*(c & 1)+0.5)*RP*s)
    for x in rows:
        cx, cy = ctr(x['col'], x['row']); off, e1, e2 = DIRS[x['dir']]
        v = min(x['dE_k6']/10, 1); col = (int(255*v), int(255*(1-v)), 40)
        if x['alpha_seam_frac'] > 0.02 or (x['feature_amp'] > 15 and abs(x['feature_lag_px']) >= 30): col = (255, 0, 255) if v < .5 else col
        dr.line([(cx+e1[0]*s, cy+e1[1]*s), (cx+e2[0]*s, cy+e2[1]*s)], fill=col, width=3)
    dr.text((10, Hd+5), summ[:150], fill=(255, 255, 255)); dr.text((10, Hd+20), 'green dE0 -> red dE>=10; magenta=seam/feature offset; north up', fill=(200, 200, 200))
    im.save(HEAT)
