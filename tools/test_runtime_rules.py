#!/usr/bin/env python3
"""Check rule conversion semantics without claiming a Surge/device runtime test."""

from __future__ import annotations

import fnmatch
import ipaddress
from pathlib import Path

from convert_to_remote_rules import FOREIGN_DNS_RULES, RELEASE_REF, active_rule_lines, validate_remote_profile

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


def literal_route(records: list[tuple], address: str, port: int) -> str:
    """Model explicit IP/port rules only; no GeoIP, ASN, DNS or live traffic.

    Push/Telegram fixtures match explicit CIDRs before the GeoIP tail. Negative
    fixtures only assert that unrelated IPs do not acquire the APNs policy.
    """
    target = ipaddress.ip_address(address)
    for kind, value, policy, _extended, _no_resolve in records:
        if kind == "FINAL":
            return policy
        if kind == "DEST-PORT" and int(value) == port:
            return policy
        if kind in {"IP-CIDR", "IP-CIDR6"} and target in ipaddress.ip_network(value):
            return policy
    raise AssertionError("missing FINAL")


def check_push_and_downloads(records: list[tuple]) -> tuple[int, int, int]:
    """Independent endpoint fixtures from Apple guidance and the reviewed lists."""
    push_hosts = (
        "courier.push.apple.com", "api.push.apple.com",
        "init-p01st.push.apple.com", "init-p01st-lb.push-apple.com.akadns.net",
        "init-p01md-lb.push-apple.com.akadns.net", "push-apple.com",
    )
    host_cases = [(host, port, "ApplePush") for host in push_hosts for port in (443, 5223)]
    host_cases += [(host, 443, "Telegram") for host in ("t.me", "api.telegram.org", "telegram.org")]
    for host, port, expected in host_cases:
        assert domain_route(records, host, port=port) == expected, (host, port, expected)
    # Keep shared CDNs, Apple services and lookalike domains outside APNs.
    not_push = (
        "www.apple.com", "identity.apple.com", "mesu.apple.com",
        "adcdownload.apple.com.akadns.net", "store.apple.com.edgekey.net",
        "example.akadns.net", "courier.push.apple.com.evil.example",
        "notpush.apple.com", "push-apple.com.akadns.net.evil.example",
    )
    for host in not_push:
        assert domain_route(records, host, port=443) != "ApplePush", host
    for host in ("raw.githubusercontent.com",):
        assert domain_route(records, host, port=443) == "Auto", host
    for host in ("raw.githubusercontent.com.evil.example", "notraw.githubusercontent.com"):
        assert domain_route(records, host, port=443) != "Auto", host
    host_count = len(host_cases) + len(not_push) + 3

    # Apple publishes these five IPv4 and four IPv6 networks for APNs.
    networks = (
        "17.249.0.0/16", "17.252.0.0/16", "17.57.144.0/22",
        "17.188.128.0/18", "17.188.20.0/23", "2620:149:a44::/48",
        "2403:300:a42::/48", "2403:300:a51::/48", "2a01:b740:a42::/48",
    )
    ip_count = 0
    for cidr in networks:
        network = ipaddress.ip_network(cidr)
        for port in (443, 5223):
            for address in (network.network_address, network.broadcast_address):
                assert literal_route(records, str(address), port) == "ApplePush", (address, port)
                ip_count += 1
            for address in (network.network_address - 1, network.broadcast_address + 1):
                assert literal_route(records, str(address), port) != "ApplePush", (address, port)
                ip_count += 1
    for address in ("149.154.167.50", "91.108.4.1", "2001:b28:f23d::1", "2001:67c:4e8::1"):
        assert literal_route(records, address, 443) == "Telegram", address
        ip_count += 1
    for port in (53, 853, 8853):
        assert literal_route(records, "17.249.0.1", port) == "REJECT", port
        ip_count += 1
    sni_count = 0
    for host in push_hosts:
        assert domain_route(records, "203.0.113.8", host, port=443) == "ApplePush", host
        sni_count += 1
    return host_count, ip_count, sni_count


