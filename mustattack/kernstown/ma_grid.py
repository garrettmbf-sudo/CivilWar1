"""Must Attack hex grid, as reverse-engineered from the stock scenarios.

Pointy-top hexes, odd-r offset (odd rows shifted half a hex east), r = 0 is the north edge,
hex list row-major (r outer, q inner), id "q-r".  Edge index clockwise from east:
0=E 1=SE 2=SW 3=W 4=NW 5=NE.  Verified by edge-symmetry of roads/rivers in the stock files
(see validate_kernstown_ma.py, check_stock_grid()).
"""
import math

DIRS_EVEN = [(1, 0), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1)]
DIRS_ODD = [(1, 0), (1, 1), (0, 1), (-1, 0), (0, -1), (1, -1)]


def neighbor(q, r, e):
    dq, dr = (DIRS_ODD if r & 1 else DIRS_EVEN)[e]
    return q + dq, r + dr


def edge_to(a, b):
    """Edge index from hex a to adjacent hex b, or None."""
    for e in range(6):
        if neighbor(*a, e) == tuple(b):
            return e
    return None


class Grid:
    """Local equirectangular projection: x east, y south (metres) from the NW corner of the bbox."""

    def __init__(self, west, north, cols, rows, hex_m=300.0):
        self.west, self.north, self.cols, self.rows, self.s = west, north, cols, rows, hex_m
        self.rp = hex_m * math.sqrt(3) / 2  # row pitch
        self.mlat = 111_132.0
        mid = north - (rows * self.rp / self.mlat) / 2
        self.mlon = 111_132.0 * math.cos(math.radians(mid))

    def center_xy(self, q, r):
        return self.s * (q + 0.5 * (r & 1)) + self.s / 2, self.rp * r + self.s / 2

    def lonlat_to_xy(self, lon, lat):
        return (lon - self.west) * self.mlon, (self.north - lat) * self.mlat

    def xy_to_lonlat(self, x, y):
        return self.west + x / self.mlon, self.north - y / self.mlat

    def center_lonlat(self, q, r):
        return self.xy_to_lonlat(*self.center_xy(q, r))

    def xy_to_hex(self, x, y):
        r0 = round((y - self.s / 2) / self.rp)
        best, bd = None, 1e18
        for r in (r0 - 1, r0, r0 + 1):
            q0 = round((x - self.s / 2) / self.s - 0.5 * (r & 1))
            for q in (q0 - 1, q0, q0 + 1):
                cx, cy = self.center_xy(q, r)
                d = (cx - x) ** 2 + (cy - y) ** 2
                if d < bd:
                    best, bd = (q, r), d
        return best

    def lonlat_to_hex(self, lon, lat):
        return self.xy_to_hex(*self.lonlat_to_xy(lon, lat))

    def inside(self, q, r):
        return 0 <= q < self.cols and 0 <= r < self.rows

    def sample_points(self, q, r, n=4):
        """Points on a triangular lattice inside the hex (for coverage fractions)."""
        cx, cy = self.center_xy(q, r)
        R = self.s / math.sqrt(3)
        pts = []
        step = self.s / (2 * n)
        for i in range(-2 * n, 2 * n + 1):
            for j in range(-2 * n, 2 * n + 1):
                x, y = cx + i * step, cy + j * step
                if self.xy_to_hex(x, y) == (q, r):
                    pts.append((x, y))
        return pts

    def trace(self, lonlats, step_m=10.0):
        """Ordered chain of adjacent hexes under a polyline (off-board hexes kept)."""
        xy = [self.lonlat_to_xy(*p) for p in lonlats]
        chain = []
        for (x0, y0), (x1, y1) in zip(xy, xy[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step_m))
            for i in range(n + 1):
                h = self.xy_to_hex(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n)
                if not chain:
                    chain.append(h)
                elif h != chain[-1]:
                    if edge_to(chain[-1], h) is None:
                        # jumped across a vertex: insert the shared neighbour nearest the segment
                        cands = [neighbor(*chain[-1], e) for e in range(6)]
                        cands = [c for c in cands if edge_to(c, h) is not None]
                        mx, my = (x0 + (x1 - x0) * i / n), (y0 + (y1 - y0) * i / n)
                        cands.sort(key=lambda c: math.dist(self.center_xy(*c), (mx, my)))
                        if cands:
                            chain.append(cands[0])
                    chain.append(h)
        return chain
