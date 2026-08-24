#!/usr/bin/env python3
"""Merge pinned blackmatrix7 Surge rules into the committed iOS snapshots."""

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
LOCK_PATH = ROOT / "Rules" / "upstreams.lock.json"
RULES_ROOT = ROOT / "Rules"

TYPE_ORDER = {
    "DOMAIN": 10,
    "DOMAIN-SUFFIX": 20,
    "DOMAIN-KEYWORD": 30,
    "DOMAIN-WILDCARD": 40,
    "USER-AGENT": 50,
    "URL-REGEX": 60,
    "AND": 70,
    "OR": 71,
    "NOT": 72,
    "IP-CIDR": 80,
    "IP-CIDR6": 81,
    "IP-ASN": 82,
}


def active_lines(payload: str) -> list[str]:
    return [
        line
        for raw in payload.splitlines()
        if (line := raw.strip()) and not line.startswith(("#", ";", "//"))
    ]


def sort_key(rule: str) -> tuple[int, str]:
    rule_type = rule.split(",", 1)[0].upper()
    return TYPE_ORDER.get(rule_type, 75), rule.casefold()


def declared_metadata(payload: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for raw in payload.splitlines():
        match = re.fullmatch(r"#\s*(NAME|AUTHOR|REPO):\s*(.+)", raw.strip())
        if match:
            metadata[match.group(1)] = match.group(2).strip()
    missing = {"NAME", "AUTHOR", "REPO"} - metadata.keys()
    if missing:
        raise ValueError(f"upstream attribution metadata is missing: {sorted(missing)}")
    return metadata


def git_blob_sha(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()  # noqa: S324 - Git object identity


def load_lock() -> dict[str, object]:
    data = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise ValueError("unsupported upstream lock schema")
    upstream = dict(data["upstream"])
    repository = str(upstream["repository"])
    commit = str(upstream["commit"])
    if repository != "blackmatrix7/ios_rule_script":
        raise ValueError(f"unexpected upstream repository: {repository}")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("upstream commit must be a full lowercase Git SHA")
    expected_base = f"https://raw.githubusercontent.com/{repository}/{commit}/"
    if upstream.get("download_base") != expected_base:
        raise ValueError("download_base does not match the pinned repository and commit")

    merge = dict(data["merge"])
    if set(merge["drop_imported_types"]) != {"PROCESS-NAME", "IP-ASN"}:
        raise ValueError("unexpected imported rule-type filter")

    services = list(data["services"])
    if len(services) != 19:
        raise ValueError(f"expected 19 pinned services, found {len(services)}")
    seen_rulesets: set[str] = set()
    seen_files: set[str] = set()
    seen_paths: set[str] = set()
    for raw_service in services:
        service = dict(raw_service)
        ruleset = str(service["ruleset"])
        local_file = str(service["local_file"])
        upstream_path = str(service["upstream_path"])
        if not re.fullmatch(r"RS_[A-Za-z0-9]+", ruleset):
            raise ValueError(f"invalid ruleset name: {ruleset}")
        if Path(local_file).name != local_file or not local_file.endswith(".list"):
            raise ValueError(f"invalid local filename: {local_file}")
        if not upstream_path.startswith("rule/Surge/") or ".." in Path(upstream_path).parts:
            raise ValueError(f"invalid upstream path: {upstream_path}")
        if not re.fullmatch(r"[0-9a-f]{40}", str(service["upstream_blob"])):
            raise ValueError(f"invalid upstream blob for {local_file}")
        if not re.fullmatch(r"[0-9a-f]{64}", str(service["upstream_sha256"])):
            raise ValueError(f"invalid upstream SHA-256 for {local_file}")
        exclusions = [str(value) for value in service.get("exclude", [])]
        if len(exclusions) != len(set(exclusions)):
            raise ValueError(f"duplicate exclusion for {local_file}")
        if ruleset in seen_rulesets or local_file in seen_files or upstream_path in seen_paths:
            raise ValueError(f"duplicate service identity in lock: {ruleset}")
        seen_rulesets.add(ruleset)
        seen_files.add(local_file)
        seen_paths.add(upstream_path)
    return data


def read_upstream(
    service: dict[str, object], upstream: dict[str, object], source_dir: Path | None
) -> bytes:
    local_file = str(service["local_file"])
    if source_dir is not None:
        source = source_dir / local_file
        if not source.is_file():
            raise FileNotFoundError(source)
        payload = source.read_bytes()
    else:
        url = str(upstream["download_base"]) + str(service["upstream_path"])
        request = urllib.request.Request(url, headers={"User-Agent": "surge-rules-auditor/1"})
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read(8 * 1024 * 1024 + 1)
        if len(payload) > 8 * 1024 * 1024:
            raise ValueError(f"upstream file is too large: {url}")

    expected_sha256 = str(service["upstream_sha256"])
    actual_sha256 = hashlib.sha256(payload).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"upstream SHA-256 mismatch for {local_file}: "
            f"expected {expected_sha256}, got {actual_sha256}"
        )
    expected_blob = str(service["upstream_blob"])
    actual_blob = git_blob_sha(payload)
    if actual_blob != expected_blob:
        raise ValueError(
            f"upstream Git blob mismatch for {local_file}: "
            f"expected {expected_blob}, got {actual_blob}"
        )
    return payload


def render_snapshot(
    service: dict[str, object],
    upstream: dict[str, object],
    source_payload: bytes,
    drop_types: set[str],
) -> str:
    local_file = str(service["local_file"])
    target = RULES_ROOT / local_file
    local_rules = active_lines(target.read_text(encoding="utf-8-sig"))
    source_text = source_payload.decode("utf-8-sig")
    metadata = declared_metadata(source_text)
    imported_rules = [
        rule
        for rule in active_lines(source_text)
        if rule.split(",", 1)[0].upper() not in drop_types
    ]
    exclusions = {str(value) for value in service.get("exclude", [])}
    merged = sorted(
        (rule for rule in dict.fromkeys(local_rules + imported_rules) if rule not in exclusions),
        key=sort_key,
    )
    name = str(service["ruleset"]).removeprefix("RS_")
    commit = str(upstream["commit"])
    header = [
        f"# 规则名称: {name}",
        f"# 规则统计: {len(merged)}",
        f"# 固定上游: blackmatrix7/ios_rule_script@{commit}",
        f"# 上游文件: {service['upstream_path']}",
        f"# 上游 SHA-256: {service['upstream_sha256']}",
        f"# 上游声明 NAME: {metadata['NAME']}",
        f"# 上游声明 AUTHOR: {metadata['AUTHOR']}",
        f"# 上游声明 REPO: {metadata['REPO']}",
        "# 本地处理: 过滤 PROCESS-NAME、未审核新增 IP-ASN 和共享平台排除项；精确去重，域名优先、IP 后置。",
        "",
    ]
    return "\n".join(header + merged) + "\n"


def verify_committed(
    services: list[object], upstream: dict[str, object], drop_types: set[str]
) -> None:
    commit = str(upstream["commit"])
    for raw_service in services:
        service = dict(raw_service)
        target = RULES_ROOT / str(service["local_file"])
        text = target.read_text(encoding="utf-8-sig")
        required_headers = {
            f"# 固定上游: blackmatrix7/ios_rule_script@{commit}",
            f"# 上游文件: {service['upstream_path']}",
            f"# 上游 SHA-256: {service['upstream_sha256']}",
        }
        missing_headers = required_headers - set(text.splitlines())
        if missing_headers:
            raise ValueError(f"missing pinned headers in {target.name}: {sorted(missing_headers)}")
        for key in ("NAME", "AUTHOR", "REPO"):
            if sum(line.startswith(f"# 上游声明 {key}: ") for line in text.splitlines()) != 1:
                raise ValueError(f"missing or duplicate upstream {key} attribution in {target.name}")
        rules = active_lines(text)
        if len(rules) != len(set(rules)):
            raise ValueError(f"duplicate active rule in {target.name}")
        banned = [rule for rule in rules if rule.split(",", 1)[0].upper() == "PROCESS-NAME"]
        if "PROCESS-NAME" in drop_types and banned:
            raise ValueError(f"PROCESS-NAME leaked into {target.name}")
        leaked = sorted(set(rules) & {str(value) for value in service.get("exclude", [])})
        if leaked:
            raise ValueError(f"excluded shared rule leaked into {target.name}: {leaked}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update the committed service snapshots from a pinned upstream commit."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--upstream-dir",
        type=Path,
        help="directory containing the 19 pinned upstream files",
    )
    source.add_argument(
        "--download",
        action="store_true",
        help="download the exact files named in Rules/upstreams.lock.json",
    )
    source.add_argument(
        "--verify-lock",
        action="store_true",
        help="validate the lock and committed provenance without network access",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing when a generated snapshot differs",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        lock = load_lock()
        upstream = dict(lock["upstream"])
        services = list(lock["services"])
        drop_types = {
            str(value).upper() for value in dict(lock["merge"])["drop_imported_types"]
        }
        if args.verify_lock:
            verify_committed(services, upstream, drop_types)
            print(f"PASS: verified upstream lock services={len(services)}")
            return 0

        source_dir: Path | None = args.upstream_dir
        changed: list[str] = []
        for raw_service in services:
            service = dict(raw_service)
            target = RULES_ROOT / str(service["local_file"])
            payload = read_upstream(service, upstream, source_dir)
            rendered = render_snapshot(service, upstream, payload, drop_types)
            current = target.read_text(encoding="utf-8-sig")
            if current == rendered:
                continue
            changed.append(target.name)
            if not args.check:
                target.write_text(rendered, encoding="utf-8", newline="\n")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, urllib.error.URLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.check and changed:
        print(f"ERROR: service snapshots need regeneration: {', '.join(changed)}", file=sys.stderr)
        return 1
    action = "checked" if args.check else "updated"
    print(f"PASS: {action} service snapshots={len(services)} changed={len(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
