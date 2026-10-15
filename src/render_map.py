"""Render an intermediate-JSON hex map (hexwright-json) to a PNG image.

Draws pointy-top hexes in odd-r offset layout, colors terrain by code, and
labels towns and the Valley Pike. Usage:

    python src/render_map.py maps/generated/map_shenandoah_valley.json \
        --out maps/generated/map_shenandoah_valley.png
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

# Terrain colors keyed by name; codes resolved from payload["terrain_codes"].
# Palette follows Hex of Steel tile looks (Plain/Field/Rocky plain/HillForest/
# ThinForest/ThickForest/Mountain/River<N>/Marsh/Village/Road<N>).
TERRAIN_STYLE = {
    "plains":           ("#cfe3a4", None),
    "field":            ("#e3dda0", None),
    "rocky_plain":      ("#c2bd9a", None),
    "hills":            ("#e6c980", None),
    "mountains":        ("#9b8f86", None),
    "forest":           ("#5d9c5a", None),   # ThinForest
    "thick_forest":     ("#33703a", None),   # ThickForest
    "river":            ("#5fa8dc", None),
    "south_fork":       ("#5fa8dc", None),   # River1
    "north_fork":       ("#5fa8dc", None),   # River2
    "shenandoah_river": ("#4a94cf", None),   # River3
    "marsh":            ("#7fb2a0", None),
    "lake":             ("#3f7fc1", None),
    "city":             ("#f2d5a0", "#b02a2a"),
    "pike":             ("#d9b380", None),
    "road":             ("#cbb894", None),
}


def hex_corners(cx: float, cy: float, size: float) -> list[tuple[float, float]]:
    """Pointy-top hex corners."""
    return [
        (cx + size * math.cos(math.radians(60 * i - 30)),
         cy + size * math.sin(math.radians(60 * i - 30)))
        for i in range(6)
    ]


def axial_to_pixel(q: int, r: int, size: float) -> tuple[float, float]:
    x = size * math.sqrt(3.0) * (q + r / 2.0)
    y = size * 1.5 * r
    return x, y


def render(payload: dict, out_path: str | Path) -> Path:
    codes = {v: k for k, v in payload["terrain_codes"].items()}
    size = 1.0
    fig, ax = plt.subplots(figsize=(10, 14))

    # terrain tiles (offset col,row in odd-r layout -> axial for pointy-top pixels)
    def off_to_axial(col: int, row: int):
        return col - (row - (row & 1)) // 2, row

    for t in payload["tiles"]:
        q, r = off_to_axial(t["col"], t["row"])
        name = codes[t["terrain"]]
        face, edge = TERRAIN_STYLE[name]
        cx, cy = axial_to_pixel(q, r, size)
        ax.add_patch(Polygon(hex_corners(cx, cy, size * 0.98),
                             facecolor=face, edgecolor="#7a7a6a", linewidth=0.35))

    # pike polyline through waypoints (col,row -> axial -> pixel)
    pike_pts = [axial_to_pixel(*off_to_axial(c, r), size) for c, r in payload["pike_waypoints"]]
    ax.plot([p[0] for p in pike_pts], [p[1] for p in pike_pts],
            color="#7a4a1e", lw=2.2, ls="--", solid_capstyle="round", zorder=3)

    # secondary road polylines (group tiles by road name, preserve order)
    roads = payload.get("roads") or []
    grouped: dict[str, list[tuple[int, int]]] = {}
    for rd in roads:
        grouped.setdefault(rd["name"], []).append((rd["col"], rd["row"]))
    for pts in grouped.values():
        px = [axial_to_pixel(*off_to_axial(c, r), size) for c, r in pts]
        ax.plot([p[0] for p in px], [p[1] for p in px],
                color="#8a7350", lw=1.2, ls=":", solid_capstyle="round", zorder=3)

    # rivers are drawn per-tile already; add town labels
    for town in payload["towns"]:
        q, r = off_to_axial(town["col"], town["row"])
        cx, cy = axial_to_pixel(q, r, size)
        marker = "o" if town["size"] >= 2 else "s"
        ax.plot(cx, cy, marker, ms=7 if town["size"] >= 2 else 5,
                mfc="#b02a2a", mec="black", zorder=4)
        ax.annotate(town["name"], (cx, cy), textcoords="offset points",
                    xytext=(7, 4), fontsize=8, fontweight="bold", zorder=5)

    # deployment zone shading (light overlays on rows)
    for side, color in (("union", "#2a5db0"), ("confederate", "#5a5a5a")):
        zone = payload["deployment_zones"][side]
        r0, r1 = zone["rows"]
        for r in range(r0, r1 + 1):
            for c in range(payload["size_x"]):
                q = c - (r - (r & 1)) // 2
                cx, cy = axial_to_pixel(q, r, size)
                ax.add_patch(Polygon(hex_corners(cx, cy, size * 0.98),
                                     facecolor=color, alpha=0.10,
                                     edgecolor="none", zorder=2))

    ax.set_aspect("equal")
    ax.invert_yaxis()  # north at top
    ax.axis("off")
    ax.set_title(f"{payload['map_name']} — {payload['scenario_name']}", fontsize=13)

    # legend (HoS tile names where available)
    tile_names = payload.get("tile_names", {})
    legend_order = [
        "plains", "field", "rocky_plain", "hills", "mountains",
        "forest", "thick_forest", "shenandoah_river", "marsh", "city", "pike", "road",
    ]
    handles = []
    for name in legend_order:
        face, _edge = TERRAIN_STYLE[name]
        label = tile_names.get(name, name.title())
        handles.append(plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=face,
                                  markeredgecolor="#7a7a6a", markersize=10, label=label))
    handles.append(plt.Line2D([0], [0], color="#7a4a1e", lw=2, ls="--", label="Valley Pike"))
    ax.legend(handles=handles, loc="upper right", ncol=2, fontsize=8, framealpha=0.9)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Render a hexwright-json map to PNG.")
    ap.add_argument("json_file", help="Path to the intermediate JSON map.")
    ap.add_argument("--out", default=None, help="Output PNG path.")
    args = ap.parse_args()

    payload = json.loads(Path(args.json_file).read_text())
    out = args.out or str(Path(args.json_file).with_suffix(".png"))
    path = render(payload, out)
    print(f"Rendered {path}")


if __name__ == "__main__":
    main()
