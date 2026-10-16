#!/usr/bin/env python3
"""Render Kernstown preview: tile art + separate faint hex-grid layer + cartographic labels.

Grid is NEVER baked into tile PNGs. HoS tessellates hex sprites by alpha mask;
stock tiles likewise have no outline stroke (verified on maps/Plain.png).
This preview draws an adjustable grid overlay for review only (default faint).
"""
from __future__ import annotations
import json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
TILE_DIR = ROOT / "mod/Graphics/Tiles/Summer"
LAYERS = ROOT / "data/layers/kernstown_hexes.json"
OUT = ROOT / "previews"

# Preview geometry (flat-top even-q), radius in px
RADIUS = 14.0  # full map
GRID_ALPHA = 55  # 0–255, faint default
GRID_COLOR = (40, 34, 28, GRID_ALPHA)

def hex_corners(cx, cy, r):
    return [(cx + r * math.cos(math.radians(60 * i)), cy + r * math.sin(math.radians(60 * i))) for i in range(6)]

def center(col, row, r):
    x = r * 1.5 * col + r
    y = r * math.sqrt(3) * (row + (0.5 if col % 2 else 0.0)) + r
    return x, y

def load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def render(radius=RADIUS, grid_alpha=GRID_ALPHA, crop=None, out_name="kernstown_full.jpg", label_mode="full"):
    data = json.loads(LAYERS.read_text())
    cols, rows = data["grid"]["cols"], data["grid"]["rows"]
    by = {(h["col"], h["row"]): h for h in data["hexes"]}
    w = int(radius * 1.5 * (cols - 1) + radius * 2 + 40)
    h = int(radius * math.sqrt(3) * (rows + 0.5) + radius * 2 + 60)
    base = Image.new("RGBA", (w, h), (62, 54, 44, 255))
    grid_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    label_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cache = {}
    for (c, r), hx in by.items():
        name = hx["tile_name"]
        if name not in cache:
            p = TILE_DIR / f"{name}.png"
            if not p.exists():
                # fallback
                for alt in ("SV_Plain", "SV_Plain2"):
                    if (TILE_DIR / f"{alt}.png").exists():
                        p = TILE_DIR / f"{alt}.png"
                        break
            if p.exists():
                cache[name] = Image.open(p).convert("RGBA").resize(
                    (int(radius * 2), int(radius * 2)), Image.Resampling.LANCZOS
                )
            else:
                cache[name] = None
        tile = cache[name]
        cx, cy = center(c, r, radius)
        if tile:
            base.alpha_composite(tile, (int(cx - radius), int(cy - radius)))
        # grid on separate layer
        if grid_alpha > 0:
            gd = ImageDraw.Draw(grid_layer)
            pts = hex_corners(cx, cy, radius * 0.98)
            gd.line(pts + [pts[0]], fill=(40, 34, 28, grid_alpha), width=1)

    # Cartographic labels — major features prominent & offset; farms tiny
    ld = ImageDraw.Draw(label_layer)
    font_major = load_font(max(13, int(radius * 1.15)), bold=True)
    font_feat = load_font(max(11, int(radius * 0.95)), bold=True)
    font_farm = load_font(max(8, int(radius * 0.65)), bold=False)

    # Major labels with smart offsets (away from Pike/creek axes)
    majors = [
        # name, lon, lat, font, dx, dy, stroke
        ("WINCHESTER", -78.1633, 39.1885, font_major, 18, -16, 3),
        ("Kernstown", -78.1967, 39.1437, font_feat, 14, 12, 2),
        ("Opequon Church", -78.1925, 39.1408, font_feat, 16, -14, 2),
        ("Sandy Ridge", -78.2180, 39.1480, font_feat, -28, -10, 2),
        ("Pritchard's Hill", -78.2050, 39.1365, font_feat, 12, 14, 2),
        ("Valley Pike", -78.1750, 39.1700, font_feat, 22, 0, 2),
        ("Middle Road", -78.2380, 39.1600, font_feat, -36, 0, 2),
        ("Opequon Creek", -78.1480, 39.1550, font_feat, 14, 8, 2),
        ("W&P RR", -78.1450, 39.1950, font_feat, 10, -12, 2),
    ]
    farms = [
        ("Pritchard", -78.2010, 39.1410),
        ("Glass", -78.2160, 39.1465),
        ("Hoge Run", -78.1850, 39.1420),
        ("Abrams Creek", -78.1750, 39.2000),
        ("Bartonsville", -78.2100, 39.1160),
        ("Cedar Creek Grade", -78.2200, 39.1400),
        ("stone wall", -78.2180, 39.1450),
    ]

    from hex_grid import KERNSTOWN as G
    def place(lon, lat):
        col, row = G.lonlat_to_hex(lon, lat)
        return center(col, row, radius)

    if label_mode in ("full", "major"):
        for name, lon, lat, font, dx, dy, stroke in majors:
            x, y = place(lon, lat)
            # soft halo then text — offset so it sits beside terrain, not on roads
            ld.text((x + dx, y + dy), name, font=font, fill=(28, 22, 16, 240),
                    stroke_width=stroke, stroke_fill=(236, 228, 206, 200))
    if label_mode == "full":
        for name, lon, lat in farms:
            x, y = place(lon, lat)
            # tiny, low-contrast farm names
            ld.text((x + 8, y + 6), name, font=font_farm, fill=(55, 48, 38, 160),
                    stroke_width=1, stroke_fill=(220, 212, 192, 100))

    composed = Image.alpha_composite(base, grid_layer)
    composed = Image.alpha_composite(composed, label_layer)

    # title bar
    d = ImageDraw.Draw(composed)
    title = load_font(22, True)
    d.text((16, 10), "First Kernstown — 23 March 1862  ·  250 yd / hex  ·  early spring", font=title,
           fill=(245, 236, 214, 255), stroke_width=2, stroke_fill=(30, 24, 18, 200))
    d.text((16, 36), f"Grid overlay α={grid_alpha} (preview only; not in tile art)  ·  custom SV_* tiles",
           font=load_font(12), fill=(210, 200, 180, 220))

    if crop:
        composed = composed.crop(crop)
    OUT.mkdir(exist_ok=True)
    composed.convert("RGB").save(OUT / out_name, quality=92, optimize=True)
    print("wrote", OUT / out_name, composed.size)
    return composed

