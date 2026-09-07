#!/usr/bin/env python3
"""Embed the reviewed Rules/*.list snapshots directly into Surge.conf.

The generated profile has no remote RULE-SET or DOMAIN-SET dependency.  Blocks
are reproducible and idempotent: rerunning this script refreshes every block
from the corresponding reviewed snapshot.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "Surge.conf"
RULES = ROOT / "Rules"

REMOTE_RE = re.compile(
    r"^(RULE-SET|DOMAIN-SET),https://cdn\.jsdelivr\.net/gh/"
    r"shenjlngbIng/surge@[0-9a-f]{40}/Rules/([^,]+),([^,]+)(?:,(.*))?$"
)
SNAPSHOT_BASE = (
    "https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@"
    "2b8fa93901061cf0482b079203630bcd11bfe0b1/Rules/"
)
BEGIN_RE = re.compile(
    r"^# BEGIN EMBEDDED-RULES: (RULE-SET|DOMAIN-SET)\|"
    r"(Rules/[^|]+)\|([^|]+)\|(.*)$"
)

DOMAIN_TYPES = {
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "DOMAIN-WILDCARD",
}
IP_TYPES = {"IP-CIDR", "IP-CIDR6", "IP-ASN", "GEOIP"}
SUPPORTED_TYPES = DOMAIN_TYPES | IP_TYPES | {"USER-AGENT"}


def active_rows(path: Path) -> list[str]:
    return [
        row.strip()
        for row in path.read_text(encoding="utf-8").splitlines()
        if row.strip() and not row.lstrip().startswith(("#", "//", ";"))
    ]


def append_once(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def render_ruleset(path: Path, policy: str, options: list[str]) -> list[str]:
    output: list[str] = []
    for row in active_rows(path):
        parts = [part.strip() for part in row.split(",")]
        if len(parts) < 2 or parts[0] not in SUPPORTED_TYPES:
            raise SystemExit(f"unsupported embedded rule in {path.name}: {row}")
        rule_type, value = parts[:2]
        local_options = parts[2:]
        if not value or any(item not in {"no-resolve", "extended-matching"} for item in local_options):
            raise ValueError(f"unsupported source options in {path.name}: {row}")
        if "extended-matching" in options and rule_type in DOMAIN_TYPES:
            append_once(local_options, "extended-matching")
        if "no-resolve" in options and rule_type in IP_TYPES:
            append_once(local_options, "no-resolve")
        fields = [rule_type, value, policy, *local_options]
        output.append(",".join(fields))
    return output


def render_domainset(path: Path, policy: str, options: list[str]) -> list[str]:
    output: list[str] = []
    for row in active_rows(path):
        if "," in row or any(char.isspace() for char in row):
            raise SystemExit(f"invalid DOMAIN-SET row in {path.name}: {row}")
        if row.startswith("."):
            rule_type, value = "DOMAIN-SUFFIX", row[1:]
        else:
            rule_type, value = "DOMAIN", row
        fields = [rule_type, value, policy]
        if "extended-matching" in options:
            fields.append("extended-matching")
        output.append(",".join(fields))
    return output


def render_block(kind: str, relative: str, policy: str, options_text: str, root: Path = ROOT) -> list[str]:
    path = root / relative
    if kind not in {"RULE-SET", "DOMAIN-SET"} or not path.is_file() or path.parent != root / "Rules" or path.is_symlink():
        raise ValueError(f"missing or unsafe embedded source: {relative}")
    options = [item for item in options_text.split(",") if item]
    if any(item not in {"extended-matching", "no-resolve", "update-interval=-1"} for item in options):
        raise ValueError(f"unknown set option in {relative}: {options_text}")
    if kind == "RULE-SET":
        rules = render_ruleset(path, policy, options)
    else:
        rules = render_domainset(path, policy, options)
    return [
        f"# BEGIN EMBEDDED-RULES: {kind}|{relative}|{policy}|{options_text}",
        *rules,
        f"# END EMBEDDED-RULES: {relative}",
    ]


def transform_profile(text: str, root: Path = ROOT) -> str:
    source = text.splitlines()
    output: list[str] = []
    source_count = 0
    rule_count = 0
    index = 0
    while index < len(source):
        row = source[index]
        remote = REMOTE_RE.match(row)
        embedded = BEGIN_RE.match(row)
        if remote:
            kind, filename, policy, options_text = remote.groups()
            options_text = options_text or ""
            block = render_block(kind, f"Rules/{filename}", policy, options_text, root)
            output.extend(block)
            source_count += 1
            rule_count += len(block) - 2
            index += 1
            continue
        if embedded:
            kind, relative, policy, options_text = embedded.groups()
            end = f"# END EMBEDDED-RULES: {relative}"
            index += 1
            while index < len(source) and source[index] != end:
                index += 1
            if index == len(source):
                raise SystemExit(f"unterminated embedded block: {relative}")
            block = render_block(kind, relative, policy, options_text, root)
            output.extend(block)
            source_count += 1
            rule_count += len(block) - 2
            index += 1
            continue
        output.append(row)
        index += 1

    rendered = "\n".join(output) + "\n"
    return rendered


def collapse_profile(text: str, root: Path = ROOT) -> tuple[str, list[tuple[str, str, str, str]]]:
    """Verify every embedded block, returning its original logical rule order.

    Former URL references exist only in this in-memory audit representation;
    they are never written to the generated profile or fetched by this helper.
    """
    rows = text.splitlines()
    output: list[str] = []
    blocks: list[tuple[str, str, str, str]] = []
    index = 0
    while index < len(rows):
        row = rows[index]
        if row.lstrip().startswith(("RULE-SET,", "DOMAIN-SET,")):
            raise ValueError("single-file profile still references an external rule resource")
        match = BEGIN_RE.fullmatch(row)
        if not match:
            if row.startswith(("# BEGIN EMBEDDED-RULES:", "# END EMBEDDED-RULES:")):
                raise ValueError("malformed or unmatched embedded block marker")
            output.append(row)
            index += 1
            continue
        kind, relative, policy, options = match.groups()
        expected = render_block(kind, relative, policy, options, root)
        if rows[index:index + len(expected)] != expected:
            raise ValueError(f"embedded content differs from its source: {relative}")
        filename = Path(relative).name
        if any(item[1] == filename for item in blocks):
            raise ValueError(f"duplicate embedded source: {relative}")
        blocks.append((kind, filename, policy, options))
        output.append(f"{kind},{SNAPSHOT_BASE}{filename},{policy},{options}")
        index += len(expected)
    return "\n".join(output) + "\n", blocks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify generated content without writing")
    args = parser.parse_args()
    original = PROFILE.read_text(encoding="utf-8")
    rendered = transform_profile(original)
    if args.check and original != rendered:
        raise SystemExit("embedded profile is not up to date")
    _collapsed, blocks = collapse_profile(rendered)
    if not blocks:
        raise SystemExit("no embedded rule sources found")
    if not args.check:
        PROFILE.write_text(rendered, encoding="utf-8")
    print(f"embedded_sources={len(blocks)} remote_runtime_rules=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
