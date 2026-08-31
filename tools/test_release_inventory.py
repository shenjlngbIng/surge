#!/usr/bin/env python3
"""Regression tests for the strict shared release inventory."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from release_inventory import RELEASE_PATHS, ROOT, remove_stale_managed_files, validate_release_tree


PACKAGER = ROOT / "tools" / "package_release.py"


def clone_release(destination: Path) -> None:
    for relative in RELEASE_PATHS:
        source = ROOT.joinpath(*relative.parts)
        target = destination.joinpath(*relative.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def rejected(mutator) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        clone_release(root)
        mutator(root)
        try:
            validate_release_tree(root)
        except ValueError:
            return
        raise AssertionError("unsafe release tree mutation was accepted")


def main() -> int:
    validate_release_tree(ROOT)
    rejected(lambda root: (root / ".env").write_text("TOKEN=secret\n"))
    rejected(lambda root: (root / "debug.log").write_text("debug\n"))
    rejected(lambda root: (root / "unknown").mkdir())
    rejected(lambda root: (root / "Rules" / ".git").write_text("nested git marker\n"))
    rejected(lambda root: (root / "LEAK.txt").symlink_to("/etc/hosts"))
    rejected(lambda root: (root / "Surge.zip").symlink_to("/etc/hosts"))
    rejected(lambda root: (root / "README.md").unlink())
    rejected(lambda root: (root / "README.md").write_bytes(b"invalid: \xff\n"))
    rejected(lambda root: (root / "README.md").write_bytes(b"NUL\x00byte\n"))
    rejected(lambda root: (root / "README.md").write_bytes(b"CRLF\r\n"))
    rejected(lambda root: (root / "README.md").write_bytes(b"missing final newline"))
    rejected(lambda root: (root / "README.md").write_bytes(b"\xef\xbb\xbfBOM\n"))

    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        root = base / "repo"
        root.mkdir()
        clone_release(root)
        stale = root / "Rules" / "Old.list"
        stale.write_text("DOMAIN,old.example\n")
        custom = root / "USER_NOTES.txt"
        custom.write_text("keep\n")
        manifest = base / "old-manifest.txt"
        manifest.write_text(
            "0" * 64 + "  Rules/Old.list\n" + "1" * 64 + "  README.md\n",
            encoding="utf-8",
        )
        removed = remove_stale_managed_files(root, manifest)
        if removed != [Path("Rules/Old.list")] or stale.exists() or not custom.exists():
            raise AssertionError("stale managed cleanup changed the wrong paths")

    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        root = base / "repo"
        root.mkdir()
        manifest = base / "old-manifest.txt"
        manifest.write_text("0" * 64 + "  ../outside\n", encoding="utf-8")
        try:
            remove_stale_managed_files(root, manifest)
        except ValueError:
            pass
        else:
            raise AssertionError("unsafe old manifest path was accepted")

    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "release.zip"
        target = Path(directory) / "must-not-change.txt"
        target.write_text("safe\n")
        output.symlink_to(target)
        result = subprocess.run(
            [sys.executable, str(PACKAGER), "--output", str(output)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 or target.read_text() != "safe\n":
            raise AssertionError("symbolic-link package output was accepted")

    print("PASS: strict release inventory regression cases=16")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
