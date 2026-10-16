#!/usr/bin/env python3
"""Semi-photorealistic hand-drawn oblique objects for the continuous basemap.

Viewpoint: from the south (camera looks north). Verticals rise toward -Y (north)
so tall trees/buildings loom over the hex behind. Light from NW → soft SE shadows.
Each instance is seeded by position so no two are identical stamps.

Overflow strategy: bake into continuous basemap; unique SV_K_* hex slices pick up
northward overhang in the northern neighbor automatically (see docs/hos_tile_overflow.md).
"""
from __future__ import annotations
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

def _rng(x, y, salt=0):
    return np.random.default_rng(abs(hash((round(x, 1), round(y, 1), salt))) % (2**32))

def _shadow(d, poly, alpha=55):
    d.polygon(poly, fill=(40, 32, 22, alpha))

def oblique_tree(d, x, y, *, h=None, bare=True, redbud=False, snag=False, salt=0):
    """Tall hand-drawn tree. Foot at (x,y); crown rises north (-y). Unique per seed."""
    r = _rng(x, y, salt)
    h = h if h is not None else float(r.uniform(22, 38))  # modest height — counters must stay readable
    lean = float(r.uniform(-0.08, 0.08))
    # SE shadow on ground
    _shadow(d, [(x-4, y+2), (x+h*0.35+6, y+h*0.15+4), (x+h*0.25, y+6), (x-2, y+5)], 45)
    # trunk — thick base, thinner top, slight lean toward N with lean
    trunk_col = (int(48+r.integers(0, 20)), int(38+r.integers(0, 14)), int(28+r.integers(0, 10)), 255)
    ink = (32, 26, 20, 255)
    top_x, top_y = x + lean * h, y - h
    # trunk as tapered quad
    bw = float(r.uniform(2.2, 3.8))
    tw = float(r.uniform(0.8, 1.4))
    trunk = [(x-bw, y), (x+bw, y), (top_x+tw, top_y+2), (top_x-tw, top_y+2)]
    d.polygon(trunk, fill=trunk_col, outline=ink)
    # bark hint lines
    for i in range(int(r.integers(2, 5))):
        t = 0.2 + 0.15*i
        bx = x*(1-t) + top_x*t + float(r.uniform(-0.8, 0.8))
        by = y*(1-t) + top_y*t
        d.line([(bx, by), (bx+float(r.uniform(-0.5,0.5)), by-h*0.08)], fill=(30,24,18,180), width=1)
    if snag:
        # broken top
        d.line([(top_x, top_y+8), (top_x-8, top_y-4)], fill=trunk_col, width=2)
        d.line([(top_x, top_y+10), (top_x+7, top_y)], fill=ink, width=1)
        return
    # scaffold branches rising into crown (north)
    n_main = int(r.integers(5, 9))
    for i in range(n_main):
        t = 0.35 + 0.55 * i / max(1, n_main-1)
        bx = x*(1-t) + top_x*t
        by = y*(1-t) + top_y*t
        side = -1 if i % 2 == 0 else 1
        length = h * float(r.uniform(0.18, 0.38))
        ang = -math.pi/2 + side * float(r.uniform(0.4, 1.1))  # mostly upward
        ex = bx + math.cos(ang) * length
        ey = by + math.sin(ang) * length
        d.line([(bx, by), (ex, ey)], fill=ink, width=max(1, int(2.2*(1-t)+1)))
        # secondary twigs
        for _ in range(int(r.integers(2, 5))):
            tt = float(r.uniform(0.3, 0.9))
            mx, my = bx+(ex-bx)*tt, by+(ey-by)*tt
            a2 = ang + float(r.uniform(-0.7, 0.7))
            L2 = length * float(r.uniform(0.25, 0.55))
            d.line([(mx, my), (mx+math.cos(a2)*L2, my+math.sin(a2)*L2)], fill=(40, 34, 28, 220), width=1)
    # crown mass — layered irregular ellipses (gray-brown bare canopy), drawn north of foot
    if bare:
        cx, cy = top_x, top_y + h*0.08
        for k in range(int(r.integers(4, 7))):
            ox = float(r.uniform(-h*0.22, h*0.22))
            oy = float(r.uniform(-h*0.18, h*0.12))
            rw = h * float(r.uniform(0.12, 0.22))
            rh = h * float(r.uniform(0.10, 0.18))
            g = int(r.integers(-12, 12))
            col = (110+g, 98+g, 82+g, int(r.integers(70, 120)))
            d.ellipse((cx+ox-rw, cy+oy-rh, cx+ox+rw, cy+oy+rh), fill=col)
        # ink branch tips over wash
        for _ in range(int(r.integers(8, 14))):
            a = float(r.uniform(-math.pi*0.9, -math.pi*0.1))
            L = h * float(r.uniform(0.12, 0.28))
            d.line([(cx, cy), (cx+math.cos(a)*L, cy+math.sin(a)*L)], fill=ink, width=1)
    if redbud:
        cx, cy = top_x, top_y + h*0.05
        for _ in range(int(r.integers(10, 18))):
            a = float(r.uniform(-math.pi, 0))
            L = h * float(r.uniform(0.08, 0.22))
            px, py = cx+math.cos(a)*L, cy+math.sin(a)*L
            # small bloom clusters as tiny crosses/petals — not big dots
            bloom = (150, 78, 120, 230)
            d.line([(px-1.5, py), (px+1.5, py)], fill=bloom, width=1)
            d.line([(px, py-1.5), (px, py+1.5)], fill=bloom, width=1)
            d.line([(px-1, py-1), (px+1, py+1)], fill=(170, 100, 140, 180), width=1)

