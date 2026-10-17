"""Hex grid in Hex of Steel's own convention (decided 2026-10-17, see docs/decisions.md).

Source of truth: the decompiled game, Assembly-CSharp 8.4.14 (/workspace/hosdll/src):
  MapGO.cs:452-459   odd column : position = (col*4.42, row*5.1)
                     even column: position = (col*4.42, row*5.1 + 2.55)
  Utils.cs:1666-1706 neighbours from the array index: N/S = (c, r+-1); even c -> (c+-1, r), (c+-1, r+1);
                     odd c -> (c+-1, r), (c+-1, r-1)
  CameraGO.cs        no rotation; "up" moves +y, so a higher row is further north on screen.
  ACW sample .sav    row 0 is south (New Orleans y=6, Pittsburgh y=57), col 0 is west.

So: flat-top hexes, origin (0,0) = south-west hex, columns run east, rows run NORTH,
EVEN columns are raised half a row, column pitch : row pitch = 4.42 : 5.1.
There is no conversion layer: (col, row) here IS the game's (PosX, PosY) and the tile index.

Tile pixels (ModsManager.cs:996-1027, "Graphics/Tiles"): a tile PNG is resized to 512 px wide and the
sprite gets ppu = 330 * 512 / source_width, i.e. 330 source pixels per world unit at prefab scale 1, pivot
at the centre. So a 2000 px tile is 6.06 x 6.06 units; row pitch = 5.1*330 = 1683 px, column pitch =
4.42*330 = 1458.6 px. (The TileGO prefab scale lives in a Unity asset, not in code; it is assumed 1 and
the slicer's 21.5 px alpha bleed covers +-20 px of error.)
"""
from __future__ import annotations
import math
from dataclasses import dataclass

# ---- the game's numbers (MapGO.cs:452-459, ModsManager.cs:1023-1026) ----
GAME_COL_PITCH = 4.42
GAME_ROW_PITCH = 5.1
GAME_EVEN_RAISE = 2.55
TILE_PX_PER_UNIT = 330.0
TILE_SIZE_PX = 2000
TILE_CENTER_PX = 999.5                                    # pivot (0.5, 0.5) of a 2000 px sprite, pixel-index coords
TILE_ROW_PITCH_PX = GAME_ROW_PITCH * TILE_PX_PER_UNIT     # 1683.0
TILE_COL_PITCH_PX = GAME_COL_PITCH * TILE_PX_PER_UNIT     # 1458.6
TILE_HEX_HALF_H_PX = TILE_ROW_PITCH_PX / 2                # 841.5  (flat edge to centre)
TILE_HEX_HALF_W_PX = TILE_COL_PITCH_PX * 2 / 3            # 972.4  (vertex to centre)


def is_raised(col: int) -> bool:
    """Even columns sit half a row north (MapGO.cs:456-459)."""
    return col % 2 == 0


def game_xy(col: int, row: int) -> tuple[float, float]:
    """Exactly MapGO.cs:452-459: world position of tile (col, row); +y = north."""
    return col * GAME_COL_PITCH, row * GAME_ROW_PITCH + (GAME_EVEN_RAISE if col % 2 == 0 else 0.0)


# ---- offset <-> axial (even columns raised, rows north) ----
def offset_to_axial(col: int, row: int) -> tuple[int, int]:
    return col, row - (col + (col & 1)) // 2


def axial_to_offset(q: int, r: int) -> tuple[int, int]:
    return q, r + (q + (q & 1)) // 2


def offset_to_cube(col: int, row: int) -> tuple[int, int, int]:
    q, r = offset_to_axial(col, row)
    return q, r, -q - r


def cube_to_offset(q: int, r: int) -> tuple[int, int]:
    return axial_to_offset(q, r)


def cube_round(q: float, r: float, s: float | None = None) -> tuple[int, int, int]:
    s = -q - r if s is None else s
    qq, rr, ss = round(q), round(r), round(s)
    dq, dr, ds = abs(qq - q), abs(rr - r), abs(ss - s)
    if dq > dr and dq > ds:
        qq = -rr - ss
    elif dr > ds:
        rr = -qq - ss
    else:
        ss = -qq - rr
    return int(qq), int(rr), int(ss)


DIRECTIONS = ("N", "NE", "SE", "S", "SW", "NW")


def neighbor(col: int, row: int, d: str) -> tuple[int, int]:
    """Same adjacency as Utils.GetAllTilesNeighbours."""
    up = 1 if col % 2 == 0 else 0           # even column raised
    return {"N": (col, row + 1), "S": (col, row - 1),
            "NE": (col + 1, row + up), "SE": (col + 1, row + up - 1),
            "NW": (col - 1, row + up), "SW": (col - 1, row + up - 1)}[d]


def neighbors(col: int, row: int) -> list[tuple[int, int]]:
    return [neighbor(col, row, d) for d in DIRECTIONS]


def hex_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    p, q = offset_to_cube(*a), offset_to_cube(*b)
    return max(abs(p[i] - q[i]) for i in range(3))


