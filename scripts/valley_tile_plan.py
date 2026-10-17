"""Prototype: assign Valley-map tile names from a finite library and render a preview mosaic.

Grid: Hex of Steel native flat-top even-q from ``src.hex_utils`` (even columns half a row north, rows increase north).

Rules
-----
* Area classes (open, woods, hill, ...): several painted variants per class. The variant
  is chosen by a deterministic hash of (seed, class, col, row). If that variant equals an
  already-assigned neighbour's, the next one is taken, so identical tiles never touch
  when the class has three or more variants.
* Linear classes (road, pike, creek, river, rail): the tile key is class + 6-bit port mask
  (bit p set = feature exits through edge p; 0=N..5=NW). A tile is valid only if every
  set port is matched by the neighbour's opposite port. ``validate_ports`` checks this.
* Hero tiles (towns, gaps, bridges, battlefields) are fixed names and are never hashed.
* Transforms: none by default. The Kernstown art is a north-looking oblique view lit
  from the NW, so mirroring or rotating would put shadows on the wrong side.

Tile names follow the HoS rule that a tile's Name equals its PNG filename in
Graphics/Tiles/<Season>/: ``SV_<CLASS>_<variant>`` for area tiles,
``SV_<CLASS>_P<mask:02d>_<variant>`` for linear tiles, ``SV_HERO_<id>`` for hero tiles.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import hex_utils as hu  # noqa: E402

LINEAR = {"road", "pike", "creek", "river", "rail"}


def stable_hash(*parts) -> int:
    return int.from_bytes(hashlib.blake2b("|".join(map(str, parts)).encode(), digest_size=8).digest(), "big")


@dataclass
class Library:
    """class -> list of variant tile names; linear classes keyed by (class, mask)."""
    area: dict[str, list[str]] = field(default_factory=dict)
    linear: dict[tuple[str, int], list[str]] = field(default_factory=dict)
    hero: set[str] = field(default_factory=set)

    def candidates(self, cls: str, mask: int = 0) -> list[str]:
        if cls in LINEAR:
            return self.linear.get((cls, mask), [])
        return self.area.get(cls, [])


@dataclass
class Cell:
    cls: str
    ports: dict[str, int] = field(default_factory=dict)  # linear class -> 6-bit mask
    hero: str | None = None


def assign_tiles(grid: dict[tuple[int, int], Cell], lib: Library, seed: int = 1862) -> dict[tuple[int, int], str]:
    out: dict[tuple[int, int], str] = {}
    for (col, row) in sorted(grid):  # deterministic order
        cell = grid[(col, row)]
        if cell.hero:
            out[(col, row)] = cell.hero
            continue
        if cell.ports:  # a hex shows its dominant linear feature
            cls = sorted(cell.ports, key=lambda c: ("river", "pike", "rail", "road", "creek").index(c))[0]
            cands = lib.candidates(cls, cell.ports[cls])
        else:
            cls, cands = cell.cls, lib.candidates(cell.cls)
        if not cands:
            raise KeyError(f"no tile for {cls} mask={cell.ports.get(cls, 0):06b} at {(col, row)}")
        i = stable_hash(seed, cls, cell.ports.get(cls, 0), col, row) % len(cands)
        taken = {out.get(n) for n in hu.offset_neighbors(col, row)}
        for step in range(len(cands)):
            name = cands[(i + step) % len(cands)]
            if name not in taken:
                break
        out[(col, row)] = name
    return out


def validate_ports(grid: dict[tuple[int, int], Cell]) -> list[str]:
    """Every linear port must have a reciprocal port on the neighbour (or leave the map)."""
    errs = []
    for (col, row), cell in grid.items():
        for cls, mask in cell.ports.items():
            for p in range(6):
                if mask >> p & 1:
                    nb = hu.offset_neighbor(col, row, p)
                    if nb not in grid:
                        continue  # map edge: allowed exit / entry point
                    if not grid[nb].ports.get(cls, 0) >> hu.opposite_port(p) & 1:
                        errs.append(f"{cls} {(col, row)} port {hu.PORT_NAMES[p]} -> {nb} has no {hu.PORT_NAMES[hu.opposite_port(p)]}")
    return errs


def trace_path(grid, cls: str, path: list[tuple[int, int]]) -> None:
    """Set reciprocal ports along a chain of adjacent hexes."""
    for a, b in zip(path, path[1:]):
        p = hu.offset_neighbors(*a).index(b)
        grid[a].ports[cls] = grid[a].ports.get(cls, 0) | 1 << p
        grid[b].ports[cls] = grid[b].ports.get(cls, 0) | 1 << hu.opposite_port(p)


# ---------------------------------------------------------------- preview
def render_preview(assign, thumb_for, out_png: Path, thumb_px: int = 200, overlay=None):
    """Mosaic downscaled tiles on the native even-q grid (north up, game pitch 4.42:5.1)."""
    from PIL import Image, ImageDraw
    w_hex, h_hex = thumb_px * hu.HEX_WIDTH_PX / hu.TILE_PX, thumb_px * hu.HEX_HEIGHT_PX / hu.TILE_PX
    cols = [c for c, _ in assign]; rows = [r for _, r in assign]
    c0, r0, r1 = min(cols), min(rows), max(rows)

    def xy(c, r):
        x = (c - c0) * hu.COL_PITCH_RATIO * h_hex
        y = (r1 - r + (0.0 if hu.is_shifted_north(c) else 0.5)) * h_hex  # even columns sit half a row north
        return x, y

    W = int((max(cols) - c0) * hu.COL_PITCH_RATIO * h_hex + thumb_px)
    H = int((r1 - r0 + 1.5) * h_hex + thumb_px)
    canvas = Image.new("RGBA", (W, H), (235, 230, 220, 255))
    for (c, r) in sorted(assign, key=lambda k: -k[1]):  # paint north first, south on top
        x, y = xy(c, r)
        canvas.alpha_composite(thumb_for(assign[(c, r)]), (int(round(x)), int(round(y))))
    if overlay:
        d = ImageDraw.Draw(canvas)
        for cls, path, colour in overlay:
            pts = [(xy(c, r)[0] + thumb_px / 2, xy(c, r)[1] + thumb_px / 2) for c, r in path]
            d.line(pts, fill=colour, width=max(2, thumb_px // 40))
    canvas.convert("RGB").save(out_png, optimize=True)
    return out_png


def seam_error(assign, thumb_for, thumb_px: int = 200, band: int = 3) -> float:
    """Mean RGB difference across N/S shared edges (pixels just inside each tile), lower = smoother."""
    import numpy as np
    h_hex = thumb_px * hu.HEX_HEIGHT_PX / hu.TILE_PX
    top, bot = int(round((thumb_px - h_hex) / 2)) + 1, int(round((thumb_px + h_hex) / 2)) - 2
    x0, x1 = int(thumb_px * 0.38), int(thumb_px * 0.62)
    diffs = []
    for (c, r), name in assign.items():
        n = hu.offset_neighbor(c, r, hu.N)
        if n in assign:
            a = np.asarray(thumb_for(name))[top:top + band, x0:x1, :3].astype(float)
            b = np.asarray(thumb_for(assign[n]))[bot - band:bot, x0:x1, :3].astype(float)
            diffs.append(np.abs(a.mean(0) - b.mean(0)).mean())
    return float(sum(diffs) / len(diffs)) if diffs else 0.0


def harmonize_rim(img, rim_rgb, rim_frac: float = 0.18):
    """Derivative preview tile: fade the outer rim toward a shared class colour.

    Two tiles of the same class then meet at nearly the same colour along any edge.
    Preview only. Never written over a source tile.
    """
    import numpy as np
    from PIL import Image
    a = np.asarray(img).astype(float)
    n = a.shape[0]
    yy, xx = np.mgrid[0:n, 0:n]
    cx = cy = (n - 1) / 2
    R = n * hu.HEX_WIDTH_PX / hu.TILE_PX / 2           # centre -> vertex
    ax, ay = np.abs(xx - cx), np.abs(yy - cy)
    # normalised flat-top hex distance: 1.0 on the boundary
    d = np.maximum(ay / (R * 0.8660254), (ax * 0.8660254 + ay * 0.5) / (R * 0.8660254))
    w = np.clip((d - (1 - rim_frac)) / rim_frac, 0, 1)[..., None] ** 1.5
    a[..., :3] = a[..., :3] * (1 - w) + np.asarray(rim_rgb, float) * w
    return Image.fromarray(a.astype("uint8"), "RGBA")


def class_rim_colour(thumbs):
    import numpy as np
    px = np.concatenate([np.asarray(t)[..., :3][np.asarray(t)[..., 3] > 200] for t in thumbs])
    return tuple(int(v) for v in np.median(px, 0))


# ---------------------------------------------------------------- demo
def kernstown_library(game_json: Path, thumbs: Path) -> Library:
    """Area-class library from Kernstown slices present in ``thumbs`` (read-only use)."""
    hexes = json.loads(game_json.read_text())["hexes"]
    cls_of = {"open": "open", "woods": "woods", "hill": "hill"}
    lib = Library()
    for h in hexes:
        name = h["tile_name"]
        if (thumbs / f"{name}.png").exists() and h["tag"] in cls_of and not h["city"]:
            lib.area.setdefault(cls_of[h["tag"]], []).append(name)
    return lib


def demo_grid(cols=24, rows=18) -> tuple[dict, list]:
    """Synthetic test region: farmland, a NE-SW wooded ridge with hill shoulders, a N-S pike, a creek."""
    g = {}
    for c in range(cols):
        for r in range(rows):
            d = (c - 0.9 * r) - 4
            g[(c, r)] = Cell("woods" if abs(d) < 1.6 else "hill" if abs(d) < 3.0 else "open")
    pike = [(12, r) for r in range(rows)]
    creek = [(c, 3 + (c + 1) // 2) for c in range(19)]  # zig-zag NE on even-q: (0,3) (1,4) (2,4) ... (18,12)
    for path in (pike, creek):  # make sure consecutive cells are true neighbours
        for a, b in zip(path, path[1:]):
            assert b in hu.offset_neighbors(*a), (a, b)
    trace_path(g, "pike", pike)
    trace_path(g, "creek", creek)
    return g, [("pike", pike, (90, 90, 90, 255)), ("creek", creek, (70, 110, 150, 255))]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--game-json", type=Path, required=True, help="kernstown-map data/layers/kernstown_game.json (read-only)")
    ap.add_argument("--thumbs", type=Path, required=True, help="folder of downscaled SV_K_*.png tiles")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--harmonize", action="store_true", help="preview with rim-harmonised derivative tiles")
    ap.add_argument("--variants", type=int, default=0, help="cap variants per class (0 = all available)")
    a = ap.parse_args(argv)
    from PIL import Image
    cache = {}

    def thumb(name):
        if name not in cache:
            cache[name] = Image.open(a.thumbs / f"{name}.png").convert("RGBA")
        return cache[name]

    lib = kernstown_library(a.game_json, a.thumbs)
    if a.variants:
        lib.area = {k: v[:a.variants] for k, v in lib.area.items()}
    if a.harmonize:
        raw = thumb
        rim = {k: class_rim_colour([raw(n) for n in v]) for k, v in lib.area.items()}
        cls_of = {n: k for k, v in lib.area.items() for n in v}
        hcache = {}

        def thumb(name):  # noqa: F811
            if name not in hcache:
                hcache[name] = harmonize_rim(raw(name), rim[cls_of[name]])
            return hcache[name]
    grid, overlay = demo_grid()
    errs = validate_ports(grid)
    area_only = {k: Cell(v.cls) for k, v in grid.items()}  # Kernstown has no port-indexed road tiles yet
    assign = assign_tiles(area_only, lib)
    a.out.mkdir(parents=True, exist_ok=True)
    tag = f"v{a.variants or 'all'}" + ("_harmonized" if a.harmonize else "")
    png = render_preview(assign, thumb, a.out / f"valley_tile_plan_preview_{tag}.png", overlay=overlay)
    report = {
        "variants_per_class": {k: len(v) for k, v in lib.area.items()},
        "unique_tiles_used": len(set(assign.values())), "hexes": len(assign),
        "port_errors": errs, "seam_error_hashed": round(seam_error(assign, thumb), 2),
        "preview": str(png),
    }
    (a.out / f"valley_tile_plan_report_{tag}.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
