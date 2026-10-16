#!/usr/bin/env python3
"""Compose Kernstown basemap: DEM + flow hydro + painted sheet1/sheet2 sprites.
Authoritative layout. Previews only — does NOT slice HoS tiles.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from hex_grid import KERNSTOWN as G
import texture_pass as TP

PX_PER_M = 0.55
FEAT = json.loads((ROOT / "data/features/kernstown_features.json").read_text())
mid = (G.south + G.north) / 2
m_lat, m_lon = G.meters_per_deg(mid)
W = int((G.east - G.west) * m_lon * PX_PER_M)
H = int((G.north - G.south) * m_lat * PX_PER_M)
R_PX = G.size_m * PX_PER_M
HOUSE_W = int(R_PX * 2 * 0.38)
rng = np.random.default_rng(42)
OUT = ROOT / "previews"
OUT.mkdir(exist_ok=True)
ASSETS = ROOT / "data/assets"
PAINTED = ASSETS / "painted" / "sprites"
(ASSETS / "textures").mkdir(parents=True, exist_ok=True)

def ll2px(lon, lat):
    return ((lon - G.west) * m_lon * PX_PER_M, (G.north - lat) * m_lat * PX_PER_M)

def hexc(col, row):
    x, y = G.hex_to_xy_m(col, row)
    return x * PX_PER_M, H - y * PX_PER_M

def load_font(size, bold=False):
    cands = [
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf",
    ]
    for p in cands:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def hex_dist(a, b):
    def to_cube(c, r):
        x = c; z = r - (c - (c & 1)) // 2; y = -x - z
        return x, y, z
    x1, y1, z1 = to_cube(*a); x2, y2, z2 = to_cube(*b)
    return (abs(x1 - x2) + abs(y1 - y2) + abs(z1 - z2)) // 2

# ---------- textures ----------
def _noise(w, h, scale=8, seed=0):
    r = np.random.default_rng(seed)
    n = r.random((h // scale + 1, w // scale + 1))
    return np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BILINEAR), np.float32) / 255

def make_texture(kind, size=256, seed=0):
    r = np.random.default_rng(seed)
    img = np.zeros((size, size, 3), np.float32)
    n = _noise(size, size, 6, seed)
    n2 = _noise(size, size, 3, seed + 1)
    if kind == "plowed":
        base = np.array([148, 108, 68], np.float32); img[:] = base
        yy = np.arange(size)[:, None]
        fur = np.sin(yy * 0.55 + n * 2) * 18
        img[:, :, 0] += fur + (n2 - 0.5) * 20
        img[:, :, 1] += fur * 0.7 + (n2 - 0.5) * 15
        img[:, :, 2] += fur * 0.4
    elif kind == "straw":
        base = np.array([214, 192, 138], np.float32)
        img[:] = base + (n[..., None] - 0.5) * 35
        img += (n2[..., None] - 0.5) * 15 * np.array([1.0, 0.9, 0.5])
    elif kind == "pasture":
        base = np.array([178, 168, 120], np.float32)
        img[:] = base + (n[..., None] - 0.5) * 22 * np.array([0.6, 1.0, 0.45])
        img[:, :, 1] += 6
    elif kind == "marsh":
        base = np.array([150, 148, 118], np.float32)
        img[:] = base + (n[..., None] - 0.5) * 20 * np.array([0.5, 0.7, 0.6])
        img[:, :, 1] += 8; img[:, :, 2] += 4
    else:
        base = np.array([96, 82, 62], np.float32)
        img[:] = base + (n[..., None] - 0.5) * 40
    img = np.clip(img, 0, 255).astype(np.uint8)
    im = Image.fromarray(img).convert("RGBA")
    im.save(ASSETS / "textures" / f"{kind}.png")
    return im

# ---------- sprites ----------
def _recolor(im, hue_shift=0.0, bright=1.0, sat=1.0):
    out = im.copy()
    if bright != 1.0:
        out = ImageEnhance.Brightness(out).enhance(bright)
    if sat != 1.0:
        out = ImageEnhance.Color(out).enhance(sat)
    if abs(hue_shift) > 1e-3:
        arr = np.array(out, np.float32)
        a = arr[:, :, 3:4]
        rgb = np.clip(arr[:, :, :3] + np.array([hue_shift * 18, -hue_shift * 8, -hue_shift * 12], np.float32), 0, 255)
        out = Image.fromarray(np.concatenate([rgb, a], axis=2).astype(np.uint8), "RGBA")
    return out

def load_painted(name, target_h=None, target_w=None):
    im = Image.open(PAINTED / f"{name}.png").convert("RGBA")
    if target_h:
        sc = target_h / im.size[1]
        im = im.resize((max(4, int(im.size[0] * sc)), max(4, int(im.size[1] * sc))), Image.Resampling.LANCZOS)
    elif target_w:
        sc = target_w / im.size[0]
        im = im.resize((max(4, int(im.size[0] * sc)), max(4, int(im.size[1] * sc))), Image.Resampling.LANCZOS)
    return im

def paste_sprite(base, sprite, x, y, anchor="foot"):
    sw, sh = sprite.size
    if anchor == "foot":
        px, py = int(x - sw / 2), int(y - sh + 4)
    elif anchor == "center":
        px, py = int(x - sw / 2), int(y - sh / 2)
    else:
        px, py = int(x), int(y)
    src_x0, src_y0 = max(0, -px), max(0, -py)
    dst_x0, dst_y0 = max(0, px), max(0, py)
    src_x1, src_y1 = min(sw, base.size[0] - px), min(sh, base.size[1] - py)
    if src_x1 <= src_x0 or src_y1 <= src_y0:
        return
    base.alpha_composite(sprite.crop((src_x0, src_y0, src_x1, src_y1)), (dst_x0, dst_y0))

def rotate_sprite(sp, angle_deg):
    return sp.rotate(angle_deg, resample=Image.Resampling.BICUBIC, expand=True)


def soft_foot_mask(sp, fade_frac=0.18):
    """Soft-blend sprite foot into ground (bottom alpha ramp)."""
    arr = np.array(sp)
    if arr.shape[2] < 4:
        return sp
    h = arr.shape[0]
    fade = max(2, int(h * fade_frac))
    ramp = np.linspace(0.55, 1.0, fade, dtype=np.float32)
    a = arr[:, :, 3].astype(np.float32)
    a[-fade:, :] *= ramp[:, None]
    from PIL import ImageFilter as _IF
    m = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(_IF.GaussianBlur(0.6))
    arr[:, :, 3] = np.array(m)
    return Image.fromarray(arr, "RGBA")

def feather_vignette(sp, blur=4.5, erode=6):
    """Feather circular/organic vignette pads into the basemap (no hard rect cutout)."""
    arr = np.array(sp.convert("RGBA"))
    a = arr[:, :, 3].astype(np.float32)
    # Distance-from-opaque erode then blur
    mask = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "L")
    # shrink opaque core slightly
    from PIL import ImageFilter as _IF, ImageOps as _IO
    mask = mask.filter(_IF.MinFilter(size=max(3, erode | 1)))
    mask = mask.filter(_IF.GaussianBlur(blur))
    arr[:, :, 3] = np.array(mask)
    return Image.fromarray(arr, "RGBA")

def grade_to_basemap(sp, strength=0.22):
    """Tint sprite toward parchment/ochre so it sits in the March palette (NW light scene)."""
    arr = np.array(sp, np.float32)
    a = arr[:, :, 3:4]
    rgb = arr[:, :, :3]
    # warm parchment grade + slight desat toward umber
    parchment = np.array([210, 190, 150], np.float32)
    umber = np.array([120, 95, 70], np.float32)
    lum = rgb.mean(axis=2, keepdims=True) / 255.0
    target = parchment * (0.55 + 0.45 * lum) + umber * (0.25 * (1.0 - lum))
    rgb = rgb * (1.0 - strength) + target * strength
    # NW key light: brighten upper-left of opaque mass slightly, shade lower-right
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    light = 1.0 + 0.08 * ((1.0 - xx / max(1, w - 1)) + (1.0 - yy / max(1, h - 1))) / 2
    shade = 1.0 - 0.10 * ((xx / max(1, w - 1)) + (yy / max(1, h - 1))) / 2
    rgb = rgb * light[..., None] * shade[..., None]
    rgb = np.clip(rgb, 0, 255)
    return Image.fromarray(np.concatenate([rgb, a], axis=2).astype(np.uint8), "RGBA")

def contact_shadow(sw, sh, strength=95):
    """Soft elliptical contact shadow offset SE (light from NW).
    Sized for high-angle (~60-70°) sprites: tighter footprint, less stretch.
    """
    pad = 6
    # High-angle buildings cast short shadows; keep ellipse near the foot
    sh_h = max(8, sh // 7 + 6)
    canv = Image.new("RGBA", (sw + pad * 2 + 6, sh_h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(canv, "RGBA")
    ex0, ey0 = pad + 2, pad
    ex1, ey1 = pad + sw - 2 + 4, pad + sh_h - 2
    d.ellipse((ex0, ey0, ex1, ey1), fill=(32, 24, 16, strength))
    canv = canv.filter(ImageFilter.GaussianBlur(2.2))
    return canv

def prepare_sprite(sp, grade=0.24, shadow=True, fade=0.16):
    """Full belonging pass: palette grade, soft foot, optional contact shadow baked under."""
    sp = grade_to_basemap(sp, strength=grade)
    sp = soft_foot_mask(sp, fade_frac=fade)
    if not shadow:
        return sp
    sw, sh = sp.size
    shad = contact_shadow(sw, sh, strength=55)
    # composite shadow then sprite; foot of sprite near shadow center-top
    out_w = max(sw, shad.size[0])
    out_h = sh + shad.size[1] // 3
    out = Image.new("RGBA", (out_w + 4, out_h + 4), (0, 0, 0, 0))
    # shadow near foot
    sx = (out_w - shad.size[0]) // 2 + 6
    sy = out_h - shad.size[1] + 2
    out.alpha_composite(shad, (max(0, sx), max(0, sy)))
    px = (out_w - sw) // 2
    py = out_h - sh
    out.alpha_composite(sp, (px, py))
    return out


def build_sprite_library():
    lib = {
        "trees": [], "hickories": [], "birches": [], "thickets": [],
        "redbuds": [], "snags": [], "cedars": [],
        "houses": [], "barns": [], "brick_houses": [],
        "townhouse_rows": [], "shop_rows": [],
        "outbuildings": [],
        "earthworks": [],
        "opequon_church": None, "pritchard_house": None, "pritchard_barn": None,
        "church": None, "steepled_church": None, "courthouse": None,
        "bridge": None, "mill": None, "depot": None, "ford": None,
        "wall_segs": [], "fence_worm": [], "marsh": [],
        "textures": {},
    }
    hex_h = R_PX * math.sqrt(3)
    oak = load_painted("bare_oak")
    hick = load_painted("bare_hickory")
    birch = load_painted("bare_birch")
    thick = load_painted("underbrush")
    redb = load_painted("redbud")
    snag = load_painted("dead_snag")
    cedar = load_painted("cedar_cluster")

    def variants(src, n, h_lo, h_hi, hue=0.5):
        out = []
        for i in range(n):
            sc = float(rng.uniform(h_lo, h_hi)) * hex_h / src.size[1]
            sp = src.resize((max(8, int(src.size[0] * sc)), max(8, int(src.size[1] * sc))), Image.Resampling.LANCZOS)
            if rng.random() < 0.5:
                sp = ImageOps.mirror(sp)
            sp = _recolor(sp, hue_shift=float(rng.uniform(-hue, hue)),
                          bright=float(rng.uniform(0.88, 1.12)),
                          sat=float(rng.uniform(0.75, 1.05)))
            out.append(sp)
        return out

    lib["trees"] = variants(oak, 10, 0.55, 0.95)
    lib["hickories"] = variants(hick, 8, 0.50, 0.90)
    lib["birches"] = variants(birch, 8, 0.50, 0.88, hue=0.35)
    lib["thickets"] = variants(thick, 6, 0.35, 0.65, hue=0.3)
    lib["redbuds"] = variants(redb, 5, 0.45, 0.75, hue=0.25)
    lib["snags"] = variants(snag, 4, 0.40, 0.70, hue=0.2)
    lib["cedars"] = variants(cedar, 5, 0.45, 0.80, hue=0.3)

    def _load_pref(names, fallback=None):
        """Load first existing painted sprite from name list (cgpt preferred)."""
        for name in names:
            p = PAINTED / f"{name}.png"
            if p.exists():
                return load_painted(name)
        if fallback and (PAINTED / f"{fallback}.png").exists():
            return load_painted(fallback)
        raise FileNotFoundError(names)

    # Townhouse / shop rows: ~0.45–0.55 hex wide per facade unit; rows wider
    TOWN_HOUSE_W = int(R_PX * 2 * 0.48)   # single townhouse ~0.48 hex
    TOWN_ROW_W = int(R_PX * 2 * 0.88)     # continuous row ~0.88 hex

    house_specs = [
        (["cgpt2_stone_farmhouse", "cgpt2_stone_house", "cgpt_stone_house", "cgpt_stone_house2", "cgpt_stone_farm", "limestone_farmhouse"], "houses", TOWN_HOUSE_W),
        (["cgpt_log_cabin", "cgpt_log_cabin_porch", "cgpt_log_cabin_small", "cgpt_log_dense", "log_house"], "houses", TOWN_HOUSE_W),
        (["cgpt_frame_house_white", "cgpt_frame_farmhouse", "cgpt_frame_house_shed", "cgpt_cottage_laundry"], "houses", TOWN_HOUSE_W),
        (["cgpt2_bank_barn", "cgpt_bank_barn", "cgpt_bank_barn2", "cgpt_barn_wagon", "cgpt_barn_wood", "cgpt_barn_doors", "cgpt_barn_dense", "bank_barn"], "barns", int(R_PX * 2 * 0.55)),
        (["cgpt_brick_house2", "cgpt_brick_house_porch", "cgpt_brick_house", "cgpt_brick_town", "brick_house_picket"], "brick_houses", TOWN_HOUSE_W),
        (["cgpt_townrow_brick_awnings", "cgpt_townhouse_row_a", "brick_townhouse_row"], "townhouse_rows", TOWN_ROW_W),
        (["cgpt_townrow_stone_shops", "cgpt_townhouse_row_b", "shop_row"], "townhouse_rows", TOWN_ROW_W),
        (["cgpt_townrow_brick_porch", "cgpt_brick_house_porch", "cgpt_brick_house2"], "shop_rows", TOWN_ROW_W),
        (["cgpt_townrow_brick_awnings", "cgpt_townrow_stone_shops"], "shop_rows", TOWN_ROW_W),
        (["cgpt_smokehouse", "cgpt_springhouse", "cgpt_springhouse2", "cgpt_corncrib", "cgpt_frame_house_shed"], "outbuildings", int(R_PX * 2 * 0.28)),
    ]
    for names, key, target_w in house_specs:
        try:
            raw = _load_pref(names)
        except FileNotFoundError:
            continue
        sc = target_w / max(1, raw.size[0])
        base_sp = raw.resize((max(8, int(raw.size[0] * sc)), max(8, int(raw.size[1] * sc))), Image.Resampling.LANCZOS)
        n = 3 if key in ("houses", "townhouse_rows", "shop_rows", "brick_houses") else 2
        for i in range(n):
            sp = _recolor(base_sp, hue_shift=float(rng.uniform(-0.15, 0.15)),
                          bright=float(rng.uniform(0.94, 1.06)))
            if rng.random() < 0.30:
                sp = ImageOps.mirror(sp)
            lib[key].append(sp)

    landmark_specs = [
        (["cgpt2_stone_church_graveyard", "cgpt_church_steeple_stone", "cgpt_church_c", "cgpt_church_a", "stone_church"], "church", 1.55),
        (["cgpt2_brick_church_graveyard", "cgpt_church_steeple_brick", "cgpt_church_steeple_mid", "cgpt_church_b", "steepled_church"], "steepled_church", 1.55),
        (["cgpt_courthouse_cupola", "cgpt_courthouse", "courthouse_cupola"], "courthouse", 1.55),
        (["cgpt2_covered_bridge", "cgpt2_covered_bridge_b", "cgpt2_stone_arch_bridge", "cgpt_covered_bridge", "covered_bridge"], "bridge", 1.55),
        (["cgpt2_mill_wheel", "cgpt_mill_wheel", "cgpt_mill_dense", "stone_mill"], "mill", 1.35),
        (["cgpt2_depot_water_tower", "cgpt_depot_wp", "cgpt_depot", "rr_depot"], "depot", 1.45),
        (["muddy_ford"], "ford", 1.5),
    ]
    for names, key, sc_w in landmark_specs:
        try:
            raw = _load_pref(names)
        except FileNotFoundError:
            continue
        sc = (HOUSE_W * sc_w) / raw.size[0]
        lib[key] = raw.resize((max(8, int(raw.size[0] * sc)), max(8, int(raw.size[1] * sc))), Image.Resampling.LANCZOS)

    # Dedicated cgpt2 vignettes for landmarks (keep full yard/graveyard pad)
    def _load_named(name, target_w):
        p = PAINTED / f"{name}.png"
        if not p.exists():
            return None
        raw = load_painted(name)
        sc = target_w / max(1, raw.size[0])
        return raw.resize((max(8, int(raw.size[0] * sc)), max(8, int(raw.size[1] * sc))), Image.Resampling.LANCZOS)

    lib["opequon_church"] = _load_named("cgpt2_stone_church_graveyard", int(R_PX * 2 * 1.15))
    lib["pritchard_house"] = _load_named("cgpt2_stone_farmhouse", int(R_PX * 2 * 0.72))
    if lib["pritchard_house"] is None:
        lib["pritchard_house"] = _load_named("cgpt2_stone_house", int(R_PX * 2 * 0.72))
    lib["pritchard_barn"] = _load_named("cgpt2_bank_barn", int(R_PX * 2 * 0.78))
    for ename in ("cgpt2_earthwork_battery", "cgpt2_earthwork_redoubt"):
        ew = _load_named(ename, int(R_PX * 2 * 0.95))
        if ew is not None:
            lib["earthworks"].append(ew)

    lib["wall_segs_raw"] = []
    for name in ("stone_wall_a", "stone_wall_b"):
        raw = load_painted(name)
        # wall segment ~0.85 hex wide (kept raw for delicate chaining)
        sc = (R_PX * 1.7) / raw.size[0]
        sp = raw.resize((max(8, int(raw.size[0] * sc)), max(8, int(raw.size[1] * sc))), Image.Resampling.LANCZOS)
        lib["wall_segs_raw"].append(sp)
        lib["wall_segs_raw"].append(ImageOps.mirror(sp))
        lib["wall_segs"].append(sp.copy())
        lib["wall_segs"].append(ImageOps.mirror(sp))

    marsh = load_painted("marsh_cattails")
    for i in range(6):
        sc = float(rng.uniform(0.55, 0.95)) * (R_PX * 1.4) / marsh.size[0]
        sp = marsh.resize((max(8, int(marsh.size[0] * sc)), max(8, int(marsh.size[1] * sc))), Image.Resampling.LANCZOS)
        if rng.random() < 0.5:
            sp = ImageOps.mirror(sp)
        sp = _recolor(sp, bright=float(rng.uniform(0.92, 1.08)), sat=float(rng.uniform(0.9, 1.15)))
        lib["marsh"].append(sp)

    fence = load_painted("worm_rail_fence")
    for i in range(4):
        sc = float(rng.uniform(0.55, 0.85)) * (R_PX * 1.6) / fence.size[0]
        sp = fence.resize((max(8, int(fence.size[0] * sc)), max(8, int(fence.size[1] * sc))), Image.Resampling.LANCZOS)
        if rng.random() < 0.5:
            sp = ImageOps.mirror(sp)
        lib["fence_worm"].append(sp)

    for kind in ("plowed", "straw", "pasture", "woodland", "marsh"):
        lib["textures"][kind] = make_texture(kind, 256, seed=hash(kind) % 10000)
    # cgpt3: patches sampled from user's style sheet, mirror-tiled to be seamless
    for kind in ("straw", "pasture"):
        fp = ASSETS / "cgpt3" / f"tex_{kind}.png"
        if fp.exists():
            pt = Image.open(fp).convert("RGBA"); w0, h0 = pt.size
            t2 = Image.new("RGBA", (w0 * 2, h0 * 2))
            t2.paste(pt, (0, 0)); t2.paste(pt.transpose(Image.FLIP_LEFT_RIGHT), (w0, 0))
            t2.paste(pt.transpose(Image.FLIP_TOP_BOTTOM), (0, h0)); t2.paste(pt.transpose(Image.ROTATE_180), (w0, h0))
            t4 = Image.new("RGBA", (w0 * 4, h0 * 4))
            for gx in range(2):
                for gy in range(2):
                    t4.paste(t2, (gx * w0 * 2, gy * h0 * 2))
            lib["textures"][kind] = t4


    # Belonging pass: grade + foot fade + contact shadow (NW light / SE shadow)
    def _prep_list(lst, grade=0.20, fade=0.16):
        return [prepare_sprite(s, grade=grade, shadow=True, fade=fade) for s in lst]
    lib["trees"] = _prep_list(lib["trees"], 0.24, 0.20)
    lib["hickories"] = _prep_list(lib["hickories"], 0.24, 0.20)
    lib["birches"] = _prep_list(lib["birches"], 0.22, 0.18)
    lib["thickets"] = _prep_list(lib["thickets"], 0.26, 0.22)
    lib["redbuds"] = _prep_list(lib["redbuds"], 0.18, 0.16)
    lib["snags"] = _prep_list(lib["snags"], 0.28, 0.18)
    lib["cedars"] = _prep_list(lib["cedars"], 0.22, 0.16)
    lib["houses"] = _prep_list(lib["houses"], 0.22, 0.14)
    lib["barns"] = _prep_list(lib["barns"], 0.20, 0.12)
    lib["brick_houses"] = _prep_list(lib["brick_houses"], 0.20, 0.12)
    lib["townhouse_rows"] = _prep_list(lib["townhouse_rows"], 0.18, 0.10)
    lib["shop_rows"] = _prep_list(lib["shop_rows"], 0.18, 0.10)
    lib["outbuildings"] = _prep_list(lib["outbuildings"], 0.22, 0.14)
    lib["wall_segs"] = _prep_list(lib["wall_segs"], 0.12, 0.08)
    lib["fence_worm"] = _prep_list(lib["fence_worm"], 0.20, 0.14)
    lib["marsh"] = _prep_list(lib["marsh"], 0.14, 0.20)
    # Courthouse: enlarge RAW first for clear landmark (~52% hex width; offset from centers for counters)
    if lib.get("courthouse"):
        cw = int(R_PX * 2 * 0.52)
        sc = cw / lib["courthouse"].size[0]
        lib["courthouse"] = lib["courthouse"].resize(
            (max(8, int(lib["courthouse"].size[0] * sc)), max(8, int(lib["courthouse"].size[1] * sc))),
            Image.Resampling.LANCZOS)
    for key in ("church", "steepled_church", "courthouse", "bridge", "mill", "depot", "ford",
                "opequon_church", "pritchard_house", "pritchard_barn"):
        if lib.get(key):
            g = 0.10 if key == "courthouse" else 0.14
            fade = 0.08 if key in ("courthouse", "opequon_church", "pritchard_house", "pritchard_barn") else 0.10
            sp = lib[key]
            if key in ("opequon_church", "pritchard_house", "pritchard_barn"):
                sp = feather_vignette(sp, blur=6.5, erode=9)
            lib[key] = prepare_sprite(sp, grade=g, shadow=True, fade=fade)
    lib["earthworks"] = [
        prepare_sprite(feather_vignette(s, blur=7.0, erode=10), grade=0.12, shadow=False, fade=0.28)
        for s in lib["earthworks"]
    ]

    print("sprites:", {k: (len(v) if isinstance(v, list) else (1 if v else 0))
                       for k, v in lib.items() if k != "textures"})
    return lib


def draw_sparse_contours(base, demh, town_w):
    """Wide-interval (~40 ft) smooth contours via marching squares; faded near Winchester."""
    try:
        from skimage import measure
    except ImportError:
        return base
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay, "RGBA")
    lo, hi = float(np.nanpercentile(demh, 8)), float(np.nanpercentile(demh, 92))
    interval = 30.0  # ~100 ft, sparse
    levels = np.arange(math.ceil(lo / interval) * interval, hi, interval)
    # Downsample DEM for smoother, faster contours
    step = 4
    dem_s = demh[::step, ::step]
    for lev in levels:
        try:
            contours = measure.find_contours(dem_s, lev)
        except Exception:
            continue
        for contour in contours:
            if len(contour) < 8:
                continue
            # contour is (row, col) in dem_s → scale to full px
            pts = []
            skip = False
            alphas = []
            for row, col in contour[::2]:  # thin vertices
                px = int(col * step)
                py = int(row * step)
                if not (0 <= px < W and 0 <= py < H):
                    continue
                tw = float(town_w[min(H - 1, py), min(W - 1, px)])
                if tw > 0.25:
                    skip = True
                    break
                alpha = int(30 * (1.0 - tw * 0.85))
                if alpha < 10:
                    continue
                pts.append((px, py))
                alphas.append(alpha)
            if skip or len(pts) < 6:
                continue
            a = int(sum(alphas) / len(alphas))
            d.line(pts, fill=(118, 102, 78, a), width=1, joint="curve")
    overlay = overlay.filter(ImageFilter.GaussianBlur(0.5))
    return Image.alpha_composite(base, overlay)


# ---------- basemap ----------
def build_rich_basemap():
    dem = np.array(Image.open(ROOT / "data/dem/kernstown_3dep.tif"), np.float32)
    dem = np.where(np.isfinite(dem), dem, np.nanmedian(dem))
    dem_img = Image.fromarray(dem)
    demh = np.array(dem_img.resize((W, H), Image.Resampling.BICUBIC), np.float32)
    lo_b, hi_b = float(np.nanmin(demh)), float(np.nanmax(demh))
    norm = ((demh - lo_b) / (hi_b - lo_b + 1e-6) * 255).astype(np.uint8)
    blurred = np.array(Image.fromarray(norm, "L").filter(ImageFilter.GaussianBlur(radius=1.6)), np.float32)
    demh = lo_b + blurred / 255.0 * (hi_b - lo_b)
    vex = 1.5  # moderate relief on a broad-smoothed surface
    def _box(a, r, axis):
        c = np.cumsum(np.pad(a, [(r + 1, r) if i == axis else (0, 0) for i in range(2)], mode="edge"), axis=axis, dtype=np.float64)
        n = a.shape[axis]
        hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
        lo = np.take(c, np.arange(0, n), axis=axis)
        return ((hi - lo) / (2 * r + 1)).astype(np.float32)
    dsm = demh
    for _ in range(3):
        dsm = _box(_box(dsm, 10, 0), 10, 1)
    gy, gx = np.gradient(dsm * vex, 1.0 / PX_PER_M)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, alt = math.radians(315), math.radians(40)
    hs = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    hs = np.clip(hs, 0, 1) ** 0.95
    lo, hi = np.percentile(demh, 2), np.percentile(demh, 98.5)
    t = np.clip((demh - lo) / (hi - lo + 1e-6), 0, 1)
    # Early-spring muddy tan hypsometry (faint green at most)
    stops = [
        (0.00, (176, 152, 102)), (0.20, (178, 154, 104)), (0.40, (180, 154, 106)),
        (0.58, (170, 138, 96)), (0.75, (148, 116, 80)), (0.90, (126, 98, 68)), (1.00, (104, 82, 58)),
    ]
    hyp = np.zeros((H, W, 3), np.float32)
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        m = (t >= t0) & (t <= t1)
        f = ((t[m] - t0) / (t1 - t0 + 1e-9))[:, None]
        hyp[m] = np.array(c0, np.float32) * (1 - f) + np.array(c1, np.float32) * f
    # Soft hillshade map-wide (gentle rolling, not harsh ridges)
    shade = 0.40 + 0.78 * hs
    shade *= 1.0 - 0.18 * np.clip(slope / math.radians(16), 0, 1)
    # broad low-frequency ground-tone variation (brown / gold / green patches)
    def lowfreq(sd, sc):
        r = np.random.default_rng(sd).random((H // sc + 2, W // sc + 2)).astype(np.float32)
        im = Image.fromarray((r * 255).astype(np.uint8)).resize((W, H), Image.Resampling.BICUBIC)
        return np.array(im.filter(ImageFilter.GaussianBlur(sc * 0.4)), np.float32) / 255.0
    n1, n2 = lowfreq(11, 160), lowfreq(23, 90)
    brown = np.array([150, 112, 78], np.float32); gold = np.array([206, 178, 110], np.float32)
    greenm = np.array([150, 160, 112], np.float32)
    wb = np.clip((n1 - 0.55) * 2.2, 0, 1)[..., None] * 0.30
    wg = np.clip((0.45 - n1) * 2.2, 0, 1)[..., None] * 0.30
    wgr = (np.clip((n2 - 0.58) * 2.5, 0, 1) * (t < 0.45))[..., None] * 0.25
    hyp = hyp * (1 - wb - wg - wgr) + brown * wb + gold * wg + greenm * wgr
    yy, xx = np.mgrid[0:H, 0:W]
    # Extra soften around Winchester valley floor
    wx0, wy1 = ll2px(-78.175, 39.172); wx1, wy0 = ll2px(-78.148, 39.208)
    tcx = (min(wx0, wx1) + max(wx0, wx1)) * 0.5
    tcy = (min(wy0, wy1) + max(wy0, wy1)) * 0.5
    tw = max(wx0, wx1) - min(wx0, wx1)
    th = max(wy0, wy1) - min(wy0, wy1)
    town_w = np.clip(1.0 - np.sqrt(((xx - tcx) / (tw * 0.55 + 1)) ** 2 + ((yy - tcy) / (th * 0.55 + 1)) ** 2), 0, 1)
    town_w = town_w ** 1.2
    shade = shade * (1.0 - 0.25 * town_w) + 0.80 * 0.25 * town_w
    mud = np.array([186, 168, 128], np.float32)
    green_hint = np.array([168, 172, 130], np.float32)
    spring = mud * 0.82 + green_hint * 0.18
    hyp = hyp * (1.0 - 0.22 * town_w[..., None]) + spring * (0.22 * town_w[..., None])
    img = np.clip(hyp * shade[..., None], 0, 255)
    grain = rng.random((H // 5 + 1, W // 5 + 1))
    grain = np.array(Image.fromarray((grain * 255).astype(np.uint8)).resize((W, H), Image.Resampling.BILINEAR), np.float32) / 255
    img = np.clip(img * (0.97 + 0.05 * grain[..., None]) + (grain[..., None] - 0.5) * 4, 0, 255)
    base_img = Image.fromarray(img.astype(np.uint8)).convert("RGBA")
    # Sparse faint contours (wide interval ~20 ft), thinned near Winchester
    base_img = draw_sparse_contours(base_img, demh, town_w)
    return base_img, t, slope, demh

def stamp_fields(base, textures, t):
    """Early-spring muddy tan fields (faint green); dry-stone walls near Winchester."""
    d = ImageDraw.Draw(base, "RGBA")
    kinds = ["straw", "straw", "plowed", "straw", "pasture", "plowed", "straw"]
    # Winchester vicinity for dry-stone field walls
    wx0, wy1 = ll2px(-78.178, 39.170); wx1, wy0 = ll2px(-78.148, 39.205)
    near_town_box = (min(wx0, wx1), min(wy0, wy1), max(wx0, wx1), max(wy0, wy1))

    def near_town(cx, cy):
        return (near_town_box[0] < cx < near_town_box[2] and near_town_box[1] < cy < near_town_box[3])

    for i in range(95):
        cx, cy = rng.uniform(0, W), rng.uniform(0, H)
        ix, iy = int(min(W - 1, cx)), int(min(H - 1, cy))
        if t[iy, ix] > 0.58 or near_town(cx, cy):
            continue
        ww, hh = rng.uniform(140, 300), rng.uniform(100, 210)
        ang = rng.uniform(0, math.pi)
        c, s = math.cos(ang), math.sin(ang)
        nvert = int(rng.integers(5, 8))
        corners = []
        for k in range(nvert):
            a = 2 * math.pi * k / nvert + rng.uniform(-0.2, 0.2)
            rr = rng.uniform(0.65, 1.15)
            corners.append((math.cos(a) * ww * rr, math.sin(a) * hh * rr))
        pts = [(cx + x * c - y * s, cy + x * s + y * c) for x, y in corners]
        kind = kinds[i % len(kinds)]
        mask = Image.new("L", base.size, 0)
        ImageDraw.Draw(mask).polygon(pts, fill=200)
        mask = mask.filter(ImageFilter.GaussianBlur(16))
        _tk = textures[kind]; _tw, _th = int(ww * 2.8 + 80), int(hh * 2.8 + 80)
        tex = Image.new("RGBA", (_tw, _th))
        for _x in range(0, _tw, _tk.size[0]):
            for _y in range(0, _th, _tk.size[1]):
                tex.paste(_tk, (_x, _y))
        tex = tex.rotate(math.degrees(ang), resample=Image.Resampling.BILINEAR, expand=False, fillcolor=tuple(int(v) for v in np.array(_tk).reshape(-1,4).mean(0)))
        # Muddy tan / faint green early-spring grade on field stamps
        tarr = np.array(tex, np.float32)
        tone = {"plowed": (128, 92, 62), "straw": (208, 176, 104), "pasture": (146, 156, 104)}[kind]
        tone = np.array(tone, np.float32) * rng.uniform(0.9, 1.08)
        tarr[:, :, :3] = tarr[:, :, :3] * 0.82 + tone * 0.18
        tarr[:, :, 3] = 255
        tex = Image.fromarray(np.clip(tarr, 0, 255).astype(np.uint8), "RGBA")
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        layer.paste(tex, (int(cx - tex.size[0] / 2), int(cy - tex.size[1] / 2)))
        layer.putalpha(mask.point(lambda v: int(v * 0.62)))
        base = Image.alpha_composite(base, layer)
        d = ImageDraw.Draw(base, "RGBA")
        if True:  # no polygon outlines (they read as stray lines)
            continue
        if False:
            # Dry-stone field wall: thin gray-brown double stroke
            d.line(pts + [pts[0]], fill=(72, 64, 52, 140), width=3)
            d.line(pts + [pts[0]], fill=(148, 138, 118, 160), width=1)
        else:
            col = (168, 162, 148, 100) if i % 3 == 0 else (90, 68, 42, 70)
            d.line(pts + [pts[0]], fill=col, width=2 if i % 3 == 0 else 1)
    return base

def paint_marsh(base, textures, lib):
    """Cattails + standing-water glints + faint green — no fog wash."""
    for m in FEAT.get("marshes", {}).values():
        poly = [ll2px(lon, lat) for lon, lat in m["polygon"]]
        mask = Image.new("L", base.size, 0)
        ImageDraw.Draw(mask).polygon(poly, fill=200)
        mask = mask.filter(ImageFilter.GaussianBlur(8))
        # faint green tint only
        wash = Image.new("RGBA", base.size, (140, 155, 120, 0))
        wash.putalpha(mask.point(lambda v: int(v * 0.22)))
        base = Image.alpha_composite(base, wash)
        # mottled olive/green-brown wet-meadow texture within soft mask, no blobs/dots
        r = np.random.default_rng(77)
        sm = r.random((H // 24 + 2, W // 24 + 2)).astype(np.float32)
        sm = np.array(Image.fromarray((sm * 255).astype(np.uint8)).resize((W, H), Image.Resampling.BICUBIC)
                      .filter(ImageFilter.GaussianBlur(10)), np.float32) / 255
        fine = r.random((H // 3 + 2, W // 3 + 2)).astype(np.float32)
        fine = np.array(Image.fromarray((fine * 255).astype(np.uint8)).resize((W, H), Image.Resampling.BILINEAR), np.float32) / 255
        mk = np.array(mask, np.float32) / 200.0
        c1 = np.array([118, 128, 88], np.float32); c2 = np.array([150, 140, 98], np.float32)
        col = c1 * sm[..., None] + c2 * (1 - sm[..., None])
        col = col * (0.92 + 0.12 * fine[..., None])
        al = np.clip(mk * (0.18 + 0.22 * sm), 0, 1) * 255
        tex = Image.fromarray(np.dstack([np.clip(col, 0, 255), al]).astype(np.uint8), "RGBA")
        base = Image.alpha_composite(base, tex)
    return base

def paint_pritchard_open(base, demh):
    return base  # no glow/halo
    for lon, lat in FEAT["ridge_cores"]["pritchards_hill"]:
        px, py = ll2px(lon, lat)
        rad = int(2.0 * R_PX)
        wash = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(wash, "RGBA").ellipse(
            (px - rad, py - rad * 0.75, px + rad, py + rad * 0.75), fill=(230, 218, 175, 70))
        base = Image.alpha_composite(base, wash.filter(ImageFilter.GaussianBlur(18)))
    return base

def forest_mask(t, slope):
    """Mosaic of 1–3 hex leafless woodlots along Sandy Ridge + sparse lots elsewhere.
    Not a solid dark forest band — open fields between woodlots. Ridge crest ~3–5 hex wide.
    """
    yy, xx = np.mgrid[0:H, 0:W]
    forest = np.zeros((H, W), bool)
    hex_w = 2 * R_PX
    spine = FEAT["ridge_cores"]["sandy_ridge"]

    # Place discrete woodlots along the ridge spine (1–3 hex radius)
    lot_centers = []
    for i in range(len(spine) - 1):
        x0, y0 = ll2px(*spine[i]); x1, y1 = ll2px(*spine[i + 1])
        seg = math.hypot(x1 - x0, y1 - y0)
        n_lots = max(1, int(seg / (hex_w * 1.8)))
        for k in range(n_lots):
            f = (k + 0.35) / max(1, n_lots)
            # skip every ~3rd for open field gaps
            if (i + k) % 3 == 1:
                continue
            cx = x0 * (1 - f) + x1 * f + float(rng.uniform(-0.4, 0.4)) * hex_w
            cy = y0 * (1 - f) + y1 * f + float(rng.uniform(-0.35, 0.35)) * hex_w
            rad = float(rng.uniform(0.55, 1.45)) * hex_w  # 1–3 hex diameter-ish
            lot_centers.append((cx, cy, rad))

    # A few scattered farm woodlots map-wide (sparse)
    for _ in range(22):
        cx, cy = rng.uniform(0, W), rng.uniform(0, H)
        rad = float(rng.uniform(0.45, 1.1)) * hex_w
        lot_centers.append((cx, cy, rad))

    for cx, cy, rad in lot_centers:
        # irregular ellipse
        rw = rad * float(rng.uniform(0.85, 1.15))
        rh = rad * float(rng.uniform(0.65, 0.95))
        forest |= ((xx - cx) ** 2 / (rw ** 2) + (yy - cy) ** 2 / (rh ** 2)) < 1

    # Clear Pritchard's Hill plateau (open)
    for lon, lat in FEAT["ridge_cores"]["pritchards_hill"]:
        px, py = ll2px(lon, lat)
        forest &= ((xx - px) ** 2 + (yy - py) ** 2) > (2.0 * hex_w) ** 2

    # Clear meadow between ridges
    for m in FEAT.get("marshes", {}).values():
        poly = m["polygon"]
        cx = sum(p[0] for p in poly) / len(poly)
        cy = sum(p[1] for p in poly) / len(poly)
        px, py = ll2px(cx, cy)
        forest &= ((xx - px) ** 2 + (yy - py) ** 2) > (1.6 * hex_w) ** 2

    for p in FEAT["places"]:
        px, py = ll2px(p["lon"], p["lat"])
        if p.get("kind") == "city" or p.get("id") == "winchester_center":
            rad = int(5.5 * R_PX)
        else:
            rad = 70
        forest &= ((xx - px) ** 2 + (yy - py) ** 2) > rad ** 2

    # Thin trees along stone-wall N-edges
    sw_path = ROOT / "data/features/stone_wall_hexsides.json"
    if sw_path.exists():
        for hs in json.loads(sw_path.read_text()).get("hexsides", []):
            cx, cy = hexc(hs["col"], hs["row"])
            for ox in range(-int(R_PX), int(R_PX) + 1, 4):
                for oy in range(-int(R_PX * 0.15), int(R_PX * 0.55), 4):
                    px, py = int(cx + ox), int(cy - R_PX * 0.55 + oy)
                    if 0 <= px < W and 0 <= py < H:
                        rad = 12
                        y0, y1 = max(0, py - rad), min(H, py + rad + 1)
                        x0, x1 = max(0, px - rad), min(W, px + rad + 1)
                        yy_l, xx_l = np.ogrid[y0:y1, x0:x1]
                        forest[y0:y1, x0:x1] &= ((xx_l - px) ** 2 + (yy_l - py) ** 2) >= rad ** 2

    # Winchester bbox clear + leave sparse edge woodlots outside
    w_lon0, w_lon1 = -78.1725, -78.1560
    w_lat0, w_lat1 = 39.1735, 39.1930
    x0, y1 = ll2px(w_lon0, w_lat0); x1, y0 = ll2px(w_lon1, w_lat1)
    xa, xb = int(min(x0, x1)), int(max(x0, x1))
    ya, yb = int(min(y0, y1)), int(max(y0, y1))
    forest[ya:yb, xa:xb] = False
    return forest


def paint_woods(base, forest, lib):

    # Muted gray-brown leafless wash (not black / solid dark)
    fm = Image.fromarray((forest.astype(np.uint8) * 255)).filter(ImageFilter.GaussianBlur(16))
    wash = Image.new("RGBA", base.size, (128, 118, 98, 0))
    wash.putalpha(fm.point(lambda v: int(v * 0.22)))
    base = Image.alpha_composite(base, wash)
    base = TP.woods_pass(base, forest)
    # Precompute water proximity mask for birch placement
    water_near = np.zeros((H, W), bool)
    rad = int(R_PX * 2.2)
    for riv in FEAT["rivers"].values():
        wps = riv["waypoints"]
        step = max(1, len(wps) // 40)
        for lon, lat in wps[::step]:
            wx, wy = ll2px(lon, lat)
            x0, x1 = max(0, int(wx) - rad), min(W, int(wx) + rad)
            y0, y1 = max(0, int(wy) - rad), min(H, int(wy) + rad)
            yy, xx = np.ogrid[y0:y1, x0:x1]
            water_near[y0:y1, x0:x1] |= (xx - wx) ** 2 + (yy - wy) ** 2 < rad ** 2
    fy, fx = np.where(forest)
    if len(fx) == 0:
        return base
    n = min(len(fx) // 320, 700)  # sparse leafless woodlots, not a solid canopy
    idx = rng.choice(len(fx), size=n, replace=False)
    pts = sorted([(float(fx[i]), float(fy[i])) for i in idx], key=lambda p: p[1])
    for i, (x, y) in enumerate(pts):
        ang = float(rng.uniform(0, 6.28)); rad = float(rng.uniform(10, 32))
        x += rad * math.cos(ang); y += rad * math.sin(ang) * 0.65
        # Birches only near water (precomputed mask); thickets reduced; mostly oak/hickory
        near_water = bool(water_near[min(H-1, int(y)), min(W-1, int(x))])
        r = rng.random()
        if r < 0.04:
            sp = lib["redbuds"][i % len(lib["redbuds"])]
        elif r < 0.08:
            sp = lib["snags"][i % len(lib["snags"])]
        elif r < 0.14:
            sp = lib["cedars"][i % len(lib["cedars"])]
        elif near_water and r < 0.22:
            sp = lib["birches"][i % len(lib["birches"])]
        elif r < 0.28:
            sp = lib["thickets"][i % len(lib["thickets"])]
        elif r < 0.55:
            sp = lib["hickories"][i % len(lib["hickories"])]
        else:
            sp = lib["trees"][i % len(lib["trees"])]
        paste_sprite(base, sp, x, y)
    return base

def draw_hydro(base):
    """Smooth meandering creeks: Chaikin + kink removal; single antialiased stroke (no double lines).
    town_run included (smoothed) for SE Winchester creek.
    """
    d = ImageDraw.Draw(base, "RGBA")

    def chaikin(pts, iters=2):
        for _ in range(iters):
            out = [pts[0]]
            for a, b in zip(pts, pts[1:]):
                out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
                out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
            out.append(pts[-1])
            pts = out
        return pts

    def remove_kinks(pts, max_turn_deg=60.0):
        if len(pts) < 3:
            return pts
        out = [pts[0]]
        i = 1
        while i < len(pts) - 1:
            ax, ay = out[-1]
            bx, by = pts[i]
            cx, cy = pts[i + 1]
            v1x, v1y = bx - ax, by - ay
            v2x, v2y = cx - bx, cy - by
            L1 = math.hypot(v1x, v1y) + 1e-12
            L2 = math.hypot(v2x, v2y) + 1e-12
            dot = max(-1.0, min(1.0, (v1x * v2x + v1y * v2y) / (L1 * L2)))
            turn = math.degrees(math.acos(dot))
            if turn > max_turn_deg:
                # skip kink point — bridge with midpoint
                out.append(((ax + cx) / 2, (ay + cy) / 2))
                i += 1
            else:
                out.append(pts[i])
            i += 1
        out.append(pts[-1])
        return out

    def densify(pts, step=2.5):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            n = max(1, int(L / step))
            for k in range(1, n + 1):
                f = k / n
                out.append((a[0] * (1 - f) + b[0] * f, a[1] * (1 - f) + b[1] * f))
        return out

    def meander(pts, amp=3.5, wavelength=42.0, seed=0):
        """Add soft natural sideways wobble (screen-space) for thin creeks."""
        if len(pts) < 3:
            return pts
        out = [pts[0]]
        dist = 0.0
        for i in range(1, len(pts)):
            ax, ay = pts[i - 1]; bx, by = pts[i]
            seg = math.hypot(bx - ax, by - ay) + 1e-9
            dist += seg
            tx, ty = (bx - ax) / seg, (by - ay) / seg
            nx, ny = -ty, tx
            # two harmonics, seeded phase
            phase = seed * 0.37
            off = (amp * math.sin(dist / wavelength * 2 * math.pi + phase)
                   + 0.45 * amp * math.sin(dist / (wavelength * 0.37) * 2 * math.pi + phase * 1.7))
            # taper near ends
            t = i / (len(pts) - 1)
            taper = math.sin(t * math.pi) ** 0.7
            out.append((bx + nx * off * taper, by + ny * off * taper))
        return out

    def stroke_creek(pts_ll, water_w, muted=False, add_meander=False, seed=0):
        if len(pts_ll) < 2:
            return
        pts = [ll2px(*c) for c in pts_ll]
        pts = densify(pts, step=3.0)
        pts = chaikin(pts, iters=3)
        pts = remove_kinks(pts, max_turn_deg=48.0)
        pts = remove_kinks(pts, max_turn_deg=48.0)
        pts = chaikin(pts, iters=1)
        pts = densify(pts, step=2.0)
        if add_meander:
            pts = meander(pts, amp=max(2.5, water_w * 0.55), wavelength=36.0 + seed, seed=seed)
            pts = chaikin(pts, iters=1)
            pts = densify(pts, step=2.0)
        if len(pts) < 2:
            return
        # All creeks: desaturated blue-gray, soft banks (no neon)
        bank = max(water_w + 6, int(water_w * 2.2))
        if muted:
            d.line(pts, fill=(100, 102, 95, 40), width=bank, joint="curve")
            d.line(pts, fill=(72, 80, 82, 90), width=water_w + 4, joint="curve")
            d.line(pts, fill=(104, 118, 126, 220), width=water_w, joint="curve")
            d.line(pts, fill=(118, 124, 122, 70), width=max(1, water_w // 2), joint="curve")
        else:
            d.line(pts, fill=(95, 105, 95, 55), width=bank, joint="curve")
            d.line(pts, fill=(96, 92, 84, 230), width=water_w + 9, joint="curve")
            d.line(pts, fill=(70, 78, 84, 220), width=water_w + 3, joint="curve")
            d.line(pts, fill=(104, 118, 126, 235), width=water_w, joint="curve")
            d.line(pts, fill=(130, 150, 155, 90), width=max(1, water_w // 3), joint="curve")
        # stony banks: small gray pebbles scattered along both banks
        _sr = np.random.default_rng(seed + 99)
        for _i in range(0, len(pts) - 1, 3):
            (_ax, _ay), (_bx, _by) = pts[_i], pts[_i + 1]
            _L = math.hypot(_bx - _ax, _by - _ay) + 1e-9; _nx, _ny = -(_by - _ay) / _L, (_bx - _ax) / _L
            for _sg in (-1, 1):
                if _sr.random() < 0.45: continue
                _o = _sg * (water_w / 2 + _sr.uniform(1, 5)); _r = _sr.uniform(1.2, 3.2)
                _x, _y = _ax + _nx * _o, _ay + _ny * _o; _g = int(_sr.uniform(120, 175))
                d.ellipse((_x - _r, _y - _r * 0.75, _x + _r, _y + _r * 0.75), fill=(_g, _g - 4, _g - 12, 230))

    specs = [
        ("opequon_creek", 12, False, False, 0),
        ("hoge_run", 4, True, True, 11),
        ("abrams_creek", 5, True, True, 5),
        ("buffalo_lick", 4, True, True, 7),
        ("town_run", 3, True, True, 3),
    ]
    # Winchester core — Abrams path through town is noisy; use Town Run there instead
    win_bbox = (-78.172, 39.173, -78.155, 39.193)

    def clip_out_winchester(wps):
        out = []
        for lon, lat in wps:
            if win_bbox[0] < lon < win_bbox[2] and win_bbox[1] < lat < win_bbox[3]:
                continue
            out.append([lon, lat])
        # break into contiguous runs
        if len(out) < 2:
            return []
        runs, cur = [], [out[0]]
        for a, b in zip(out, out[1:]):
            if abs(a[0] - b[0]) > 0.01 or abs(a[1] - b[1]) > 0.01:
                if len(cur) >= 2:
                    runs.append(cur)
                cur = [b]
            else:
                cur.append(b)
        if len(cur) >= 2:
            runs.append(cur)
        return runs

    for name, water_w, muted, add_m, seed in specs:
        if name not in FEAT["rivers"]:
            continue
        wps = FEAT["rivers"][name]["waypoints"]
        if name == "abrams_creek":
            for run in clip_out_winchester(wps):
                stroke_creek(run, water_w, muted=muted, add_meander=add_m, seed=seed)
        else:
            stroke_creek(wps, water_w, muted=muted, add_meander=add_m, seed=seed)
    return base

def draw_roads(base):
    d = ImageDraw.Draw(base, "RGBA")
    for k, rd in FEAT["roads"].items():
        pts = [ll2px(*c) for c in rd["waypoints"]]
        if rd.get("kind") == "pike":
            d.line(pts, fill=(42, 34, 26, 255), width=20, joint="curve")
            d.line(pts, fill=(118, 100, 72, 255), width=15, joint="curve")
            d.line(pts, fill=(168, 148, 112, 255), width=10, joint="curve")
        else:
            d.line(pts, fill=(48, 34, 22, 255), width=10, joint="curve")
            d.line(pts, fill=(120, 88, 55, 255), width=6, joint="curve")
    rr = [ll2px(*c) for c in FEAT["railroads"]["winchester_and_potomac"]["waypoints"]]
    d.line(rr, fill=(40, 34, 28, 255), width=3, joint="curve")
    d.line(rr, fill=(165, 150, 125, 255), width=9, joint="curve")
    for i in range(0, len(rr) - 1, 2):
        a, b = rr[i], rr[i + 1]
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        nx, ny = -math.sin(ang), math.cos(ang)
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        d.line([(mx - nx * 7, my - ny * 7), (mx + nx * 7, my + ny * 7)], fill=(90, 65, 42, 255), width=2)
    return base

def densify_ll(wps, step_m=18.0):
    """Densify lon/lat polyline to ~step_m spacing."""
    out = [wps[0]]
    for a, b in zip(wps, wps[1:]):
        dx = (b[0] - a[0]) * m_lon
        dy = (b[1] - a[1]) * m_lat
        L = math.hypot(dx, dy)
        n = max(1, int(L / step_m))
        for t in range(1, n + 1):
            f = t / n
            out.append([a[0] * (1 - f) + b[0] * f, a[1] * (1 - f) + b[1] * f])
    return out

def draw_stone_wall_sprites(base, lib):
    """Continuous dry-stone wall: one trimmed sprite per hexside, butt-joined at corners.
    No overlap, no doubled stones, no protruding end caps.
    """
    side_path = ROOT / "data/features/stone_wall_hexsides.json"
    if not side_path.exists():
        print("WARN: no stone_wall_hexsides.json"); return base
    data = json.loads(side_path.read_text())
    confed = {(int(c), int(r)) for c, r in data["confederate_hexes"]}
    if not confed:
        return base
    d = ImageDraw.Draw(base, "RGBA")
    size_m = G.size_m
    segs = lib.get("wall_segs_raw") or lib.get("wall_segs") or []
    if not segs:
        print("WARN: no wall_segs"); return base

    def verts_m(col, row):
        cx_m, cy_m = G.hex_to_xy_m(col, row)
        return [(cx_m + size_m * math.cos(math.radians(60 * i)),
                 cy_m + size_m * math.sin(math.radians(60 * i))) for i in range(6)]

    def to_scr(xm, ym):
        return xm * PX_PER_M, H - ym * PX_PER_M

    # N-edge + connectors between consecutive Confed hexes (W→E)
    ordered = sorted(confed)

    def n_edge(col, row):
        vs = verts_m(col, row)
        a, b = vs[1], vs[2]
        return (a, b) if a[0] <= b[0] else (b, a)

    chain = []  # list of (a_m, b_m) edges W→E
    for i, (col, row) in enumerate(ordered):
        a, b = n_edge(col, row)
        if chain:
            prev = chain[-1][1]
            if math.hypot(a[0] - prev[0], a[1] - prev[1]) > 1.0:
                chain.append((prev, a))
        chain.append((a, b))

    # Southward inset into Confed hexes
    inset_m = 4.0 / PX_PER_M
    inset_chain = []
    for a, b in chain:
        tx, ty = b[0] - a[0], b[1] - a[1]
        tL = math.hypot(tx, ty) + 1e-9
        n1x, n1y = -ty / tL, tx / tL
        n2x, n2y = ty / tL, -tx / tL
        nx, ny = (n1x, n1y) if n1y <= n2y else (n2x, n2y)
        inset_chain.append((
            (a[0] + nx * inset_m, a[1] + ny * inset_m),
            (b[0] + nx * inset_m, b[1] + ny * inset_m),
        ))

    # Screen-space poly for underlay shadow (single thin course)
    poly = []
    for a, b in inset_chain:
        sa, sb = to_scr(*a), to_scr(*b)
        if not poly:
            poly.append(sa)
        poly.append(sb)
    # Procedural continuous dry-stone wall along one polyline: no sprites, no posts/joints.
    wr = np.random.default_rng(1862)
    th = max(10.0, R_PX * 0.13)  # thin course width in px
    # Wall drawn INSIDE the Confederate hexes (offset ~35% of apothem south of the N edge),
    # one smoothed polyline -> continuous, no overlaps, not a hex outline.
    apo = R_PX * math.sqrt(3) / 2
    pts = []
    for col, row in ordered:
        cx, cy = hexc(col, row)
        yv = cy - 0.62 * apo
        pts += [(cx - 0.62 * R_PX, yv), (cx + 0.62 * R_PX, yv)]
    for _ in range(3):
        o = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            o += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        o.append(pts[-1]); pts = o
    # dense resample
    dense = [pts[0]]
    for p0, p1 in zip(pts, pts[1:]):
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); n = max(1, int(L / 1.0))
        for k in range(1, n + 1):
            f = k / n; dense.append((p0[0] * (1 - f) + p1[0] * f, p0[1] * (1 - f) + p1[1] * f))
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay, "RGBA")
    # cast shadow (light from NW -> shadow SE), soft
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh, "RGBA").line([(x + th * 0.45, y + th * 0.55) for x, y in pts],
                                    fill=(60, 50, 38, 120), width=int(th * 1.1), joint="curve")
    base = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(th * 0.35)))
    # mortarless dark bed
    ld.line(pts, fill=(88, 82, 72, 255), width=int(th), joint="curve")
    for x, y in pts:
        r = th / 2; ld.ellipse((x - r, y - r, x + r, y + r), fill=(88, 82, 72, 255))
    # individual stones walked along the path (two rough courses)
    acc = 0.0; i = 0
    while i < len(dense) - 1:
        sl = wr.uniform(th * 0.55, th * 1.05)
        j = min(len(dense) - 1, i + max(1, int(sl)))
        (x0, y0), (x1, y1) = dense[i], dense[j]
        tx, ty = x1 - x0, y1 - y0; L = math.hypot(tx, ty) + 1e-9; ux, uy = tx / L, ty / L
        nx, ny = -uy, ux
        for off, hw in ((-th * 0.22, th * 0.26), (th * 0.22, th * 0.26)):
            shift = wr.uniform(-0.25, 0.25) * th
            ax, ay = x0 + ux * shift + nx * off, y0 + uy * shift + ny * off
            bx, by = x1 + ux * shift + nx * off, y1 + uy * shift + ny * off
            g = wr.uniform(0.86, 1.08)
            base_c = np.array([158, 154, 146]) * g
            c = tuple(int(min(255, v)) for v in base_c) + (255,)
            q = [(ax + nx * hw + ux * 0.6, ay + ny * hw + uy * 0.6), (bx + nx * hw - ux * 0.6, by + ny * hw - uy * 0.6),
                 (bx - nx * hw - ux * 0.6, by - ny * hw - uy * 0.6), (ax - nx * hw + ux * 0.6, ay - ny * hw + uy * 0.6)]
            ld.polygon(q, fill=c)
            # top-left highlight edge
            hl = tuple(int(min(255, v * 1.12)) for v in base_c) + (200,)
            ld.line([q[0], q[1]], fill=hl, width=1)
        i = j
    lay = lay.filter(ImageFilter.GaussianBlur(0.45))
    base = Image.alpha_composite(base, lay)
    print(f"stone wall: procedural continuous {len(pts)-1} edges, th={th:.1f}px")
    return base

def place_fords(base, lib):
    for f in FEAT.get("fords", []):
        x, y = ll2px(f["lon"], f["lat"])
        paste_sprite(base, lib["ford"], x, y)
    return base

def place_landmarks(base, lib):
    """Pritchard-Grim farm on Pritchard's Hill; Kernstown village; rural props."""
    # --- Pritchard-Grim farm on Pritchard's Hill (open plateau) ---
    # cgpt2 stone farmhouse + bank barn; plus log cabin & tenant house
    ph_lon, ph_lat = -78.2020, 39.1545
    hx, hy = ll2px(ph_lon, ph_lat)
    phouse = lib.get("pritchard_house") or (lib["brick_houses"][0] if lib["brick_houses"] else lib["houses"][0])
    pbarn = lib.get("pritchard_barn") or (lib["barns"][0] if lib["barns"] else phouse)
    log_cabin = lib["houses"][1 % len(lib["houses"])]
    tenant = lib["houses"][2 % len(lib["houses"])]
    paste_sprite(base, phouse, hx - 6, hy - 2)          # stone Pritchard house
    paste_sprite(base, pbarn, hx + HOUSE_W * 1.05, hy + HOUSE_W * 0.55)
    paste_sprite(base, log_cabin, hx - HOUSE_W * 1.15, hy + 16)
    paste_sprite(base, tenant, hx + HOUSE_W * 0.15, hy + HOUSE_W * 0.95)
    FEAT.setdefault("_runtime", {})["pritchard_house_ll"] = [ph_lon, ph_lat]

    # Glass farmstead (unlabeled)
    gx, gy = ll2px(-78.2248, 39.1470)
    paste_sprite(base, lib["houses"][0], gx - 6, gy)
    if lib["barns"]:
        paste_sprite(base, lib["barns"][1 % len(lib["barns"])], gx + HOUSE_W * 0.85, gy + 6)

    # Opequon Church — stone church with graveyard (cgpt2)
    opequon = lib.get("opequon_church") or lib.get("church")
    paste_sprite(base, opequon, *ll2px(-78.1915, 39.1392))
    paste_sprite(base, lib["mill"], *ll2px(-78.175, 39.165))
    paste_sprite(base, lib["bridge"], *ll2px(-78.172, 39.146))

    # --- Kernstown: 8–12 buildings along Valley Pike + Cedar Creek Grade ---
    # Village cluster on the Pike (~N-S) and Grade branching west
    kx, ky = ll2px(-78.1978, 39.1425)
    # Toll house at Pike edge (south of village)
    toll = lib["houses"][0]
    paste_sprite(base, toll, *ll2px(-78.1982, 39.1398))
    # Buildings along Pike (NS)
    pike_spots = [
        (-78.1978, 39.1438), (-78.1976, 39.1428), (-78.1979, 39.1418),
        (-78.1975, 39.1408), (-78.1980, 39.1445),
    ]
    for i, (lon, lat) in enumerate(pike_spots):
        sp = lib["houses"][i % len(lib["houses"])]
        # square to Pike (NS street) — face westward/eastward
        ang = 90 if i % 2 == 0 else -90
        ssp = rotate_sprite(sp, ang)
        paste_sprite(base, ssp, *ll2px(lon, lat))
    # Buildings along Cedar Creek Grade (roughly EW west of Kernstown)
    grade_spots = [
        (-78.2005, 39.1420), (-78.2025, 39.1415), (-78.2045, 39.1412),
        (-78.1995, 39.1432), (-78.2015, 39.1405),
    ]
    for i, (lon, lat) in enumerate(grade_spots):
        sp = lib["houses"][(i + 3) % len(lib["houses"])]
        # Grade runs roughly E-W → buildings face N/S
        ang = 0 if i % 2 == 0 else 180
        ssp = rotate_sprite(sp, ang) if abs(ang) > 0.5 else sp
        paste_sprite(base, ssp, *ll2px(lon, lat))
    # Small outbuilding near toll
    if lib.get("outbuildings"):
        paste_sprite(base, lib["outbuildings"][0], *ll2px(-78.1970, 39.1395))

    print("landmarks: Pritchard-Grim farm + Kernstown village (~11 bldgs) + Opequon Church")
    return base


