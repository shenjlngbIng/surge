#!/usr/bin/env python3
"""Validate the R13.4 external runtime-rule inventory.

The profile keeps the 30 reviewed repository snapshots pinned to one immutable
commit and adds exactly three reviewed, auto-updating Sukka runtime supplements.
No rule snapshot may be embedded in the public profile.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "Surge.conf"
PROFILE_NAME = "Surge iOS Privacy + Push R13.4 Strict DNS"
RELEASE_DATE = "2026-08-28"
RULE_SNAPSHOT_TAG = "r12.17-20260825"
RELEASE_REF = "d1d714d575d5494ef1a7613238f4f301e1b293df"
REMOTE_BASE = f"https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@{RELEASE_REF}/Rules/"
UPDATE_OPTION = "update-interval=-1"
DYNAMIC_UPDATE_OPTION = "update-interval=86400"

DOMESTIC_DNS_RULES: tuple[str, ...] = (
    "DOMAIN,dns.alidns.com,Domestic",
    "DOMAIN,dns.pub,Domestic",
    "DOMAIN,doh.pub,Domestic",
    "DOMAIN,dot.pub,Domestic",
    "DOMAIN,dns.360.cn,Domestic",
    "DOMAIN,doh.360.cn,Domestic",
    "DOMAIN-SUFFIX,alibabadns.com,Domestic",
    "DOMAIN-SUFFIX,alidns.com,Domestic",
    "DOMAIN-SUFFIX,bdydns.com,Domestic",
    "DOMAIN-SUFFIX,bytednsdoc.com,Domestic",
    "DOMAIN-SUFFIX,dns.la,Domestic",
    "DOMAIN-SUFFIX,dnspod.cn,Domestic",
    "DOMAIN-SUFFIX,dnspod.com,Domestic",
    "DOMAIN-SUFFIX,dnsv1.com,Domestic",
    "DOMAIN-SUFFIX,jomodns.com,Domestic",
    "DOMAIN-SUFFIX,smtcdns.net,Domestic",
)

FOREIGN_DNS_RULES: tuple[str, ...] = (
    "DOMAIN,dns.google,Proxy",
    "DOMAIN,one.one.one.one,Proxy",
    "DOMAIN,dns.nextdns.io,Proxy",
    "DOMAIN,dns.adguard.com,Proxy",
    "DOMAIN,doh.opendns.com,Proxy",
    "DOMAIN,doh.cleanbrowsing.org,Proxy",
    "DOMAIN,doh.dns.sb,Proxy",
    "DOMAIN,doh.tiar.app,Proxy",
    "DOMAIN,dot.tiar.app,Proxy",
    "DOMAIN,dns.twnic.tw,Proxy",
    "DOMAIN-SUFFIX,cloudflare-dns.com,Proxy",
    "DOMAIN-SUFFIX,quad9.net,Proxy",
    "DOMAIN-SUFFIX,nextdns.io,Proxy",
)

DOMESTIC_GEOIP_RULE = "GEOIP,CN,Domestic,no-resolve"

# The original 30 reviewed runtime snapshots. Policies changed to Domestic are
# routing changes only; filenames, immutable URLs and local bytes are preserved.
REPOSITORY_RULES: tuple[tuple[str, str, str, str], ...] = (
    ("DOMAIN-SET", "Pegasus.list", "Pegasus spyware IOC", "Security"),
    ("RULE-SET", "APNs.list", "APNs", "ApplePush"),
    ("RULE-SET", "AppleCN.list", "AppleCN · Apple", "Apple"),
    ("RULE-SET", "WeChat.list", "WeChat · Domestic", "Domestic"),
    ("RULE-SET", "Direct.list", "Direct · Domestic", "Domestic"),
    ("RULE-SET", "Ads.list", "Ads · AdBlock", "AdBlock"),
    ("RULE-SET", "ChatGPT.list", "ChatGPT", "ChatGPT"),
    ("RULE-SET", "Claude.list", "Claude", "Claude"),
    ("RULE-SET", "Gemini.list", "Gemini", "Gemini"),
    ("RULE-SET", "YouTube.list", "YouTube", "YouTube"),
    ("RULE-SET", "Netflix.list", "Netflix", "NETFLIX"),
    ("RULE-SET", "Disney.list", "Disney+", "Disney+"),
    ("RULE-SET", "HBO.list", "HBO", "HBO"),
    ("RULE-SET", "PrimeVideo.list", "PrimeVideo", "PrimeVideo"),
    ("RULE-SET", "Emby.list", "Emby", "Emby"),
    ("RULE-SET", "TikTok.list", "TikTok", "TikTok"),
    ("RULE-SET", "Bahamut.list", "Bahamut", "Bahamut"),
    ("RULE-SET", "BiliBiliIntl.list", "BiliBili international edition", "Streaming"),
    ("RULE-SET", "BiliBili.list", "BiliBili domestic API and video CDN", "Domestic"),
    ("RULE-SET", "Spotify.list", "Spotify", "Spotify"),
    ("RULE-SET", "ProxyMedia.list", "ProxyMedia · Streaming", "Streaming"),
    ("RULE-SET", "Telegram.list", "Telegram", "Telegram"),
    ("RULE-SET", "Github.list", "GitHub", "GitHub"),
    ("RULE-SET", "Twitter.list", "X", "X"),
    ("RULE-SET", "Google.list", "Google", "Google"),
    ("RULE-SET", "Game.list", "Game", "Games"),
    ("RULE-SET", "OneDrive.list", "OneDrive", "Microsoft"),
    ("RULE-SET", "Microsoft.list", "Microsoft", "Microsoft"),
    ("DOMAIN-SET", "China.list", "China domains · precise", "Domestic"),
    ("DOMAIN-SET", "Global.list", "Global domains · precise", "Proxy"),
)

# Exact reviewed third-party runtime supplements and release-time observations.
# These files are intentionally not bundled because they are dynamic sources.
DYNAMIC_RULES: tuple[dict[str, object], ...] = (
    {
        "name": "reject_phishing.conf",
        "kind": "DOMAIN-SET",
        "url": "https://ruleset.skk.moe/List/domainset/reject_phishing.conf",
        "policy": "Security",
        "active_entries": 147474,
        "size_bytes": 3146841,
        "last_updated": "2026-08-28T05:59:58.088Z",
        "content_hash_v1": "ZZWjEn5pEka4NbiG9zg0OkMmib0aU6vxkPj1mS7BkE4",
        "sha256": "7c7b64d378542824170c87cf63511bc67974db39c6894493153f9d003a89756e",
    },
    {
        "name": "reject.conf",
        "kind": "DOMAIN-SET",
        "url": "https://ruleset.skk.moe/List/domainset/reject.conf",
        "policy": "AdBlock",
        "active_entries": 135224,
        "size_bytes": 3013194,
        "last_updated": "2026-08-28T05:59:58.088Z",
        "content_hash_v1": "sYj8bnVsQRgGiRCGGukfGJm3KSLJL0-r7zFAuhD692g",
        "sha256": "4b87642adc8c58c0336b58a570abf33342b81043f358691fed16e207be028b49",
    },
    {
        "name": "domestic.conf",
        "kind": "RULE-SET",
        "url": "https://ruleset.skk.moe/List/non_ip/domestic.conf",
        "policy": "Domestic",
        "active_entries": 869,
        "size_bytes": 22632,
        "last_updated": "2026-08-08T06:31:42.029Z",
        "content_hash_v1": "T_za7NN7pWO6RMdaJduvv6ssx377hsJAKf_gBeOSZrA",
        "sha256": "56809cd8399666433acb1229c3a472667a32c86fc2a0b9861a5dca54020564aa",
    },
)


def repository_line(kind: str, filename: str, policy: str) -> str:
    options = f"no-resolve,{UPDATE_OPTION}" if kind == "RULE-SET" else UPDATE_OPTION
    return f"{kind},{REMOTE_BASE}{filename},{policy},{options}"


def dynamic_line(item: dict[str, object]) -> str:
    middle = ",no-resolve" if item["kind"] == "RULE-SET" else ""
    return f"{item['kind']},{item['url']},{item['policy']}{middle},{DYNAMIC_UPDATE_OPTION}"


def expected_remote_order() -> list[str]:
    phishing, advertising, domestic = (dynamic_line(item) for item in DYNAMIC_RULES)
    ordered = [phishing]
    for kind, filename, _label, policy in REPOSITORY_RULES:
        if filename == "China.list":
            ordered.append(domestic)
        ordered.append(repository_line(kind, filename, policy))
        if filename == "Ads.list":
            ordered.append(advertising)
    return ordered


def expected_remote_lines() -> set[str]:
    return set(expected_remote_order())


def active_rule_lines(text: str) -> list[str]:
    if "[Rule]" not in text:
        raise SystemExit("[Rule] section not found")
    return [
        line.strip()
        for line in text.split("[Rule]", 1)[1].splitlines()
        if line.strip() and not line.lstrip().startswith(("#", ";", "//"))
    ]


def main() -> int:
    text = PROFILE.read_text(encoding="utf-8")
    rules = active_rule_lines(text)
    external = [line for line in rules if line.startswith(("RULE-SET,", "DOMAIN-SET,"))]
    if external != expected_remote_order():
        raise SystemExit("runtime rule inventory or relative order differs from the reviewed R13.4 inventory")

    repository_urls = {f"{REMOTE_BASE}{filename}" for _kind, filename, _label, _policy in REPOSITORY_RULES}
    dynamic_urls = {str(item["url"]) for item in DYNAMIC_RULES}
    for line in external:
        fields = [field.strip() for field in line.split(",")]
        url = fields[1]
        expected_fields = 5 if fields[0] == "RULE-SET" else 4
        if len(fields) != expected_fields:
            raise SystemExit(f"runtime resource field count changed: {line}")
        if fields[0] == "RULE-SET" and fields[3] != "no-resolve":
            raise SystemExit(f"runtime RULE-SET may not trigger local DNS: {line}")
        if url in repository_urls and fields[-1] != UPDATE_OPTION:
            raise SystemExit(f"immutable repository resource options changed: {line}")
        if url in dynamic_urls and fields[-1] != DYNAMIC_UPDATE_OPTION:
            raise SystemExit(f"dynamic resource options changed: {line}")
        if url not in repository_urls | dynamic_urls:
            raise SystemExit(f"unreviewed runtime resource URL: {url}")

    embedded = [
        line for line in rules
        if line.endswith((",Security", ",AdBlock"))
        and not line.startswith(("RULE-SET,", "DOMAIN-SET,"))
    ]
    if embedded:
        raise SystemExit(f"embedded Security/AdBlock rules are forbidden: {embedded[:3]}")
    print(
        "PASS: immutable_runtime_resources=30 dynamic_runtime_resources=3 "
        "embedded_rule_contents=0 reviewed_third_party_runtime_urls=3"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
