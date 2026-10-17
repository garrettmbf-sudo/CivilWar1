"""Shared flat-top odd-q convention tests (mirrors kernstown-map scripts/hex_grid.py)."""
import importlib.util
import math
import subprocess
import sys
from pathlib import Path

import pytest

from src import hex_utils as hu
from src.hex_utils import Hex, axial_distance, axial_neighbors, axial_to_offset, offset_to_axial

ROOT = Path(__file__).resolve().parents[1]


def test_row_direction_is_north_by_default():
    assert hu.ROW_DIRECTION == 1


def test_six_unique_neighbors_at_distance_one():
    ns = axial_neighbors(Hex(0, 0))
    assert len(set(ns)) == 6 and all(axial_distance(Hex(0, 0), n) == 1 for n in ns)


def test_offset_axial_roundtrip():
    for col in range(-5, 6):
        for row in range(-5, 6):
            assert axial_to_offset(offset_to_axial(col, row)) == (col, row)


def test_odd_columns_shifted_half_row_north():
    assert hu.hex_center(1, 0)[1] == pytest.approx(0.5)
    assert hu.hex_center(0, 0)[1] == 0


def test_explicit_neighbors_even_and_odd_columns():
    # even column: NE/SE share row and row-1
    assert hu.offset_neighbors(2, 5) == [(2, 6), (3, 5), (3, 4), (2, 4), (1, 4), (1, 5)]
    # odd column (shifted north): NE/SE are row+1 and row
    assert hu.offset_neighbors(3, 5) == [(3, 6), (4, 6), (4, 5), (3, 4), (2, 5), (2, 6)]


def test_ports_reciprocal_and_geometric():
    for col in range(0, 6):
        for row in range(0, 6):
            cx, cy = hu.hex_center(col, row)
            for p in range(6):
                nb = hu.offset_neighbor(col, row, p)
                assert hu.offset_neighbor(*nb, hu.opposite_port(p)) == (col, row)
                nx, ny = hu.hex_center(*nb)
                assert math.hypot(nx - cx, ny - cy) == pytest.approx(1.0)
                bearing = math.degrees(math.atan2(nx - cx, ny - cy)) % 360
                assert bearing == pytest.approx(p * 60, abs=1e-6) or (p == 0 and bearing == pytest.approx(360))


def test_point_to_offset_roundtrip():
    for col in range(-3, 8):
        for row in range(-3, 8):
            assert hu.point_to_offset(*hu.hex_center(col, row)) == (col, row)


def test_tile_constants_match_kernstown_mask():
    assert (hu.TILE_PX, hu.HEX_WIDTH_PX, hu.HEX_HEIGHT_PX) == (2000, 1910, 1672)


def _load_kernstown_hex_grid(tmp_path):
    try:
        src = subprocess.run(["git", "-C", str(ROOT), "show", "origin/kernstown-map:scripts/hex_grid.py"],
                             capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("kernstown-map branch not fetched")
    p = tmp_path / "kern_hex_grid.py"
    p.write_text(src)
    spec = importlib.util.spec_from_file_location("kern_hex_grid", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["kern_hex_grid"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_matches_kernstown_hex_grid(tmp_path):
    kg = _load_kernstown_hex_grid(tmp_path)
    g = kg.GridSpec(0, 0, 1, 1, 40, 40, 250.0)
    for col in range(0, 12):
        for row in range(0, 12):
            x, y = g.hex_to_xy_m(col, row)
            ux, uy = hu.hex_center(col, row, g.hex_m)
            assert (ux, uy) == (pytest.approx(x), pytest.approx(y))
            assert g.xy_m_to_hex(x, y) == hu.point_to_offset(x, y, g.hex_m) == (col, row)
            # neighbours per Kernstown: step one hex-spacing in each port bearing and re-snap
            for p in range(6):
                a = math.radians(60 * p)
                kn = g.xy_m_to_hex(x + g.hex_m * math.sin(a), y + g.hex_m * math.cos(a))
                assert kn == hu.offset_neighbor(col, row, p)


def test_row_direction_flip_keeps_ports_geometric(monkeypatch):
    monkeypatch.setattr(hu, "ROW_DIRECTION", -1)
    for col in range(0, 5):
        for row in range(0, 5):
            cx, cy = hu.hex_center(col, row)
            assert hu.point_to_offset(cx, cy) == (col, row)
            for p in range(6):
                nb = hu.offset_neighbor(col, row, p)
                nx, ny = hu.hex_center(*nb)
                assert math.hypot(nx - cx, ny - cy) == pytest.approx(1.0)
                bearing = math.degrees(math.atan2(nx - cx, ny - cy)) % 360
                assert min(abs(bearing - p * 60), abs(bearing - p * 60 - 360)) < 1e-6
