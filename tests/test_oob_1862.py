"""Date-specific 1862 Valley OOB smoke tests for the recovered historical data.

These test source-data behavior only; they do NOT validate Hex of Steel integration.
"""
from datetime import date
from src.oob import OOB, validate


def test_recovered_oob_validates_baseline_rules():
    oob = OOB.load()
    assert validate(oob) == []
    assert (len(oob.formations), len(oob.regiments), len(oob.artillery), len(oob.commanders)) == (50, 96, 34, 45)


def test_key_campaign_snapshots():
    oob = OOB.load()
    expected = {
        '1862-03-23': (8, 3),
        '1862-05-08': (11, 7),
        '1862-05-25': (18, 9),
        '1862-06-09': (27, 10),
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