def main():
    # Full map, faint grid
    full = render(radius=13.5, grid_alpha=50, out_name="kernstown_full.jpg")
    # Also a no-grid version for beauty check
    render(radius=13.5, grid_alpha=0, out_name="kernstown_full_nogrid.jpg")
    # Close-ups: denser tiles, slightly stronger but still soft grid
    # Approximate crop regions from hex centers
    G = KERNSTOWN
    # Kernstown / Sandy Ridge area
    render(radius=28, grid_alpha=40, out_name="closeup_kernstown_sandy_ridge.jpg", label_mode="full")
    # Better: render full at larger radius then crop — memory heavy; instead re-render with focus
    # Winchester closeup
    render(radius=28, grid_alpha=40, out_name="closeup_winchester.jpg", label_mode="major")

    # Contact sheet authentic
    names = ["SV_ValleyPike1","SV_Road1","SV_Railroad1","SV_StoneWall","SV_Church",
             "SV_Kernstown","SV_WinchesterBlock","SV_Plain","SV_SandyRidge","SV_PritchardsHill"]
    cell = 200
    sheet = Image.new("RGBA", (cell * len(names), cell), (36, 32, 28, 255))
    for i, n in enumerate(names):
        p = TILE_DIR / f"{n}.png"
        if p.exists():
            sheet.alpha_composite(Image.open(p).resize((cell, cell), Image.Resampling.LANCZOS), (i * cell, 0))
    sheet.convert("RGB").save(OUT / "tile_contact_authentic.jpg", quality=92)
    print("previews complete")

if __name__ == "__main__":
    main()
