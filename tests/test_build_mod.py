from src.hex_utils import Hex, axial_distance, axial_neighbors


def test_axial_neighbors_count():
    neighbors = axial_neighbors(Hex(0, 0))
    assert len(neighbors) == 6


def test_axial_distance_known_values():
    assert axial_distance(Hex(0, 0), Hex(2, 0)) == 2
    assert axial_distance(Hex(0, 0), Hex(0, 3)) == 3
