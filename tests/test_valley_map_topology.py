"""Connectivity invariants; this is NOT a Hex of Steel save/load test."""
from pathlib import Path
import tempfile

from src.valley_map_topology import (
    EVEN, ODD, RAIL_PORTS, RIVER_PORTS, asset_duplicates,
    build_networks, create_report, hex_line, neighbor, parse_ps_paths,
    port_to, trace_waypoints, variant,
)


def test_neighbor_reciprocity_both_column_parities():
    for cell in ((8, 14), (9, 14), (0, 0), (1, 0)):
        for d in range(6):
            other = neighbor(cell, d)
            assert neighbor(other, (d + 3) % 6) == cell
            assert port_to(cell, other) == d


def test_line_is_contiguous_including_long_diagonal():
    for a, b in [((0, 0), (0, 0)), ((4, 7), (22, 31)),
                 ((63, 70), (82, 91)), ((5, 9), (0, 0))]:
        cells = hex_line(a, b)
        assert cells[0] == a and cells[-1] == b
        assert all(port_to(x, y) in range(6) for x, y in zip(cells, cells[1:]))


def test_no_false_connections_between_merely_adjacent_paths():
    routes = {"river": {"creekA": [(2, 4), (2, 5)],
                        "creekB": [(3, 4), (3, 5)]}, "road": {}, "rail": {}}
    net = build_networks(routes, 30, 30)
    assert port_to((2, 4), (3, 4)) not in net["grids"]["river"][(2, 4)]


def test_railroad_port_numbering_differs_from_river():
    assert variant("river", (0, 4)) == "River6"
    assert variant("rail", (0, 4)) == "Railroad9"
    assert variant("river", (0, 2)) == "River7"
    assert variant("rail", (0, 2)) == "Railroad6"
    assert variant("river", (1, 3)) == "River8"
    assert variant("rail", (1, 3)) == "Railroad7"
    assert variant("river", (3, 5)) == "River9"
    assert variant("rail", (3, 5)) == "Railroad8"
    assert variant("river", (1, 3, 5)) == "River10"
    assert variant("river", (0, 2, 4)) == "River11"
    assert variant("river", (0, 1, 3)) == "River12"
    assert variant("rail", (1, 3, 5)) is None  # rail junction art not audited
    assert variant("river", (0, 1)) is None    # no incorrect bend fallback
    assert variant("road", (0, 3)) is None     # no custom Road atlas verified


def test_ps_parser_and_crossing_audit_does_not_invent_bridges():
    src = '''$riverSouthFork = @(6,6, 6,10)
$valleyPike = @(4,8, 8,8)
$rrManassasGap = @(12,9, 13,9)
'''
    paths = parse_ps_paths(src)
    assert len(paths["river"]) == len(paths["road"]) == len(paths["rail"]) == 1
    report = create_report(src, 30, 30)
    assert report["river_route_crossings"]
    assert all(c["crossing_status"] == "UNVERIFIED_NO_AUTOMATIC_BRIDGE"
               for c in report["river_route_crossings"])


def test_unexpected_powershell_cannot_be_executed():
    try:
        parse_ps_paths('$riverAttack = @(1,2, $(evil),3)')
    except ValueError:
        pass
    else:
        assert False, "parser accepted a PowerShell expression"


def test_duplicate_asset_detection():
    with tempfile.TemporaryDirectory() as dirname:
        directory = Path(dirname)
        (directory / "RailroadCross9.png").write_bytes(b"placeholder")
        (directory / "RailroadCross10.png").write_bytes(b"placeholder")
        (directory / "River1.png").write_bytes(b"unique")
        assert ["RailroadCross10.png", "RailroadCross9.png"] == sorted(asset_duplicates(directory)[0])

