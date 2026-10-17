from scripts.valley_tile_plan import LINEAR, Cell, Library, assign_tiles, demo_grid, stable_hash, trace_path, validate_ports
from src import hex_utils as hu


def _lib():
    lib = Library(area={"open": [f"SV_OPEN_{i}" for i in range(6)], "woods": [f"SV_WOODS_{i}" for i in range(4)], "hill": [f"SV_HILL_{i}" for i in range(4)]})
    for m in range(64):
        for cls in LINEAR:
            lib.linear[(cls, m)] = [f"SV_{cls.upper()}_P{m:02d}_{v}" for v in range(2)]
    return lib


def test_hash_is_stable_across_runs():
    assert stable_hash(1862, "open", 0, 3, 4) == stable_hash(1862, "open", 0, 3, 4)
    assert stable_hash(1862, "open", 0, 3, 4) != stable_hash(1862, "open", 0, 4, 3)


def test_assignment_deterministic_and_seed_sensitive():
    g, _ = demo_grid()
    a = assign_tiles(g, _lib(), seed=7)
    assert a == assign_tiles(g, _lib(), seed=7)
    assert a != assign_tiles(g, _lib(), seed=8)


def test_no_identical_area_tiles_touch():
    g = {(c, r): Cell("open") for c in range(20) for r in range(20)}
    a = assign_tiles(g, _lib())
    for (c, r), name in a.items():
        for n in hu.offset_neighbors(c, r):
            assert a.get(n) != name


def test_demo_ports_reciprocal_and_tiles_match_mask():
    g, _ = demo_grid()
    assert validate_ports(g) == []
    a = assign_tiles(g, _lib())
    for k, cell in g.items():
        for cls, mask in cell.ports.items():
            if a[k].startswith(f"SV_{cls.upper()}_"):
                assert f"_P{mask:02d}_" in a[k]


def test_validator_catches_one_sided_port():
    g = {(0, 0): Cell("open"), (0, 1): Cell("open")}
    g[(0, 0)].ports["road"] = 1 << hu.N  # exits north, neighbour has no S port
    assert validate_ports(g)
    trace_path(g, "road", [(0, 0), (0, 1)])
    assert validate_ports(g) == []


def test_hero_tiles_are_never_hashed():
    g = {(0, 0): Cell("open", hero="SV_HERO_LEXINGTON_VMI"), (1, 0): Cell("open")}
    assert assign_tiles(g, _lib())[(0, 0)] == "SV_HERO_LEXINGTON_VMI"
