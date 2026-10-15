from pathlib import Path

from src.sav_parser import dump_first_64_bytes


def test_dump_first_64_bytes(tmp_path):
    sample = tmp_path / "sample.sav"
    payload = bytes(range(0, 64))
    sample.write_bytes(payload)

    assert dump_first_64_bytes(sample) == payload[:64]
