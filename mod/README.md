"""Package the /mod directory into a distributable zip archive.

This script reads the repository's `/mod` folder and writes a zip file containing the
mod content. It is intentionally simple and deterministic for early tooling.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def build_mod_zip(mod_dir: str | Path, output_zip: str | Path) -> Path:
    """Create a zip archive of the mod directory."""
    mod_dir = Path(mod_dir)
    output_zip = Path(output_zip)

    if not mod_dir.exists():
        raise FileNotFoundError(f"Mod directory not found: {mod_dir}")

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    shutil.make_archive(str(output_zip.with_suffix("")), "zip", str(mod_dir))
    return output_zip.with_suffix(".zip")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a zip archive from the /mod folder.")
    parser.add_argument("--mod-dir", default="mod", help="Path to the mod directory.")
    parser.add_argument("--output", default="dist/mod.zip", help="Output zip path.")
    args = parser.parse_args()

    built = build_mod_zip(args.mod_dir, args.output)
    print(f"Created {built}")


if __name__ == "__main__":
    main()
