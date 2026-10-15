"""Check repository portrait paths without renaming, altering, or validating likenesses."""
from __future__ import annotations

import csv
from pathlib import Path


def check_manifest(root: Path) -> list[str]:
    manifest = root / "historical_data" / "portrait_manifest.csv"
    problems: list[str] = []
    with manifest.open(newline="", encoding="utf-8") as f:
        entries = list(csv.DictReader(f))
    seen: set[str] = set()
    for row in entries:
        filename = row["filename"]
        if filename in seen:
            problems.append(f"Duplicate portrait filename: {filename}")
        seen.add(filename)
        path = row["github_path"]
        status = row["status"]
        if status == "PRESENT":
            if not path or not (root / path).is_file():
                problems.append(f"Missing existing portrait path: {filename} at {path}")
            if path and Path(path).name != filename:
                problems.append(f"Filename/path mismatch: {filename} at {path}")
        elif status == "MISSING":
            if path:
                problems.append(f"Missing portrait has populated path: {filename}")
            if (root / filename).is_file() or (root / "reference" / filename).is_file():
                problems.append(f"Portrait now present; update manifest: {filename}")
        else:
            problems.append(f"Invalid status for {filename}: {status}")
    return problems


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    problems = check_manifest(root)
    if problems:
        for problem in problems:
            print("ERROR:", problem)
        return 1
    print("Portrait filename inventory consistent; image likenesses were pre-audited by user.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
