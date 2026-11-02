#!/usr/bin/env python3
"""Render a PNG preview of a Must Attack scenario JSON: terrain colours, roads, trails, creeks,
one-sided fences (drawn on the hexside, with a tick into the owning hex), VP/CP hexes, units."""
import json, math, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, __import__("os").path.dirname(__file__))
from ma_grid import neighbor

COL = {"plain": (196, 205, 150), "forest": (86, 128, 72), "mountain": (196, 168, 112), "rough": (110, 112, 70),
       "marsh": (140, 170, 160), "city": (150, 150, 150), "wasteland": (170, 120, 90), "fortress": (120, 100, 90)}
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def render(path, out, R=26):
    s = json.load(open(path))
    hexes = s["scenario"]["map"]["hexes"]
    W, H = s["scenario"]["map"]["width"], s["scenario"]["map"]["height"]
    w = math.sqrt(3) * R
    def C(q, r):
        return 20 + w * (q + 0.5 * (r & 1)) + w / 2, 20 + 1.5 * R * r + R
    def corner(c, i):  # pointy-top; corner i at angle -90+60i... edge e between corners e and e+1 (from E, cw)
        a = math.radians(-30 + 60 * i)
        return c[0] + R * math.cos(a), c[1] + R * math.sin(a)
    img = Image.new("RGB", (int(40 + w * (W + 0.5)), int(40 + 1.5 * R * H + R / 2) + 60), (250, 248, 240))
    d = ImageDraw.Draw(img)
    f, fb, fs = ImageFont.truetype(FONT, 11), ImageFont.truetype(FONTB, 12), ImageFont.truetype(FONT, 9)
    byid = {(h["q"], h["r"]): h for h in hexes}
    for h in hexes:
        c = C(h["q"], h["r"])
        d.polygon([corner(c, i) for i in range(6)], fill=COL.get(h["terrainId"], (255, 0, 255)), outline=(150, 150, 130))
    # edge e of a pointy-top hex: 0=E between corners -30 and +30 => corners(0..)  with corner(i) at -30+60i:
    # E edge = corner 0 (-30) & corner 1 (+30); SE = 1,2; SW = 2,3; W = 3,4; NW = 4,5; NE = 5,0
    def edge_pts(c, e):
        return corner(c, e), corner(c, (e + 1) % 6)
    for key, col, wd in (("rivers", (40, 110, 200), 4), ("trails", (150, 110, 70), 2), ("roads", (120, 70, 30), 4)):
        for h in hexes:
            c = C(h["q"], h["r"])
            for e in h[key]:
                n = neighbor(h["q"], h["r"], e)
                m = ((c[0] + C(*n)[0]) / 2, (c[1] + C(*n)[1]) / 2)
                d.line([c, m], fill=col, width=wd)
    for h in hexes:
        c = C(h["q"], h["r"])
        for e in h["fences"]:
            a, b = edge_pts(c, e)
            d.line([a, b], fill=(200, 20, 20), width=5)
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            d.line([m, (m[0] + (c[0] - m[0]) * 0.3, m[1] + (c[1] - m[1]) * 0.3)], fill=(200, 20, 20), width=3)
    for h in hexes:
        c = C(h["q"], h["r"])
        if h["isVPLocation"]:
            col = (37, 58, 105) if h["initialControl"] == 0 else (140, 30, 30)
            d.regular_polygon((c[0], c[1], R * 0.55), 5, fill=None, outline=col, width=3)
            d.text((c[0], c[1] - R * 0.95), f'{h["name"]} {h["vp"]["first"]}', font=fb, fill=col, anchor="mm")
        if h["pp"]["first"] or h["pp"]["second"]:
            d.regular_polygon((c[0], c[1], R * 0.45), 4, rotation=45, outline=(120, 0, 160), width=3)
            d.text((c[0], c[1] + R * 0.95), f'CP {h["name"]} +{h["pp"]["first"]}', font=fb, fill=(120, 0, 160), anchor="mm")
    stack = {}
    for u in s["scenario"]["units"]:
        k = (u["q"], u["r"])
        i = stack.get(k, 0); stack[k] = i + 1
        c = C(*k)
        x, y = c[0] - 13 + i * 6, c[1] - 7 + i * 6
        fill = (37, 58, 105) if u["side"] == 0 else (181, 176, 161)
        tc = (255, 255, 255) if u["side"] == 0 else (20, 20, 20)
        d.rectangle([x, y, x + 26, y + 15], fill=fill, outline=(0, 0, 0))
        d.text((x + 13, y + 8), f'{u["combatStrength"]}-{u["movePoints"]}' + (f'r{u["range"]}' if u["range"] > 1 else '') + ('*' if u["standbyGroup"] else ''), font=fs, fill=tc, anchor="mm")
        d.text((x + 13, y + 22), u["boxes"][3], font=fs, fill=(0, 0, 0), anchor="mm")
    for q in range(0, W, 5):
        d.text((C(q, 0)[0], 8), str(q), font=f, fill=(0, 0, 0), anchor="mm")
    for r in range(0, H, 5):
        d.text((8, C(0, r)[1]), str(r), font=f, fill=(0, 0, 0), anchor="mm")
    y0 = img.height - 50
    x = 20
    for k, v in COL.items():
        d.rectangle([x, y0, x + 14, y0 + 14], fill=v); d.text((x + 18, y0 + 7), k, font=f, fill=(0, 0, 0), anchor="lm"); x += 95
    d.text((20, y0 + 30), s["meta"]["scenarioName"] + f"  {W}x{H} hexes, {s['meta']['scaleMeters']} m/hex. Units: CS-MP[rRange], * = standby. Red line = stone-wall fence (tick = owning hex). Star = VP (blue Union / red CSA start), diamond = CP.", font=f, fill=(0, 0, 0))
    img.save(out)
    return out


if __name__ == "__main__":
    print(render(sys.argv[1], sys.argv[2]))
