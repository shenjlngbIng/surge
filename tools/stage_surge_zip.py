#!/usr/bin/env python3
"""Safely stage an untrusted Surge.zip without mutating the checkout."""

from __future__ import annotations

import argparse
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath


MAX_FILES = 512
MAX_FILE_SIZE = 8 * 1024 * 1024
MAX_TOTAL_SIZE = 32 * 1024 * 1024


def normalized_target(name: str) -> PurePosixPath | None:
    if "\\" in name:
        raise ValueError(f"backslash path is forbidden: {name!r}")
    source = PurePosixPath(name)
    if source.is_absolute() or ".." in source.parts:
        raise ValueError(f"unsafe archive path: {name!r}")
    parts = list(source.parts)
    if parts and parts[0] in {"Surge", "Surge-R10-Candidate", "Surge-R12-Candidate", "Surge-R12.14-Candidate"}:
        parts.pop(0)
    if not parts:
        return None
    target = PurePosixPath(*parts)
    if str(target) in {"Surge.conf", "README.md", "NOTICE.md", "CHANGELOG.md", "MIGRATION.md"}:
        return target
    if str(target) in {"Rules/upstreams.lock.json", "Rules/r10.lock.json"}:
        return target
    if len(target.parts) == 2 and target.parts[0] == "Rules" and target.suffix == ".list":
        return target
    if len(target.parts) == 2 and target.parts[0] == "THIRD_PARTY_LICENSES" and target.suffix == ".txt":
        return target
    raise ValueError(f"file is outside the import allowlist: {name!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    if args.archive.is_symlink() or not args.archive.is_file():
        print(f"ERROR: archive not found: {args.archive}", file=sys.stderr)
        return 2
    if args.output.exists():
        if args.output.is_symlink() or not args.output.is_dir():
            print(f"ERROR: output path is not a directory: {args.output}", file=sys.stderr)
            return 2
        if any(args.output.iterdir()):
            print(f"ERROR: output directory is not empty: {args.output}", file=sys.stderr)
            return 2

    staged: dict[PurePosixPath, zipfile.ZipInfo] = {}
    total_size = 0
    try:
        with zipfile.ZipFile(args.archive) as archive:
            entries = [entry for entry in archive.infolist() if not entry.is_dir()]
            if len(entries) > MAX_FILES:
                raise ValueError(f"archive contains too many files: {len(entries)}")
            for entry in entries:
                if entry.flag_bits & 0x1:
                    raise ValueError(f"encrypted archive entries are forbidden: {entry.filename!r}")
                mode = entry.external_attr >> 16
                if stat.S_ISLNK(mode) or stat.S_ISCHR(mode) or stat.S_ISBLK(mode) or stat.S_ISFIFO(mode):
                    raise ValueError(f"links and special files are forbidden: {entry.filename!r}")
                if entry.file_size > MAX_FILE_SIZE:
                    raise ValueError(f"file is too large: {entry.filename!r}")
                total_size += entry.file_size
                if total_size > MAX_TOTAL_SIZE:
                    raise ValueError("archive exceeds the total uncompressed size limit")
                target = normalized_target(entry.filename)
                if target is None:
                    continue
                if target in staged:
                    raise ValueError(f"duplicate target path: {target}")
                staged[target] = entry

            if PurePosixPath("Surge.conf") not in staged:
                raise ValueError("archive does not contain Surge.conf")

            args.output.mkdir(parents=True, exist_ok=True)
            for target, entry in staged.items():
                destination = args.output.joinpath(*target.parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as source:
                    data = source.read(MAX_FILE_SIZE + 1)
                if len(data) != entry.file_size or len(data) > MAX_FILE_SIZE:
                    raise ValueError(f"size mismatch while reading: {entry.filename!r}")
                destination.write_bytes(data)
    except (ValueError, zipfile.BadZipFile, OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"STAGED: files={len(staged)} bytes={total_size} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
