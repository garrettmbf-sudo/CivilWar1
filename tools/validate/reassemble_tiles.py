"""Composite SV_K tiles the way the game lays them out (odd-q, rows north, odd cols half row north,
col pitch 1432.5 px, row pitch 1672 px). Writes previews/reassembled_from_tiles.jpg (1/16 scale) and full-res seam closeups."""
import sys, json
from multiprocessing import Pool
from PIL import Image
TD = 'mod/Graphics/Tiles/Summer'; COLS, ROWS = 62, 55; CP, RP = 1432.5, 1672.0
def pos(c, r, s, rows=ROWS, par=None):
    par = (c & 1) if par is None else par
    return round(c*CP*s), round((rows-1-r-0.5*par)*RP*s+RP/2*s)
def small(cr):
    c, r = cr; return cr, Image.open(f'{TD}/SV_K_{c}_{r}.png').resize((125, 125), Image.Resampling.BOX)
def closeup(cols, rows, focus, name):
    s = 1.0; c0, r0 = min(cols), min(rows); nr = max(rows)-r0+2
    canvas = Image.new('RGBA', (int((max(cols)-c0+2)*CP+600), int(nr*RP+2000)), (0, 0, 0, 255))
    def p(c, r): x, y = pos(c-c0, r-r0, 1, nr, c & 1); return x, y
    for c in cols:
        for r in rows: canvas.alpha_composite(Image.open(f'{TD}/SV_K_{c}_{r}.png'), p(c, r))
    fx, fy = p(*focus[:2]); fx += 1000+ (CP/2 if focus[2] else 0); fy += 1000
    canvas.crop((int(fx-700), int(fy-500), int(fx+700), int(fy+500))).convert('RGB').save(name, quality=90)
if __name__ == '__main__':
    W = int(COLS*CP/16+200); H = int((ROWS+1)*RP/16+200)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    with Pool(6) as pl:
        for (c, r), t in pl.imap_unordered(small, [(c, r) for c in range(COLS) for r in range(ROWS)], chunksize=16):
            im.alpha_composite(t, pos(c, r, 1/16))
    im.convert('RGB').save('previews/reassembled_from_tiles.jpg', quality=88)
    # seam closeups: focus on the shared edge east of (c,r) (third elem True => centre on the E-side edge)
    closeup(range(14, 18), range(21, 25), (15, 23, True), 'previews/seam_closeup_stone_wall.jpg')
    closeup(range(5, 9), range(4, 8), (6, 6, True), 'previews/seam_closeup_pike_road.jpg')
