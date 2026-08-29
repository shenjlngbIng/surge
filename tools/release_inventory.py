#!/usr/bin/env python3
"""Single strict inventory for every R13.4 release producer and verifier."""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parent.parent

TOP_LEVEL_FILES = {
    ".gitignore",
    "AUDIT_REPORT.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "MIGRATION.md",
    "NOTICE.md",
    "README.md",
    "RELEASE_MANIFEST.txt",
    "SECURITY.md",
    "SHA256SUMS.txt",
    "SHA256SUMS_fixed.txt",
    "Surge.conf",
}

RULE_FILES = {
    "APNs.list", "Ads.list", "AppleCN.list", "Bahamut.list", "BiliBili.list",
    "ChatGPT.list", "China.list", "Claude.list",
    "Direct.list", "Disney.list", "Emby.list", "Game.list", "Gemini.list",
    "Github.list", "Global.list", "Google.list", "HBO.list", "Microsoft.list",
    "Netflix.list", "OneDrive.list", "Pegasus.list", "PrimeVideo.list",
    "ProxyMedia.list", "Spotify.list", "Telegram.list", "TikTok.list",
    "Twitter.list", "WeChat.list", "YouTube.list",
    "maintained_sources.lock.json", "r10.lock.json", "resources.lock.json", "upstreams.lock.json",
}

TOOL_FILES = {
    "audit_config.py", "audit_precise_domains.py", "audit_rules.py",
    "convert_to_remote_rules.py", "generate_runtime_lock.py",
    "generate_checksums.py", "generate_release_manifest.py", "package_release.py",
    "release_inventory.py", "stage_surge_zip.py", "test_audit_config.py",
    "test_release_inventory.py", "test_stage_surge_zip.py",
    "update_external_resources.py", "update_service_rules.py",
}

LICENSE_FILES = {
    "AmnestyTech-NOTICE.txt",
    "SukkaW-AGPL-3.0.txt",
    "blackmatrix7-GPL-2.0.txt",
}

RELEASE_PATHS = frozenset(
    {PurePosixPath(name) for name in TOP_LEVEL_FILES}
    | {PurePosixPath("Rules", name) for name in RULE_FILES}
    | {PurePosixPath("tools", name) for name in TOOL_FILES}
    | {PurePosixPath("THIRD_PARTY_LICENSES", name) for name in LICENSE_FILES}
    | {PurePosixPath(".github/workflows/install.yml")}
)

MANIFEST_EXCLUDED = {
    PurePosixPath("RELEASE_MANIFEST.txt"),
    PurePosixPath("SHA256SUMS.txt"),
    PurePosixPath("SHA256SUMS_fixed.txt"),
}
GENERATED_PATHS = MANIFEST_EXCLUDED
CHECKSUM_EXCLUDED = {
    PurePosixPath("SHA256SUMS.txt"),
    PurePosixPath("SHA256SUMS_fixed.txt"),
}
TRANSIENT_ARCHIVES = {
    PurePosixPath("Surge.zip"),
    PurePosixPath("Surge-R12.17-self-maintained-20260825.zip"),
    PurePosixPath("Surge-R12.17-Privacy-Auto-20260826.zip"),
    PurePosixPath("Surge-R13.1-Complete-20260827.zip"),
    PurePosixPath("Surge-R13.1-Complete-No-Embedded-20260827.zip"),
    PurePosixPath("Surge-R13.2-Complete-No-Embedded-20260828.zip"),
    PurePosixPath("Surge-R13.3-Complete-No-Embedded-20260828.zip"),
    PurePosixPath("Surge-R13.4-Complete-No-Embedded-20260828.zip"),
}
IGNORED_DIRECTORY_NAMES = {".git", "__pycache__"}
ALLOWED_DIRECTORIES = frozenset(
    parent
    for path in RELEASE_PATHS
    for parent in path.parents
    if parent != PurePosixPath(".")
)


def _relative(root: Path, path: Path) -> PurePosixPath:
    return PurePosixPath(path.relative_to(root).as_posix())


