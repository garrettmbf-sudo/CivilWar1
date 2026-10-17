"""hos_stats: deterministic, engine-real fields only, no faction bias."""
import csv
import os

from src import hos_stats as H

ENGINE_FIELDS = {"soft_damage", "hard_damage", "air_damage", "armor", "hp", "ammo", "fuel",
                 "movement_points", "range", "visibility", "rank"}


def test_deterministic_and_matches_committed_csv():
    a, b = H.build(), H.build()
    assert a == b
    with open(H.OUT, newline="", encoding="utf-8") as f:
        committed = list(csv.DictReader(f))
    assert len(committed) == len(a)
    assert [r["unit_id"] for r in committed] == [r["unit_id"] for r in a]


def test_only_engine_fields_and_ranges():
    for r in H.build():
        assert ENGINE_FIELDS <= set(r)
        assert 1 <= r["rank"] <= 5
        assert r["air_damage"] == 0 and r["armor"] == 0
        if r["row_type"] == "commander":
            lo, hi = H.ECHELON_RANGE[r["echelon"]]
            assert lo <= r["range"] <= hi
            assert 1 <= r["soft_damage"] <= H.BONUS_MAX
        else:
            assert H.HP_MIN <= r["hp"] <= H.HP_MAX
            assert r["range"] in (1, 3)
    assert "morale" not in " ".join(H.FIELDS).replace("cohesion_morale", "")


def test_no_faction_bias():
    # identical ratings -> identical stats regardless of side
    assert H.unit_stats("infantry", 4, 3, 4, 5) == H.unit_stats("infantry", 4, 3, 4, 5)
    assert "faction" not in H.unit_stats.__code__.co_varnames
    assert "faction" not in H.commander_stats.__code__.co_varnames


def test_inheritance_flags_and_echelons():
    rows = H.build()
    regs = [r for r in rows if r["row_type"] in ("regiment", "battery")]
    assert regs and all("INHERITED_FROM_PARENT" in r["flags"] for r in regs)
    provisional = [r for r in rows if r["confidence"] == "provisional"]
    assert provisional and all(r["flags"].startswith("PROVISIONAL_RATING") for r in provisional)
    cmd = {(r["unit_id"], r["as_of_date"]): r for r in rows if r["row_type"] == "commander"}
    assert cmd[("CMD_JACKSON", "1862-03-23")]["echelon"] == "army"
    assert cmd[("CMD_EWELL", "1862-05-25")]["echelon"] == "division"
    assert cmd[("CMD_BANKS", "1862-03-23")]["echelon"] == "department"
    assert cmd[("CMD_JOHNSON_E", "1862-05-08")]["echelon"] == "division"  # documented override
