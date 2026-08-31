#!/usr/bin/env python3
"""Regression checks for the candidate ZIP import allowlist."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from stage_surge_zip import collision_key, normalized_target


ROOT = Path(__file__).resolve().parent.parent
STAGER = ROOT / "tools" / "stage_surge_zip.py"


def run_archive(entries: list[tuple[str, bytes]], *, corrupt: bytes | None = None) -> tuple[int, bool]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        archive = root / "candidate.zip"
        output = root / "stage"
        with zipfile.ZipFile(archive, "w") as target:
            for name, payload in entries:
                target.writestr(name, payload)
        if corrupt is not None:
            data = archive.read_bytes()
            position = data.find(corrupt)
            if position < 0:
                raise AssertionError("test payload was not found in ZIP bytes")
            changed = bytearray(data)
            changed[position] ^= 0x01
            archive.write_bytes(changed)
        result = subprocess.run(
            [sys.executable, str(STAGER), str(archive), str(output)],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, output.exists()


def main() -> int:
    allowed = {
        "Surge.conf": "Surge.conf",
        "CHANGELOG.md": "CHANGELOG.md",
        "Rules/Ads.list": "Rules/Ads.list",
        "Rules/maintained_sources.lock.json": "Rules/maintained_sources.lock.json",
        "Rules/upstreams.lock.json": "Rules/upstreams.lock.json",
        "Rules/resources.lock.json": "Rules/resources.lock.json",
        "Rules/r10.lock.json": "Rules/r10.lock.json",
        "Surge/NOTICE.md": "NOTICE.md",
        "Surge-R10-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R12-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R12.14-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R12.15-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R12.16-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R12.17-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R13.1-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R13.2-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R13.3-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R13.4-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R13.5-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R13.6-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R13.7-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R13.8-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R13.9-Candidate/MIGRATION.md": "MIGRATION.md",
        "Surge-R13.10-Candidate/MIGRATION.md": "MIGRATION.md",
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

    if collision_key(PurePosixPath("Rules/Ads.list")) != collision_key(PurePosixPath("Rules/ads.list")):
        raise AssertionError("case-insensitive collision key is incorrect")
    if collision_key(PurePosixPath("Rules/Caf\u00e9.list")) != collision_key(PurePosixPath("Rules/Cafe\u0301.list")):
        raise AssertionError("Unicode-normalized collision key is incorrect")

    code, exists = run_archive([
        ("Surge.conf", b"[General]\n"),
        ("Rules/Ads.list", b"DOMAIN,one.example\n"),
        ("Rules/ads.list", b"DOMAIN,two.example\n"),
    ])
    if code == 0 or exists:
        raise AssertionError("case-colliding ZIP was accepted or left output")

    corrupt_payload = b"DOMAIN,crc-failure.example\n"
    code, exists = run_archive([
        ("Surge.conf", b"[General]\n"),
        ("Rules/Ads.list", corrupt_payload),
    ], corrupt=corrupt_payload)
    if code == 0 or exists:
        raise AssertionError("CRC-failing ZIP was accepted or left partial output")

    print(f"PASS: ZIP allowlist regression cases={len(allowed) + len(rejected) + 4}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
