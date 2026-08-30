#!/usr/bin/env python3
"""Create a deterministic full-repository release ZIP.

The package contains the complete repository layout, including ``Rules/`` as
separate files and ``.github/`` workflows. The profile is checked for the exact
29 immutable resources, one reviewed dynamic supplement and the absence of
embedded rule snapshots before the ZIP is written.
"""

from __future__ import annotations

import argparse
import os
import tempfile
import zipfile
from pathlib import Path

from convert_to_remote_rules import expected_remote_lines
from release_inventory import validate_release_tree


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT.parent / "Surge-R13.6-Complete-No-Embedded-20260830.zip"


def active_rule_lines(text: str) -> list[str]:
    if "[Rule]" not in text:
        raise ValueError("Surge.conf has no [Rule] section")
    return [
        line.strip()
        for line in text.split("[Rule]", 1)[1].splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def validate_profile_sources() -> None:
    profile = (ROOT / "Surge.conf").read_text(encoding="utf-8")
    active = active_rule_lines(profile)
    external = {
        line for line in active if line.startswith(("RULE-SET,", "DOMAIN-SET,"))
    }
    expected = expected_remote_lines()
    if external != expected:
        raise ValueError("Surge.conf external rule inventory is incomplete or unexpected")

    forbidden_mobile_sources = (
        "ruleset.skk.moe/List/domainset/reject.conf",
        "ruleset.skk.moe/List/domainset/reject_phishing.conf",
    )
    if any(source in profile for source in forbidden_mobile_sources):
        raise ValueError("Surge.conf contains a forbidden mobile reject source")
    if len(active) != 142 or active[-1] != "FINAL,Final,dns-failed":
        raise ValueError("Surge.conf reviewed rule count or FINAL invariant changed")
    if any(marker in profile for marker in ("raw.githubusercontent.com", "@main/Rules/")):
        raise ValueError("Surge.conf contains a mutable or unreviewed runtime rule URL")


def release_files(output: Path) -> list[Path]:
    if output.is_symlink():
        raise ValueError(f"release output must not be a symbolic link: {output}")
    ignored = {output} if output.is_relative_to(ROOT) else set()
    return validate_release_tree(ROOT, ignored_paths=ignored)


def write_archive(output: Path, files: list[Path]) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    total_size = 0
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in files:
                relative = path.relative_to(ROOT).as_posix()
                data = path.read_bytes()
                info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
                total_size += len(data)
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()
    return total_size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    candidate = args.output.expanduser()
    output = candidate if candidate.is_absolute() else (Path.cwd() / candidate).absolute()
    try:
        validate_profile_sources()
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
