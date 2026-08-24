#!/usr/bin/env python3
"""Create a deterministic full-repository release ZIP.

The package contains the complete repository layout, including ``Rules/`` as
separate files and ``.github/`` workflows. ``Surge.conf`` is checked to ensure
that rule snapshot contents are not embedded into the profile before the ZIP
is written.
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

from convert_to_remote_rules import expected_remote_lines


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT.parent / "Surge-R12.15-release.zip"
EXCLUDED_PARTS = {".git", "__pycache__"}
EXCLUDED_SUFFIXES = {".pyc", ".zip", ".7z", ".rar"}


def included(path: Path, output: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.resolve() == output.resolve():
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    return path.is_file()


def active_rule_lines(text: str) -> set[str]:
    if "[Rule]" not in text:
        raise ValueError("Surge.conf has no [Rule] section")
    return {
        line.strip()
        for line in text.split("[Rule]", 1)[1].splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def snapshot_rule_lines() -> set[str]:
    rules: set[str] = set()
    for path in sorted((ROOT / "Rules").glob("*.list")):
        for raw in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if line and not line.startswith(("#", ";", "//")):
                rules.add(line)
    return rules


def validate_remote_only_profile() -> None:
    profile = (ROOT / "Surge.conf").read_text(encoding="utf-8")
    if "# Embedded rules" in profile or "embedded_sources" in profile:
        raise ValueError("Surge.conf contains an embedded-rule marker")

    active = active_rule_lines(profile)
    external = {
        line for line in active if line.startswith(("RULE-SET,", "DOMAIN-SET,"))
    }
    expected = expected_remote_lines()
    if external != expected:
        raise ValueError("Surge.conf external rule inventory is incomplete or unexpected")

    embedded = sorted(active & snapshot_rule_lines())
    if embedded:
        raise ValueError(
            "Surge.conf contains rule snapshot contents; first entries: "
            + ", ".join(embedded[:3])
        )


def release_files(output: Path) -> list[Path]:
    return sorted(
        (path for path in ROOT.rglob("*") if included(path, output)),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )


def write_archive(output: Path, files: list[Path]) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    total_size = 0
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
            total_size += len(data)
    return total_size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    try:
        validate_remote_only_profile()
        files = release_files(output)
        if not files:
            raise ValueError("no release files found")
        total_size = write_archive(output, files)
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"PACKAGED: files={len(files)} bytes={total_size} output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
