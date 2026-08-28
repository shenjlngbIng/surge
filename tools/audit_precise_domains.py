#!/usr/bin/env python3
"""Audit the two curated Surge DOMAIN-SET files.

The precise sets intentionally trade breadth for deterministic ownership. They
must contain suffix domains only, must not contain public suffixes, keywords or
shared infrastructure, and may never overlap across Domestic and Proxy policies.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SETS = {
    "Domestic": ROOT / "Rules" / "China.list",
    "Proxy": ROOT / "Rules" / "Global.list",
}
LOCK = ROOT / "Rules" / "upstreams.lock.json"
DOMAIN_RE = re.compile(
    r"^\.(?=.{3,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)
SHARED_INFRASTRUCTURE = {
    ".akamai.net",
    ".akamaiedge.net",
    ".akamaized.net",
    ".amazonaws.com",
    ".auth0.com",
    ".azureedge.net",
    ".azurewebsites.net",
    ".cloudflare.com",
    ".cloudflare.net",
    ".cloudfront.net",
    ".fastly.net",
    ".sentry.io",
    ".stripe.com",
}


def active_lines(path: Path) -> list[str]:
    if not path.is_file():
        raise AssertionError(f"missing precise domain set: {path}")
    return [
        raw.strip()
        for raw in path.read_text(encoding="utf-8-sig").splitlines()
        if raw.strip() and not raw.lstrip().startswith(("#", ";", "//"))
    ]


def suffix_overlap(left: str, right: str) -> bool:
    left_domain = left[1:]
    right_domain = right[1:]
    return (
        left_domain == right_domain
        or left_domain.endswith("." + right_domain)
        or right_domain.endswith("." + left_domain)
    )


parsed: dict[str, list[str]] = {}
for policy, path in SETS.items():
    lines = active_lines(path)
    if len(lines) != len(set(lines)):
        duplicates = sorted({line for line in lines if lines.count(line) > 1})
        raise AssertionError(f"{path.name}: duplicate domains: {duplicates}")
    for line in lines:
        if line != line.lower() or not DOMAIN_RE.fullmatch(line):
            raise AssertionError(f"{path.name}: invalid DOMAIN-SET entry: {line}")
        if line in SHARED_INFRASTRUCTURE:
            raise AssertionError(f"{path.name}: shared infrastructure is forbidden: {line}")
    for index, left in enumerate(lines):
        for right in lines[index + 1 :]:
            if suffix_overlap(left, right):
                raise AssertionError(
                    f"{path.name}: redundant suffix coverage: {left} <-> {right}"
                )
    parsed[policy] = lines

for direct in parsed["Domestic"]:
    for proxy in parsed["Proxy"]:
        if suffix_overlap(direct, proxy):
            raise AssertionError(f"cross-policy domain conflict: {direct} <-> {proxy}")

if not (200 <= len(parsed["Domestic"]) <= 500):
    raise AssertionError("China precise set must remain intentionally bounded")
if not (75 <= len(parsed["Proxy"]) <= 250):
    raise AssertionError("Global precise set must remain intentionally bounded")

summary = []
expected_lock_sources = []
for policy, path in SETS.items():
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    expected_lock_sources.append(
        {
            "kind": "DOMAIN-SET",
            "path": path.relative_to(ROOT).as_posix(),
            "policy": policy,
            "active_entries": len(parsed[policy]),
            "sha256": digest,
        }
    )
    summary.append(f"{policy}={len(parsed[policy])}:{digest[:12]}")

lock = json.loads(LOCK.read_text(encoding="utf-8"))
precise_lock = dict(lock.get("precise_domains", {}))
if precise_lock.get("schema") != 1:
    raise AssertionError("precise domain lock schema mismatch")
if precise_lock.get("mode") != "repository-curated-domain-set":
    raise AssertionError("precise domain lock mode mismatch")
if precise_lock.get("sources") != expected_lock_sources:
    raise AssertionError("precise domain lock inventory or hash is stale")
print("PASS precise domains " + " ".join(summary) + " conflicts=0")
