#!/usr/bin/env python3
"""Generate the deterministic file manifest shipped with the R12.15 release."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "RELEASE_MANIFEST.txt"
GENERATED = {"RELEASE_MANIFEST.txt", "SHA256SUMS.txt", "SHA256SUMS_fixed.txt"}
EXCLUDED_PARTS = {".git", "__pycache__"}
EXCLUDED_SUFFIXES = {".pyc", ".zip", ".7z", ".rar"}


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.name in GENERATED or path.suffix in EXCLUDED_SUFFIXES:
        return False
    return path.is_file()


files = sorted(
    (path for path in ROOT.rglob("*") if included(path)),
    key=lambda path: path.relative_to(ROOT).as_posix(),
)
lines = [
    "Surge iOS Privacy + Push R12.15 release manifest",
    "Generated: 2026-08-24",
    f"Files: {len(files)}",
    "",
]
for path in files:
    relative = path.relative_to(ROOT).as_posix()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    lines.append(f"{digest}  {relative}")

OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"updated {OUTPUT}: files={len(files)}")
