"""Reference-sheet texture quilting for the Kernstown basemap.
Patches are cut from the user's hex reference sheet (data/assets/refpatches/rRcC.png)
and scattered densely with feathered masks + horizontal flips (art stays upright).
"""
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RP = Path(__file__).resolve().parents[1] / "data/assets/refpatches"
SCALE = 0.56  # sheet hex ~265px -> map hex ~142px

def _load(name, inner=1.0):
    im = Image.open(RP / f"{name}.png").convert("RGB")
    if inner < 1.0:
        w, h = im.size; dx, dy = int(w * (1 - inner) / 2), int(h * (1 - inner) / 2)
        im = im.crop((dx, dy, w - dx, h - dy))
    im = im.resize((max(8, int(im.size[0] * SCALE / inner * inner)), max(8, int(im.size[1] * SCALE))), Image.Resampling.LANCZOS)
    return np.asarray(im, np.float32)

GROUND = ["r0c0", "r0c0", "r0c3", "r3c3", "r1c0", "r0c0", "r0c3"]
WOODS = ["r0c4", "r0c4", "r1c0", "r0c4"]

def _feather(h, w):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.maximum(np.abs(xx - w / 2) / (w / 2), np.abs(yy - h / 2) / (h / 2))
    d2 = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
    d = 0.5 * d + 0.5 * d2
    return np.clip((1.0 - d) / 0.35, 0, 1) ** 1.5