def oblique_house(d, x, y, *, w=None, depth=None, wall=None, roof=None, salt=0):
    """Farmhouse: south facade + roof rising north. Unique proportions/colors."""
    r = _rng(x, y, salt+11)
    w = w or float(r.uniform(18, 28))
    depth = depth or float(r.uniform(12, 20))  # modest northward rise
    h_eave = float(r.uniform(9, 13))
    h_ridge = h_eave + float(r.uniform(5, 9))
    wall = wall or (int(r.integers(140, 175)), int(r.integers(70, 100)), int(r.integers(55, 80)), 255)
    if r.random() < 0.35:  # limestone
        wall = (int(r.integers(160, 185)), int(r.integers(156, 178)), int(r.integers(145, 165)), 255)
    roof = roof or (int(r.integers(85, 115)), int(r.integers(60, 85)), int(r.integers(45, 65)), 255)
    ink = (28, 22, 16, 255)
    # SE ground shadow
    _shadow(d, [(x-w/2, y+2), (x+w/2+8, y+4), (x+w/2+depth*0.3, y-depth*0.2), (x-w/2+4, y-2)], 50)
    # south facade (front)
    facade = [(x-w/2, y), (x+w/2, y), (x+w/2, y-h_eave), (x-w/2, y-h_eave)]
    d.polygon(facade, fill=wall, outline=ink)
    # door
    dw = w*0.18; dh = h_eave*0.55
    d.rectangle((x-dw/2, y-dh, x+dw/2, y), fill=(50, 38, 28, 255), outline=ink)
    # windows
    for wx in (-w*0.28, w*0.28):
        ww, wh = w*0.12, h_eave*0.28
        d.rectangle((x+wx-ww/2, y-h_eave*0.75, x+wx+ww/2, y-h_eave*0.75+wh),
                    fill=(180, 200, 210, 220), outline=ink)
        d.line([(x+wx, y-h_eave*0.75), (x+wx, y-h_eave*0.75+wh)], fill=ink, width=1)
    # roof: south eave → north ridge (isometric-ish)
    ridge_y = y - h_ridge - depth*0.55
    ridge_x = x + float(r.uniform(-1, 1))
    roof_poly = [
        (x-w/2-1, y-h_eave), (x+w/2+1, y-h_eave),
        (ridge_x+w*0.15, ridge_y), (ridge_x-w*0.15, ridge_y),
    ]
    d.polygon(roof_poly, fill=roof, outline=ink)
    # north roof face (darker)
    dark = tuple(max(0, c-35) for c in roof[:3])+(255,)
    d.polygon([(x-w/2-1, y-h_eave), (ridge_x-w*0.15, ridge_y),
               (ridge_x-w*0.05, ridge_y-depth*0.15), (x-w/2+2, y-h_eave-depth*0.35)],
              fill=dark, outline=ink)
    # chimney
    if r.random() < 0.7:
        cx = x + w*float(r.uniform(-0.25, 0.25))
        d.rectangle((cx-2, ridge_y-10, cx+2, ridge_y+2), fill=(120, 70, 55, 255), outline=ink)

