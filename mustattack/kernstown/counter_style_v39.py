"""v3.9 counter style (opt-in: MA_COUNTER_STYLE=v39).

Only the two shape types the stock scenarios use ("image" and "text", stock keys only).  Every new
mark is a small PIL-drawn RGBA image, like make_nato / make_hq_frame / make_range_badge.  Portraits
are not touched: the builder passes the same portrait imageRef, and HQ and brigade portraits keep
their v3.8.1 x/y/w/h.  Which unit gets which mark is data (counter_style_v39.json, scoped by
staff_notes/quartermaster_counters_v39.md); this file only draws and places.
"""
import json, os, re

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC_PATH = os.path.join(HERE, "counter_style_v39.json")
SS = 4  # supersampling for the small marks

CREAM, INK = (239, 236, 226, 255), (22, 22, 26, 255)
GOLD, GOLD_HI, GOLD_LO = (201, 162, 39, 255), (255, 228, 140, 255), (110, 80, 12, 255)


def rgba(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


# ---------------------------------------------------------------- spec
def _merge(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load_spec(units, path=SPEC_PATH, overrides=None):
    spec = json.load(open(path))
    overrides = overrides if overrides is not None else os.environ.get("MA_COUNTER_OVERRIDES")
    if overrides:
        spec = _merge(spec, json.load(open(overrides)))
    keys = {f"{u[1]}|{u[2]}" for u in units}
    missing, stray = keys - set(spec["units"]), set(spec["units"]) - keys
    assert not missing and not stray, ("counter_style_v39.json out of step with UNITS", sorted(missing), sorted(stray))
    for k, u in spec["units"].items():
        assert u.get("formation") is None or u["formation"] in spec["formations"], (k, u.get("formation"))
        assert u.get("rank") is None or u["rank"] in spec["ranks"], (k, u.get("rank"))
    return spec


# ---------------------------------------------------------------- images
def make_plate(side, spec, px=384):
    """Cloth plate: subtle wool (Union) or jean-cloth (Confederate) weave, rounded corners, a soft rim
    and an engraved double rule (dark cut + light lip).  No gold here: gold marks elite and HQ."""
    p = spec["plates"][str(side)]
    rng = np.random.default_rng(1862 + side)
    yy, xx = np.mgrid[0:px, 0:px].astype(np.float32)
    if p.get("texture"):
        tex = Image.open(os.path.join(HERE, p["texture"])).convert("RGB").resize((px, px), Image.LANCZOS)
        a = np.asarray(tex).astype(np.float32)
    else:
        base = np.array(rgba(p["base"])[:3], np.float32)
        fine = rng.normal(0, 1, (px, px)).astype(np.float32)
        fine = np.asarray(Image.fromarray(((fine * 40) + 128).clip(0, 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(0.6))).astype(np.float32) / 40 - 3.2
        mott = rng.normal(0, 1, (24, 24)).astype(np.float32)
        mott = np.asarray(Image.fromarray(((mott * 40) + 128).clip(0, 255).astype(np.uint8)).resize(
            (px, px), Image.BICUBIC)).astype(np.float32) / 40 - 3.2
        if side == 0:   # 2/2 twill, the diagonal of a wool kersey
            weave = np.sin((xx + yy) * 2 * np.pi / 5.0) * 2.2
        else:           # jean: a cotton warp crossed with a wool weft, a finer and flatter cross-weave
            weave = (np.sin(xx * 2 * np.pi / 4.0) + np.sin(yy * 2 * np.pi / 6.0)) * 1.4
        lum = fine * 3.2 + mott * 2.2 + weave
        a = base[None, None, :] + lum[..., None]
        if side == 1:   # butternut cast in the weft
            a += (np.sin(yy * 2 * np.pi / 6.0) > 0.6)[..., None] * np.array([3.0, 1.5, -2.5], np.float32)
    rim = np.clip((np.maximum(np.abs(xx - px / 2), np.abs(yy - px / 2)) / (px / 2) - 0.80) / 0.2, 0, 1)
    a *= (1 - 0.16 * rim ** 1.5)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im)
    u = px / 30.0
    base = np.array(rgba(p["base"])[:3])
    dark = tuple(int(c) for c in (base * (0.42 if side == 0 else 0.30))) + (255,)
    lite = tuple(int(min(255, c * 1.35 + 30)) for c in base) + (150,)
    for inset, w in ((0.75, 0.32), (1.35, 0.14)):
        o = round(inset * u)
        ww = max(1, round(w * u))
        d.rounded_rectangle([o + 1, o + 1, px - 1 - o + 1, px - 1 - o + 1], radius=round(1.2 * u), outline=lite, width=ww)
        d.rounded_rectangle([o, o, px - 1 - o, px - 1 - o], radius=round(1.2 * u), outline=dark, width=ww)
    mask = Image.new("L", (px * SS, px * SS), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, px * SS - 1, px * SS - 1], radius=round(1.5 * u * SS), fill=255)
    im.putalpha(mask.resize((px, px), Image.LANCZOS))
    return im


def _centre_text(d, xy, text, f, fill):
    """Centre the ink box (Playfair's old-style figures sit low on an "mm" anchor)."""
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    d.text((xy[0] - (l + r) / 2, xy[1] - (t + b) / 2), text, font=f, fill=fill)


def _ss(w, h):
    return Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))


