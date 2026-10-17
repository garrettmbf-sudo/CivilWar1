"""Date-specific 1862 Valley OOB smoke tests for the recovered historical data.

These test source-data behavior only; they do NOT validate Hex of Steel integration.
"""
import os
from datetime import date
from src.oob import OOB, validate


def test_recovered_oob_validates_baseline_rules():
    oob = OOB.load()
    assert validate(oob) == []
    assert (len(oob.formations), len(oob.regiments), len(oob.artillery), len(oob.commanders)) == (50, 96, 34, 45)


def test_key_campaign_snapshots():
    oob = OOB.load()
    expected = {
        '1862-03-22': (8, 3),
        '1862-03-23': (8, 3),
        '1862-05-08': (11, 7),
        '1862-05-25': (18, 9),
        '1862-06-09': (26, 10),  # FRM_US_KIMBALL1 closed 5/31 (was empty)
    }
    for date_str, (counters, hqs) in expected.items():
        snapshot = oob.snapshot(date.fromisoformat(date_str))
        assert len(snapshot['counters']) == counters
        assert len(snapshot['headquarters']) == hqs
    march = oob.snapshot(date(1862, 3, 23))
    may = oob.snapshot(date(1862, 5, 25))
    assert 'FRM_CS_EWELLDIV' not in march['headquarters']
    assert 'FRM_CS_EWELLDIV' in may['headquarters']


def test_date_correct_parent_transfers_and_state_flags():
    oob = OOB.load()
    march = date(1862, 3, 23)
    may = date(1862, 5, 25)
    assert oob.parent_on("FRM_CS_STONEWALL", march) == "FRM_CS_VALLEY"
    assert oob.parent_on("FRM_CS_STONEWALL", may) == "FRM_CS_JACKSONDIV"
    assert oob.parent_on("FRM_US_KIMBALL1", march) == "FRM_US_SHIELDSDIV_K"
    assert oob.parent_on("FRM_US_KIMBALL1", may) == "FRM_US_SHIELDSDIV_R"
    assert oob.state_flag("FRM_CS_STONEWALL", march) == "VA"
    assert oob.state_flag("FRM_US_KIMBALL1", march) == "MIXED"
    assert oob.state_origins("FRM_US_KIMBALL1", march) == ["IN", "OH", "PA"]
    assert oob.state_flag("FRM_CS_VALLEY", march) == "UNKNOWN"
    for snap_day in [march, date(1862, 5, 8), may, date(1862, 6, 9)]:
        for counter in oob.snapshot(snap_day)["counters"]:
            assert counter["state_flag"] in ("MIXED", "UNKNOWN") or len(counter["state_flag"]) == 2
            assert isinstance(counter["command_chain"], list)


def test_no_reversed_historical_windows():
    oob = OOB.load()
    assert all(not r["valid_to"] or r["valid_from"] <= r["valid_to"]
               for r in oob.assignments)
    assert all(not r["valid_to"] or r["valid_from"] <= r["valid_to"]
               for r in oob.commands)


def test_fixed_records_cite_sources_and_pages():
    oob = OOB.load()
    for fid in ["FRM_US_SCHENCK_MCD", "FRM_US_STAHEL", "FRM_US_KOLTES",
                "FRM_US_BOHLEN", "FRM_US_FRMC_CAV"]:
        assert oob.formations[fid]["sources"].strip()
        assert oob.formations[fid]["notes"].strip() != "SRC007"
    a = {r["assignment_id"]: r for r in oob.assignments}
    assert a["A060"]["sources"].startswith("SRC") and a["A062"]["sources"].startswith("SRC")
    assert all(c["sources"].strip() for c in oob.commands)
    assert "SRC009" in oob.sources and "SRC010" in oob.sources


def test_command_and_counter_resolutions():
    oob = OOB.load()
    assert "FRM_US_KIMBALL1" not in oob.active_formations(date(1862, 6, 1))
    assert oob.command_rows("FRM_US_FRMC_CAV", date(1862, 6, 9))  # documented vacancy
    assert oob.commander_of("FRM_CS_FULKERSON", date(1862, 5, 25)) == "CMD_FULKERSON"
    e008 = [ev for ev in oob.events if ev["event_id"] == "E008"][0]
    assert e008["date"] == date(1862, 5, 23)
    assert [p["formation_id"] for p in oob.parents_of("REG_NY04C", date(1862, 6, 8))] == ["FRM_US_BLENKERDIV"]
    assert oob.artillery["ART_US_1NY_I"]["commander"]


