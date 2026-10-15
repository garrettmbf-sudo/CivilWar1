"""The prototype must not advertise arbitrary bytes as playable .sav files."""
import pytest

from scripts.generate_sav import generate_minimal
from scripts.validate_sav import validate


def test_generator_fails_closed(tmp_path):
    output = tmp_path / "invalid.sav"
    with pytest.raises(NotImplementedError):
        generate_minimal(output)
    assert not output.exists()


def test_validator_fails_closed_on_unknown_bytes(tmp_path):
    sample = tmp_path / "unknown.sav"
    sample.write_bytes(b"arbitrary nonempty bytes")
    assert validate(str(sample)) != 0
