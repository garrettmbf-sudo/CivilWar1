"""Parallel slicer (same geometry as scripts/slice_sv_tiles.py) for data/basemap_painted_full.png.
Writes mod/Graphics/Tiles/Summer/SV_K_<col>_<row>.png, 2000x2000, alpha = stock hex mask, NO grid."""
import json, math, sys, os
from multiprocessing import Pool
import numpy as np
from PIL import Image
sys.path.insert(0, 'scripts')
from hex_grid import KERNSTOWN as G
Image.MAX_IMAGE_PIXELS = None
P = 0.55
ARR = np.array(Image.open('data/basemap_painted_full.png').convert('RGBA')); H, W = ARR.shape[:2]
R = G.size_m*P
MASK = np.array(Image.open('data/hex_mask.png').convert('L').resize((2000, 2000), Image.Resampling.NEAREST))
OUT = 'mod/Graphics/Tiles/Summer'; os.makedirs(OUT, exist_ok=True)
side = int(round(2*R))
def job(cr):
    col, row = cr
    x, y = G.hex_to_xy_m(col, row); cx, cy = x*P, H-y*P
    reg = np.zeros((side, side, 4), np.uint8); reg[..., :3] = (150, 125, 90); reg[..., 3] = 255
    x0, y0 = int(math.floor(cx-R)), int(math.floor(cy-R))
    sx0, sy0 = max(0, x0), max(0, y0); sx1, sy1 = min(W, x0+side), min(H, y0+side)
    if sx1 > sx0 and sy1 > sy0: reg[sy0-y0:sy1-y0, sx0-x0:sx1-x0] = ARR[sy0:sy1, sx0:sx1]
    rgba = np.array(Image.fromarray(reg).resize((2000, 2000), Image.Resampling.BICUBIC)); rgba[..., 3] = MASK
    Image.fromarray(rgba).save(f'{OUT}/SV_K_{col}_{row}.png', compress_level=6)
    return 1
if __name__ == '__main__':
    with Pool(7) as p: n = sum(p.imap_unordered(job, [(c, r) for c in range(G.cols) for r in range(G.rows)], chunksize=8))
    print('sliced', n)
