"""Reserved command for future, empirically validated Hex of Steel map generation.

This repository previously wrote a made-up b'HSAV' header and zero bytes; that
file was NOT a verified Hex of Steel .sav map. Refuse to emit misleading files.
"""

from __future__ import annotations

import argparse


def generate_minimal(*_args, **_kwargs) -> None:
    """Fail closed until a genuine, game-tested format writer is implemented."""
    raise NotImplementedError(
        "Hex of Steel .sav writing is unverified. Use a small editor-exported "
        "test map, document its format in docs/sav-format.md, and perform an "
        "in-game load/save/reload test before enabling this command."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reserved: verified Hex of Steel .sav writing is not implemented"
    )
    parser.add_argument("out", help="Reserved destination; no file is created")
    parser.add_argument("--width", type=int, default=10)
    parser.add_argument("--height", type=int, default=10)
    args = parser.parse_args()
    parser.error(
        "Generation disabled: format unverified; no output written. "
        "See docs/sav-format.md."
    )


if __name__ == "__main__":
    main()