def oblique_barn(d, x, y, *, salt=0):
    r = _rng(x, y, salt+22)
    w = float(r.uniform(24, 36))
    depth = float(r.uniform(14, 22))
    h_eave = float(r.uniform(11, 15))
    h_ridge = h_eave + float(r.uniform(6, 10))
    wall = (int(r.integers(100, 140)), int(r.integers(70, 100)), int(r.integers(45, 70)), 255)
    roof = (int(r.integers(90, 120)), int(r.integers(70, 95)), int(r.integers(50, 70)), 255)
    ink = (28, 22, 16, 255)
    _shadow(d, [(x-w/2, y+3), (x+w/2+10, y+5), (x+w/2, y-4), (x-w/2, y)], 50)
    d.polygon([(x-w/2, y), (x+w/2, y), (x+w/2, y-h_eave), (x-w/2, y-h_eave)], fill=wall, outline=ink)
    # big barn door
    dw = w*0.35
    d.rectangle((x-dw/2, y-h_eave*0.85, x+dw/2, y), fill=(60, 45, 32, 255), outline=ink)
    d.line([(x, y-h_eave*0.85), (x, y)], fill=ink, width=1)
    # loft window
    d.rectangle((x-3, y-h_eave*0.95, x+3, y-h_eave*0.7), fill=(170, 190, 200, 200), outline=ink)
    ridge_y = y - h_ridge - depth*0.5
    d.polygon([(x-w/2-2, y-h_eave), (x+w/2+2, y-h_eave),
               (x+w*0.1, ridge_y), (x-w*0.1, ridge_y)], fill=roof, outline=ink)
    # vertical board lines
    for i in range(int(r.integers(4, 8))):
        bx = x - w/2 + (i+1)*w/(r.integers(5,9))
        d.line([(bx, y), (bx, y-h_eave)], fill=(40, 30, 22, 100), width=1)

def oblique_church(d, x, y, *, salt=0):
    """Opequon Church — limestone body, steeple rising high to the north."""
    r = _rng(x, y, salt+33)
    w = float(r.uniform(22, 30))
    depth = float(r.uniform(14, 20))
    h_eave = 14
    h_ridge = 22
    stone = (172, 168, 156, 255)
    roof = (78, 80, 86, 255)
    ink = (28, 22, 16, 255)
    _shadow(d, [(x-w/2, y+3), (x+w/2+12, y+6), (x+8, y-8), (x-w/2, y)], 55)
    d.polygon([(x-w/2, y), (x+w/2, y), (x+w/2, y-h_eave), (x-w/2, y-h_eave)], fill=stone, outline=ink)
    # arched door
    d.rectangle((x-4, y-10, x+4, y), fill=(45, 35, 28, 255), outline=ink)
    d.arc((x-4, y-14, x+4, y-6), 0, 180, fill=ink, width=1)
    # windows
    for wx in (-w*0.28, w*0.28):
        d.rectangle((x+wx-2.5, y-h_eave+3, x+wx+2.5, y-5), fill=(160, 185, 200, 220), outline=ink)
    ridge_y = y - h_ridge - depth*0.45
    d.polygon([(x-w/2-1, y-h_eave), (x+w/2+1, y-h_eave), (x, ridge_y)], fill=roof, outline=ink)
    # steeple tower — rises far north
    tw = 6
    tower_top = ridge_y - 18
    d.rectangle((x-tw/2, tower_top, x+tw/2, y-h_eave+2), fill=stone, outline=ink)
    d.polygon([(x-tw/2-1, tower_top), (x, tower_top-10), (x+tw/2+1, tower_top)], fill=roof, outline=ink)
    d.line([(x, tower_top-10), (x, tower_top-16)], fill=ink, width=2)  # finial
    # belfry slit
    d.rectangle((x-1.5, tower_top+6, x+1.5, tower_top+12), fill=(40, 40, 45, 255))

