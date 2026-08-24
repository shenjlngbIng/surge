#!/usr/bin/env python3
"""Regression checks for the candidate ZIP import allowlist."""

from __future__ import annotations

from pathlib import PurePosixPath

from stage_surge_zip import normalized_target


def main() -> int:
    allowed = {
        "Surge.conf": "Surge.conf",
        "CHANGELOG.md": "CHANGELOG.md",
        "Rules/Ads.list": "Rules/Ads.list",
        "Rules/BiliBiliIntl.list": "Rules/BiliBiliIntl.list",
        "Rules/upstreams.lock.json": "Rules/upstreams.lock.json",
        "Rules/r10.lock.json": "Rules/r10.lock.json",
        "Surge/NOTICE.md": "NOTICE.md",
        "Surge-R10-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R12-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R12.14-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R12.15-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R12.16-Candidate/MIGRATION.md": "MIGRATION.md",
    }
    for source, expected in allowed.items():
        if normalized_target(source) != PurePosixPath(expected):
            raise AssertionError(f"allowed path was not normalized correctly: {source}")

    rejected = (
        "../Surge.conf",
        "/Surge.conf",
        "tools/audit_config.py",
        "Rules/lock.yaml",
        "a\\b",
    )
    for source in rejected:
        try:
            normalized_target(source)
        except ValueError:
            continue
        raise AssertionError(f"unsafe path was accepted: {source}")

    print(f"PASS: ZIP allowlist regression cases={len(allowed) + len(rejected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
