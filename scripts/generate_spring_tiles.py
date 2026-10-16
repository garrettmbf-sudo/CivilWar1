#!/usr/bin/env python3
"""Fast early-spring Shenandoah tiles for Hex of Steel (2000x2000 flat-top hex PNG)."""
from __future__ import annotations
import math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MASK = Image.open(ROOT / "data" / "hex_mask.png").convert("L")
SIZE = 2000
CX = CY = SIZE / 2
R = 955.0

PAL = {
    "field_tan": (186, 158, 112),
    "field_brown": (148, 118, 78),
    "dormant_grass": (156, 138, 96),
    "mud": (120, 96, 70),
    "limestone": (168, 166, 158),
    "limestone_dark": (130, 128, 120),
    "bare_wood": (92, 78, 58),
    "dead_wood": (70, 62, 52),
    "bark": (78, 58, 42),
    "redbud": (148, 88, 128),
    "redbud_light": (180, 120, 160),
    "water": (78, 102, 118),
    "water_deep": (48, 72, 92),
    "water_edge": (140, 150, 140),
    "road": (120, 100, 72),
    "road_edge": (90, 72, 50),
    "rail": (48, 44, 40),
    "stone_wall": (150, 148, 140),
    "roof": (110, 70, 55),
    "roof_slate": (90, 92, 98),
    "brick": (140, 100, 80),
    "whitewash": (210, 200, 180),
    "hill_lit": (170, 145, 105),
    "hill_shade": (110, 88, 60),
    "shadow": (60, 50, 38),
}
VARIANTS = {
    1: (0, 3), 2: (1, 4), 3: (2, 5), 4: (0, 2), 5: (1, 3),
    6: (2, 4), 7: (3, 5), 8: (0, 4), 9: (1, 5),
}

def hex_points(cx, cy, r):
    return [(cx + r * math.cos(math.radians(60 * i)), cy + r * math.sin(math.radians(60 * i))) for i in range(6)]

def edge_point(cx, cy, r, edge, t=0.5):
    pts = hex_points(cx, cy, r)
    a, b = pts[edge], pts[(edge + 1) % 6]
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

def apply_mask(im):
    im = im.convert("RGBA")
    im.putalpha(MASK)
    return im

def base_field(seed=0, relief=0.0):
    rng = np.random.default_rng(seed)
    # generate small noise then upscale (fast)
    s = 250
    n = rng.random((s, s))
    n = Image.fromarray((n * 255).astype(np.uint8), "L").resize((SIZE, SIZE), Image.Resampling.BICUBIC)
    n = np.asarray(n).astype(np.float32) / 255.0
    yy, xx = np.ogrid[0:SIZE, 0:SIZE]
    shade = 1.0 + relief * ((CX - xx) / SIZE * 0.35 + (CY - yy) / SIZE * 0.45)
    tan = np.array(PAL["field_tan"], np.float32)
    brn = np.array(PAL["field_brown"], np.float32)
    rgb = tan * (1 - n)[..., None] + brn * n[..., None]
    rgb *= shade[..., None]
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    alpha = np.full((SIZE, SIZE, 1), 255, np.uint8)
    im = Image.fromarray(np.concatenate([rgb, alpha], 2), "RGBA")
    d = ImageDraw.Draw(im)
    rr = random.Random(seed)
    for _ in range(700):
        x, y = rr.randint(100, SIZE - 100), rr.randint(220, SIZE - 220)
        col = PAL["dormant_grass"] if rr.random() < 0.7 else PAL["mud"]
        d.ellipse((x, y, x + rr.randint(2, 5), y + rr.randint(2, 4)), fill=col + (255,))
    return im

def add_limestone(im, seed=1, count=14):
    rng = random.Random(seed)
    d = ImageDraw.Draw(im)
    for _ in range(count):
        x, y = rng.randint(320, SIZE - 320), rng.randint(420, SIZE - 420)
        w, h = rng.randint(16, 48), rng.randint(8, 24)
        d.polygon([(x, y), (x + w, y - 2), (x + w + 3, y + h), (x - 2, y + h + 1)],
                  fill=PAL["limestone"] + (255,), outline=PAL["limestone_dark"] + (255,))

