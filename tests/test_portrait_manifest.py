"""Manifest checks only — image identity audit has already been approved by user."""
from pathlib import Path

from scripts.check_portrait_manifest import check_manifest


def test_manifest_consistent():
    assert check_manifest(Path(__file__).resolve().parents[1]) == []
