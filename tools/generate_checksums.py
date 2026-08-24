#!/usr/bin/env python3
"""Generate deterministic SHA-256 checksums for tracked release files."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "SHA256SUMS.txt"
FIXED_OUTPUT = ROOT / "SHA256SUMS_fixed.txt"
EXCLUDED_PARTS = {".git", "__pycache__"}
EXCLUDED_NAMES = {"SHA256SUMS.txt", "SHA256SUMS_fixed.txt", "Surge.zip"}
EXCLUDED_SUFFIXES = {".pyc", ".zip"}


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.name in EXCLUDED_NAMES or path.suffix in EXCLUDED_SUFFIXES:
        return False
    return path.is_file()


entries: list[str] = []
for path in sorted((path for path in ROOT.rglob("*") if included(path)), key=lambda p: p.as_posix()):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    entries.append(f"{digest}  {path.relative_to(ROOT).as_posix()}")

OUTPUT.write_text("\n".join(entries) + "\n", encoding="utf-8")
FIXED_OUTPUT.write_text("\n".join(entries) + "\n", encoding="utf-8")
print(f"updated checksums: files={len(entries)}")
