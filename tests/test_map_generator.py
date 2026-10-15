"""Tests for the procedural Shenandoah Valley map generator and renderer input."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402

from map_generator import (  # noqa: E402
    HEIGHT,
    HOS_TILE_NAMES,
    TERRAIN_CODES,
    WIDTH,
    generate_map,
    validate,
)


@pytest.fixture(scope="module")
def payload():
    return generate_map()


def test_dimensions(payload):
    assert payload["size_x"] == WIDTH
    assert payload["size_y"] == HEIGHT
    assert len(payload["tiles"]) == WIDTH * HEIGHT


def test_terrain_codes_valid(payload):
    codes = set(TERRAIN_CODES.values())
    assert all(t["terrain"] in codes for t in payload["tiles"])


def test_towns_on_city_tiles(payload):
    by_pos = {(t["col"], t["row"]): t["terrain"] for t in payload["tiles"]}
    city = TERRAIN_CODES["city"]
    for town in payload["towns"]:
        assert by_pos[(town["col"], town["row"])] == city


def test_valley_geography(payload):
    """Ridge lines and river forks must exist where history says they are."""
    by_pos = {(t["col"], t["row"]): t["terrain"] for t in payload["tiles"]}
    mtn = TERRAIN_CODES["mountains"]
    river = {TERRAIN_CODES[k] for k in ("river", "south_fork", "north_fork",
                                        "shenandoah_river")}
    # Blue Ridge mountains mid-valley-east at row 25
    assert any(by_pos[(c, 25)] == mtn for c in range(18, 24))
    # Allegheny Front west at row 25
    assert any(by_pos[(c, 25)] == mtn for c in range(3, 9))
    # Massanutten between rows 18..33 near col 13
    assert by_pos[(13, 25)] == mtn
    # South Fork (west of Massanutten) present around rows 36-46 near col 9
    assert any(by_pos[(c, r)] in river for c in (8, 9, 10) for r in range(36, 47))
    # North Fork (east of Massanutten) present around rows 36-46 near col 15-16
    assert any(by_pos[(c, r)] in river for c in (15, 16, 17) for r in range(36, 47))


def test_hos_tile_names(payload):
    """Every tile carries a HoS-style name drawn from the Hexerreich vocabulary."""
    names = set(HOS_TILE_NAMES.values())
    assert all(t["tile"] in names for t in payload["tiles"])
    # named streams: each fork keeps its own River<N> identity
    tiles_sf = [t for t in payload["tiles"] if t["terrain"] == TERRAIN_CODES["south_fork"]]
    tiles_nf = [t for t in payload["tiles"] if t["terrain"] == TERRAIN_CODES["north_fork"]]
    assert tiles_sf and all(t["tile"] == "River1" for t in tiles_sf)
    assert tiles_nf and all(t["tile"] == "River2" for t in tiles_nf)
    town_by_pos = {(t["col"], t["row"]): t["tile"] for t in payload["tiles"]}
    for town in payload["towns"]:
        assert town_by_pos[(town["col"], town["row"])] == "Village"


def test_validate_passes(payload):
    validate(payload)  # should not raise
