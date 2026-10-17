import csv

from scripts.valley_map_shape import DATA, feature_points, grid_counts, load_polygon, mechanics, point_in_polygon, town_coords


def test_every_named_place_pass_exit_and_road_waypoint_inside_polygon():
    poly = load_polygon()
    pts = {**town_coords(), **feature_points()}
    assert "Lexington" in pts and "gap_rockfish" in pts and "rd_staunton_parkersburg_tpk#4" in pts
    outside = [k for k, (lon, lat) in pts.items() if not point_in_polygon(lon, lat, poly)]
    assert outside == []


def test_piedmont_points_excluded():
    poly = load_polygon()
    for name, lon, lat in [("Culpeper", -77.996, 38.473), ("Charlottesville", -78.477, 38.029),
                           ("Warrenton", -77.795, 38.713), ("Gordonsville", -78.188, 38.137)]:
        assert not point_in_polygon(lon, lat, poly), name


def test_each_pass_has_an_exit():
    passes = {r["feature_id"] for r in csv.DictReader((DATA / "blue_ridge_passes.csv").open())}
    exits = {r["via_feature"] for r in csv.DictReader((DATA / "east_exit_edges.csv").open())}
    assert passes == exits


def test_counts_shrink_with_scale_and_mask_trims_rectangle():
    a, b = grid_counts(load_polygon(), 500), grid_counts(load_polygon(), 1000)
    assert a["playable_hexes"] > b["playable_hexes"] > 0
    assert a["playable_hexes"] < a["rect_hexes"]


def test_500yd_artillery_fits_documented_1_to_4_range():
    m = mechanics(500, 1)
    assert (m["napoleon_range"], m["rifled_range"]) == (3, 4)
    assert round(m["inf_road_mp"]) == 9
