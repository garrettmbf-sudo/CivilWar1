#!/usr/bin/env python3
"""PNG previews of a Must Attack scenario JSON, drawn the way the board is assembled from the file:
meta.boardArt image (if any) placed with its own origin/scale, the hex grid at meta.boardArt
grid/gridAlpha, hex names, VP (star: blue Union / grey Confederate / white neutral start) and
CP (diamond) markers, fences, and each unit's own template renderedUrl counter (30x30 world units,
the stock counter size).  This is an approximation of the game's renderer, not a screenshot.

usage: render_preview.py scenario.json out.png [zoom_out.png counters_out.png]
"""
import base64, io, json, math, os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ma_grid import neighbor

Image.MAX_IMAGE_PIXELS = None
COL = {"plain": (206, 210, 160), "forest": (96, 128, 72), "mountain": (200, 172, 118), "rough": (120, 118, 74),
       "marsh": (150, 175, 165), "city": (170, 150, 140), "wasteland": (180, 130, 100), "fortress": (150, 140, 128)}
FB = "/usr/share/fonts/truetype/sand-box/google/IM Fell English SC/IMFellEnglishSC-Regular.ttf"
FD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SQ3 = math.sqrt(3)
HR = 45.0  # world hex radius (boardArt.hexSize)


def img_of(url):
    return Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))).convert("RGBA")


