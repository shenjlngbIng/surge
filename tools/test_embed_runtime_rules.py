#!/usr/bin/env python3
"""Check rule conversion semantics without claiming a Surge/device runtime test."""

from __future__ import annotations

import fnmatch
import ipaddress
import tempfile
from pathlib import Path

from convert_to_remote_rules import active_rule_lines, validate_embedded_profile
from embed_runtime_rules import collapse_profile, render_domainset, render_ruleset, transform_profile

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
    """Independent reader of former source-list semantics, not the renderer."""
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
        validate_embedded_profile(text)
    except (ValueError, SystemExit):
        return
    raise AssertionError("corrupted embedded profile was accepted")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "fixture.list"
        path.write_text("# comment\nexact.example\n.suffix.example\n")
        assert render_domainset(path, "Proxy", ["extended-matching"]) == [
            "DOMAIN,exact.example,Proxy,extended-matching",
            "DOMAIN-SUFFIX,suffix.example,Proxy,extended-matching",
        ]
        path.write_text(
            "DOMAIN,exact.example\nDOMAIN-SUFFIX,suffix.example\n"
            "IP-CIDR,203.0.113.0/24,no-resolve\nIP-CIDR6,2001:db8::/32\n"
            "IP-ASN,64512\nUSER-AGENT,Example App*\n"
        )
        assert render_ruleset(path, "Service", ["extended-matching", "no-resolve"]) == [
            "DOMAIN,exact.example,Service,extended-matching",
            "DOMAIN-SUFFIX,suffix.example,Service,extended-matching",
            "IP-CIDR,203.0.113.0/24,Service,no-resolve",
            "IP-CIDR6,2001:db8::/32,Service,no-resolve",
            "IP-ASN,64512,Service,no-resolve",
            "USER-AGENT,Example App*,Service",
        ]
        path.write_text("IP-CIDR,203.0.113.0/24\n")
        assert render_ruleset(path, "Proxy", []) == ["IP-CIDR,203.0.113.0/24,Proxy"]

    text = (ROOT / "Surge.conf").read_text()
    collapsed = validate_embedded_profile(text)
    assert transform_profile(text) == text
    assert transform_profile(collapsed) == text
    expected = reference_records(collapsed)
    actual = [record(row) for row in active_rule_lines(text)]
    assert actual == expected, "rule expansion changed order, policy, matching or resolution flags"
    assert len(actual) == 5664
    for kind, value, _policy, _extended, no_resolve in actual:
        if kind in {"IP-CIDR", "IP-CIDR6"}:
            ipaddress.ip_network(value, strict=False)
            assert no_resolve, "embedded IP rule unexpectedly triggers DNS"

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
        ("123tramites.com", "", "REJECT"),
        ("203.0.113.8", "123tramites.com", "REJECT"),
        ("sub.123tramites.com", "", "Final"),
        ("sub.openai.com", "", "ChatGPT"),
        ("dns.alidns.com", "", "Proxy"),
        ("unknown.example", "", "Final"),
    ]
    for hostname, sni, policy in cases:
        assert domain_route(actual, hostname, sni) == policy, (hostname, sni, policy)
        assert domain_route(expected, hostname, sni) == policy

    first = "DOMAIN,123tramites.com,REJECT,extended-matching\n"
    assert first in text
    reject_bad_profile(text.replace(first, "", 1))
    reject_bad_profile(text.replace(first, first.replace("REJECT", "DIRECT"), 1))
    reject_bad_profile(text.replace(first, first.replace(",extended-matching", ""), 1))
    reject_bad_profile(text.replace("# END EMBEDDED-RULES: Rules/Pegasus.list", "# END EMBEDDED-RULES: Rules/Ads.list", 1))
    reject_bad_profile(text.replace("[Rule]\n", "[Rule]\nRULE-SET,https://example.invalid/ad.list,REJECT\n", 1))
    reject_bad_profile(text.replace("IP-CIDR,17.249.0.0/16,ApplePush,no-resolve", "IP-CIDR,17.249.0.0/16,ApplePush", 1))
    print(f"PASS embedded conversion rules={len(actual)} routing_cases={len(cases)} corruption_cases=6; offline model only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