def hex_line(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    q1, r1, _ = offset_to_cube(*a)
    q2, r2, _ = offset_to_cube(*b)
    n = hex_distance(a, b)
    if n == 0:
        return [a]
    out = []
    for i in range(n + 1):
        t = i / n
        q, r, _ = cube_round(q1 + (q2 - q1) * t + 1e-6, r1 + (r2 - r1) * t + 1e-6)
        h = cube_to_offset(q, r)
        if not out or out[-1] != h:
            out.append(h)
    return out


@dataclass(frozen=True)
class GridSpec:
    west: float
    south: float
    east: float
    north: float
    cols: int
    rows: int
    hex_yards: float = 250.0      # N-S neighbour distance (= one row)
    x0_m: float = 0.0             # ground metres east of `west` of game x = 0
    y0_m: float = 0.0             # ground metres north of `south` of game y = 0

    @property
    def hex_m(self) -> float:
        return self.hex_yards * 0.9144

    @property
    def m_per_unit(self) -> float:
        """Ground metres per game world unit (one row = 5.1 units = hex_m)."""
        return self.hex_m / GAME_ROW_PITCH

    @property
    def row_pitch_m(self) -> float:
        return self.hex_m

    @property
    def col_pitch_m(self) -> float:
        return GAME_COL_PITCH * self.m_per_unit           # 4.42/5.1 of a row

    @property
    def size_m(self) -> float:
        """Nominal outer radius (regular-hex value, used by the painters for sprite scale)."""
        return self.hex_m / math.sqrt(3)

    @property
    def cell_half_w_m(self) -> float:
        return self.col_pitch_m * 2 / 3

    def meters_per_deg(self, lat: float) -> tuple[float, float]:
        m_lat = 111_132.0
        m_lon = 111_132.0 * math.cos(math.radians(lat))
        return m_lat, m_lon

    def lonlat_to_xy_m(self, lon: float, lat: float) -> tuple[float, float]:
        mid = (self.south + self.north) / 2
        m_lat, m_lon = self.meters_per_deg(mid)
        return (lon - self.west) * m_lon, (lat - self.south) * m_lat

    def xy_m_to_lonlat(self, x: float, y: float) -> tuple[float, float]:
        mid = (self.south + self.north) / 2
        m_lat, m_lon = self.meters_per_deg(mid)
        return self.west + x / m_lon, self.south + y / m_lat

    def hex_to_xy_m(self, col: int, row: int) -> tuple[float, float]:
        gx, gy = game_xy(col, row)
        return self.x0_m + gx * self.m_per_unit, self.y0_m + gy * self.m_per_unit

    def xy_m_to_game(self, x: float, y: float) -> tuple[float, float]:
        return (x - self.x0_m) / self.m_per_unit, (y - self.y0_m) / self.m_per_unit

    def xy_m_to_hex(self, x: float, y: float) -> tuple[int, int]:
        """Hex whose centre is nearest (exact cell membership); may be outside 0..cols/rows."""
        gx, gy = self.xy_m_to_game(x, y)
        c0 = round(gx / GAME_COL_PITCH)
        best, bd = None, 1e18
        for c in (c0 - 1, c0, c0 + 1):
            raise_ = GAME_EVEN_RAISE if c % 2 == 0 else 0.0
            r = round((gy - raise_) / GAME_ROW_PITCH)
            for rr in (r - 1, r, r + 1):
                cx, cy = game_xy(c, rr)
                d = (cx - gx) ** 2 + (cy - gy) ** 2
                if d < bd:
                    best, bd = (c, rr), d
        return best

    def lonlat_to_hex(self, lon: float, lat: float) -> tuple[int, int]:
        return self.xy_m_to_hex(*self.lonlat_to_xy_m(lon, lat))

    def hex_to_lonlat(self, col: int, row: int) -> tuple[float, float]:
        return self.xy_m_to_lonlat(*self.hex_to_xy_m(col, row))

    def in_grid(self, col: int, row: int) -> bool:
        return 0 <= col < self.cols and 0 <= row < self.rows

    def trace_xy_m(self, pts, step_m: float = 2.0) -> list[tuple[int, int]]:
        """Ordered hex chain under a polyline (metres), sampled every step_m; gaps filled with hex_line,
        so consecutive entries are always game neighbours. Off-grid hexes are kept (filter afterwards)."""
        chain: list[tuple[int, int]] = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step_m))
            for i in range(n + 1):
                h = self.xy_m_to_hex(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n)
                if not chain:
                    chain.append(h)
                elif chain[-1] != h:
                    chain.extend(hex_line(chain[-1], h)[1:])
        if len(pts) == 1:
            chain = [self.xy_m_to_hex(*pts[0])]
        return chain

    def trace_lonlat(self, waypoints, step_m: float = 2.0) -> list[tuple[int, int]]:
        return self.trace_xy_m([self.lonlat_to_xy_m(lon, lat) for lon, lat in waypoints], step_m)


# Kernstown 1862 (v0.4.2+). Same ground extent and hex centres as the v0.4.1 odd-q grid, re-indexed to the
# game convention: game y = 0 sits half a row north of the bbox south edge; 62 x 54 hexes.
# Migration from the legacy (<= v0.4.1) indices: see legacy_oddq_to_game().
KERNSTOWN = GridSpec(-78.260, 39.100, -78.120, 39.210, cols=62, rows=54, hex_yards=250.0,
                     x0_m=0.0, y0_m=0.5 * 250.0 * 0.9144)


def legacy_oddq_to_game(col: int, row: int, grid: GridSpec = KERNSTOWN) -> tuple[int, int] | None:
    """Legacy (<= v0.4.1, odd columns raised, 62x55) hex -> game-convention hex with the same centre.
    Odd columns keep their row; even columns move down one row. Legacy even row 0 and odd row 54
    (half / fully outside the painted map) have no counterpart and return None."""
    new = (col, row - (1 if col % 2 == 0 else 0))
    return new if grid.in_grid(*new) else None


def game_to_legacy_oddq(col: int, row: int) -> tuple[int, int]:
    return col, row + (1 if col % 2 == 0 else 0)
