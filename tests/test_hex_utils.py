"""Flat-top EVEN-Q tests against Hex of Steel's own math (MapGO and Utils.GetAllTilesNeighbours)."""
import math

import pytest

from src import hex_utils as hu
from src.hex_utils import Hex, axial_distance, axial_neighbors, axial_to_offset, offset_to_axial


# Transcribed from the decompiled game (HoS 8.4.14), non-circular map, interior tiles.
def game_neighbours(num, num2):
    """Utils.GetAllTilesNeighbours, in the order the game adds them."""
    out = [(num, num2 + 1), (num, num2 - 1)]
    if num % 2 == 0:
        out += [(num - 1, num2 + 1), (num + 1, num2 + 1), (num - 1, num2), (num + 1, num2)]
    else:
        out += [(num - 1, num2), (num + 1, num2), (num - 1, num2 - 1), (num + 1, num2 - 1)]
    return out


def mapgo_position(num, num2):
    """MapGO.cs:452-459."""
    if num % 2 != 0:
        return (num * 4.42, num2 * 5.1)
    return (num * 4.42, num2 * 5.1 + 2.55)


def test_no_row_direction_switch():
    assert not hasattr(hu, "ROW_DIRECTION")


def test_even_column_neighbours_match_game():
    assert hu.offset_neighbors(2, 5) == [(2, 6), (3, 6), (3, 5), (2, 4), (1, 5), (1, 6)]
    assert set(hu.offset_neighbors(2, 5)) == set(game_neighbours(2, 5))


def test_odd_column_neighbours_match_game():
    assert hu.offset_neighbors(3, 5) == [(3, 6), (4, 5), (4, 4), (3, 4), (2, 4), (2, 5)]
    assert set(hu.offset_neighbors(3, 5)) == set(game_neighbours(3, 5))


def test_all_neighbours_match_game_on_a_block():
    for c in range(0, 30):
        for r in range(1, 30):
            assert set(hu.offset_neighbors(c, r)) == set(game_neighbours(c, r)), (c, r)


def test_positions_match_mapgo():
    for c in range(0, 20):
        for r in range(0, 20):
            assert hu.game_position(c, r) == pytest.approx(mapgo_position(c, r))
            x, y = hu.hex_center(c, r, 5.1)
            assert (x, y) == (pytest.approx(mapgo_position(c, r)[0]), pytest.approx(mapgo_position(c, r)[1]))


def test_even_columns_shifted_half_row_north():
    assert hu.hex_center(0, 0)[1] == pytest.approx(0.5)
    assert hu.hex_center(1, 0)[1] == 0
    assert hu.hex_center(1, 0)[0] == pytest.approx(4.42 / 5.1)


def test_ports_point_the_named_way_in_game_space():
    for c in range(0, 6):
        for r in range(1, 6):
            cx, cy = mapgo_position(c, r)
            for p in range(6):
                nb = hu.offset_neighbor(c, r, p)
                assert hu.offset_neighbor(*nb, hu.opposite_port(p)) == (c, r)
                nx, ny = mapgo_position(*nb)
                bearing = math.degrees(math.atan2(nx - cx, ny - cy)) % 360
                assert min(abs(bearing - p * 60), 360 - abs(bearing - p * 60)) < 0.1  # 4.42:5.1 is ~regular


def test_six_unique_axial_neighbours_at_distance_one():
    ns = axial_neighbors(Hex(0, 0))
    assert len(set(ns)) == 6 and all(axial_distance(Hex(0, 0), n) == 1 for n in ns)


def test_offset_axial_and_cube_roundtrip():
    for col in range(-5, 6):
        for row in range(-5, 6):
            assert axial_to_offset(offset_to_axial(col, row)) == (col, row)
            assert hu.cube_to_offset(*hu.offset_to_cube(col, row)) == (col, row)


def test_axial_neighbours_agree_with_offset_neighbours():
    for col in range(-4, 5):
        for row in range(-4, 5):
            ax = [axial_to_offset(h) for h in axial_neighbors(offset_to_axial(col, row))]
            assert ax == hu.offset_neighbors(col, row)


def test_distance_is_bfs_steps_on_game_graph():
    start = (4, 4)
    dist = {start: 0}
    frontier = [start]
    while frontier:
        nxt = []
        for a in frontier:
            for b in game_neighbours(*a):
                if b not in dist and dist[a] < 6:
                    dist[b] = dist[a] + 1
                    nxt.append(b)
        frontier = nxt
    for b, d in dist.items():
        assert hu.offset_distance(start, b) == d


def test_point_to_offset_roundtrip():
    for col in range(-3, 8):
        for row in range(-3, 8):
            assert hu.point_to_offset(*hu.hex_center(col, row)) == (col, row)
            x, y = hu.hex_center(col, row, 250.0)
            assert hu.point_to_offset(x + 40, y - 40, 250.0) == (col, row)


def test_tile_constants_match_kernstown_mask():
    assert (hu.TILE_PX, hu.HEX_WIDTH_PX, hu.HEX_HEIGHT_PX) == (2000, 1910, 1672)


def test_hex_line_is_adjacent_chain_of_right_length():
    import random
    rnd = random.Random(5)
    for _ in range(2000):
        a = (rnd.randint(-5, 130), rnd.randint(-5, 140))
        b = (rnd.randint(-5, 130), rnd.randint(-5, 140))
        line = hu.hex_line(a, b)
        assert line[0] == a and line[-1] == b and len(line) == hu.offset_distance(a, b) + 1
        assert all(q in game_neighbours(*p) for p, q in zip(line, line[1:]))