def _validate_text_file(path: Path, relative: PurePosixPath) -> None:
    """Reject byte patterns that can be parsed differently across release consumers."""

    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"UTF-8 BOM is forbidden in a release file: {relative}")
    if b"\x00" in data:
        raise ValueError(f"NUL byte is forbidden in a release file: {relative}")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"release file is not valid UTF-8: {relative}") from exc
    if b"\r" in data:
        raise ValueError(f"release file must use LF line endings: {relative}")
    if data and not data.endswith(b"\n"):
        raise ValueError(f"release file must end with a newline: {relative}")


def validate_release_tree(
    root: Path = ROOT,
    *,
    ignored_paths: set[Path] | None = None,
) -> list[Path]:
    """Return the exact release files or reject missing, unknown, linked, or special paths."""

    root = root.resolve()
    ignored = {
        PurePosixPath(path.resolve().relative_to(root).as_posix())
        for path in (ignored_paths or set())
        if path.resolve().is_relative_to(root)
    }
    ignored |= TRANSIENT_ARCHIVES
    found: set[PurePosixPath] = set()
    pending = [root]

    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                relative = _relative(root, path)
                mode = entry.stat(follow_symlinks=False).st_mode
                if stat.S_ISLNK(mode):
                    raise ValueError(f"symbolic links are forbidden in a release tree: {relative}")
                if relative in ignored:
                    if stat.S_ISREG(mode):
                        continue
                    raise ValueError(f"ignored archive path is not a regular file: {relative}")
                if stat.S_ISDIR(mode):
                    if entry.name in IGNORED_DIRECTORY_NAMES:
                        continue
                    if relative not in ALLOWED_DIRECTORIES:
                        raise ValueError(f"unknown release directory: {relative}")
                    pending.append(path)
                    continue
                if not stat.S_ISREG(mode):
                    raise ValueError(f"special files are forbidden in a release tree: {relative}")
                if relative not in RELEASE_PATHS:
                    raise ValueError(f"unknown release file: {relative}")
                found.add(relative)

    missing = sorted(RELEASE_PATHS - found, key=str)
    if missing:
        raise ValueError("release files are missing: " + ", ".join(map(str, missing)))
    paths = [root.joinpath(*path.parts) for path in sorted(RELEASE_PATHS, key=str)]
    for path in paths:
        _validate_text_file(path, _relative(root, path))
    return paths


def manifest_files(root: Path = ROOT) -> list[Path]:
    return [
        path
        for path in validate_release_tree(root)
        if _relative(root.resolve(), path) not in MANIFEST_EXCLUDED
    ]


def checksum_files(root: Path = ROOT) -> list[Path]:
    return [
        path
        for path in validate_release_tree(root)
        if _relative(root.resolve(), path) not in CHECKSUM_EXCLUDED
    ]


def parse_manifest_paths(path: Path) -> set[PurePosixPath]:
    """Read only canonical SHA-256 rows from an earlier release manifest."""

    paths: set[PurePosixPath] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"[0-9a-f]{64}  (.+)", line)
        if not match:
            continue
        name = match.group(1)
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != name:
            raise ValueError(f"unsafe path in old release manifest: {name}")
        paths.add(relative)
    return paths


def remove_stale_managed_files(root: Path, old_manifest: Path) -> list[PurePosixPath]:
    """Delete only paths explicitly managed by the prior manifest and absent now."""

    old = parse_manifest_paths(old_manifest) | GENERATED_PATHS
    stale = sorted(old - RELEASE_PATHS, key=lambda path: (-len(path.parts), path.as_posix()))
    for relative in stale:
        target = root.joinpath(*relative.parts)
        if target.is_symlink() or target.is_file():
            target.unlink()
    for relative in stale:
        for parent in reversed(relative.parents):
            if parent == PurePosixPath("."):
                continue
            try:
                root.joinpath(*parent.parts).rmdir()
            except OSError:
                pass
    return stale


if __name__ == "__main__":
    files = validate_release_tree(ROOT)
    print(f"PASS: strict release inventory files={len(files)}")