def oblique_bridge(d, x, y, *, length=42, angle=0.0, salt=0):
    """Wooden plank bridge over creek — deck + rails, slight 3D."""
    r = _rng(x, y, salt+44)
    ink = (30, 24, 18, 255)
    wood = (120, 88, 58, 255)
    c, s = math.cos(angle), math.sin(angle)
    # deck corners
    hw, hd = length/2, 5
    def rot(px, py):
        return (x + px*c - py*s, y + px*s + py*c)
    deck = [rot(-hw, -hd), rot(hw, -hd), rot(hw, hd), rot(-hw, hd)]
    _shadow(d, [rot(-hw, hd+2), rot(hw+4, hd+4), rot(hw, -hd), rot(-hw, -hd)], 40)
    d.polygon(deck, fill=wood, outline=ink)
    # planks
    for i in range(int(r.integers(6, 10))):
        t = -hw + (i+0.5)*(length/(r.integers(7,11)))
        d.line([rot(t, -hd+1), rot(t, hd-1)], fill=(70, 50, 32, 180), width=1)
    # rails rising slightly north
    for side in (-hd-1, hd+1):
        d.line([rot(-hw, side), rot(hw, side)], fill=ink, width=2)
        for i in range(5):
            t = -hw + i*(length/4)
            d.line([rot(t, side), rot(t, side-9)], fill=ink, width=2)

def oblique_mill(d, x, y, *, salt=0):
    r = _rng(x, y, salt+55)
    oblique_house(d, x, y, w=20, depth=18, wall=(155, 150, 138, 255), roof=(90, 70, 50, 255), salt=salt)
    # water wheel on east side
    ink = (28, 22, 16, 255)
    wx, wy = x+14, y-6
    d.ellipse((wx-8, wy-8, wx+8, wy+8), outline=ink, width=2)
    for a in range(0, 360, 45):
        rad = math.radians(a)
        d.line([(wx, wy), (wx+7*math.cos(rad), wy+7*math.sin(rad))], fill=ink, width=1)

def worm_fence_oblique(d, pts, *, salt=0):
    """Zigzag rail fence with slight vertical posts (rise north a bit)."""
    if len(pts) < 2:
        return
    r = _rng(pts[0][0], pts[0][1], salt+66)
    ink = (36, 28, 20, 255)
    wood = (100, 74, 48, 255)
    for a, b in zip(pts, pts[1:]):
        n = max(2, int(math.hypot(b[0]-a[0], b[1]-a[1]) / 10))
        ang = math.atan2(b[1]-a[1], b[0]-a[0])
        nx, ny = -math.sin(ang), math.cos(ang)
        zz = []
        for i in range(n+1):
            f = i/n
            side = 7 if i % 2 else -7
            px = a[0]+(b[0]-a[0])*f + nx*side*0.5
            py = a[1]+(b[1]-a[1])*f + ny*side*0.5
            zz.append((px, py))
            # short post rising north
            d.line([(px, py), (px+0.5, py-5)], fill=ink, width=1)
        d.line(zz, fill=wood, width=2)
        d.line(zz, fill=ink, width=1)