def place_winchester(base, lib):
    """March 1862 Winchester (~pop 4400): dense brick strip on Loudoun St only;
    side streets = detached houses, yards, gardens, outbuildings, vacant lots, orchards.
    Town ~25–40 hexes, mostly open; edges meet fields abruptly. Buildings square to streets.
    """
    loudoun = -78.1645
    streets_ns = {
        "Academy": -78.1690, "Braddock": -78.1672, "Loudoun": loudoun,
        "Cameron": -78.1624, "Kent": -78.1606, "East": -78.1588,
    }
    streets_ew = {
        "Fairfax": 39.1905, "Peyton": 39.1888, "Piccadilly": 39.1870,
        "Boscawen": 39.1839, "Amherst": 39.1816, "Cork": 39.1794,
        "Germain": 39.1774, "South": 39.1756,
    }
    lat_n, lat_s = 39.1910, 39.1758
    lon_w, lon_e = -78.1695, -78.1585
    c_lon, c_lat = -78.16444, 39.18389  # Frederick County Courthouse
    setback = 0.00022

    # --- muddy street surfaces (pale) ---
    street_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(street_layer, "RGBA")

    def muddy_lane(a, b, main=False):
        pts = [a, b]
        if main:
            wd = 34
        else:
            wd = 30
        d.line(pts, fill=(78, 62, 44, 235), width=wd + 6, joint="curve")
        d.line(pts, fill=(112, 88, 62, 250), width=wd, joint="curve")
        # wheel ruts + puddle-dark centre
        (ax, ay), (bx, by) = a, b
        L = math.hypot(bx - ax, by - ay) + 1e-9; nx, ny = -(by - ay) / L, (bx - ax) / L
        for o in (-wd * 0.22, wd * 0.22):
            d.line([(ax + nx * o, ay + ny * o), (bx + nx * o, by + ny * o)], fill=(96, 78, 56, 170), width=2)
        d.line([(ax, ay), (bx, by)], fill=(146, 122, 88, 120), width=max(2, wd // 5))

    # irregular lengths: town thins toward its edges (no full rectangular grid)
    ns_span = {"Braddock": (39.1774, 39.1905), "Loudoun": (lat_s - 0.0012, lat_n + 0.0012),
               "Cameron": (39.1794, 39.1888), "Kent": (39.1816, 39.1870)}
    ew_span = {"Peyton": (-78.1672, -78.1624), "Piccadilly": (-78.1680, -78.1606),
               "Boscawen": (-78.1690, -78.1600), "Amherst": (-78.1680, -78.1606),
               "Cork": (-78.1672, -78.1624), "Germain": (-78.1660, -78.1630)}
    for name, (la0, la1) in ns_span.items():
        muddy_lane(ll2px(streets_ns[name], la0), ll2px(streets_ns[name], la1), main=(name == "Loudoun"))
    for name, (lo0, lo1) in ew_span.items():
        muddy_lane(ll2px(lo0, streets_ew[name]), ll2px(lo1, streets_ew[name]), main=False)
    street_layer = street_layer.filter(ImageFilter.GaussianBlur(1.2))
    # fade street ends into fields (no hard rectangular grid)
    sx0, sy1 = ll2px(lon_w, lat_s); sx1, sy0 = ll2px(lon_e, lat_n)
    scx, scy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
    rx, ry = abs(sx1 - sx0) / 2, abs(sy1 - sy0) / 2
    fm = Image.new("L", base.size, 0)
    ImageDraw.Draw(fm).ellipse((scx - rx * 1.6, scy - ry * 1.45, scx + rx * 1.6, scy + ry * 1.45), fill=255)
    fm = fm.filter(ImageFilter.GaussianBlur(rx * 0.06))
    sa = np.array(street_layer); sa[:, :, 3] = (sa[:, :, 3].astype(np.float32) * np.array(fm, np.float32) / 255).astype(np.uint8)
    street_layer = Image.fromarray(sa, "RGBA")
    base = Image.alpha_composite(base, street_layer)

    # Courthouse square lawn
    cx, cy = ll2px(c_lon, c_lat)
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow, "RGBA")
    gd.ellipse((cx - 50, cy - 36, cx + 58, cy + 30), fill=(175, 168, 138, 90))
    base = Image.alpha_composite(base, glow.filter(ImageFilter.GaussianBlur(6)))

    def place_aligned(sp, lon, lat, angle_deg, sc=1.0):
        if sc != 1.0:
            sp = sp.resize((max(8, int(sp.size[0] * sc)), max(8, int(sp.size[1] * sc))),
                           Image.Resampling.LANCZOS)
        if abs(angle_deg) > 0.5:
            sp = rotate_sprite(sp, angle_deg)
        paste_sprite(base, sp, *ll2px(lon, lat))

    def yard_patch(lon, lat, w=28, h=18):
        x, y = ll2px(lon, lat)
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer, "RGBA")
        ld.ellipse((x - w, y - h, x + w, y + h), fill=(158, 162, 128, 55))
        base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(3)))

    def orchard(lon, lat, n=4):
        """Small leafless orchard — vacant-lot fruit trees."""
        if not lib["trees"]:
            return
        for i in range(n):
            ox = (i % 2 - 0.5) * 0.00035
            oy = (i // 2 - 0.5) * 0.00028
            sp = lib["trees"][i % len(lib["trees"])]
            # smaller orchard trees
            sc = 0.45
            sp = sp.resize((max(6, int(sp.size[0] * sc)), max(6, int(sp.size[1] * sc))),
                           Image.Resampling.LANCZOS)
            paste_sprite(base, sp, *ll2px(lon + ox, lat + oy))

    n_placed = 0
    rows = lib["townhouse_rows"] or lib["shop_rows"] or lib["brick_houses"]
    shops = lib["shop_rows"] or rows
    bricks = lib["brick_houses"] or lib["houses"]
    houses = lib["houses"] or bricks
    outs = lib.get("outbuildings") or []

    # === LOUDOUN ST: contiguous two-story brick commercial strip ===
    # From Germain to Peyton, both sides, continuous rows
    ew_lats = [streets_ew[k] for k in
               ["Peyton", "Piccadilly", "Boscawen", "Amherst", "Cork", "Germain"]]
    for j in range(len(ew_lats) - 1):
        la, lb = ew_lats[j], ew_lats[j + 1]
        n_b = 2  # continuous strip, not overcrowded
        for side, sgn, ang in (("w", -1, 90), ("e", +1, -90)):
            for k in range(n_b):
                t = (k + 0.5) / n_b
                lat = la + (lb - la) * t
                lon = loudoun + sgn * setback
                # leave courthouse square open
                if abs(lat - c_lat) < 0.0007 and abs(lon - c_lon) < 0.0010:
                    continue
                # occasional vacant lot breaks in the strip
                if (j + k + (0 if side == "w" else 2)) % 5 == 0:
                    continue
                pool = rows if (j + k) % 2 == 0 else shops
                sp = pool[(j * 5 + k + (0 if side == "w" else 3)) % len(pool)]
                place_aligned(sp, lon, lat, ang, sc=1.0)
                n_placed += 1

    # === SIDE STREETS: detached houses, yards, outbuildings, vacant lots ===
    # Explicit sparse placements — not continuous frontages
    side_lots = [
        # Braddock — sparse detached (Jackson HQ placed separately)
        ("Braddock", 39.1868, -1, 90), ("Braddock", 39.1848, 1, -90),
        ("Braddock", 39.1815, -1, 90), ("Braddock", 39.1788, 1, -90),
        # Cameron
        ("Cameron", 39.1885, 1, -90), ("Cameron", 39.1850, -1, 90),
        ("Cameron", 39.1810, 1, -90), ("Cameron", 39.1778, -1, 90),
        # Kent
        ("Kent", 39.1875, -1, 90), ("Kent", 39.1835, 1, -90),
        ("Kent", 39.1795, -1, 90),
        # Academy fringe
        ("Academy", 39.1860, 1, -90), ("Academy", 39.1815, 1, -90),
        # East fringe
        ("East", 39.1855, -1, 90), ("East", 39.1805, -1, 90),
    ]
    # Filter and place side-street houses
    for item in side_lots:
        if item[0] is None:
            continue
        sname, lat, sgn, ang = item
        lon = streets_ns[sname] + sgn * setback
        if abs(lat - c_lat) < 0.0005 and abs(lon - c_lon) < 0.001:
            continue
        use_brick = abs(lon - loudoun) < 0.0022
        sp = bricks[n_placed % len(bricks)] if use_brick else houses[n_placed % len(houses)]
        place_aligned(sp, lon, lat, ang, sc=0.92)
        yard_patch(lon + sgn * 0.00015, lat)
        # outbuilding behind house
        if outs and n_placed % 2 == 0:
            ob = outs[n_placed % len(outs)]
            place_aligned(ob, lon + sgn * 0.00038, lat + 0.00012, ang, sc=0.75)
        n_placed += 1

    # EW-facing detached houses on selected blocks (sparse)
    ew_houses = [
        ("Piccadilly", -78.1682, 1, 0), ("Piccadilly", -78.1612, -1, 180),
        ("Boscawen", -78.1685, 1, 0), ("Boscawen", -78.1608, -1, 180),
        ("Amherst", -78.1680, 1, 0), ("Amherst", -78.1615, -1, 180),
        ("Cork", -78.1678, 1, 0), ("Cork", -78.1605, -1, 180),
        ("Peyton", -78.1675, -1, 180), ("Fairfax", -78.1628, 1, 0),
    ]
    for ename, lon, sgn, ang in ew_houses:
        # skip if too close to Loudoun commercial
        if abs(lon - loudoun) < 0.0009:
            continue
        lat = streets_ew[ename] + sgn * setback
        sp = houses[n_placed % len(houses)]
        place_aligned(sp, lon, lat, ang, sc=0.90)
        yard_patch(lon, lat + sgn * 0.00012)
        if outs and n_placed % 3 == 0:
            place_aligned(outs[n_placed % len(outs)], lon + 0.00025, lat + sgn * 0.0003, ang, sc=0.7)
        n_placed += 1

    # Vacant lots + small orchards (clear space)
    for lon, lat in [(-78.1685, 39.1860), (-78.1610, 39.1855), (-78.1595, 39.1810),
                     (-78.1680, 39.1790), (-78.1605, 39.1770), (-78.1668, 39.1900)]:
        orchard(lon, lat, n=3)

    # === LANDMARKS ===
    # Frederick County Courthouse — Greek Revival, largest on Loudoun
    ch = lib.get("courthouse")
    if ch:
        cw = int(R_PX * 2 * 0.58)
        sc = cw / ch.size[0]
        ch = ch.resize((max(10, int(ch.size[0] * sc)), max(10, int(ch.size[1] * sc))),
                       Image.Resampling.LANCZOS)
        paste_sprite(base, ch, cx + 2, cy)
    FEAT.setdefault("_runtime", {})["courthouse_ll"] = [c_lon, c_lat]

    # Taylor Hotel — 125 N Loudoun, just N of courthouse
    t_lon, t_lat = loudoun + setback, 39.1856
    if rows:
        th = rows[0]
        place_aligned(th, t_lon, t_lat, -90, sc=1.15)
    FEAT.setdefault("_runtime", {})["taylor_hotel_ll"] = [t_lon, t_lat]

    # Jackson's HQ — Gothic cottage, 415 N Braddock
    j_lon, j_lat = streets_ns["Braddock"] - setback, 39.1888
    # Prefer cottage sprite
    cottage = None
    for cand in houses:
        cottage = cand
        break
    # Try load cottage if available in lib via houses; also check raw
    cot_path = PAINTED / "cgpt_cottage_laundry.png"
    if cot_path.exists():
        raw = load_painted("cgpt_cottage_laundry", target_w=int(R_PX * 2 * 0.42))
        cottage = prepare_sprite(raw, grade=0.20, shadow=True, fade=0.12)
    place_aligned(cottage, j_lon, j_lat, 90, sc=1.05)
    FEAT.setdefault("_runtime", {})["jackson_hq_ll"] = [j_lon, j_lat]

    # Churches
    # Christ Episcopal — W Boscawen / Washington (~Braddock–Academy)
    if lib.get("church"):
        place_aligned(lib["church"], -78.1680, streets_ew["Boscawen"] + setback, 0, sc=1.0)
    # Kent St Presbyterian — NE Kent & Boscawen
    if lib.get("steepled_church"):
        place_aligned(lib["steepled_church"], streets_ns["Kent"] + setback,
                      streets_ew["Boscawen"] + 0.0001, -90, sc=1.0)
        # Loudoun St Presbyterian (E Loudoun / Piccadilly area)
        place_aligned(lib["steepled_church"], loudoun + setback, 39.1865, -90, sc=0.95)
        # Old Stone / simple churches
        place_aligned(lib["church"] or lib["steepled_church"],
                      streets_ns["Cameron"] + 0.0001, streets_ew["Amherst"] + setback, 0, sc=0.9)
        place_aligned(lib["steepled_church"], streets_ns["Braddock"] - setback,
                      streets_ew["Cork"] + 0.0001, 90, sc=0.85)

    # Sparse fringe farmhouses at N/S Pike ends
    for lat in (39.1922, 39.1745):
        for k, sgn in enumerate((-1, +1)):
            place_aligned(houses[k % len(houses)], loudoun + sgn * setback, lat,
                          90 if sgn < 0 else -90, sc=0.85)

    # W&P depot
    if lib.get("depot"):
        rr = FEAT["railroads"]["winchester_and_potomac"]["waypoints"]
        east_rr = [p for p in rr if p[0] > -78.162 and 39.178 < p[1] < 39.190]
        if not east_rr:
            east_rr = [min(rr, key=lambda p: (p[0] + 78.160) ** 2 + (p[1] - 39.184) ** 2)]
        depot_pt = min(east_rr, key=lambda p: abs(p[1] - 39.184))
        dep = rotate_sprite(lib["depot"], -20)
        paste_sprite(base, dep, *ll2px(depot_pt[0], depot_pt[1]))
        FEAT.setdefault("_runtime", {})["depot_ll"] = list(depot_pt)

    # Earthworks
    base = draw_earthworks(base, lib)

    print(f"winchester: ~{n_placed} buildings (sparse 1862), Loudoun strip + detached sides")
    return base


def draw_earthworks(base, lib=None):
    """Subtle painted earthwork ridges with hatching — Fort Collier & Fort Alabama."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")

    def ridge_ring(lon, lat, rx, ry, n_seg=28):
        cx, cy = ll2px(lon, lat)
        pts = []
        for i in range(n_seg):
            a = 2 * math.pi * i / n_seg
            # irregular earthwork outline
            jitter = 0.88 + 0.14 * math.sin(i * 1.7)
            pts.append((cx + math.cos(a) * rx * jitter, cy + math.sin(a) * ry * jitter))
        # Outer berm (tan earth)
        d.line(pts + [pts[0]], fill=(130, 108, 78, 150), width=7, joint="curve")
        d.line(pts + [pts[0]], fill=(175, 158, 122, 175), width=4, joint="curve")
        # Inner ditch shadow
        inset = []
        for i, (px, py) in enumerate(pts):
            a = 2 * math.pi * i / n_seg
            inset.append((px - math.cos(a) * 4, py - math.sin(a) * 3))
        d.line(inset + [inset[0]], fill=(95, 80, 60, 90), width=2, joint="curve")
        # Hatching across parapet
        for i in range(0, n_seg, 2):
            a = 2 * math.pi * i / n_seg
            x0 = cx + math.cos(a) * rx * 0.92
            y0 = cy + math.sin(a) * ry * 0.92
            x1 = cx + math.cos(a) * rx * 1.05
            y1 = cy + math.sin(a) * ry * 1.05
            d.line([(x0, y0), (x1, y1)], fill=(115, 95, 70, 130), width=1)
        # Soft fill wash inside
        d.polygon(pts, fill=(155, 138, 105, 50))

        # Fort Collier — redoubt E of Martinsburg Pike, N edge of town
    ridge_ring(-78.1536, 39.2014, rx=R_PX * 1.15, ry=R_PX * 0.90, n_seg=24)
    FEAT.setdefault("_runtime", {})["fort_collier_ll"] = [-78.1536, 39.2014]

    # Fort Alabama — high ground NW (later Star Fort)
    ridge_ring(-78.1644, 39.2061, rx=R_PX * 1.35, ry=R_PX * 1.0, n_seg=20)
    ridge_ring(-78.1660, 39.2050, rx=R_PX * 0.7, ry=R_PX * 0.55, n_seg=16)
    FEAT.setdefault("_runtime", {})["fort_alabama_ll"] = [-78.1644, 39.2061]

    layer = layer.filter(ImageFilter.GaussianBlur(0.8))
    base = Image.alpha_composite(base, layer)

    # Painted earthwork vignettes (subtle) at the forts
    if lib and lib.get("earthworks"):
        ew0 = lib["earthworks"][0]
        paste_sprite(base, ew0, *ll2px(-78.1536, 39.2014))
        if len(lib["earthworks"]) > 1:
            paste_sprite(base, lib["earthworks"][1], *ll2px(-78.1644, 39.2061))
        else:
            paste_sprite(base, ew0, *ll2px(-78.1648, 39.2055))
    return base



def draw_labels(img, box=None, scale=1.0):

    """Understated labels: majors only + small Stone Wall beside the wall."""
    lab = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lab, "RGBA")
    major = load_font(int(26 * scale), True)
    place = load_font(int(20 * scale), True)
    minor = load_font(int(14 * scale), False)
    ox = box[0] if box else 0
    oy = box[1] if box else 0
    prit = next(p for p in FEAT["places"] if p["id"] == "pritchards_hill")
    sandy = next(p for p in FEAT["places"] if p["id"] == "sandy_ridge")
    court = FEAT.get("_runtime", {}).get("courthouse_ll", [-78.16444, 39.18389])
    # (name, lon, lat, font, dx, dy, stroke, priority, fill)
    ink = (28, 22, 16, 235)
    ink_light = (55, 48, 38, 195)  # understated Stone Wall
    taylor = FEAT.get("_runtime", {}).get("taylor_hotel_ll", [-78.1643, 39.1856])
    jackson = FEAT.get("_runtime", {}).get("jackson_hq_ll", [-78.1674, 39.1888])
    fort_c = FEAT.get("_runtime", {}).get("fort_collier_ll", [-78.1536, 39.2014])
    phouse = FEAT.get("_runtime", {}).get("pritchard_house_ll", [-78.2020, 39.1545])
    items = [
        ("WINCHESTER", -78.1645, 39.1900, major, 0, -16, 3, 100, ink),
        ("Courthouse", court[0], court[1], place, 16, -30, 2, 92, ink),
        ("Taylor Hotel", taylor[0], taylor[1], minor, 14, -18, 1, 84, ink),
        ("Fort Collier", fort_c[0], fort_c[1], minor, 10, -16, 1, 82, ink),
        ("Pritchard's Hill", prit["lon"], prit["lat"], place, -18, -36, 2, 90, ink),
        ("Pritchard House", phouse[0], phouse[1], minor, 12, 14, 1, 78, ink),
        ("Sandy Ridge", sandy["lon"], sandy["lat"], place, -40, -14, 2, 88, ink),
        ("Kernstown", -78.1978, 39.1425, place, 12, 18, 2, 86, ink),
        ("Opequon Church", -78.1915, 39.1392, place, 12, -30, 2, 82, ink),
        ("Valley Pike", -78.1975, 39.1580, minor, 16, -8, 2, 70, ink),
        ("Hoge Run", -78.200, 39.1408, minor, 10, 14, 1, 65, ink),
        ("Opequon Creek", -78.155, 39.160, minor, 0, 0, 1, 64, ink),
        ("Stone Wall", 0, 0, minor, -30, -26, 1, 95, ink_light),
    ]
    items.sort(key=lambda it: -it[7])
    placed_boxes = []

    def text_size(txt, fnt, st):
        bbox = ld.textbbox((0, 0), txt, font=fnt, stroke_width=st)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def overlaps(b):
        x0, y0, x1, y1 = b
        for px0, py0, px1, py1 in placed_boxes:
            if x0 < px1 + 6 and x1 > px0 - 6 and y0 < py1 + 4 and y1 > py0 - 4:
                return True
        return False

    for name, lon, lat, fnt, dx, dy, st, pri, fill in items:
        x, y = ll2px(lon, lat)
        if name == "Stone Wall":  # anchor to actual wall hexsides (N edge of hex 17,23)
            x, y = FEAT.get("_runtime", {}).get("stone_wall_label_xy") or (hexc(17, 23)[0], hexc(17, 23)[1] - R_PX * 0.87)
        x, y = x - ox + dx, y - oy + dy
        tw, th = text_size(name, fnt, st)
        candidates = [(0, 0), (12, -10), (-12, -10), (14, 8), (-16, 6), (0, -18), (20, 0)]
        placed = False
        for ox2, oy2 in candidates:
            bx0, by0 = x + ox2 - 2, y + oy2 - 2
            bb = (bx0, by0, bx0 + tw + 4, by0 + th + 4)
            if overlaps(bb):
                continue
            # light halo then ink
            halo = (245, 238, 220, 210)
            ld.text((x + ox2, y + oy2), name, font=fnt, fill=halo, stroke_width=st + 1, stroke_fill=halo)
            ld.text((x + ox2, y + oy2), name, font=fnt, fill=fill, stroke_width=max(0, st - 1), stroke_fill=(240, 232, 210, 180))
            placed_boxes.append(bb)
            placed = True
            break
        if not placed:
            ld.text((x, y), name, font=fnt, fill=fill, stroke_width=st, stroke_fill=(240, 232, 210, 160))
    return Image.alpha_composite(img.convert("RGBA"), lab)

def draw_legend(img):
    panel_w, panel_h = 300, 380
    margin = 24
    x0 = img.size[0] - panel_w - margin
    y0 = margin
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay, "RGBA")
    d.rounded_rectangle((x0, y0, x0 + panel_w, y0 + panel_h), radius=10,
                        fill=(236, 228, 206, 235), outline=(40, 32, 24, 255), width=2)
    title = load_font(20, True)
    body = load_font(14)
    small = load_font(12)
    d.text((x0 + 14, y0 + 10), "LEGEND", font=title, fill=(28, 22, 16, 255))
    d.text((x0 + 14, y0 + 34), "First Kernstown — 23 Mar 1862", font=small, fill=(60, 48, 36, 255))
    d.text((x0 + 14, y0 + 50), "1 hex = 250 yd  ·  N ↑", font=small, fill=(60, 48, 36, 255))
    items = [
        ("elevation", None, "Elevation (DEM)"),
        ("woods", (88, 72, 58), "Woods (oak/hickory/birch)"),
        ("open", (214, 192, 138), "Open field / broom straw"),
        ("marsh", (130, 145, 118), "Marsh / wet meadow"),
        ("wall", (210, 200, 178), "Stone wall (Conf. line)"),
        ("fence", (105, 78, 50), "Worm rail fence"),
        ("road", (168, 148, 112), "Roads / Valley Pike"),
        ("union", (50, 70, 140), "Union units (placeholder)"),
        ("confed", (140, 55, 50), "Confederate units (placeholder)"),
    ]
    yy = y0 + 74
    for key, col, label in items:
        if key == "elevation":
            for i in range(44):
                t = i / 43
                r = int(236 * (1 - t) + 102 * t)
                g = int(224 * (1 - t) + 74 * t)
                b = int(188 * (1 - t) + 50 * t)
                d.rectangle((x0 + 16 + i, yy + 4, x0 + 17 + i, yy + 16), fill=(r, g, b, 255))
            d.rectangle((x0 + 14, yy + 2, x0 + 62, yy + 18), outline=(40, 32, 24, 200), width=1)
        elif key == "wall":
            d.line([(x0 + 16, yy + 10), (x0 + 58, yy + 10)], fill=(40, 36, 30, 255), width=6)
            d.line([(x0 + 16, yy + 10), (x0 + 58, yy + 10)], fill=col + (255,), width=4)
        elif key == "fence":
            pts = [(x0 + 16 + i * 6, yy + 14 if i % 2 else yy + 6) for i in range(7)]
            d.line(pts, fill=col + (255,), width=2)
        elif key == "road":
            d.line([(x0 + 16, yy + 10), (x0 + 58, yy + 10)], fill=(42, 34, 26, 255), width=7)
            d.line([(x0 + 16, yy + 10), (x0 + 58, yy + 10)], fill=col + (255,), width=4)
        else:
            d.rectangle((x0 + 16, yy + 3, x0 + 56, yy + 17), fill=col + (220,), outline=(40, 32, 24, 200))
        d.text((x0 + 70, yy + 2), label, font=body, fill=(28, 22, 16, 255))
        yy += 28
    return Image.alpha_composite(img.convert("RGBA"), overlay)

def measure_report():
    spine = FEAT["ridge_cores"]["sandy_ridge"]
    wall = FEAT["stone_walls"]["glass_wall_sandy_ridge"]["waypoints"]
    prit = FEAT["ridge_cores"]["pritchards_hill"][1]
    hs, he = G.lonlat_to_hex(*spine[0]), G.lonlat_to_hex(*spine[-1])
    ww, we = G.lonlat_to_hex(*wall[0]), G.lonlat_to_hex(*wall[-1])
    wall_hexes = sorted({G.lonlat_to_hex(lon, lat) for lon, lat in wall})
    ph = G.lonlat_to_hex(*prit)
    wm = wall[len(wall) // 2]
    # Winchester hex span
    win_hexes = set()
    for lon in np.linspace(-78.1695, -78.1610, 20):
        for lat in np.linspace(39.1815, 39.1875, 16):
            win_hexes.add(G.lonlat_to_hex(float(lon), float(lat)))
    # Hoge vs wall clearance
    hoge = FEAT["rivers"]["hoge_run"]["waypoints"]
    min_d = min(
        min(math.hypot(h[0] - w[0], h[1] - w[1]) for w in wall[::4])
        for h in hoge[::3]
    )
    return {
        "ridge_length_hex": hex_dist(hs, he),
        "wall_end_dist_hex": hex_dist(ww, we),
        "wall_unique_hexes": len(wall_hexes),
        "wall_hexes": [list(h) for h in wall_hexes],
        "pritchard_hex": list(ph),
        "wall_to_pritchard_hex": hex_dist(G.lonlat_to_hex(*wm), ph),
        "winchester_hex_count": len(win_hexes),
        "hoge_min_dist_wall_m": round(min_d * 111000, 0),
        "vex": 1.0,
    }

def write_layer_tags(report):
    layers_dir = ROOT / "layers"
    layers_dir.mkdir(exist_ok=True)
    hexes_path = layers_dir / "kernstown_hexes.json"
    data = json.loads(hexes_path.read_text()) if hexes_path.exists() else {"cols": G.cols, "rows": G.rows, "hexes": {}}
    wall_set = {tuple(h) for h in report["wall_hexes"]}
    # Prefer Confederate wall hexes from hexside chain (authoritative)
    sw_path = ROOT / "data/features/stone_wall_hexsides.json"
    if sw_path.exists():
        sw = json.loads(sw_path.read_text())
        wall_set = {tuple(h) for h in sw.get("confederate_hexes", [])}
    marsh_hexes = set()
    for m in FEAT.get("marshes", {}).values():
        poly = m["polygon"]
        lons = [p[0] for p in poly]; lats = [p[1] for p in poly]
        for lon in np.linspace(min(lons) - 0.002, max(lons) + 0.002, 40):
            for lat in np.linspace(min(lats) - 0.002, max(lats) + 0.002, 40):
                x, y = lon, lat
                inside = False
                j = len(poly) - 1
                for i in range(len(poly)):
                    xi, yi = poly[i]; xj, yj = poly[j]
                    if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
                        inside = not inside
                    j = i
                if inside:
                    marsh_hexes.add(G.lonlat_to_hex(lon, lat))
    wall_wps = FEAT["stone_walls"]["glass_wall_sandy_ridge"]["waypoints"]
    wall_sides = []; prev = None
    for lon, lat in wall_wps[::3]:
        h = G.lonlat_to_hex(lon, lat)
        if prev and h != prev:
            wall_sides.append([list(prev), list(h)])
        prev = h
    sw_meta = {}
    sw_path = ROOT / "data/features/stone_wall_hexsides.json"
    if sw_path.exists():
        sw_meta = json.loads(sw_path.read_text())
    tags = {
        "marsh_hexes": [list(h) for h in sorted(marsh_hexes)],
        "stone_wall_hexes": [list(h) for h in sorted(wall_set)],
        "stone_wall_hexsides": sw_meta.get("hexsides", wall_sides),
        "stone_wall_confederate_hexes": [list(h) for h in sorted(wall_set)],
        "stone_wall_damage_modificator": sw_meta.get("damage_modificator", 35),
        "stone_wall_notes": sw_meta.get("notes", "") + " " + sw_meta.get("damage_modificator_notes", ""),
        "stone_wall_hex_sides": wall_sides,
        "measurements": report,
    }
    if isinstance(data, dict) and "hexes" in data:
        for c, r in marsh_hexes:
            cell = data["hexes"].setdefault(f"{c},{r}", {"col": c, "row": r})
            cell["marsh"] = True; cell["terrain_tag"] = "marsh"
        for c, r in wall_set:
            cell = data["hexes"].setdefault(f"{c},{r}", {"col": c, "row": r})
            cell["stone_wall"] = True
            cell["terrain_tag"] = "stone_wall"
            cell["damage_modificator"] = 35
            cell["wall_edge"] = "N"  # faces Union approach
        hexes_path.write_text(json.dumps(data, indent=2))
    # Frederick County Courthouse — primary VP hex in Winchester
    court_ll = FEAT.get("_runtime", {}).get("courthouse_ll", [-78.1633, 39.1852])
    cc, cr = G.lonlat_to_hex(court_ll[0], court_ll[1])
    tags["winchester_courthouse_vp"] = {
        "hex": [cc, cr],
        "lon": court_ll[0],
        "lat": court_ll[1],
        "name": "Frederick County Courthouse",
        "primary_vp": True,
        "victory_points": 1,
    }
    if isinstance(data, dict) and "hexes" in data:
        key = f"{cc},{cr}"
        cell = data["hexes"].setdefault(key, {"col": cc, "row": cr})
        cell["vp"] = True
        cell["primary_vp"] = True
        cell["vp_name"] = "Frederick County Courthouse"
        cell["victory_points"] = 1
        cell["terrain_tag"] = "city_vp"
        cell["label"] = "Courthouse"
        hexes_path.write_text(json.dumps(data, indent=2))
    # also stamp into features places
    places = FEAT.setdefault("places", [])
    if not any(p.get("id") == "frederick_courthouse" for p in places):
        places.append({
            "id": "frederick_courthouse",
            "name": "Frederick County Courthouse",
            "lon": court_ll[0],
            "lat": court_ll[1],
            "kind": "courthouse",
            "owner": "Union",
            "vp": True,
            "primary": True,
            "primary_vp": True,
        })
        (ROOT / "data/features/kernstown_features.json").write_text(json.dumps(FEAT, indent=2))
    (layers_dir / "kernstown_terrain_tags.json").write_text(json.dumps(tags, indent=2))
    print("tagged marsh", len(marsh_hexes), "wall", len(wall_set), "courthouse VP", (cc, cr))
    return tags

def render_previews(base, report):
    def grid_overlay(img, box=None, width=3, alpha=200):
        g = Image.new("RGBA", img.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(g, "RGBA")
        for col in range(G.cols):
            for row in range(G.rows):
                cx, cy = hexc(col, row)
                if box:
                    cx -= box[0]; cy -= box[1]
                    ww, hh = box[2] - box[0], box[3] - box[1]
                else:
                    ww, hh = W, H
                if cx < -R_PX or cy < -R_PX or cx > ww + R_PX or cy > hh + R_PX:
                    continue
                pts = [(cx + R_PX * math.cos(math.radians(60 * i)),
                        cy + R_PX * math.sin(math.radians(60 * i))) for i in range(6)]
                gd.line(pts + [pts[0]], fill=(24, 18, 12, alpha), width=width)
        return Image.alpha_composite(img, g)

    def crop_save(lon0, lat0, lon1, lat1, name, scale=1.45):
        x0, y1 = ll2px(lon0, lat0); x1, y0 = ll2px(lon1, lat1)
        box = (int(min(x0, x1)), int(min(y0, y1)), int(max(x0, x1)), int(max(y0, y1)))
        crop = base.crop(box)
        crop = grid_overlay(crop, box=box, width=3, alpha=150)
        crop = draw_labels(crop, box=box, scale=scale).convert("RGB")
        if max(crop.size) < 1600:
            s = 1600 / max(crop.size)
            crop = crop.resize((int(crop.size[0] * s), int(crop.size[1] * s)), Image.Resampling.LANCZOS)
        crop.save(OUT / name, quality=93)
        print("wrote", name, crop.size)

    crop_save(-78.242, 39.132, -78.188, 39.162, "closeup_sandy_wall_pritchard.jpg", 1.55)
    crop_save(-78.215, 39.130, -78.175, 39.155, "closeup_kernstown_pike.jpg", 1.55)
    crop_save(-78.176, 39.170, -78.148, 39.208, "closeup_winchester.jpg", 1.30)
    # Woods close-up (Sandy Ridge forest texture — oaks/hickories, sparse birches near water only)
    crop_save(-78.235, 39.135, -78.205, 39.155, "closeup_woods.jpg", 1.5)
    # 2x zoom on stone wall hexes
    crop_save(-78.230, 39.144, -78.212, 39.151, "closeup_wall_2x.jpg", 2.0)
    crop_save(-78.242, 39.132, -78.188, 39.162, "closeup_pritchards_hill.jpg", 1.55)
    crop_save(-78.242, 39.128, -78.175, 39.160, "closeup_kernstown_sandy_ridge.jpg", 1.4)
    crop_save(-78.242, 39.132, -78.188, 39.162, "closeup_oblique_demo.jpg", 1.55)

    full = grid_overlay(base.copy(), width=max(2, int(R_PX * 0.045)), alpha=160)
    full = draw_labels(full, scale=1.15)
    full = draw_legend(full).convert("RGB")
    full.save(OUT / "kernstown_full.jpg", quality=90)
    s = 2000 / max(full.size)
    full.resize((int(full.size[0] * s), int(full.size[1] * s)), Image.Resampling.LANCZOS).save(
        OUT / "kernstown_medium.jpg", quality=91)
    nogrid = draw_legend(draw_labels(base.copy(), scale=1.15)).convert("RGB")
    s2 = 2000 / max(nogrid.size)
    nogrid.resize((int(nogrid.size[0] * s2), int(nogrid.size[1] * s2)), Image.Resampling.LANCZOS).save(
        OUT / "kernstown_full_nogrid.jpg", quality=91)
    print("previews done", report)

def main():
    global FEAT
    FEAT = json.loads((ROOT / "data/features/kernstown_features.json").read_text())
    print(f"compose {W}x{H} R_px={R_PX:.1f} house_w={HOUSE_W} vex=1.0")
    assert PAINTED.exists()
    lib = build_sprite_library()
    base, t, slope, demh = build_rich_basemap()
    base = stamp_fields(base, lib["textures"], t)
    base = paint_pritchard_open(base, demh)
    base = TP.ground_pass(base)
    wx0_, wy1_ = ll2px(-78.178, 39.170); wx1_, wy0_ = ll2px(-78.148, 39.205)
    _forest_pre = forest_mask(t, slope)
    def _skip(c, r):
        x, y = hexc(c, r)
        if not (0 <= x < W and 0 <= y < H): return True
        if wx0_ - 60 < x < wx1_ + 60 and wy0_ - 60 < y < wy1_ + 60: return True
        return bool(_forest_pre[int(y), int(x)]) or t[int(y), int(x)] > 0.7
    base = TP.hex_patchwork(base, hexc, R_PX, G.cols, G.rows, _skip)
    base = paint_marsh(base, lib["textures"], lib)
    forest = _forest_pre
    print("forest cells", int(forest.sum()))
    _fh = {}
    for _c in range(G.cols):
        for _r in range(G.rows):
            _x, _y = hexc(_c, _r); _x0, _x1 = int(max(0, _x - R_PX * 0.6)), int(min(W, _x + R_PX * 0.6))
            _y0, _y1 = int(max(0, _y - R_PX * 0.5)), int(min(H, _y + R_PX * 0.5))
            if _x1 > _x0 and _y1 > _y0:
                _f = float(forest[_y0:_y1, _x0:_x1].mean())
                if _f > 0.02: _fh[f"{_c},{_r}"] = round(_f, 3)
    (ROOT / "data/layers").mkdir(parents=True, exist_ok=True)
    (ROOT / "data/layers/painted_forest_fraction.json").write_text(json.dumps(_fh))
    base = paint_woods(base, forest, lib)
    base = draw_hydro(base)
    base = draw_roads(base)
    base = place_fords(base, lib)
    base = place_landmarks(base, lib)
    base = place_winchester(base, lib)
    # Wall LAST among terrain props so it sits above ground/woods/farms and stays visible
    base = draw_stone_wall_sprites(base, lib)
    base = ImageEnhance.Contrast(base).enhance(1.06)
    base = ImageEnhance.Color(base).enhance(1.02)
    base.save(ROOT / "data/basemap_kernstown.png", compress_level=4)
    report = measure_report()
    json.dump({"W": W, "H": H, "px_per_m": PX_PER_M, "R_px": R_PX,
               "style": "painted-sheet1+sheet2; wall sprites; fixed Hoge Run; Winchester grid",
               "vex": 1.0, "measurements": report,
               "note": "previews only; no tile re-slice"},
              open(ROOT / "data/basemap_meta.json", "w"), indent=2)
    write_layer_tags(report)
    render_previews(base, report)
    print("MEASUREMENTS", json.dumps(report))
    print("DONE — no tile re-slice, no push")

if __name__ == "__main__":
    main()
