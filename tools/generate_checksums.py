#!/usr/bin/env python3
"""Generate deterministic SHA-256 checksums for tracked release files."""

from __future__ import annotations

import hashlib
from pathlib import Path

from release_inventory import checksum_files

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "SHA256SUMS.txt"
FIXED_OUTPUT = ROOT / "SHA256SUMS_fixed.txt"
entries: list[str] = []
for path in checksum_files(ROOT):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    entries.append(f"{digest}  {path.relative_to(ROOT).as_posix()}")

OUTPUT.write_text("\n".join(entries) + "\n", encoding="utf-8")
FIXED_OUTPUT.write_text("\n".join(entries) + "\n", encoding="utf-8")
print(f"updated checksums: files={len(entries)}")
