"""Shared hex-grid convention for CivilWar1: Hex of Steel's native flat-top EVEN-Q.

This copies the game exactly; there is no conversion layer. Source: the decompiled
Assembly-CSharp of HoS 8.4.14, which is not committed. The two methods it copies are:

* ``MapGO`` (``MapGO.cs:452-459``): tile (col, row) sits at
  ``x = col * 4.42``, ``y = row * 5.1 (+ 2.55 if col is even)``.
  Unity y points up, so **rows increase NORTH** and **EVEN columns are shifted half a row
  north**. The column-to-row pitch ratio is 4.42 : 5.1.
* ``Utils.GetAllTilesNeighbours``: an even column's neighbours are (c, r±1), (c±1, r+1)
  and (c±1, r). An odd column's are (c, r±1), (c±1, r) and (c±1, r-1).

Our (col, row) is the game's (PosX, PosY). Decided by Major Hotchkiss on 2026-10-17
(docs/decisions.md). The old odd-q layout and its ROW_DIRECTION switch are gone.

Edge ports (directive section IX): 0=N, 1=NE, 2=SE, 3=S, 4=SW, 5=NW;
opposite = (port + 3) % 6.

Native tile: 2000x2000 PNG with a centred flat-top hex 1910 px wide (vertex to
vertex) x 1672 px tall (flat to flat), per kernstown-map:data/hex_mask.png.
"""

from __future__ import annotations

from dataclasses import dataclass

# MapGO tile placement, in Unity world units.
GAME_COL_PITCH = 4.42
GAME_ROW_PITCH = 5.1
GAME_EVEN_COL_SHIFT = 2.55          # added to y for even columns (half a row north)
COL_PITCH_RATIO = GAME_COL_PITCH / GAME_ROW_PITCH   # 0.8667 (a regular hex would be 0.8660)

TILE_PX = 2000
HEX_WIDTH_PX = 1910   # flat-top: vertex-to-vertex, east-west
HEX_HEIGHT_PX = 1672  # flat-top: flat-to-flat, north-south

N, NE, SE, S, SW, NW = range(6)
PORT_NAMES = ("N", "NE", "SE", "S", "SW", "NW")

# Offset deltas (dc, dr) per port, from Utils.GetAllTilesNeighbours.
_EVEN_COL_DELTAS = ((0, 1), (1, 1), (1, 0), (0, -1), (-1, 0), (-1, 1))
_ODD_COL_DELTAS = ((0, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0))


def opposite_port(port: int) -> int:
    return (port + 3) % 6


def is_shifted_north(col: int) -> bool:
    """True for even columns, which MapGO lifts by half a row (+2.55)."""
    return col % 2 == 0


@dataclass(frozen=True)
class Hex:
    """Axial coordinate (q = column, r) for the flat-top grid, north-up."""
    q: int
    r: int


# Axial direction vectors, ordered by port (N, NE, SE, S, SW, NW).
_AXIAL_DIRS = ((0, 1), (1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1))


def axial_neighbors(h: Hex) -> list[Hex]:
    """Six axial neighbours ordered by port (N, NE, SE, S, SW, NW)."""
    return [Hex(h.q + dq, h.r + dr) for dq, dr in _AXIAL_DIRS]


def axial_distance(a: Hex, b: Hex) -> int:
    dq, dr = a.q - b.q, a.r - b.r
    return max(abs(dq), abs(dr), abs(dq + dr))


def offset_to_axial(col: int, row: int) -> Hex:
    """Even-q offset (game PosX, PosY) -> axial."""
    return Hex(col, row - (col + (col & 1)) // 2)


def axial_to_offset(h: Hex) -> tuple[int, int]:
    """Axial -> even-q offset (game PosX, PosY)."""
    return h.q, h.r + (h.q + (h.q & 1)) // 2


def offset_to_cube(col: int, row: int) -> tuple[int, int, int]:
    h = offset_to_axial(col, row)
    return h.q, h.r, -h.q - h.r


def cube_to_offset(x: int, y: int, z: int) -> tuple[int, int]:
    if x + y + z != 0:
        raise ValueError("cube coordinates must sum to 0")
    return axial_to_offset(Hex(x, y))


def offset_neighbor(col: int, row: int, port: int) -> tuple[int, int]:
    """Offset coordinate of the neighbour across edge ``port`` (geographic N/NE/...)."""
    dc, dr = (_EVEN_COL_DELTAS if is_shifted_north(col) else _ODD_COL_DELTAS)[port]
    return col + dc, row + dr


def offset_neighbors(col: int, row: int) -> list[tuple[int, int]]:
    """Neighbours ordered by port (N, NE, SE, S, SW, NW)."""
    return [offset_neighbor(col, row, p) for p in range(6)]


def offset_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    return axial_distance(offset_to_axial(*a), offset_to_axial(*b))


def game_position(col: int, row: int) -> tuple[float, float]:
    """Exact MapGO world position of tile (col, row)."""
    y = row * GAME_ROW_PITCH + (GAME_EVEN_COL_SHIFT if is_shifted_north(col) else 0.0)
    return col * GAME_COL_PITCH, y


def hex_center(col: int, row: int, spacing: float = 1.0) -> tuple[float, float]:
    """Centre (x east, y north), scaled so that the N-S neighbour spacing equals ``spacing``.

    This is game_position scaled by spacing / 5.1, so it keeps the game's 4.42:5.1 pitch.
    """
    gx, gy = game_position(col, row)
    k = spacing / GAME_ROW_PITCH
    return gx * k, gy * k


def point_to_offset(x: float, y: float, spacing: float = 1.0) -> tuple[int, int]:
    """Nearest tile centre to (x, y) on the hex_center grid (exact inverse at centres)."""
    c0 = round(x / (spacing * COL_PITCH_RATIO))
    best = None
    for c in (c0 - 1, c0, c0 + 1):
        shift = 0.5 if is_shifted_north(c) else 0.0
        r0 = round(y / spacing - shift)
        for r in (r0 - 1, r0, r0 + 1):
            cx, cy = hex_center(c, r, spacing)
            d = (cx - x) ** 2 + (cy - y) ** 2
            if best is None or d < best[0]:
                best = (d, c, r)
    return best[1], best[2]


def hex_line(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    """Chain of adjacent hexes from ``a`` to ``b`` inclusive (centre lerp + nearest-centre snap).

    The tiny nudge breaks ties the same way in the PowerShell port (tools/powershell/HexEvenQ.ps1).
    """
    n = offset_distance(a, b)
    ax, ay = hex_center(*a)
    bx, by = hex_center(*b)
    out = []
    for i in range(n + 1):
        t = 0.0 if n == 0 else i / n
        out.append(point_to_offset(ax + (bx - ax) * t + 1e-6, ay + (by - ay) * t + 2e-6))
    return out
