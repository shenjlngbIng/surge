#!/usr/bin/env python3
"""Check rule conversion semantics without claiming a Surge/device runtime test."""

from __future__ import annotations

import fnmatch
import ipaddress
from pathlib import Path

from convert_to_remote_rules import FOREIGN_DNS_RULES, active_rule_lines, validate_remote_profile

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


def domain_route(
    records: list[tuple], hostname: str, sni: str = "", *, port: int | None = None,
) -> str:
    """Model known-host TCP rules, optionally including the destination port.

    IP/GeoIP, protocol detection, DNS hijacking and live I/O are not simulated.
    Omitting port retains the domain/SNI-only model used by the original cases.
    """
    for kind, value, policy, extended, _no_resolve in records:
        hosts = [hostname.lower().rstrip(".")]
        if extended and sni:
            hosts.append(sni.lower().rstrip("."))
        value = value.lower()
        if kind == "FINAL":
            return policy
        if kind == "DEST-PORT" and port is not None and int(value) == port:
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


def check_behavior(records: list[tuple]) -> tuple[int, int, int]:
    """Independent positive/negative fixtures, not generated from policy constants."""
    normal_sites = (
        "www.footlocker.com", "stores.footlocker.com",
        "www.zooplus.com", "support.zooplus.com",
        "www.zoohit.cz", "support.zoohit.cz",
        "www.bitiba.co.uk", "support.bitiba.co.uk",
        "www.stenaline.com", "stenaline.com",
        "www.dolce-gusto.com", "www.dolce-gusto.co.uk",
        "www.nimiq.com", "wallet.nimiq.com",
        "www.seniorliving.org", "seniorliving.org",
    )
    ads = (
        "x-ad.sm.cn", "ads-api.tiktok.com", "ads-track.xhscdn.com",
        "pixel1.adswizz.com", "sanl.footlocker.com", "example.doubleclick.net",
        "tracking.eu.miui.com", "log1-normal-test.tiktokv.com",
    )
    for hostname in normal_sites:
        actual = domain_route(records, hostname, port=443)
        assert actual == "Final", ("normal website blocked/misrouted", hostname, actual)
    for hostname in ads:
        actual = domain_route(records, hostname, port=443)
        assert actual == "AdBlock", ("advertising regression", hostname, actual)

    domestic = (
        "dns.pub", "doh.pub", "dot.pub", "dns.360.cn", "doh.360.cn",
        "dns.alibabadns.com", "dns.alidns.com", "httpdns.baidubce.bdydns.com",
        "doh.bytednsdoc.com", "dns.la", "dns.dnspod.cn", "dns.dnspod.com",
        "dns.dnsv1.com", "dns.jomodns.com", "dns.smtcdns.net",
    )
    foreign = (
        "dns.google", "one.one.one.one", "dns.adguard.com", "doh.opendns.com",
        "doh.cleanbrowsing.org", "doh.dns.sb", "doh.tiar.app", "dot.tiar.app",
        "dns.twnic.tw", "cloudflare-dns.com", "dns.quad9.net", "dns.nextdns.io",
    )
    # Test routing, not whether every provider serves every listed port.
    dns_cases = [
        (host, port, "REJECT" if host in foreign and port == 53 else "Proxy")
        for host in (*domestic, *foreign) for port in (53, 443, 853, 8853)
    ]
    unknown = (
        "unknown-resolver.example", "dns.google.evil.example", "evildns.google",
        "notcloudflare-dns.com", "cloudflare-dns.com.evil.example",
        "quad9.net.evil.example", "nextdns.io.evil.example", "dot.pub.evil.example",
    )
    dns_cases.extend((host, port, "REJECT") for host in unknown for port in (53, 853, 8853))
    for host, port, expected in dns_cases:
        actual = domain_route(records, host, port=port)
        assert actual == expected, ("DNS port routing", host, port, actual, expected)
    return len(normal_sites), len(ads), len(dns_cases)


def reject_bad_profile(text: str) -> None:
    try:
        validate_remote_profile(text)
    except (ValueError, SystemExit):
        return
    raise AssertionError("corrupted external profile was accepted")


def check_behavior_regressions(text: str, records: list[tuple]) -> int:
    """Prove fixtures catch the old bugs without relying on hashes or rule counts."""
    insertion = next(index for index, row in enumerate(records) if row[2] == "AdBlock")
    retired = (
        ".bitiba.", ".footlocker.", ".nimiq.", ".stenaline.",
        ".zoohit.", ".zooplus.", "dolce-gusto.", "seniorliving.",
    )
    mutants = [
        records[:insertion] + [record(f"DOMAIN-KEYWORD,{keyword}", "AdBlock")] + records[insertion:]
        for keyword in retired
    ]
    foreign_block = "\n".join(FOREIGN_DNS_RULES) + "\n"
    assert text.count(foreign_block) == 1
    without_foreign = text.replace(foreign_block, "", 1)
    mutants.extend((
        reference_records(without_foreign.replace(
            "DEST-PORT,8853,REJECT\n", "DEST-PORT,8853,REJECT\n" + foreign_block, 1,
        )),
        reference_records(without_foreign.replace(
            "DEST-PORT,53,REJECT\n", foreign_block + "DEST-PORT,53,REJECT\n", 1,
        )),
    ))
    for index, candidate in enumerate(mutants):
        try:
            check_behavior(candidate)
        except AssertionError:
            continue
        raise AssertionError(f"behavior fixtures accepted regression {index}")
    return len(mutants)


def main() -> int:
    text = (ROOT / "Surge.conf").read_text()
    validate_remote_profile(text)
    actual = reference_records(text)
    assert len(actual) == 5650
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
    normal_count, ad_count, dns_count = check_behavior(actual)
    behavior_mutations = check_behavior_regressions(text, actual)

    rules = active_rule_lines(text)
    remote = [row for row in rules if row.startswith(("RULE-SET,", "DOMAIN-SET,"))]
    assert len(remote) == 29
    reject_bad_profile(text.replace(remote[0] + "\n", "", 1))
    reject_bad_profile(text.replace(remote[0], remote[0].replace(",Security,", ",Proxy,"), 1))
    reject_bad_profile(text.replace(remote[0], remote[0].replace(",extended-matching", ""), 1))
    reject_bad_profile(text.replace(remote[0], remote[0].replace("6e8e1bfbbdda66ee8ad0a5ad3979b6de8b5b7a51", "main"), 1))
    reject_bad_profile(text.replace("[Rule]\n", "[Rule]\nDOMAIN,123tramites.com,Security\n", 1))
    reject_bad_profile(text.replace(remote[1], remote[1].replace(",no-resolve", ""), 1))
    print(
        f"PASS external rules={len(remote)} semantic_rules={len(actual)} "
        f"routing_cases={len(cases)} normal_sites={normal_count} advertising={ad_count} "
        f"dns_port_cases={dns_count} corruption_cases=6 "
        f"behavior_mutations={behavior_mutations}; offline model only"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
