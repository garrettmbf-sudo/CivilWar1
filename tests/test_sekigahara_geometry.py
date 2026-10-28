"""Geometry contract for the separate point-top Sekigahara adapter."""
import importlib.util
import math
from pathlib import Path

spec = importlib.util.spec_from_file_location('sekigahara_builder',
    Path(__file__).parents[1]/'tools/sekigahara_valley/build_scenario.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_neighbors_are_equidistant_and_reciprocal():
    for row in (4,5):
        origin=(6,row)
        for neighbor in builder.neighbors(*origin):
            assert math.isclose(math.dist(builder.center(*origin),builder.center(*neighbor)),400)
            assert origin in builder.neighbors(*neighbor)


def test_import_mapping_preserves_target_centers():
    for q in range(31):
        for r in range(36):
            assert builder.nearest(*builder.center(q,r),31,36)==(q,r)


def test_north_up_and_east_right():
    assert builder.center(3,4)[0] > builder.center(2,4)[0]
    assert builder.center(3,4)[1] < builder.center(3,5)[1]