def check_push_regressions(records: list[tuple]) -> int:
    """Catch missing APNs, early Apple matching, overly broad lists and old routing."""
    no_push = [row for row in records if row[2] != "ApplePush"]
    raw_manual = [
        (kind, value, "Proxy" if kind == "DOMAIN" and value == "raw.githubusercontent.com" else policy, extended, no_resolve)
        for kind, value, policy, extended, no_resolve in records
    ]
    mutants = [
        no_push,
        [record("DOMAIN-SUFFIX,apple.com", "Apple"), *records],
        [record("DOMAIN-SUFFIX,akadns.net", "ApplePush"), *records],
        [record("DOMAIN-KEYWORD,apple.com.edgekey.net", "ApplePush"), *records],
        [record("IP-CIDR,17.0.0.0/8,no-resolve", "ApplePush"), *records],
        raw_manual,
    ]
    for index, candidate in enumerate(mutants):
        try:
            check_push_and_downloads(candidate)
        except AssertionError:
            continue
        raise AssertionError(f"push/download fixtures accepted regression {index}")
    return len(mutants)


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


def check_bilibili(records: list[tuple]) -> int:
    """Exercise app API/comment hosts, CDN omissions and international boundaries.

    Literal-address fixtures model a visible TLS SNI/HTTP Host only; they do not
    claim that Surge can recover a hostname from opaque IP/QUIC traffic.
    """
    domestic = (
        "api.bilibili.com", "app.bilibili.com", "grpc.biliapi.net",
        "api.biliapi.net", "comment.bilibili.com", "api.vc.bilibili.com",
        "passport.bilibili.com", "httpdns.bilivideo.com", "i0.hdslb.com",
        "upos-sz-mirrorcoso1.bilivideo.com", "video.bilivideo.cn",
        "video.bilivideo.net", "upos-hz-mirrorakam.akamaized.net",
        "uposdash-302-bilivideo.yfcdn.net", "video.bilicdn2.com",
        "video.bilicdn3.com", "video.bilicdn4.com", "video.bilicdn5.com",
        "img.hdslb.net", "img.hdslb.org", "i0.hdslb.com.w.kunlunhuf.com",
        "i0.hdslb.com.w.kunlunpi.com", "xy-test.v1d.szbdyd.com",
    )
    international = (
        "apiintl.biliapi.net", "p-bstarstatic.akamaized.net", "p.bstarstatic.com",
        "upos-bstar-mirrorakam.akamaized.net", "upos-bstar1-mirrorakam.akamaized.net",
        "www.bilibili.tv", "api.biliintl.com",
    )
    shared_or_lookalike = (
        "akamaized.net", "other.akamaized.net", "other.yfcdn.net",
        "other.kunlunhuf.com", "other.kunlunpi.com", "other.ksyungslb.com",
        "upos-hz-mirrorakam.akamaized.net.evil.example",
        "api.bilibili.com.evil.example", "notbilibili.com", "notszbdyd.com",
    )
    count = 0
    for hostname, expected in [(host, "DIRECT") for host in domestic] + [(host, "Proxy") for host in international]:
        for port in (80, 443):
            for address, sni in ((hostname, ""), ("203.0.113.8", hostname), ("2001:db8::8", hostname)):
                actual = domain_route(records, address, sni, port=port)
                assert actual == expected, ("Bilibili routing", hostname, address, port, actual, expected)
                count += 1
    for hostname in shared_or_lookalike:
        actual = domain_route(records, hostname, port=443)
        assert actual != "DIRECT", ("Bilibili overbroad CDN bypass", hostname)
        count += 1
    for port in (4480, 9305, 9400):
        assert domain_route(records, "xy-test.v1d.szbdyd.com", port=port) == "DIRECT", port
        count += 1
    for hostname in ("api.bilibili.com", "httpdns.bilivideo.com", "xy-test.v1d.szbdyd.com"):
        for port in (53, 853, 8853):
            assert domain_route(records, hostname, port=port) == "REJECT", (hostname, port)
            count += 1
    return count


def check_bilibili_regressions(records: list[tuple]) -> int:
    additions = {
        "upos-hz-mirrorakam.akamaized.net", "uposdash-302-bilivideo.yfcdn.net",
        "bilicdn2.com", "bilicdn3.com", "bilicdn4.com", "bilicdn5.com",
        "hdslb.com.w.kunlunhuf.com", "hdslb.com.w.kunlunpi.com",
        "hdslb.net", "hdslb.org", "szbdyd.com",
    }
    mutants = [[row for row in records if row[1] not in additions]]
    mutants.append([
        (kind, value, policy, False if value == "apiintl.biliapi.net" else extended, no_resolve)
        for kind, value, policy, extended, no_resolve in records
    ])
    # A shared CDN parent must never inherit the domestic service exception.
    mutants.append([("DOMAIN-SUFFIX", "akamaized.net", "DIRECT", True, False)] + records)
    for number, candidate in enumerate(mutants):
        try:
            check_bilibili(candidate)
        except AssertionError:
            continue
        raise AssertionError(f"Bilibili fixtures accepted routing regression {number}")
    return len(mutants)


