"""Flat-top odd-q hex grid matching Hex of Steel stock tiles (flat-top alpha hexes)."""
from __future__ import annotations
import math
from dataclasses import dataclass

@dataclass(frozen=True)
class GridSpec:
    west: float
    south: float
    east: float
    north: float
    cols: int
    rows: int
    hex_yards: float = 250.0  # center-to-center to any neighbor

    @property
    def hex_m(self) -> float:
        return self.hex_yards * 0.9144

    @property
    def size_m(self) -> float:
        """Outer radius (center → vertex) so neighbor distance == hex_m."""
        return self.hex_m / math.sqrt(3)

    @property
    def col_pitch_m(self) -> float:
        return 1.5 * self.size_m  # = hex_m * sqrt(3)/2

    @property
    def row_pitch_m(self) -> float:
        return math.sqrt(3) * self.size_m  # = hex_m

    def meters_per_deg(self, lat: float) -> tuple[float, float]:
        m_lat = 111_132.0
        m_lon = 111_132.0 * math.cos(math.radians(lat))
        return m_lat, m_lon

    def lonlat_to_xy_m(self, lon: float, lat: float) -> tuple[float, float]:
        mid = (self.south + self.north) / 2
        m_lat, m_lon = self.meters_per_deg(mid)
        return (lon - self.west) * m_lon, (lat - self.south) * m_lat

    def hex_to_xy_m(self, col: int, row: int) -> tuple[float, float]:
        # odd-q flat-top: odd columns shifted down by half row
        x = self.col_pitch_m * col
        y = self.row_pitch_m * (row + 0.5 * (col & 1))
        return x, y

    def xy_m_to_hex(self, x: float, y: float) -> tuple[int, int]:
        # inverse odd-q flat-top via axial
        size = self.size_m
        q = (2 / 3 * x) / size
        r = (-1 / 3 * x + math.sqrt(3) / 3 * y) / size
        return self._axial_to_oddr(self._cube_round(q, r))

    def _cube_round(self, q: float, r: float) -> tuple[int, int]:
        s = -q - r
        qq, rr, ss = round(q), round(r), round(s)
        dq, dr, ds = abs(qq - q), abs(rr - r), abs(ss - s)
        if dq > dr and dq > ds:
            qq = -rr - ss
        elif dr > ds:
            rr = -qq - ss
        return int(qq), int(rr)

    def _axial_to_oddr(self, qr: tuple[int, int]) -> tuple[int, int]:
        q, r = qr
        col = q
        row = r + (q - (q & 1)) // 2
        return col, row

    def lonlat_to_hex(self, lon: float, lat: float) -> tuple[int, int]:
        return self.xy_m_to_hex(*self.lonlat_to_xy_m(lon, lat))

    def hex_to_lonlat(self, col: int, row: int) -> tuple[float, float]:
        x, y = self.hex_to_xy_m(col, row)
        mid = (self.south + self.north) / 2
        m_lat, m_lon = self.meters_per_deg(mid)
        return self.west + x / m_lon, self.south + y / m_lat


# Fit cols/rows so bbox is covered at 250 yd neighbor spacing
def fit_grid(west, south, east, north, hex_yards=250.0) -> GridSpec:
    probe = GridSpec(west, south, east, north, 1, 1, hex_yards)
    mid = (south + north) / 2
    m_lat, m_lon = probe.meters_per_deg(mid)
    width_m = (east - west) * m_lon
    height_m = (north - south) * m_lat
    cols = int(math.ceil(width_m / probe.col_pitch_m)) + 1
    rows = int(math.ceil(height_m / probe.row_pitch_m)) + 1
    return GridSpec(west, south, east, north, cols, rows, hex_yards)


KERNSTOWN = fit_grid(-78.260, 39.100, -78.120, 39.210, 250.0)
