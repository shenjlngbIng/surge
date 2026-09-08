#!/usr/bin/env python3
"""Check rule conversion semantics without claiming a Surge/device runtime test."""

from __future__ import annotations

import fnmatch
import ipaddress
from pathlib import Path

from convert_to_remote_rules import active_rule_lines, validate_remote_profile

ROOT = Path(__file__).resolve().parent.parent


def record(row: str, policy: str | None = None, outer: set[str] | None = None) -> tuple:
    fields = row.split(",")
    kind = fields[0]
    if kind == "FINAL":
        return (kind, "", fields[1], False, False)
    options = set(fields[2:] if policy is not None else fields[3:]) | (outer or set())
    return (
        kind, fields[1], policy if policy is not None else fields[2],
        "extended-matching" in options and kind.startswith("DOMAIN"),
        "no-resolve" in options and kind in {"IP-CIDR", "IP-CIDR6", "IP-ASN", "GEOIP"},
    )


def reference_records(profile: str) -> list[tuple]:
    """Read external source semantics only in memory; never write a flattened profile."""
    output: list[tuple] = []
    for row in active_rule_lines(profile):
        fields = row.split(",")
        if fields[0] not in {"DOMAIN-SET", "RULE-SET"}:
            output.append(record(row))
            continue
        kind, url, policy, *options = fields
        source = ROOT / "Rules" / url.rsplit("/", 1)[1]
        for entry in source.read_text().splitlines():
            entry = entry.strip()
            if not entry or entry.startswith(("#", "//", ";")):
                continue
            if kind == "DOMAIN-SET":
                output.append((
                    "DOMAIN-SUFFIX" if entry[0] == "." else "DOMAIN",
                    entry.lstrip("."), policy, "extended-matching" in options, False,
                ))
            else:
                output.append(record(entry, policy, set(options)))
    return output


def domain_route(records: list[tuple], hostname: str, sni: str = "") -> str:
    """Model first-match domain routing; it does not simulate live Surge I/O."""
    for kind, value, policy, extended, _no_resolve in records:
        hosts = [hostname.lower().rstrip(".")]
        if extended and sni:
            hosts.append(sni.lower().rstrip("."))
        value = value.lower()
        if kind == "FINAL":
            return policy
        for host in hosts:
            matched = (
                (kind == "DOMAIN" and host == value)
                or (kind == "DOMAIN-SUFFIX" and (host == value or host.endswith("." + value)))
                or (kind == "DOMAIN-KEYWORD" and value in host)
                or (kind == "DOMAIN-WILDCARD" and fnmatch.fnmatchcase(host, value))
            )
            if matched:
                return policy
    raise AssertionError("missing FINAL")


def reject_bad_profile(text: str) -> None:
    try:
        validate_remote_profile(text)
    except (ValueError, SystemExit):
        return
    raise AssertionError("corrupted external profile was accepted")


def main() -> int:
    text = (ROOT / "Surge.conf").read_text()
    validate_remote_profile(text)
    actual = reference_records(text)
    assert len(actual) == 5659
    for kind, value, _policy, _extended, no_resolve in actual:
        if kind in {"IP-CIDR", "IP-CIDR6"}:
            ipaddress.ip_network(value, strict=False)
            assert no_resolve, "external IP rule unexpectedly triggers DNS"

    cases = [
        ("captive.apple.com", "", "DIRECT"),
        ("httpdns.bilivideo.com", "", "DIRECT"),
        ("apiintl.biliapi.net", "", "Proxy"),
        ("api.bilibili.com", "", "DIRECT"),
        ("video.bilivideo.com", "", "DIRECT"),
        ("rum.browser-intake-datadoghq.com", "", "ChatGPT"),
        ("chatgpt.com", "", "ChatGPT"),
        ("hls.itunes.apple.com", "", "Streaming"),
        ("viu.now.com", "", "Streaming"),
        ("login.live.com", "", "Microsoft"),
        ("123tramites.com", "", "Security"),
        ("203.0.113.8", "123tramites.com", "Security"),
        ("sub.123tramites.com", "", "Final"),
        ("sub.openai.com", "", "ChatGPT"),
        ("dns.alidns.com", "", "Proxy"),
        ("alidns.com", "", "Proxy"),
        ("dns.nextdns.io", "", "Proxy"),
        ("nextdns.io", "", "Proxy"),
        ("test.nextdns.io", "", "Proxy"),
        ("unknown.example", "", "Final"),
        ("x-ad.sm.cn", "", "AdBlock"),
        ("www.1688.com", "", "Domestic"),
        ("raw.githubusercontent.com", "", "Proxy"),
    ]
    for hostname, sni, policy in cases:
        assert domain_route(actual, hostname, sni) == policy, (hostname, sni, policy)

    rules = active_rule_lines(text)
    remote = [row for row in rules if row.startswith(("RULE-SET,", "DOMAIN-SET,"))]
    assert len(remote) == 29
    reject_bad_profile(text.replace(remote[0] + "\n", "", 1))
    reject_bad_profile(text.replace(remote[0], remote[0].replace(",Security,", ",Proxy,"), 1))
    reject_bad_profile(text.replace(remote[0], remote[0].replace(",extended-matching", ""), 1))
    reject_bad_profile(text.replace(remote[0], remote[0].replace("2b8fa93901061cf0482b079203630bcd11bfe0b1", "main"), 1))
    reject_bad_profile(text.replace("[Rule]\n", "[Rule]\nDOMAIN,123tramites.com,Security\n", 1))
    reject_bad_profile(text.replace(remote[1], remote[1].replace(",no-resolve", ""), 1))
    print(f"PASS external rules={len(remote)} semantic_rules={len(actual)} routing_cases={len(cases)} corruption_cases=6; offline model only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