def paint_scene_objects(base: Image.Image, ll2px, FEAT):
    """Paint unique oblique objects onto continuous basemap (RGBA)."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")

    # --- Wooded ridge: tall unique trees (draw south-to-north so northern crowns layer correctly on basemap;
    #     when hex-sliced, crowns in northern hexes). Sort by y descending (south first). ---
    trees = []
    # Sandy Ridge corridor
    for i, (lon, lat) in enumerate(FEAT["ridge_cores"]["sandy_ridge"]):
        px, py = ll2px(lon, lat)
        for k in range(2):
            trees.append((px + (k-7)*11 + (i%3)*3, py + (k%5)*9 - 20, i*100+k))
    # denser scatter along ridge line
    sw = FEAT["stone_walls"]["glass_wall_sandy_ridge"]["waypoints"]
    for i, (lon, lat) in enumerate(sw[:: max(1, len(sw)//8)]):
        px, py = ll2px(lon, lat)
        trees.append((px + (i%5-2)*8, py + (i%3)*6, 500+i))

    trees.sort(key=lambda t: -t[1])  # south (large y) first; north crowns paint later on top in image... 
    # Actually for basemap we want north objects painted AFTER south so crowns aren't covered by southern trunks.
    # View from S: a northern tree is farther; a southern tree is closer and should occlude.
    # So paint north first (small y), then south (large y) on top.
    trees.sort(key=lambda t: t[1])  # north first
    # COUNTER CLEARANCE: HoS unit counters are large opaque circles (~70% of hex).
    # Nudge trees off hex centers so counters remain readable over continuous terrain.

    # Nudge off hex centers (counters obscure ~70% of hex) + modest heights
    from hex_grid import KERNSTOWN as _G
    def _nudge(tx, ty, salt):
        r = _rng(tx, ty, salt + 999)
        # offset 18–40 px so trunks/detail sit toward hex edges, not under counter
        ang = float(r.uniform(0, 6.28)); rad = float(r.uniform(18, 40))
        return tx + rad * __import__('math').cos(ang), ty + rad * __import__('math').sin(ang) * 0.7

    for i, (tx, ty, salt) in enumerate(trees):
        r = _rng(tx, ty, salt)
        kind_r = r.random()
        tx2, ty2 = _nudge(tx, ty, salt)
        oblique_tree(d, tx2, ty2, h=float(r.uniform(20, 34)),
                     redbud=(kind_r < 0.05), snag=(0.05 <= kind_r < 0.10),
                     bare=True, salt=salt)

    # Open-land specimen trees near farms (fewer, taller character trees)
    for lon, lat, salt in [
        (-78.203, 39.143, 1), (-78.200, 39.139, 2), (-78.210, 39.142, 3),
        (-78.193, 39.141, 4), (-78.215, 39.148, 5), (-78.188, 39.145, 6),
    ]:
        px, py = ll2px(lon, lat)
        oblique_tree(d, px, py, h=34, salt=salt)

    # Farmsteads — unique house+barn+fence+orchard trees
    farms = [
        ("Pritchard", -78.2015, 39.1418, 10),
        ("Glass", -78.2248, 39.1470, 20),
        ("Grim", -78.1990, 39.1375, 30),
        ("Hoge", -78.1860, 39.1430, 40),
        ("Barton", -78.2060, 39.1190, 50),
    ]
    for name, lon, lat, salt in farms:
        px, py = ll2px(lon, lat)
        oblique_house(d, px, py, salt=salt)
        oblique_barn(d, px + 30, py + 6, salt=salt+1)
        worm_fence_oblique(d, [(px-30, py+12), (px+50, py+10), (px+55, py-25)], salt=salt)
        for k in range(5):
            oblique_tree(d, px - 28 + k*14, py + 20, h=28, salt=salt+10+k)

    # Opequon Church + graveyard
    cx, cy = ll2px(-78.1915, 39.1392)
    oblique_church(d, cx, cy, salt=99)
    for k in range(2):
        gx, gy = cx + 16 + k*5, cy + 4
        d.rectangle((gx, gy-4, gx+2, gy), fill=(200, 196, 186, 255), outline=(40, 32, 24, 255))
    worm_fence_oblique(d, [(cx-20, cy+14), (cx+40, cy+12)], salt=100)

    # Bridge / ford on Hoge Run near Pike
    ford = FEAT["fords"][0]
    fx, fy = ll2px(ford["lon"], ford["lat"])
    # estimate creek tangent ~ east-west → bridge N-S-ish across
    oblique_bridge(d, fx, fy - 2, length=40, angle=math.radians(8), salt=77)
    # ford shallows mark beside bridge
    for k in range(-2, 3):
        d.line([(fx-18, fy+8+k*2), (fx+18, fy+8+k*2)], fill=(220, 208, 170, 200), width=1)

    # Mill near Abrams / Winchester approach
    mx, my = ll2px(-78.170, 39.178)
    oblique_mill(d, mx, my, salt=88)

    # Kernstown village buildings — unique small houses
    kx, ky = ll2px(-78.1978, 39.1425)
    for i in range(8):
        oblique_house(d, kx + (i%4)*16 - 22, ky + (i//4)*14 - 8,
                      w=16+i%3, depth=12, salt=200+i)

    # Winchester: leave existing street grid; add a few landmark 3D buildings on top
    wx, wy = ll2px(-78.1633, 39.1857)
    oblique_house(d, wx, wy, w=24, depth=20, wall=(160, 90, 70, 255), salt=300)
    oblique_church(d, wx - 40, wy + 10, salt=301)  # secondary church form as courthouse tower feel

    base = Image.alpha_composite(base, layer)
    return base