def test_validator_catches_empty_sources_counters_and_commanders():
    from src import oob as m
    oob = OOB.load()
    oob.formations["FRM_US_STAHEL"] = {**oob.formations["FRM_US_STAHEL"], "sources": ""}
    oob.commands = [c for c in oob.commands if c["brigade_id"] != "FRM_US_KOLTES"]
    oob.assignments = [a for a in oob.assignments if a["formation_id"] != "FRM_US_BOHLEN"]
    errs = "\n".join(validate(oob))
    assert "FRM_US_STAHEL: empty sources" in errs
    assert "FRM_US_KOLTES on 1862-06-09: no commander record" in errs
    assert "FRM_US_BOHLEN on 1862-06-09: empty counter" in errs


def test_opening_snapshot_complete_and_cited():
    from src.oob import OPENING_DATE
    oob = OOB.load()
    assert OPENING_DATE == date(1862, 3, 22)
    snap = oob.snapshot(OPENING_DATE)
    ids = {c["formation_id"] for c in snap["counters"]}
    # Kernstown OR returns: CS p.384 (Garnett, Burks, Fulkerson + Ashby p.385); US p.346 (Kimball, Sullivan, Tyler, Brodhead)
    for fid in ["FRM_CS_STONEWALL", "FRM_CS_BURKS", "FRM_CS_FULKERSON", "FRM_CS_ASHBY",
                "FRM_US_KIMBALL1", "FRM_US_SULLIVAN2", "FRM_US_TYLER3", "FRM_US_CAV_BRODHEAD"]:
        assert fid in ids, fid
        assert "p." in oob.formations[fid]["sources"], fid
    for c in snap["counters"]:
        if oob.formations[c["formation_id"]]["counter"] == "Y":
            assert c["commander"], c["formation_id"]
            assert c["regiments"], c["formation_id"]


def test_arrival_schedule_complete():
    from src.oob import OPENING_DATE, arrival_schedule_errors
    oob = OOB.load()
    assert arrival_schedule_errors(oob) == []
    later = [fid for fid, f in oob.formations.items()
             if f["active_from"] and date.fromisoformat(f["active_from"]) > OPENING_DATE]
    assert later  # later-date data retained, not deleted
    by_id = {e["event_id"]: e for e in oob.events}
    # key historical arrivals present with OR pages
    assert by_id["E005"]["subject_id"] == "FRM_CS_EWELLDIV" and "p.470" in by_id["E005"]["sources"]
    assert by_id["E014"]["date"] == date(1862, 5, 7)   # Johnson junction, OR 12/1 p.471
    assert by_id["E016"]["date"] == date(1862, 5, 9)   # Blenker joins Fremont, p.8
    assert by_id["E017"]["date"] == date(1862, 5, 30)  # Shields back at Front Royal, p.282
    assert by_id["E013"]["date"] == date(1862, 4, 6)   # Taliaferro assigned, Pt.3 p.844


def test_opening_0322_start_positions_and_commands():
    from src.oob import OPENING_DATE
    oob = OOB.load()
    by_id = {e["event_id"]: e for e in oob.events}
    assert all(f"E{n}" in by_id for n in range(100, 132))
    starts = [e for e in oob.events if e["event_type"] == "start_position"]
    assert len(starts) == 14 and all(e["date"] == OPENING_DATE for e in starts)
    # Ewell's and Blenker's 3/22 camps are not in the OR: must stay unverified
    assert by_id["E108"]["date_certainty"] == "unverified"
    assert by_id["E115"]["date_certainty"] == "unverified"
    # Shields commands at dawn 3/22; Kimball from 3/23 after Shields is wounded
    assert oob.commander_of("FRM_US_SHIELDSDIV_K", date(1862, 3, 22)) == "CMD_SHIELDS"
    assert oob.commander_of("FRM_US_SHIELDSDIV_K", date(1862, 3, 23)) == "CMD_KIMBALL"
    assert oob.commander_of("FRM_CS_STONEWALL", OPENING_DATE) == "CMD_GARNETT"


def test_opening_strength_flags():
    oob = OOB.load()
    r = {x["return_id"]: x for x in oob.returns}
    for rid in ("R108", "R109", "R112"):
        assert "UNION_0322_FROM_FEB_RETURN" in r[rid]["basis"]
    shields = {k: r[k] for k in ("R110", "R119", "R120")}
    assert all(v["subject_id"] == "FRM_US_SHIELDSDIV_K" for v in shields.values())
    for k, page in (("R110", "p.342"), ("R119", "p.335"), ("R120", "p.336")):
        assert page in shields[k]["sources"], k


def test_shields_r120_is_estimate():
    oob = OOB.load()
    r = {x["return_id"]: x for x in oob.returns}["R120"]
    assert r["kind"] == "estimate"
    assert "between 7,000 and 8,000" in r["basis"]
