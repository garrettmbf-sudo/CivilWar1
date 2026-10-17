"""Buildings must never sit on roads, the Valley Pike, the railroad, town streets or water.
Re-rasterises the exact painted lines (data/layers/painted_lines.json, written by build_full_map.py) with the same
widths + dilation as the painter, and tests every painted building sprite's opaque pixels
(data/layers/painted_buildings.json footprints + _masks.npz). Exit 1 on any overlap.
Usage: python3 tools/validate/check_buildings.py"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
L = json.load(open('data/layers/painted_lines.json'))
B = json.load(open('data/layers/painted_buildings.json'))
M = np.load(B['footprint_masks'].split(' ')[0])
W, H = L['W'], L['H']
layers = {'road': [(v['pts'], v['width_px']) for v in L['roads'].values() if v['kind'] != 'pike'],
          'pike': [(v['pts'], v['width_px']) for v in L['roads'].values() if v['kind'] == 'pike'],
          'rail': [(L['rail']['pts'], L['rail']['width_px'])],
          'water': [(c['pts'], c['width_px']) for c in L['creeks']],
          'street': [(s['pts'], s['width_px']) for s in L['streets']]}
masks = {}
for k, lines in layers.items():
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    for pts, w in lines: d.line([tuple(p) for p in pts], fill=255, width=w, joint='curve')
    masks[k] = ndi.binary_dilation(np.asarray(im) > 0, iterations=L['dilate_px'])
bad = []
for i, (px, py, w, h) in enumerate(B['footprints_px']):
    am = np.unpackbits(M[f'm{i}'], axis=1)[:, :w].astype(bool)
    x0, y0, x1, y1 = max(px, 0), max(py, 0), min(px + w, W), min(py + h, H)
    if x1 <= x0 or y1 <= y0: continue
    sub = am[y0 - py:y1 - py, x0 - px:x1 - px]
    for k, m in masks.items():
        n = int((m[y0:y1, x0:x1] & sub).sum())
        if n: bad.append((i, k, n, px, py))
print(f"buildings checked={len(B['footprints_px'])} overlapping={len(bad)} "
      f"(nudged at paint time: {B['nudged_off_roads_water']}, max {B['nudge_px_max']} px, skipped {len(B['skipped'])})")
for b in bad[:20]: print('  overlap', b)
sys.exit(1 if bad else 0)
