"""Shared hex-grid convention for CivilWar1: flat-top ODD-Q.

Mirrors ``scripts/hex_grid.py`` on the ``kernstown-map`` branch (release
kernstown-v0.4.0). Columns run west to east. Odd columns sit half a row
offset in the direction of increasing row numbers. With ROW_DIRECTION = +1,
rows increase NORTH, so odd columns are shifted half a row north.

STATUS: matches Kernstown tooling. In-game confirmation is PENDING a corner-tile
test in Hex of Steel. If that test shows rows increase southward, set
ROW_DIRECTION = -1. That one-line change is the only edit needed.

Edge ports (directive section IX): 0=N, 1=NE, 2=SE, 3=S, 4=SW, 5=NW;
opposite = (port + 3) % 6.

Native tile: 2000x2000 PNG with a centred flat-top hex 1910 px wide (vertex to
vertex) x 1672 px tall (flat to flat), per kernstown-map:data/hex_mask.png.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# +1: row numbers increase NORTH (kernstown-map convention). -1: increase SOUTH.
ROW_DIRECTION = 1

TILE_PX = 2000
HEX_WIDTH_PX = 1910   # flat-top: vertex-to-vertex, east-west
HEX_HEIGHT_PX = 1672  # flat-top: flat-to-flat, north-south

N, NE, SE, S, SW, NW = range(6)
PORT_NAMES = ("N", "NE", "SE", "S", "SW", "NW")


def opposite_port(port: int) -> int:
    return (port + 3) % 6


@dataclass(frozen=True)
class Hex:
    """Axial coordinate (q = column, r) for the flat-top grid."""
    q: int
    r: int


# Axial direction vectors for flat-top hexes in "north-up" axial space,
# ordered by port (N, NE, SE, S, SW, NW).
_AXIAL_DIRS_NORTH_UP = ((0, 1), (1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1))


def axial_neighbors(h: Hex) -> list[Hex]:
    """Six axial neighbours, ordered by port with ROW_DIRECTION=+1 (N, NE, SE, S, SW, NW)."""
    return [Hex(h.q + dq, h.r + dr) for dq, dr in _AXIAL_DIRS_NORTH_UP]


def axial_distance(a: Hex, b: Hex) -> int:
    dq, dr = a.q - b.q, a.r - b.r
    return max(abs(dq), abs(dr), abs(dq + dr))


def offset_to_axial(col: int, row: int) -> Hex:
    """Flat-top odd-q offset -> axial (row measured along ROW_DIRECTION)."""
    return Hex(col, row - (col - (col & 1)) // 2)


def axial_to_offset(h: Hex) -> tuple[int, int]:
    """Axial -> flat-top odd-q offset; same formula as hex_grid._axial_to_oddr."""
    return h.q, h.r + (h.q - (h.q & 1)) // 2


def offset_neighbor(col: int, row: int, port: int) -> tuple[int, int]:
    """Offset coordinate of the neighbour across edge ``port`` (geographic N/NE/...)."""
    dq, dr = _AXIAL_DIRS_NORTH_UP[port]
    if ROW_DIRECTION < 0:  # mirror north/south when rows count southward
        dq, dr = _AXIAL_DIRS_NORTH_UP[(3 - port) % 6]
    nq, nr = axial_to_offset(Hex(*_add(offset_to_axial(col, row), dq, dr)))
    return nq, nr


def offset_neighbors(col: int, row: int) -> list[tuple[int, int]]:
    return [offset_neighbor(col, row, p) for p in range(6)]


def offset_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    return axial_distance(offset_to_axial(*a), offset_to_axial(*b))


def hex_center(col: int, row: int, spacing: float = 1.0) -> tuple[float, float]:
    """Centre (x east, y north) for neighbour spacing ``spacing``; mirrors GridSpec.hex_to_xy_m."""
    col_pitch = spacing * math.sqrt(3) / 2
    y = spacing * (row + 0.5 * (col & 1))
    return col_pitch * col, ROW_DIRECTION * y


def point_to_offset(x: float, y: float, spacing: float = 1.0) -> tuple[int, int]:
    """Inverse of hex_center; mirrors GridSpec.xy_m_to_hex (cube rounding)."""
    y = ROW_DIRECTION * y
    size = spacing / math.sqrt(3)
    q = (2 / 3 * x) / size
    r = (-1 / 3 * x + math.sqrt(3) / 3 * y) / size
    s = -q - r
    qq, rr, ss = round(q), round(r), round(s)
    dq, dr, ds = abs(qq - q), abs(rr - r), abs(ss - s)
    if dq > dr and dq > ds:
        qq = -rr - ss
    elif dr > ds:
        rr = -qq - ss
    return axial_to_offset(Hex(int(qq), int(rr)))


def _add(h: Hex, dq: int, dr: int) -> tuple[int, int]:
    return h.q + dq, h.r + dr
