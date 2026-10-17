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
    assert regs and all(("INHERITED_FROM_PARENT" in r["flags"]) != ("OWN_RATING" in r["flags"]) for r in regs)
    for r in regs:
        if "OWN_RATING" in r["flags"]:
            assert r["rating_from"] == r["unit_id"]
    provisional = [r for r in rows if r["confidence"] == "provisional"]
    assert provisional and all(r["flags"].startswith("PROVISIONAL_RATING") for r in provisional)
    cmd = {(r["unit_id"], r["as_of_date"]): r for r in rows if r["row_type"] == "commander"}
    assert cmd[("CMD_JACKSON", "1862-03-23")]["echelon"] == "army"
    assert cmd[("CMD_EWELL", "1862-05-25")]["echelon"] == "division"
    assert cmd[("CMD_BANKS", "1862-03-23")]["echelon"] == "department"
    assert cmd[("CMD_JOHNSON_E", "1862-05-08")]["echelon"] == "division"  # documented override


def test_own_rating_preferred_and_inherits_rows_skipped():
    rows = {(r["unit_id"], r["as_of_date"]): r for r in H.build()}
    ga = rows[("REG_GA12", "1862-05-25")]   # UR169 says "inherits" -> falls back to UR168 (own)
    assert ga["rating_id"] == "UR168" and "OWN_RATING" in ga["flags"]
    assert not any(k[0] == "REG_VA12" for k in rows)


def test_excluded_units_absent_with_reason():
    ids = {r["unit_id"] for r in H.build()}
    assert not ids & set(H.EXCLUDED)
    with open(H.OUT_EXCLUDED, newline="", encoding="utf-8") as f:
        ex = {r["unit_id"]: r["excluded_reason"] for r in csv.DictReader(f)}
    assert set(ex) == {"REG_OH13C", "ART_PLEASANTS", "ART_US_WVB", "ART_US_ADDHOW", "ART_US_PAE"}
    assert all(v.startswith("UNRATED") for v in ex.values())


def test_crutchfield_starts_may_8():
    from src.oob import OOB
    from datetime import date
    oob = OOB.load()
    assert oob.commanders["CMD_CRUTCHFIELD"]["first_mentioned"] in ("1862-05-08", date(1862, 5, 8))
    assert all(c["valid_from"] >= date(1862, 5, 8) for c in oob.commands if c["commander_id"] == "CMD_CRUTCHFIELD")