def quilt(H, W, names, seed, step=None, inner=0.92, region=None):
    """Return (tex float32 HxWx3, weight HxW) covering region (x0,y0,x1,y1)."""
    rng = np.random.default_rng(seed)
    pats = [_load(n, inner) for n in names]
    x0, y0, x1, y1 = region or (0, 0, W, H)
    tex = np.zeros((y1 - y0, x1 - x0, 3), np.float32); wt = np.zeros((y1 - y0, x1 - x0), np.float32)
    ph, pw = pats[0].shape[:2]
    step = step or int(min(ph, pw) * 0.55)
    feats = {}
    for gy in range(-ph // 2, y1 - y0, step):
        for gx in range(-pw // 2, x1 - x0, step):
            p = pats[int(rng.integers(len(pats)))]
            if rng.random() < 0.5: p = p[:, ::-1]
            h, w = p.shape[:2]
            f = feats.setdefault((h, w), _feather(h, w))
            # random sub-crop jitter + tone jitter
            px, py = gx + int(rng.integers(-step // 3, step // 3 + 1)), gy + int(rng.integers(-step // 3, step // 3 + 1))
            sx0, sy0 = max(0, px), max(0, py); sx1, sy1 = min(x1 - x0, px + w), min(y1 - y0, py + h)
            if sx1 <= sx0 or sy1 <= sy0: continue
            sub = p[sy0 - py:sy1 - py, sx0 - px:sx1 - px] * rng.uniform(0.93, 1.06)
            ff = f[sy0 - py:sy1 - py, sx0 - px:sx1 - px] * rng.uniform(0.6, 1.0)
            tex[sy0:sy1, sx0:sx1] += sub * ff[..., None]; wt[sy0:sy1, sx0:sx1] += ff
    tex /= np.maximum(wt, 1e-4)[..., None]
    return tex, wt

def blend(base: Image.Image, tex, mask, strength, region=None, keep_shade=True):
    """Blend tex into base (RGBA PIL). mask HxW 0..1 (region-sized)."""
    x0, y0, x1, y1 = region or (0, 0, base.size[0], base.size[1])
    arr = np.asarray(base.crop((x0, y0, x1, y1)), np.float32)
    rgb = arr[..., :3]
    if keep_shade:
        lum = rgb.mean(-1)
        loc = np.asarray(Image.fromarray(np.clip(lum, 0, 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(60)), np.float32)
        # relief: local hillshade relative to map mean; colour: from texture
        shade = np.clip(loc / 150.0, 0.62, 1.22)
        tl = tex.mean(-1, keepdims=True) + 1e-3
        t2 = tex * shade[..., None]
        # tone: pull a little toward base hue (fields/marsh variation survive)
        bh = rgb / (lum[..., None] + 1e-3)
        t2 = 0.8 * t2 + 0.2 * (bh * tl * shade[..., None])
    else:
        t2 = tex
    a = (mask * strength)[..., None]
    rgb = rgb * (1 - a) + t2 * a
    arr[..., :3] = rgb
    base.paste(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA"), (x0, y0))
    return base

def ground_pass(base, strength=0.78, seed=7):
    W, H = base.size
    # do in horizontal bands to bound memory
    band = 1200
    for y0 in range(0, H, band):
        y1 = min(H, y0 + band + 80)
        tex, _ = quilt(H, W, GROUND, seed + y0, region=(0, y0, W, y1))
        m = np.ones((y1 - y0, W), np.float32)
        if y0 > 0: m[:80] = np.linspace(0, 1, 80)[:, None]
        base = blend(base, tex, m, strength, region=(0, y0, W, y1))
    return base

def woods_pass(base, forest_bool, strength=0.92, seed=11):
    W, H = base.size
    ys, xs = np.where(forest_bool[::4, ::4])
    if len(xs) == 0: return base
    fm = np.asarray(Image.fromarray(forest_bool.astype(np.uint8) * 255).filter(ImageFilter.GaussianBlur(10)), np.float32) / 255
    band = 1200
    for y0 in range(0, H, band):
        y1 = min(H, y0 + band)
        m = fm[y0:y1]
        if m.max() < 0.02: continue
        tex, _ = quilt(H, W, WOODS, seed + y0, region=(0, y0, W, y1))
        # mute redbud pinks -> mostly gray-brown, a few survive
        r, g, b = tex[..., 0], tex[..., 1], tex[..., 2]
        pink = np.clip((r - g - 25) / 40, 0, 1) * np.clip((b - g) / 25, 0, 1)
        gray = tex.mean(-1, keepdims=True) * np.array([1.0, 0.95, 0.88])
        tex = tex * (1 - 0.7 * pink[..., None]) + gray * 0.7 * pink[..., None]
        tex *= 0.9
        base = blend(base, tex, np.clip(m * 1.3, 0, 1), strength, region=(0, y0, W, y1))
    return base

def plowed_fields(base, t, n=34, seed=5, avoid=None):
    """Furrowed fields: tile plowed patch interior, rotate to field angle, mask polygon."""
    W, H = base.size
    rng = np.random.default_rng(seed)
    src = Image.open(RP / "r0c1.png").convert("RGB")
    w, h = src.size; src = src.crop((int(w * .25), int(h * .25), int(w * .75), int(h * .75)))
    src = src.resize((int(src.size[0] * SCALE * 1.2), int(src.size[1] * SCALE * 1.2)), Image.Resampling.LANCZOS)
    done = 0; tries = 0
    while done < n and tries < 2000:
        tries += 1
        cx, cy = rng.uniform(200, W - 200), rng.uniform(200, H - 200)
        if t[int(cy), int(cx)] > 0.55: continue
        if avoid is not None and avoid(cx, cy): continue
        ww, hh = rng.uniform(90, 190), rng.uniform(70, 140)
        size = int(max(ww, hh) * 2.6)
        tile = Image.new("RGB", (size * 2, size * 2))
        for xx in range(0, size * 2, src.size[0]):
            for yy in range(0, size * 2, src.size[1]):
                tile.paste(src, (xx, yy))
        ang = rng.uniform(-40, 40)
        tile = tile.rotate(ang, resample=Image.Resampling.BICUBIC).crop((size // 2, size // 2, size // 2 + size, size // 2 + size))
        m = Image.new("L", (size, size), 0)
        c, s = math.cos(math.radians(-ang)), math.sin(math.radians(-ang))
        pts = []
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2 + rng.uniform(-0.12, 0.12)
            x, y = math.cos(a) * ww * 0.9, math.sin(a) * hh * 0.9
            pts.append((size / 2 + x * c - y * s, size / 2 + x * s + y * c))
        ImageDraw.Draw(m).polygon(pts, fill=235)
        m = m.filter(ImageFilter.GaussianBlur(3))
        x0, y0 = int(cx - size / 2), int(cy - size / 2)
        if x0 < 0 or y0 < 0 or x0 + size > W or y0 + size > H: continue
        tex = np.asarray(tile, np.float32) * rng.uniform(0.9, 1.05)
        base = blend(base, tex, np.asarray(m, np.float32) / 255, 0.9, region=(x0, y0, x0 + size, y0 + size))
        done += 1
    print("plowed fields", done)
    return base

TINTS = {"wheat": (150, 158, 98), "straw": (204, 170, 96), "pasture": (166, 156, 100), "fallow": (170, 140, 96)}

def hex_patchwork(base, hexc, R, cols, rows, skip, seed=3):
    """New Market-style patchwork: hex-shaped fields that follow the grid, some fenced."""
    W, H = base.size
    rng = np.random.default_rng(seed)
    src = Image.open(RP / "r0c1.png").convert("RGB")
    w, h = src.size; src = src.crop((int(w * .22), int(h * .22), int(w * .78), int(h * .78)))
    src = src.resize((int(src.size[0] * SCALE * 1.1), int(src.size[1] * SCALE * 1.1)), Image.Resampling.LANCZOS)
    kinds = {}
    for c in range(cols):
        for r in range(rows):
            if skip(c, r) or rng.random() < 0.28: continue
            kinds[(c, r)] = rng.choice(["wheat", "straw", "straw", "plowed", "pasture", "fallow"], p=[.22, .2, .14, .18, .16, .10])
    side = int(2 * R + 4)
    for (c, r), k in kinds.items():
        cx, cy = hexc(c, r); x0, y0 = int(cx - side / 2), int(cy - side / 2)
        if x0 < 0 or y0 < 0 or x0 + side > W or y0 + side > H: continue
        m = Image.new("L", (side, side), 0)
        pts = [(side / 2 + 0.95 * R * math.cos(math.radians(60 * i)), side / 2 + 0.95 * R * math.sin(math.radians(60 * i))) for i in range(6)]
        ImageDraw.Draw(m).polygon(pts, fill=255); m = np.asarray(m.filter(ImageFilter.GaussianBlur(1.5)), np.float32) / 255
        reg = (x0, y0, x0 + side, y0 + side)
        arr = np.asarray(base.crop(reg), np.float32)
        lum = arr[..., :3].mean(-1, keepdims=True)
        if k == "plowed":
            tile = Image.new("RGB", (side * 2, side * 2))
            for xx in range(0, side * 2, src.size[0]):
                for yy in range(0, side * 2, src.size[1]): tile.paste(src, (xx, yy))
            ang = rng.choice([0, 60, -60]) + rng.uniform(-5, 5)
            tile = tile.rotate(ang, resample=Image.Resampling.BICUBIC).crop((side // 2, side // 2, side // 2 + side, side // 2 + side))
            tex = np.asarray(tile, np.float32) * np.clip(lum / 150, 0.75, 1.15) * rng.uniform(0.92, 1.05)
            a = 0.85
        else:
            tint = np.array(TINTS[k], np.float32) * rng.uniform(0.93, 1.06)
            tex = arr[..., :3] * 0.45 + (lum / 140.0) * tint * 0.55
            a = 0.62
        arr[..., :3] = arr[..., :3] * (1 - a * m[..., None]) + tex * a * m[..., None]
        base.paste(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA"), (x0, y0))
    # fences: rail line + posts along some field edges
    d = ImageDraw.Draw(base, "RGBA")
    for (c, r) in kinds:
        cx, cy = hexc(c, r)
        for i in range(6):
            if rng.random() > 0.22: continue
            a0, a1 = math.radians(60 * i), math.radians(60 * (i + 1))
            p0 = (cx + 0.93 * R * math.cos(a0), cy + 0.93 * R * math.sin(a0)); p1 = (cx + 0.93 * R * math.cos(a1), cy + 0.93 * R * math.sin(a1))
            d.line([(p0[0] + 1, p0[1] + 1.5), (p1[0] + 1, p1[1] + 1.5)], fill=(40, 32, 24, 90), width=2)
            d.line([p0, p1], fill=(92, 72, 50, 230), width=2)
            for f in np.linspace(0, 1, 7):
                x, y = p0[0] * (1 - f) + p1[0] * f, p0[1] * (1 - f) + p1[1] * f
                d.ellipse((x - 1.6, y - 1.6, x + 1.6, y + 1.6), fill=(58, 44, 30, 240))
    print("patchwork fields", len(kinds))
    return base
