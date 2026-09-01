#!/usr/bin/env python3
"""Validate the R13.13 external runtime-rule inventory.

The iOS profile loads 29 repository snapshots from one immutable commit and
one reviewed dynamic domestic supplement.  Large mutable reject lists are not
part of the mobile runtime.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "Surge.conf"
PROFILE_NAME = "Surge iOS Privacy + Push R13.13 Simple Subscription"
RELEASE_DATE = "2026-09-01"
RULE_SNAPSHOT_TAG = "r12.17-20260825"
RELEASE_REF = "2b8fa93901061cf0482b079203630bcd11bfe0b1"
REMOTE_BASE = f"https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@{RELEASE_REF}/Rules/"
UPDATE_OPTION = "update-interval=-1"
DYNAMIC_UPDATE_OPTION = "update-interval=86400"

DOMESTIC_DNS_RULES: tuple[str, ...] = (
    "DOMAIN,dns.alidns.com,DIRECT",
    "DOMAIN,dns.pub,DIRECT",
    "DOMAIN,doh.pub,DIRECT",
    "DOMAIN,dot.pub,DIRECT",
    "DOMAIN,dns.360.cn,DIRECT",
    "DOMAIN,doh.360.cn,DIRECT",
    "DOMAIN-SUFFIX,alibabadns.com,DIRECT",
    "DOMAIN-SUFFIX,alidns.com,DIRECT",
    "DOMAIN-SUFFIX,bdydns.com,DIRECT",
    "DOMAIN-SUFFIX,bytednsdoc.com,DIRECT",
    "DOMAIN-SUFFIX,dns.la,DIRECT",
    "DOMAIN-SUFFIX,dnspod.cn,DIRECT",
    "DOMAIN-SUFFIX,dnspod.com,DIRECT",
    "DOMAIN-SUFFIX,dnsv1.com,DIRECT",
    "DOMAIN-SUFFIX,jomodns.com,DIRECT",
    "DOMAIN-SUFFIX,smtcdns.net,DIRECT",
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

DOMESTIC_GEOIP_RULE = "GEOIP,CN,DIRECT,no-resolve"

FUNCTIONAL_GUARDS: tuple[str, ...] = (
    "DOMAIN,httpdns.bilivideo.com,DIRECT",
    "DOMAIN,line3-h5-mobile-api.biligame.com,DIRECT",
    "DOMAIN,audio-ak.cdn.spotify.com,Spotify",
    "DOMAIN,video-ak.cdn.spotify.com,Spotify",
    "DOMAIN,audio-ak-spotify-com.akamaized.net,Spotify",
    "DOMAIN-SUFFIX,pod.spoti.fi,Spotify",
    "DOMAIN-SUFFIX,tv-static.scdn.co,Spotify",
    "DOMAIN-SUFFIX,gvt2.com,Google",
    "DOMAIN,rum.browser-intake-datadoghq.com,ChatGPT",
)

RETIRED_BILIBILI_INTL_GUARDS: tuple[str, ...] = (
    "DOMAIN,apiintl.biliapi.net,Proxy",
    "DOMAIN,p-bstarstatic.akamaized.net,Proxy",
    "DOMAIN,p.bstarstatic.com,Proxy",
    "DOMAIN,upos-bstar-mirrorakam.akamaized.net,Proxy",
    "DOMAIN,upos-bstar1-mirrorakam.akamaized.net,Proxy",
    "DOMAIN-SUFFIX,bilibili.tv,Proxy",
    "DOMAIN-SUFFIX,biliintl.com,Proxy",
)

REPOSITORY_RULES: tuple[tuple[str, str, str, str], ...] = (
    ("DOMAIN-SET", "Pegasus.list", "Pegasus spyware IOC", "REJECT"),
    ("RULE-SET", "APNs.list", "APNs", "ApplePush"),
    ("RULE-SET", "AppleCN.list", "AppleCN · Apple", "Apple"),
    ("RULE-SET", "WeChat.list", "WeChat · DIRECT", "DIRECT"),
    ("RULE-SET", "Direct.list", "Direct · DIRECT", "DIRECT"),
    ("RULE-SET", "Ads.list", "Ads · REJECT", "REJECT"),
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
    ("RULE-SET", "BiliBili.list", "BiliBili domestic API and video CDN", "DIRECT"),
    ("RULE-SET", "Spotify.list", "Spotify", "Spotify"),
    ("RULE-SET", "ProxyMedia.list", "ProxyMedia · Streaming", "Streaming"),
    ("RULE-SET", "Telegram.list", "Telegram", "Telegram"),
    ("RULE-SET", "Github.list", "GitHub", "GitHub"),
    ("RULE-SET", "Twitter.list", "X", "X"),
    ("RULE-SET", "Google.list", "Google", "Google"),
    ("RULE-SET", "Game.list", "Game", "Games"),
    ("RULE-SET", "OneDrive.list", "OneDrive", "Microsoft"),
    ("RULE-SET", "Microsoft.list", "Microsoft", "Microsoft"),
    ("DOMAIN-SET", "China.list", "China domains · precise", "DIRECT"),
    ("DOMAIN-SET", "Global.list", "Global domains · precise", "Proxy"),
)

EXTENDED_MATCH_RESOURCES = frozenset(
    filename for _kind, filename, _label, _policy in REPOSITORY_RULES
    if filename != "Ads.list"
)

DYNAMIC_RULES: tuple[dict[str, object], ...] = (
    {
        "name": "domestic.conf",
        "kind": "RULE-SET",
        "url": "https://ruleset.skk.moe/List/non_ip/domestic.conf",
        "policy": "DIRECT",
        "extended_matching": True,
        "active_entries": 869,
        "size_bytes": 22632,
        "last_updated": "2026-08-08T06:31:42.029Z",
        "content_hash_v1": "T_za7NN7pWO6RMdaJduvv6ssx377hsJAKf_gBeOSZrA",
        "sha256": "56809cd8399666433acb1229c3a472667a32c86fc2a0b9861a5dca54020564aa",
    },
)


def repository_line(kind: str, filename: str, policy: str) -> str:
    options: list[str] = []
    if filename in EXTENDED_MATCH_RESOURCES:
        options.append("extended-matching")
    if kind == "RULE-SET":
        options.append("no-resolve")
    options.append(UPDATE_OPTION)
    return f"{kind},{REMOTE_BASE}{filename},{policy},{','.join(options)}"


def dynamic_line(item: dict[str, object]) -> str:
    options: list[str] = []
    if item.get("extended_matching"):
        options.append("extended-matching")
    if item["kind"] == "RULE-SET":
        options.append("no-resolve")
    options.append(DYNAMIC_UPDATE_OPTION)
    return f"{item['kind']},{item['url']},{item['policy']},{','.join(options)}"


def expected_remote_order() -> list[str]:
    domestic = dynamic_line(DYNAMIC_RULES[0])
    ordered: list[str] = []
    for kind, filename, _label, policy in REPOSITORY_RULES:
        if filename == "China.list":
            ordered.append(domestic)
        ordered.append(repository_line(kind, filename, policy))
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
        raise SystemExit("runtime rule inventory or order differs from the reviewed R13.13 inventory")

    repository_urls = {
        f"{REMOTE_BASE}{filename}" for _kind, filename, _label, _policy in REPOSITORY_RULES
    }
    dynamic_urls = {str(item["url"]) for item in DYNAMIC_RULES}
    for line in external:
        fields = [field.strip() for field in line.split(",")]
        url = fields[1]
        if url not in repository_urls | dynamic_urls:
            raise SystemExit(f"unreviewed runtime resource URL: {url}")
        if fields[-1] not in {UPDATE_OPTION, DYNAMIC_UPDATE_OPTION}:
            raise SystemExit(f"runtime resource update interval changed: {line}")
        if fields[0] == "RULE-SET" and "no-resolve" not in fields[3:]:
            raise SystemExit(f"runtime RULE-SET may not trigger local DNS: {line}")

    forbidden = ("reject_phishing.conf", "/domainset/reject.conf", "@main/Rules/", "raw.githubusercontent.com")
    if any(marker in text for marker in forbidden):
        raise SystemExit("profile contains a mutable, mobile-heavy or unreviewed runtime source")
    print(
        "PASS: immutable_runtime_resources=29 dynamic_runtime_resources=1 "
        "embedded_rule_contents=0 reviewed_third_party_runtime_urls=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
