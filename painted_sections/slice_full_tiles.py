"""Parallel slicer: data/basemap_painted_full.png -> <OUT>/SV_K_<col>_<row>.png (2000x2000 RGBA, no grid).
v0.4.2: the game's own convention and geometry (scripts/hex_grid.py, MapGO.cs:452-459, ModsManager.cs:1023-1026):
  tile (col,row) is centred at game (4.42*col, 5.1*row + 2.55 if col even); 330 tile px per world unit, so
  row pitch 1683 px and column pitch 1458.6 px (4.42:5.1). The basemap is mapped isotropically (one scale for x and y)
  onto that cell; the opaque area is the cell hex (half-height 841.5 px, vertex half-width 972.4 px) grown by BLEED px
  with a 1.5 px antialiased ramp, so neighbours overlap by ~2x20 px and +-20 px of placement/scale error leaves no seam.
Usage: python3 painted_sections/slice_full_tiles.py [OUT_DIR]   (default mod/Graphics/Tiles/Summer)"""
import math, sys, os
from multiprocessing import Pool
import numpy as np
from PIL import Image
sys.path.insert(0, 'scripts')
from hex_grid import (KERNSTOWN as G, TILE_PX_PER_UNIT, TILE_SIZE_PX as TS, TILE_CENTER_PX as C0,
                      TILE_HEX_HALF_H_PX as HB, TILE_HEX_HALF_W_PX as HA)
Image.MAX_IMAGE_PIXELS = None
P = 0.55; PAD = 300; BLEED = 21.5
S = TILE_PX_PER_UNIT / G.m_per_unit          # tile px per ground metre (7.362)
K = P / S                                    # basemap px per tile px
OUT = sys.argv[1] if len(sys.argv) > 1 else 'mod/Graphics/Tiles/Summer'
SRC = Image.open('data/basemap_painted_full.png').convert('RGB'); H = SRC.height
BIG = Image.new('RGB', (SRC.width + 2 * PAD, SRC.height + 2 * PAD), (150, 125, 90)); BIG.paste(SRC, (PAD, PAD)); del SRC
u = np.arange(TS) - C0; X, Y = np.abs(u)[None, :], np.abs(u)[:, None]
d = np.maximum(Y - HB, (X * 2 * HB + Y * HA - 2 * HA * HB) / math.hypot(2 * HB, HA))  # signed px distance outside the cell hex
ALPHA = (np.clip((BLEED - d) / 1.5 + 0.5, 0, 1) * 255 + 0.5).astype(np.uint8)
assert ALPHA[:, 0].max() == 0 and ALPHA[:, -1].max() == 0 and ALPHA[0].max() == 0, 'bleed must stay inside the PNG'
os.makedirs(OUT, exist_ok=True)
def job(cr):
    col, row = cr
    x, y = G.hex_to_xy_m(col, row); cx, cy = x * P + PAD, H - y * P + PAD
    rgb = BIG.transform((TS, TS), Image.Transform.AFFINE,
                        (K, 0, cx - (C0 + 0.5) * K, 0, K, cy - (C0 + 0.5) * K), Image.Resampling.BICUBIC)
    rgba = np.dstack([np.asarray(rgb), ALPHA]); rgba[ALPHA == 0, :3] = 0
    Image.fromarray(rgba).save(f'{OUT}/SV_K_{col}_{row}.png', compress_level=1)
    return 1
if __name__ == '__main__':
    with Pool(int(os.environ.get('SLICE_WORKERS', 7))) as p:
        n = sum(p.imap_unordered(job, [(c, r) for c in range(G.cols) for r in range(G.rows)], chunksize=8))
    print('sliced', n, 'S=%.4f px/m, row pitch %.1f px, col pitch %.1f px, bleed %.1f px' % (S, S * G.row_pitch_m, S * G.col_pitch_m, BLEED))
