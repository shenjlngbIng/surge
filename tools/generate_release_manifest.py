#!/usr/bin/env python3
"""Generate the deterministic file manifest shipped with the R13.17 release."""

from __future__ import annotations

import hashlib
from pathlib import Path

from release_inventory import manifest_files

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "RELEASE_MANIFEST.txt"
files = manifest_files(ROOT)
lines = [
    "Surge iOS Privacy + Push R13.17 Connectivity Recovery release manifest",
    "Generated: 2026-09-02",
    f"Files: {len(files)}",
    "",
]
for path in files:
    relative = path.relative_to(ROOT).as_posix()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    lines.append(f"{digest}  {relative}")

OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"updated {OUTPUT}: files={len(files)}")