def add_trees(im, seed=2, bare=30, dead=8, redbud=6):
    rng = random.Random(seed)
    d = ImageDraw.Draw(im)
    def trunk(x, y, h, lean=0):
        d.line([(x, y), (x + lean, y - h)], fill=PAL["bark"] + (255,), width=rng.randint(2, 4))
        for _ in range(rng.randint(3, 5)):
            ang = rng.uniform(-1.0, 1.0)
            bl = h * rng.uniform(0.25, 0.5)
            d.line([(x + lean * 0.4, y - h * 0.55),
                    (x + lean * 0.4 + math.sin(ang) * bl, y - h * 0.55 - abs(math.cos(ang)) * bl * 0.35)],
                   fill=PAL["bare_wood"] + (255,), width=1)
    for _ in range(bare):
        trunk(rng.randint(280, SIZE - 280), rng.randint(380, SIZE - 380), rng.randint(36, 85), rng.randint(-8, 8))
    for _ in range(dead):
        x, y = rng.randint(280, SIZE - 280), rng.randint(380, SIZE - 380)
        h = rng.randint(28, 65)
        d.line([(x, y), (x, y - h)], fill=PAL["dead_wood"] + (255,), width=3)
        d.line([(x, y - h * 0.55), (x - 16, y - h * 0.8)], fill=PAL["dead_wood"] + (255,), width=2)
        d.line([(x, y - h * 0.45), (x + 14, y - h * 0.75)], fill=PAL["dead_wood"] + (255,), width=2)
    for _ in range(redbud):
        x, y = rng.randint(300, SIZE - 300), rng.randint(400, SIZE - 400)
        h = rng.randint(32, 60)
        trunk(x, y, h, rng.randint(-4, 4))
        for _ in range(rng.randint(8, 18)):
            bx, by = x + rng.randint(-20, 20), y - h + rng.randint(-6, 22)
            d.ellipse((bx, by, bx + 5, by + 4), fill=PAL["redbud"] + (230,))

def add_stone_wall(im, edges=(5, 2), seed=3):
    d = ImageDraw.Draw(im)
    a = edge_point(CX, CY, R * 0.92, edges[0])
    b = edge_point(CX, CY, R * 0.92, edges[1])
    d.line([a, b], fill=PAL["stone_wall"] + (255,), width=14)
    d.line([a, b], fill=PAL["limestone_dark"] + (255,), width=4)
    rng = random.Random(seed)
    for i in range(1, 18):
        t = i / 18
        x = a[0] + (b[0] - a[0]) * t
        y = a[1] + (b[1] - a[1]) * t
        d.rectangle((x - 4, y - 5, x + 4, y + 5), fill=PAL["limestone"] + (255,), outline=PAL["limestone_dark"] + (255,))

def link(d, edges, bank, core, bank_w, core_w):
    a, b = edges
    p1 = edge_point(CX, CY, R * 0.98, a)
    p2 = edge_point(CX, CY, R * 0.98, b)
    d.line([p1, p2], fill=bank, width=bank_w)
    d.line([p1, p2], fill=core, width=core_w)
    return p1, p2

def paint_plain(seed=10):
    im = base_field(seed, 0.05); add_limestone(im, seed+1, 10); add_trees(im, seed+2, 16, 5, 4); return apply_mask(im)

def paint_forest(seed=20, thick=False):
    im = base_field(seed, 0.08)
    add_trees(im, seed+2, 65 if thick else 40, 16 if thick else 9, 6 if thick else 9)
    add_limestone(im, seed+3, 7); return apply_mask(im)

