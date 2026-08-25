#!/usr/bin/env python3
"""Verify or refresh pinned third-party static resources used by Surge.

Runtime profiles never load these third-party URLs directly.  The URLs below
are maintenance inputs only; downloaded bytes must match the full commit,
Git-blob identity and SHA-256 recorded in ``Rules/resources.lock.json``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LOCK_PATH = ROOT / "Rules/resources.lock.json"
RULES_ROOT = ROOT / "Rules"
MAX_RESOURCE_SIZE = 2 * 1024 * 1024
DOMAIN_RE = re.compile(
    r"(?=.{1,253}\Z)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z",
    re.IGNORECASE,
)


def fail(message: str) -> None:
    raise ValueError(message)


def git_blob_sha(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()  # noqa: S324 - Git identity


def source_rows(payload: bytes) -> list[str]:
    text = payload.decode("utf-8-sig")
    rows = [line.strip().lower() for line in text.splitlines() if line.strip()]
    if not rows:
        fail("resource contains no active rows")
    if len(rows) != len(set(rows)):
        fail("resource contains duplicate rows")
    invalid = [row for row in rows if not DOMAIN_RE.fullmatch(row)]
    if invalid:
        fail(f"resource contains invalid domains: {invalid[:3]}")
    return rows


def render(resource: dict[str, object], payload: bytes) -> bytes:
    rows = source_rows(payload)
    expected_count = int(resource["active_entries"])
    if len(rows) != expected_count:
        fail(f"expected {expected_count} rows, found {len(rows)}")
    header = [
        f"# NAME: {resource['name']}",
        f"# FORMAT: Surge {resource['format']}",
        f"# POLICY: {resource['policy']}",
        f"# ENTRIES: {expected_count}",
        f"# PINNED SOURCE: {resource['repository']}@{resource['commit']}",
        f"# SOURCE FILE: {resource['upstream_path']}",
        f"# SOURCE SHA-256: {resource['upstream_sha256']}",
        f"# SOURCE GIT BLOB: {resource['upstream_blob']}",
        "# LOCAL PROCESSING: Exact non-empty source rows; no third-party runtime URL.",
        "",
    ]
    return ("\n".join(header + rows) + "\n").encode("utf-8")


def load_lock() -> tuple[dict[str, object], dict[str, object]]:
    data = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        fail("unsupported resource lock schema")
    resources = list(data.get("resources", []))
    if len(resources) != 1:
        fail(f"expected one pinned runtime resource, found {len(resources)}")
    resource = dict(resources[0])
    expected = {
        "name": "Pegasus",
        "format": "DOMAIN-SET",
        "policy": "Security",
        "local_file": "Pegasus.list",
        "repository": "AmnestyTech/investigations",
        "commit": "3d8f248a0d015f183724ae7d096a5c46a8bb5fc7",
        "upstream_path": "2021-07-18_nso/domains.txt",
    }
    for key, value in expected.items():
        if resource.get(key) != value:
            fail(f"unexpected resource {key}: {resource.get(key)!r}")
    for key, size in (("commit", 40), ("upstream_blob", 40), ("upstream_sha256", 64), ("local_sha256", 64)):
        value = str(resource.get(key, ""))
        if len(value) != size or not re.fullmatch(r"[0-9a-f]+", value):
            fail(f"invalid {key}")
    expected_url = (
        f"https://raw.githubusercontent.com/{resource['repository']}/"
        f"{resource['commit']}/{resource['upstream_path']}"
    )
    if resource.get("upstream_url") != expected_url:
        fail("resource URL does not match its repository, commit and path")
    return data, resource


def download(resource: dict[str, object]) -> bytes:
    request = urllib.request.Request(
        str(resource["upstream_url"]),
        headers={"User-Agent": "surge-pinned-resource-maintainer/1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read(MAX_RESOURCE_SIZE + 1)
    if len(payload) > MAX_RESOURCE_SIZE:
        fail("resource exceeds size limit")
    if hashlib.sha256(payload).hexdigest() != resource["upstream_sha256"]:
        fail("upstream SHA-256 mismatch")
    if git_blob_sha(payload) != resource["upstream_blob"]:
        fail("upstream Git blob mismatch")
    return payload


def verify_local(resource: dict[str, object]) -> None:
    target = RULES_ROOT / str(resource["local_file"])
    if not target.is_file():
        fail(f"local resource is missing: {target.name}")
    payload = target.read_bytes()
    if hashlib.sha256(payload).hexdigest() != resource["local_sha256"]:
        fail(f"local SHA-256 mismatch: {target.name}")
    active = [
        line.strip()
        for line in payload.decode("utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith(("#", ";", "//"))
    ]
    if len(active) != int(resource["active_entries"]):
        fail(f"local entry count mismatch: {target.name}")
    if len(active) != len(set(active)) or any(not DOMAIN_RE.fullmatch(row) for row in active):
        fail(f"local domain set is invalid: {target.name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--verify-lock", action="store_true", help="verify the local copy without network access")
    action.add_argument("--download", action="store_true", help="download the exact pinned source")
    parser.add_argument("--check", action="store_true", help="with --download, fail instead of writing when content differs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        _lock, resource = load_lock()
        if args.verify_lock:
            verify_local(resource)
            print(f"PASS: verified pinned resources=1 entries={resource['active_entries']}")
            return 0
        source = download(resource)
        rendered = render(resource, source)
        rendered_sha = hashlib.sha256(rendered).hexdigest()
        if rendered_sha != resource["local_sha256"]:
            fail("rendered local SHA-256 differs from the reviewed lock")
        target = RULES_ROOT / str(resource["local_file"])
        current = target.read_bytes() if target.is_file() else b""
        if current != rendered:
            if args.check:
                fail(f"local resource needs refresh: {target.name}")
            target.write_bytes(rendered)
        verify_local(resource)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, urllib.error.URLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("PASS: downloaded pinned resources=1 changed=" + str(int(current != rendered)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
