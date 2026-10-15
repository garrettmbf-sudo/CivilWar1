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