def paint_hill(seed=30, forest=False):
    im = base_field(seed, 0.55)
    d = ImageDraw.Draw(im)
    for i in range(6):
        y = 750 + i * 50
        d.arc((380, y - 220, 1620, y + 220), 200, 340, fill=(PAL["hill_lit"] if i < 3 else PAL["hill_shade"]) + (50,), width=28)
    add_limestone(im, seed+1, 20)
    add_trees(im, seed+2, 32 if forest else 12, 9 if forest else 4, 4)
    return apply_mask(im)

def paint_river(v, seed=40):
    im = base_field(seed+v, 0.05); d = ImageDraw.Draw(im)
    e = VARIANTS.get(v, (0, 3))
    link(d, e, PAL["water_edge"]+(255,), PAL["water"]+(255,), 70, 42)
    link(d, e, PAL["water"]+(180,), PAL["water_deep"]+(255,), 28, 14)
    add_trees(im, seed+2, 8, 3, 2); return apply_mask(im)

def paint_road(v, seed=50, pike=False):
    im = base_field(seed+v, 0.05); d = ImageDraw.Draw(im)
    e = VARIANTS.get(v, (0, 3))
    if pike:
        link(d, e, PAL["road_edge"]+(255,), PAL["road"]+(255,), 40, 24)
        p1, p2 = edge_point(CX, CY, R*0.98, e[0]), edge_point(CX, CY, R*0.98, e[1])
        d.line([p1, p2], fill=(160, 140, 100, 200), width=4)
    else:
        link(d, e, PAL["road_edge"]+(255,), PAL["road"]+(255,), 28, 16)
        add_trees(im, seed+2, 7, 2, 2)
    return apply_mask(im)

def paint_rail(v, seed=60):
    im = base_field(seed+v, 0.04); d = ImageDraw.Draw(im)
    e = VARIANTS.get(v, (0, 3))
    p1, p2 = link(d, e, (80, 70, 55, 255), PAL["rail"]+(255,), 18, 8)
    for i in range(1, 14):
        t = i / 14
        mx, my = p1[0]+(p2[0]-p1[0])*t, p1[1]+(p2[1]-p1[1])*t
        ang = math.atan2(p2[1]-p1[1], p2[0]-p1[0]) + math.pi/2
        L = 14
        d.line([(mx-math.cos(ang)*L, my-math.sin(ang)*L), (mx+math.cos(ang)*L, my+math.sin(ang)*L)],
               fill=PAL["rail"]+(255,), width=3)
    return apply_mask(im)

def paint_bridge(v, seed=70):
    im = paint_river(v, seed); d = ImageDraw.Draw(im)
    a = VARIANTS.get(v, (0, 3))[0]
    link(d, ((a+1)%6, (a+4)%6), PAL["road_edge"]+(255,), (200, 185, 150, 255), 34, 20)
    return apply_mask(im)

def paint_stone_wall_hex(seed=80):
    im = base_field(seed, 0.2); add_stone_wall(im); add_trees(im, seed+2, 14, 5, 3); add_limestone(im, seed+1, 10)
    return apply_mask(im)

