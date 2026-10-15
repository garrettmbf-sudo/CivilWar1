"""Hex geometry regression tests — distinguish hex distance from miles."""
from src.hex_utils import Hex, axial_neighbors, axial_distance, axial_to_offset, offset_to_axial


def test_six_unique_neighbors_at_distance_one():
    neighbors = axial_neighbors(Hex(0, 0))
    assert len(neighbors) == 6
    assert len(set(neighbors)) == 6
    assert all(axial_distance(Hex(0, 0), n) == 1 for n in neighbors)


def test_axial_distance():
    assert axial_distance(Hex(0, 0), Hex(2, 0)) == 2
    assert axial_distance(Hex(0, 0), Hex(0, 3)) == 3
    assert axial_distance(Hex(3, -2), Hex(0, 1)) == 3
    assert axial_distance(Hex(-3, 4), Hex(-3, 4)) == 0


def test_offset_axial_roundtrip():
    for odd_r in (True, False):
        for row in range(-4, 5):
            for col in range(-4, 5):
                assert axial_to_offset(offset_to_axial(col, row, odd_r), odd_r) == (col, row)