def _down(im):
    return im.resize((im.width // SS, im.height // SS), Image.LANCZOS)


def make_band(f, font, w_units=27.4, h_units=2.2, k=16):
    """Brigade band: a coloured strip with its numeral/letter at the left end (reads without colour)."""
    W, H = round(w_units * k), round(h_units * k)
    im = _ss(W, H)
    d = ImageDraw.Draw(im)
    s = SS
    d.rounded_rectangle([0, 0, W * s - 1, H * s - 1], radius=H * s // 3, fill=rgba(f["band"]), outline=INK, width=s * 2)
    cx = round((w_units / 2 - 12.0) * k) * s   # glyph at x -12.0 on the counter
    r = (H * s) // 2 - s * 2
    ink = rgba(f["ink"])
    fs = H * s * 0.6
    while True:   # size by ink height so old-style "1"/"3" read as large as the capitals "A"/"C"/"F"
        l, t, r, b = d.textbbox((0, 0), f["glyph"], font=font(fs + s, 900))
        if b - t > H * s * 0.74:
            break
        fs += s
    _centre_text(d, (cx, H * s / 2), f["glyph"], font(fs, 900), ink)
    return _down(im)


def make_star(px=48):
    im = _ss(px, px)
    d = ImageDraw.Draw(im)
    c, R = px * SS / 2, px * SS / 2 - SS * 2
    pts = []
    for i in range(10):
        r = R if i % 2 == 0 else R * 0.42
        a = -np.pi / 2 + i * np.pi / 5
        pts.append((c + r * np.cos(a), c + r * np.sin(a) + SS))
    d.polygon(pts, fill=GOLD, outline=GOLD_LO, width=SS * 2)
    return _down(im)


def make_elite_frame(px=384):
    """Gold inner rule, 0.8 counter units, transparent centre (Quartermaster: like make_hq_frame)."""
    im = _ss(px, px)
    d = ImageDraw.Draw(im)
    u = px * SS / 30.0
    o, w = 1.75 * u, 0.8 * u
    d.rounded_rectangle([o, o, px * SS - 1 - o, px * SS - 1 - o], radius=round(1.0 * u), outline=GOLD_LO, width=round(w))
    o2 = o + 0.12 * u
    d.rounded_rectangle([o2, o2, px * SS - 1 - o2, px * SS - 1 - o2], radius=round(0.9 * u), outline=GOLD, width=round(w - 0.24 * u))
    o3 = o + 0.30 * u
    d.rounded_rectangle([o3, o3, px * SS - 1 - o3, px * SS - 1 - o3], radius=round(0.8 * u), outline=GOLD_HI, width=max(1, round(0.08 * u)))
    return _down(im)


def make_hq_frame(w=240, h=274):
    """Gilt frame behind an HQ portrait (same 12.6 x 14.4 slot as v3.8.1): bevelled gold, a dark
    fillet, a bright bead and small corner bosses.  The portrait sits on top unchanged."""
    im = _ss(w, h)
    d = ImageDraw.Draw(im)
    W, H, s = w * SS, h * SS, SS
    steps = 10
    for i in range(steps):   # bevel: light top-left to dark bottom-right
        t = i / (steps - 1)
        col = tuple(int(GOLD_HI[c] * (1 - t) + GOLD_LO[c] * t * 1.4) for c in range(3)) + (255,)
        o = i * s * 1.6
        d.rectangle([o, o, W - 1 - o, H - 1 - o], fill=col)
    d.rectangle([0, 0, W - 1, H - 1], outline=(60, 42, 8, 255), width=s * 3)
    m = 17 * s
    d.rectangle([m, m, W - 1 - m, H - 1 - m], fill=GOLD, outline=(70, 50, 10, 255), width=s * 3)
    m2 = m + 5 * s
    d.rectangle([m2, m2, W - 1 - m2, H - 1 - m2], outline=GOLD_HI, width=s * 2)
    for cx, cy in ((m / 2, m / 2), (W - m / 2, m / 2), (m / 2, H - m / 2), (W - m / 2, H - m / 2)):
        r = 5 * s
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD_HI, outline=(70, 50, 10, 255), width=s * 2)
    return _down(im)


NUM_W, NUM_H, NUM_X, NUM_Y = {1: 5.2, 2: 7.6}, 5.8, 9.4, 9.6


def make_numplate(digits, k=40):
    """Cream cartouche behind CS / MP so the strength reads on the cloth plates."""
    w_units = NUM_W[min(digits, 2)]
    W, H = round(w_units * k), round(NUM_H * k)
    im = _ss(W, H)
    d = ImageDraw.Draw(im)
    s = SS
    d.rounded_rectangle([s * 2, s * 2, W * s - 1 - s * 2, H * s - 1 - s * 2], radius=H * s // 4, fill=CREAM, outline=INK, width=s * 4)
    d.rounded_rectangle([s * 11, s * 11, W * s - 1 - s * 11, H * s - 1 - s * 11], radius=H * s // 6, outline=(160, 150, 128, 255), width=s * 2)
    return _down(im), w_units


def make_text_plate(text, font, w_units, h_units, k=40, strap=None):
    """One routine for the gun and rank plates, styled like make_range_badge (cream, dark rule)."""
    W, H = round(w_units * k), round(h_units * k)
    im = _ss(W, H)
    d = ImageDraw.Draw(im)
    s = SS
    d.rounded_rectangle([s, s, W * s - 1 - s, H * s - 1 - s], radius=H * s // 4, fill=CREAM, outline=INK, width=s * 4)
    x0 = s * 10
    if strap == "eagle":   # 1861 US regs para. 95: colonel's strap, sky-blue (infantry) ground, silver eagle
        sh, sw = H * s * 0.62, H * s * 1.55
        sy0 = (H * s - sh) / 2
        d.rectangle([x0, sy0, x0 + sw, sy0 + sh], fill=(135, 175, 215, 255), outline=GOLD, width=s * 5)
        d.rectangle([x0, sy0, x0 + sw, sy0 + sh], outline=GOLD_LO, width=s * 1)
        ex, ey, eu = x0 + sw / 2, sy0 + sh / 2, sh * 0.30
        silver, sdark = (232, 234, 238, 255), (90, 94, 104, 255)
        d.polygon([(ex - eu * 2.2, ey - eu * 0.9), (ex - eu * 0.4, ey - eu * 0.1), (ex, ey - eu * 0.8),
                   (ex + eu * 0.4, ey - eu * 0.1), (ex + eu * 2.2, ey - eu * 0.9), (ex + eu * 0.9, ey + eu * 0.6),
                   (ex + eu * 0.35, ey + eu * 1.2), (ex - eu * 0.35, ey + eu * 1.2), (ex - eu * 0.9, ey + eu * 0.6)],
                  fill=silver, outline=sdark, width=s)
        x0 = x0 + sw + s * 8
    avail = W * s - x0 - s * 12
    fs = H * s * 0.70
    while fs > 6 and d.textlength(text, font=font(fs, 900)) > avail:
        fs -= s
    _centre_text(d, (x0 + avail / 2, H * s / 2), text, font(fs, 900), INK)
    return _down(im)


def make_colours(side, w_units=6.0, h_units=4.0, k=40):
    """Colours glyph.  Union: a 34-star national colour (13 stripes, the canton as a field of dots, as
    34 stars do not read at this size).  Confederate: staff and a blank flag outline, no pattern."""
    W, H = round(w_units * k), round(h_units * k)
    im = _ss(W, H)
    d = ImageDraw.Draw(im)
    s = SS
    staff_x = W * s * 0.12
    fx0, fy0, fx1, fy1 = staff_x + s * 3, H * s * 0.08, W * s * 0.94, H * s * 0.74
    halo = (242, 238, 226, 255) if side == 1 else (20, 20, 24, 255)
    d.line([(staff_x, H * s * 0.04), (staff_x, H * s * 0.98)], fill=halo, width=s * 14)
    d.line([(staff_x, H * s * 0.04), (staff_x, H * s * 0.98)], fill=(90, 60, 28, 255), width=s * 8)
    d.ellipse([staff_x - s * 8, 0, staff_x + s * 8, s * 16], fill=GOLD)
    if side == 0:
        d.rectangle([fx0 - s * 3, fy0 - s * 3, fx1 + s * 3, fy1 + s * 3], fill=(20, 20, 24, 255))
        sh = (fy1 - fy0) / 13
        for i in range(13):
            d.rectangle([fx0, fy0 + i * sh, fx1, fy0 + (i + 1) * sh], fill=(178, 34, 52, 255) if i % 2 == 0 else (250, 250, 248, 255))
        cx1, cy1 = fx0 + (fx1 - fx0) * 0.42, fy0 + sh * 7
        d.rectangle([fx0, fy0, cx1, cy1], fill=(40, 52, 120, 255))
        for r in range(4):
            for c in range(5):
                x = fx0 + (cx1 - fx0) * (c + 0.5) / 5
                y = fy0 + (cy1 - fy0) * (r + 0.5) / 4
                d.ellipse([x - s * 3, y - s * 3, x + s * 3, y + s * 3], fill=(250, 250, 248, 255))
    else:
        d.rectangle([fx0, fy0, fx1, fy1], outline=halo, width=s * 22)
        d.rectangle([fx0 + s * 4, fy0 + s * 4, fx1 - s * 4, fy1 - s * 4], outline=INK, width=s * 14)
    return _down(im)


def make_images(spec, font):
    out = {"img_v39_plate_us": make_plate(0, spec), "img_v39_plate_cs": make_plate(1, spec),
           "img_v39_elite_frame": make_elite_frame(), "img_v39_star": make_star(),
           "img_v39_hq_frame": make_hq_frame(),
           "img_v39_colours_us": make_colours(0), "img_v39_colours_cs": make_colours(1)}
    for n in (1, 2):
        out[f"img_v39_num{n}"] = make_numplate(n)[0]
    used = {u.get("formation") for u in spec["units"].values()}
    for fid, f in spec["formations"].items():
        if fid in used:
            out[f"img_v39_band_{fid}"] = make_band(f, font)
    for g in sorted({u["guns"] for u in spec["units"].values() if u.get("guns")}):
        out[f"img_v39_guns_{slug(g)}"] = make_text_plate(g, font, 8.0, 3.0)
    for rid in sorted({u["rank"] for u in spec["units"].values() if u.get("rank")}):
        r = spec["ranks"][rid]
        out[f"img_v39_rank_{rid}"] = make_text_plate(r["text"], font, 10.0, 3.0, strap=r.get("strap"))
    return out


# ---------------------------------------------------------------- layout
def template_shapes(side, kind, leader, uname, portrait, elite, cs, mp, spec, nato_keys, text_width_units):
    u = spec["units"][f"{leader}|{uname}"]
    if side == 0:
        col, scol, sw = "#ffffff", "#000000", 0.6
    else:
        col, scol, sw = "#111111", "#f2efe6", 0.4

    def txt(link, z, x, y, fs, fw, c=col, sc=scol, w=sw):
        return {"type": "text", "link": link, "z": z, "x": x, "y": y, "fontSize": fs, "color": c,
                "fontFamily": "Playfair Display", "fontWeight": fw, "strokeWidth": w, "strokeColor": sc}

    def img(ref, x, y, w, h, z):
        return {"type": "image", "z": z, "x": x, "y": y, "w": w, "h": h, "imageRef": ref}

    fs_name = 4.6 if kind != "hq" else 3.6
    while fs_name > 3.0 and text_width_units(uname, fs_name, 900) > 25.0:
        fs_name = round(fs_name - 0.1, 1)
    fs_lead = 3.0 if kind != "hq" else 4.4
    while fs_lead > 2.4 and text_width_units(leader, fs_lead, 700) > 22.0:
        fs_lead = round(fs_lead - 0.1, 1)
    shapes = [img("img_v39_plate_us" if side == 0 else "img_v39_plate_cs", 0, 0, 30, 30, 0)]
    if elite:
        shapes.append(img("img_v39_elite_frame", 0, 0, 30, 30, 1))
    if u.get("formation"):
        shapes.append(img(f"img_v39_band_{u['formation']}", 0, -13.2, 27.4, 2.2, 2))
    if elite:
        shapes.append(img("img_v39_star", 12.0, -13.2, 3.2, 3.2, 3))
    # strengths on cream cartouches, dark ink on both sides
    for link, x, v in (("box5", -NUM_X, cs), ("box6", NUM_X, mp)):
        n = min(len(str(v)), 2)
        shapes.append(img(f"img_v39_num{n}", x, NUM_Y, NUM_W[n], NUM_H, 2))
    lead_y = -10.5 if u.get("formation") else -11.2
    shapes += [txt("box3", 3, 0, lead_y, fs_lead, 700 if kind != "hq" else 900),
               txt("box4", 4, 0, -7.0 if kind != "hq" else -7.4, fs_name, 900 if kind != "hq" else 700),
               txt("box5", 5, -NUM_X, 9.4, 6.0, 900, "#111111", "#efece2", 0.3),
               txt("box6", 5, NUM_X, 9.4, 6.0, 900, "#111111", "#efece2", 0.3)]
    if kind == "hq":
        shapes.append(img("img_v39_hq_frame", 0, 2.4, 12.6, 14.4, 5))
        shapes.append(img(portrait, 0, 2.4, 10.6, 12.4, 6))          # v3.8.1 geometry, unchanged
        if u.get("rank"):
            shapes.append(img(f"img_v39_rank_{u['rank']}", 0, 11.9, 10.0, 3.0, 2))
        return shapes
    if kind == "art":
        shapes.append(img("img_emb_range3", 0, 10.4, 7.0, 3.5, 2))
        if u.get("guns"):
            shapes.append(img(f"img_v39_guns_{slug(u['guns'])}", 0, 6.6, 8.0, 3.0, 2))
            shapes.append(img(nato_keys[(kind, side)], 0, 0.8, 10.0, 8.0, 5))
        else:
            shapes.append(img(nato_keys[(kind, side)], 0, 1.6, 12.0, 9.6, 5))
        return shapes
    if u.get("colours"):
        shapes.append(img("img_v39_colours_us" if side == 0 else "img_v39_colours_cs", 0, 10.2, 6.0, 4.0, 2))
    if portrait:
        shapes.append(img(portrait, -8.4, 1.6, 7.8, 9.2, 6))            # v3.8.1 geometry, unchanged
        shapes.append(img(nato_keys[(kind, side)], 4.0, 1.6, 11.0, 8.8, 5))
    else:
        shapes.append(img(nato_keys[(kind, side)], 0, 1.6, 12.0, 9.6, 5))
    return shapes


V39_PREFIX = "img_v39_"
