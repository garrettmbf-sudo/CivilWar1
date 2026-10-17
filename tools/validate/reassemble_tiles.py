"""Composite SV_K tiles exactly the way Hex of Steel places them: MapGO.cs:452-459
    odd column : (col*4.42, row*5.1)      even column: (col*4.42, row*5.1 + 2.55)      (+y = north)
at 330 px per world unit (ModsManager.cs:1023-1026; scripts/hex_grid.py). Writes
  previews/reassembled_from_tiles.jpg (1/16 scale, north up)
  previews/seam_closeup_stone_wall.jpg, previews/seam_closeup_pike_road.jpg (full res)
  previews/pike_game_placement.jpg: left = painted master map, right = the same ground rebuilt from tiles placed by MapGO.
Usage: python3 tools/validate/reassemble_tiles.py [tile_dir]"""
import sys, os
from multiprocessing import Pool
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from hex_grid import KERNSTOWN as G, game_xy, TILE_PX_PER_UNIT as PPU, TILE_CENTER_PX as C0, TILE_SIZE_PX as TS
Image.MAX_IMAGE_PIXELS = None
TD = sys.argv[1] if len(sys.argv) > 1 else 'mod/Graphics/Tiles/Summer'
COLS, ROWS = G.cols, G.rows
YMAX = game_xy(0, ROWS)[1] + 2.55
def pos(c, r, s, origin=(0.0, YMAX)):
    """Top-left screen px (north up) of tile (c,r) at scale s: world (gx, gy) -> ((gx-ox)*PPU, (oy-gy)*PPU) - pivot."""
    gx, gy = game_xy(c, r)
    return round(((gx - origin[0]) * PPU - C0) * s), round(((origin[1] - gy) * PPU - C0) * s)
def small(cr):
    c, r = cr; return cr, Image.open(f'{TD}/SV_K_{c}_{r}.png').resize((round(TS / 16),) * 2, Image.Resampling.BOX)
def window(cols, rows, s=1.0):
    """Tiles cols x rows composited with MapGO placement; returns image and world->px function."""
    gx0 = min(game_xy(c, 0)[0] for c in cols) - 3.4; gy1 = max(game_xy(c, max(rows))[1] for c in cols) + 3.4
    gx1 = max(game_xy(c, 0)[0] for c in cols) + 3.4; gy0 = min(game_xy(c, min(rows))[1] for c in cols) - 3.4
    im = Image.new('RGBA', (int((gx1 - gx0) * PPU * s), int((gy1 - gy0) * PPU * s)), (0, 0, 0, 255))
    for c in cols:
        for r in rows:
            t = Image.open(f'{TD}/SV_K_{c}_{r}.png')
            if s != 1.0: t = t.resize((round(TS * s),) * 2, Image.Resampling.LANCZOS)
            im.alpha_composite(t, pos(c, r, s, (gx0, gy1)))
    return im, (lambda wx, wy: ((wx - gx0) * PPU * s, (gy1 - wy) * PPU * s)), (gx0, gy0, gx1, gy1)
def closeup(cols, rows, focus, name):
    im, w2p, _ = window(cols, rows)
    gx, gy = game_xy(*focus[:2]); fx, fy = w2p(gx + (4.42 / 2 if focus[2] else 0), gy)
    im.crop((int(fx - 700), int(fy - 500), int(fx + 700), int(fy + 500))).convert('RGB').save(name, quality=90)
def pike_compare(cols, rows, name, s=0.25):
    im, w2p, (gx0, gy0, gx1, gy1) = window(cols, rows, s)
    # same ground from the master: world -> metres -> basemap px (0.55 px/m, y down)
    P = 0.55; base = Image.open('data/basemap_painted_full.png'); BH = base.height
    def w2b(wx, wy):
        x, y = G.x0_m + wx * G.m_per_unit, G.y0_m + wy * G.m_per_unit; return x * P, BH - y * P
    (bx0, by0), (bx1, by1) = w2b(gx0, gy1), w2b(gx1, gy0)
    ref = base.crop((int(bx0), int(by0), int(bx1), int(by1))).resize(im.size, Image.Resampling.LANCZOS)
    out = Image.new('RGB', (im.width * 2 + 20, im.height + 40), (0, 0, 0)); out.paste(ref, (0, 40)); out.paste(im.convert('RGB'), (im.width + 20, 40))
    d = ImageDraw.Draw(out)
    d.text((8, 8), 'painted master map (ground truth)', fill=(255, 255, 0))
    d.text((im.width + 28, 8), f'SV_K tiles cols {cols[0]}-{cols[-1]} rows {rows[0]}-{rows[-1]} placed by MapGO.cs:452-459 (even cols +2.55)', fill=(255, 255, 0))
    out.save(name, quality=88)
if __name__ == '__main__':
    W = int((game_xy(COLS - 1, 0)[0] * PPU + TS) / 16) + 10; H = int((YMAX + 3.1) * PPU / 16) + 10
    im = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    with Pool(6) as pl:
        for (c, r), t in pl.imap_unordered(small, [(c, r) for c in range(COLS) for r in range(ROWS)], chunksize=16):
            x, y = pos(c, r, 1 / 16); im.alpha_composite(t, (x + 64, y + 64))
    im.convert('RGB').save('previews/reassembled_from_tiles.jpg', quality=88)
    # seam closeups: focus on the shared edge east of (c,r) (third elem True => centre on the E-side edge)
    closeup(range(14, 18), range(20, 25), (15, 23, True), 'previews/seam_closeup_stone_wall.jpg')
    closeup(range(21, 25), range(1, 7), (22, 3, True), 'previews/seam_closeup_pike_road.jpg')
    pike_compare(range(19, 26), range(0, 9), 'previews/pike_game_placement.jpg')
    print('reassembled', COLS, 'x', ROWS)
