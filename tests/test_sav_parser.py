"""Only test existing read-only header inspection; not game-valid serialization."""
from src.sav_parser import dump_first_64_bytes


def test_dump_first_64_bytes(tmp_path):
    sample = tmp_path / "example.sav"
    payload = bytes(range(128))
    sample.write_bytes(payload)
    assert dump_first_64_bytes(sample) == payload[:64]


def test_short_header(tmp_path):
    sample = tmp_path / "small.sav"
    sample.write_bytes(b"not_a_real_sav")
    assert dump_first_64_bytes(sample) == b"not_a_real_sav"