def main() -> int:
    text = (ROOT / "Surge.conf").read_text()
    validate_remote_profile(text)
    actual = reference_records(text)
    assert len(actual) == 5676
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
        ("viu.now.com", "", "HongKong-Nodes"),
        ("api.nowe.com", "", "HongKong-Nodes"),
        ("now.com", "", "HongKong-Nodes"),
        ("now.com.hk", "", "HongKong-Nodes"),
        ("now-tv.com", "", "HongKong-Nodes"),
        ("now-ashare.com", "", "HongKong-Nodes"),
        ("nowe.hk", "", "HongKong-Nodes"),
        ("mytvsuper.com", "", "HongKong-Nodes"),
        ("api.viu.tv", "", "HongKong-Nodes"),
        ("api.tver.jp", "", "Japan-Nodes"),
        ("hulu.com", "", "America-Nodes"),
        ("vod.hulustream.com", "", "America-Nodes"),
        ("hulu.tv", "", "America-Nodes"),
        ("hulu.us", "", "America-Nodes"),
        ("huluim.com", "", "America-Nodes"),
        ("max.com", "", "HBO"),
        ("hbomax.com", "", "HBO"),
        ("ani.gamer.com.tw", "", "Bahamut"),
        ("hulu.com.not-hulu.example", "", "Final"),
        ("tver.jp.not-tver.example", "", "Final"),
        ("now.com.not-now.example", "", "Final"),
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
        ("raw.githubusercontent.com", "", "Auto"),
    ]
    for hostname, sni, policy in cases:
        assert domain_route(actual, hostname, sni) == policy, (hostname, sni, policy)
    for domain, wrong in (("hulu.com", "HongKong-Nodes"), ("tver.jp", "America-Nodes"), ("now.com", "HBO")):
        mutant = [(kind, value, wrong if kind == "DOMAIN-SUFFIX" and value == domain else policy, extended, no_resolve)
                  for kind, value, policy, extended, no_resolve in actual]
        try:
            for hostname, sni, policy in cases:
                assert domain_route(mutant, hostname, sni) == policy
        except AssertionError:
            pass
        else:
            raise AssertionError(f"media cases accepted an incorrect country for {domain}")
    normal_count, ad_count, dns_count = check_behavior(actual)
    behavior_mutations = check_behavior_regressions(text, actual)
    push_hosts, push_ips, push_sni = check_push_and_downloads(actual)
    push_mutations = check_push_regressions(actual)
    bili_cases = check_bilibili(actual)
    bili_mutations = check_bilibili_regressions(actual)

    rules = active_rule_lines(text)
    remote = [row for row in rules if row.startswith(("RULE-SET,", "DOMAIN-SET,"))]
    assert len(remote) == 29
    reject_bad_profile(text.replace(remote[0] + "\n", "", 1))
    reject_bad_profile(text.replace(remote[0], remote[0].replace(",Security,", ",Proxy,"), 1))
    reject_bad_profile(text.replace(remote[0], remote[0].replace(",extended-matching", ""), 1))
    reject_bad_profile(text.replace(remote[0], remote[0].replace(RELEASE_REF, "main"), 1))
    reject_bad_profile(text.replace("[Rule]\n", "[Rule]\nDOMAIN,123tramites.com,Security\n", 1))
    reject_bad_profile(text.replace(remote[1], remote[1].replace(",no-resolve", ""), 1))
    print(
        f"PASS external rules={len(remote)} semantic_rules={len(actual)} "
        f"routing_cases={len(cases)} normal_sites={normal_count} advertising={ad_count} "
        f"dns_port_cases={dns_count} corruption_cases=6 "
        f"behavior_mutations={behavior_mutations} push_download_hosts={push_hosts} "
        f"push_telegram_ip_cases={push_ips} push_sni_cases={push_sni} "
        f"push_download_mutations={push_mutations} media_mutations=3 "
        f"bilibili_cases={bili_cases} bilibili_mutations={bili_mutations}; offline model only"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
