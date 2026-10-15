"""Read and dump the first 64 bytes of a Hex of Steel .sav file.

This is intentionally a minimal stub for reverse engineering: it reads a file,
prints the first 64 bytes as hexadecimal, and exits.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def dump_first_64_bytes(path: str | Path) -> bytes:
    """Read the first 64 bytes of a binary file and return them."""
    sample = Path(path).read_bytes()[:64]
    return sample


def main() -> None:
    parser = argparse.ArgumentParser(description="Print the first 64 bytes of a .sav file in hex.")
    parser.add_argument("file_path", help="Path to the .sav sample file.")
    args = parser.parse_args()

    raw = dump_first_64_bytes(args.file_path)
    print(raw.hex())


if __name__ == "__main__":
    main()
