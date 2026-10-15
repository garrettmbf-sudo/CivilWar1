"""Basic file inspection only — NOT verification of Hex of Steel compatibility.

The previous validator assumed an invented b'HSAV' magic and could report
"passed" for invalid or arbitrary files. Fail closed until an engine-verified
format/parser and game loading test exist.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def validate(path: str) -> int:
    sample = Path(path)
    if not sample.is_file():
        print(f"Not found: {sample}")
        return 2
    size = sample.stat().st_size
    if size == 0:
        print(f"Empty file: {sample}")
        return 2
    with sample.open("rb") as f:
        header = f.read(32)
    print(f"File exists: {sample} ({size} bytes). Header: {header.hex()}")
    print(
        "UNVERIFIED: no documented Hex of Steel .sav schema or in-game "
        "round-trip yet. Existence and readable bytes are not a validation pass."
    )
    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()
    raise SystemExit(validate(args.file))