def paint_town(kind="village", seed=90):
    im = base_field(seed, 0.05); d = ImageDraw.Draw(im); rng = random.Random(seed)
    if kind == "city":
        for i in range(-2, 3):
            d.line([(CX-280, CY+i*55), (CX+280, CY+i*55)], fill=PAL["road"]+(180,), width=6)
            d.line([(CX+i*70, CY-220), (CX+i*70, CY+220)], fill=PAL["road"]+(180,), width=5)
        buildings, spread = 14, 220
    else:
        buildings, spread = 6, 140
        d.line([(CX-160, CY+20), (CX+160, CY+20)], fill=PAL["road"]+(200,), width=8)
    for _ in range(buildings):
        x = CX + rng.randint(-spread, spread); y = CY + rng.randint(-spread+20, spread-20)
        w, h = rng.randint(28, 55), rng.randint(22, 40)
        wall = PAL["whitewash"] if rng.random() < 0.55 else PAL["brick"]
        d.rectangle((x, y, x+w, y+h), fill=wall+(255,), outline=PAL["shadow"]+(255,))
        roof = PAL["roof"] if rng.random() < 0.7 else PAL["roof_slate"]
        d.polygon([(x-3, y), (x+w/2, y-18), (x+w+3, y)], fill=roof+(255,))
        if rng.random() < 0.7:
            d.rectangle((x+8, y+10, x+16, y+18), fill=(60, 70, 80, 255))
    if kind == "church":
        d.rectangle((CX-18, CY-10, CX+18, CY+40), fill=PAL["whitewash"]+(255,))
        d.polygon([(CX-28, CY-10), (CX, CY-55), (CX+28, CY-10)], fill=PAL["roof"]+(255,))
        d.rectangle((CX-4, CY-70, CX+4, CY-55), fill=PAL["limestone_dark"]+(255,))
    add_trees(im, seed+2, 7, 2, 5)
    return apply_mask(im)

def main():
    out_summer = ROOT / "mod" / "Graphics" / "Tiles" / "Summer"
    out_spring = ROOT / "mod" / "Graphics" / "Tiles" / "Spring"
    out_summer.mkdir(parents=True, exist_ok=True)
    out_spring.mkdir(parents=True, exist_ok=True)
    jobs = {
        "SV_Plain": paint_plain(11), "SV_Plain2": paint_plain(12), "SV_Plain3": paint_plain(13),
        "SV_ThinForest": paint_forest(21, False), "SV_ThinForest2": paint_forest(22, False),
        "SV_ThickForest": paint_forest(31, True),
        "SV_Hill": paint_hill(41, False), "SV_Hill2": paint_hill(42, False),
        "SV_HillForest": paint_hill(43, True),
        "SV_SandyRidge": paint_hill(44, True), "SV_PritchardsHill": paint_hill(45, False),
        "SV_StoneWall": paint_stone_wall_hex(50),
        "SV_Village": paint_town("village", 500), "SV_Village2": paint_town("village", 501),
        "SV_Town": paint_town("city", 510),
        "SV_WinchesterBlock": paint_town("city", 520),
        "SV_WinchesterBlock2": paint_town("city", 521),
        "SV_WinchesterBlock3": paint_town("city", 522),
        "SV_Church": paint_town("church", 530), "SV_Kernstown": paint_town("village", 540),
        "SV_River6Bridge": paint_bridge(6, 400), "SV_River1Bridge": paint_bridge(1, 401),
    }
    for v in range(1, 10):
        jobs[f"SV_River{v}"] = paint_river(v, 100+v)
        jobs[f"SV_Road{v}"] = paint_road(v, 200+v, False)
        jobs[f"SV_ValleyPike{v}"] = paint_road(v, 250+v, True)
        jobs[f"SV_Railroad{v}"] = paint_rail(v, 300+v)
    for name, im in jobs.items():
        for folder in (out_summer, out_spring):
            im.save(folder / f"{name}.png", optimize=True)
        print("tile", name, flush=True)
    names = ["SV_Plain","SV_ThinForest","SV_ThickForest","SV_Hill","SV_SandyRidge","SV_PritchardsHill",
             "SV_River6","SV_ValleyPike1","SV_Railroad1","SV_StoneWall","SV_Church","SV_WinchesterBlock",
             "SV_Kernstown","SV_River6Bridge"]
    cell = 220
    sheet = Image.new("RGBA", (cell*len(names), cell), (40, 36, 32, 255))
    for i, n in enumerate(names):
        sheet.alpha_composite(jobs[n].resize((cell, cell), Image.Resampling.LANCZOS), (i*cell, 0))
    (ROOT/"previews").mkdir(exist_ok=True)
    sheet.convert("RGB").save(ROOT/"previews"/"tile_contact_sheet.jpg", quality=92)
    print("DONE", len(jobs), "tiles")

if __name__ == "__main__":
    main()