def render(s, out, sc=0.6, crop=None, legend=True):
    """sc = output px per world unit; crop = (q0, r0, q1, r1) inclusive hex window."""
    hexes = s["scenario"]["map"]["hexes"]
    W, H = s["scenario"]["map"]["width"], s["scenario"]["map"]["height"]
    def C(q, r):
        return SQ3 * HR * (q + 0.5 * (r & 1)), 1.5 * HR * r
    if crop:
        q0, r0, q1, r1 = crop
        wx0, wy0 = C(q0, r0)[0] - SQ3 * HR, C(q0, r0)[1] - 1.2 * HR
        wx1, wy1 = C(q1, r1)[0] + SQ3 * HR, C(q1, r1)[1] + 1.2 * HR
    else:
        wx0, wy0 = -SQ3 * HR / 2 - 13.5, -HR - 13.5
        wx1, wy1 = SQ3 * HR * (W + 0.5) - SQ3 * HR / 2 + 13.5, 1.5 * HR * (H - 1) + HR + 13.5
    P = lambda x, y: ((x - wx0) * sc, (y - wy0) * sc)
    img = Image.new("RGBA", (int((wx1 - wx0) * sc), int((wy1 - wy0) * sc) + (70 if legend else 0)), (250, 248, 240, 255))
    ba = s["meta"].get("boardArt")
    d = ImageDraw.Draw(img)
    if ba:
        art = img_of(ba["image"])
        k = sc / ba["scale"]
        ax, ay = P(ba["originX"], ba["originY"])
        if crop:
            box = (int((wx0 - ba["originX"]) * ba["scale"]), int((wy0 - ba["originY"]) * ba["scale"]),
                   int((wx1 - ba["originX"]) * ba["scale"]), int((wy1 - ba["originY"]) * ba["scale"]))
            art = art.crop(box)
            ax, ay = 0, 0
        art = art.resize((max(1, int(art.width * k)), max(1, int(art.height * k))), Image.LANCZOS)
        img.alpha_composite(art, (int(ax), int(ay)))
        gc = tuple(int(ba["grid"][i:i + 2], 16) for i in (1, 3, 5)) + (int(255 * ba["gridAlpha"]),)
    else:
        gc = (150, 150, 130, 255)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    o = ImageDraw.Draw(ov)
    def corner(c, i):
        a = math.radians(-30 + 60 * i)
        return c[0] + HR * sc * math.cos(a), c[1] + HR * sc * math.sin(a)
    for h in hexes:
        c = P(*C(h["q"], h["r"]))
        poly = [corner(c, i) for i in range(6)]
        if not ba:
            o.polygon(poly, fill=COL.get(h["terrainId"], (255, 0, 255)) + (255,))
        o.polygon(poly, outline=gc)
        if not ba:
            for key, col, wd in (("rivers", (40, 110, 200), 3), ("trails", (150, 110, 70), 2), ("roads", (120, 70, 30), 3)):
                for e in h[key]:
                    n = P(*C(*neighbor(h["q"], h["r"], e)))
                    o.line([c, ((c[0] + n[0]) / 2, (c[1] + n[1]) / 2)], fill=col + (255,), width=wd)
            for e in h["fences"]:
                o.line([corner(c, e), corner(c, (e + 1) % 6)], fill=(90, 80, 70, 255), width=4)
    img.alpha_composite(ov)
    d = ImageDraw.Draw(img)
    fn = ImageFont.truetype(FB, max(9, int(15 * sc)))
    for h in hexes:
        c = P(*C(h["q"], h["r"]))
        if h["isVPLocation"]:
            ic = h["initialControl"]
            col = {0: (37, 58, 105), 1: (120, 116, 104), None: (250, 250, 250)}[ic]
            d.regular_polygon((c[0], c[1] - HR * sc * 0.05, HR * sc * 0.3), 5, fill=col, outline=(20, 20, 20))
        if h["pp"]["first"]:
            d.regular_polygon((c[0], c[1], HR * sc * 0.28), 4, rotation=45, fill=(150, 60, 170), outline=(20, 20, 20))
        if h["name"]:
            lab = h["name"] + (f'  {h["vp"]["first"]}' if h["isVPLocation"] else "") + (f'  CP+{h["pp"]["first"]}' if h["pp"]["first"] else "")
            d.text((c[0], c[1] + HR * sc * 0.7), lab, font=fn, anchor="mm", fill=(30, 24, 18), stroke_width=2, stroke_fill=(246, 240, 224))
    tm = {t["id"]: t for t in s["assets"]["unitTemplates"]}
    stack = {}
    cs = int(30 * sc)
    for u in s["scenario"]["units"]:
        k = (u["q"], u["r"])
        if crop and not (crop[0] <= k[0] <= crop[2] and crop[1] <= k[1] <= crop[3]):
            continue
        i = stack.get(k, 0); stack[k] = i + 1
        c = P(*C(*k))
        ci = img_of(tm[u["templateId"]]["visuals"]["renderedUrl"]).resize((cs, cs), Image.LANCZOS)
        sh = Image.new("RGBA", (cs, cs), (0, 0, 0, 90))
        x, y = int(c[0] - cs / 2 + i * cs * 0.18), int(c[1] - cs / 2 - cs * 0.15 + i * cs * 0.18)
        img.alpha_composite(sh, (x + 2, y + 2))
        img.alpha_composite(ci, (x, y))
        if u["standbyGroup"]:
            d.text((x + cs - 2, y + 2), "S%d" % u["standbyGroup"], font=ImageFont.truetype(FD, max(8, int(7 * sc))),
                   anchor="ra", fill=(200, 20, 20), stroke_width=1, stroke_fill=(255, 255, 255))
    if legend:
        f = ImageFont.truetype(FD, 13)
        y0 = img.height - 55
        d.text((14, y0), s["meta"]["scenarioName"] + f"  {W}x{H} hexes, {s['meta']['scaleMeters']} m/hex."
               "  Star = VP (blue Union / grey Confederate / white neutral start), diamond = CP, S# = standby group.", font=f, fill=(0, 0, 0))
        d.text((14, y0 + 22), "Preview assembled from the file (boardArt + grid + hex names + unit renderedUrl counters); not an in-game screenshot.", font=f, fill=(60, 60, 60))
    img.convert("RGB").save(out, optimize=True)
    return out


def counter_sheet(s, out):
    tm = {t["id"]: t for t in s["assets"]["unitTemplates"]}
    us = s["scenario"]["units"]
    n = 7
    cell = 200
    sheet = Image.new("RGB", (n * cell + 20, ((len(us) + n - 1) // n) * cell + 20), (232, 226, 210))
    for i, u in enumerate(us):
        ci = img_of(tm[u["templateId"]]["visuals"]["renderedUrl"]).resize((180, 180), Image.LANCZOS)
        sheet.paste(ci, (10 + (i % n) * cell + 10, 10 + (i // n) * cell + 10), ci)
    sheet.save(out, optimize=True)
    return out


if __name__ == "__main__":
    s = json.load(open(sys.argv[1]))
    print(render(s, sys.argv[2], 0.5))
    if len(sys.argv) > 3:
        print(render(s, sys.argv[3], 1.6, crop=(6, 13, 21, 25)))
    if len(sys.argv) > 4:
        print(counter_sheet(s, sys.argv[4]))
