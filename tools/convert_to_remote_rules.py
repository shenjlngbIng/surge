#!/usr/bin/env python3
"""Validate the R13.25 external rule inventory without embedding rule lists."""

from __future__ import annotations

from pathlib import Path



ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "Surge.conf"
PROFILE_NAME = "Surge iOS Privacy + Push R13.25 Service Regions + Latency + Sentinel"
RELEASE_DATE = "2026-09-09"
RULE_SNAPSHOT_TAG = None  # This snapshot is pinned by commit, not a legacy tag.
RELEASE_REF = "4057ea435ece7617cabec5b7ac5a49c1d93937de"
REMOTE_BASE = f"https://raw.githubusercontent.com/shenjlngbIng/surge/{RELEASE_REF}/Rules/"
UPDATE_OPTION = "update-interval=-1"
DYNAMIC_UPDATE_OPTION = "update-interval=86400"


# Reviewed service candidates within the five supported name classifiers.
# None means the service has no common country whitelist in this profile.
REGIONS = ("HongKong", "TaiWan", "Japan", "Singapore", "America")
AI_REGIONS = ("America", "Japan", "Singapore", "TaiWan")
SERVICE_REGIONS = {
    "ChatGPT": AI_REGIONS, "Claude": AI_REGIONS, "Gemini": AI_REGIONS,
    "GitHub": None, "YouTube": None,
    "NETFLIX": REGIONS, "Disney+": REGIONS,
    "HBO": ("America", "Singapore", "HongKong", "TaiWan"),
    "PrimeVideo": REGIONS, "Emby": None,
    "TikTok": AI_REGIONS, "Bahamut": ("TaiWan",), "Spotify": REGIONS,
    "Streaming": None, "Telegram": None, "X": None,
    "Google": None, "Microsoft": None, "Games": None,
}
SERVICE_SOURCE_GROUPS = {
    name: [region + "-Nodes" for region in regions] if regions is not None else ["桔子"]
    for name, regions in SERVICE_REGIONS.items()
}
AUTO_TEST_OPTIONS = (
    "policy-regex-filter=^(?!REJECT$).+", "interval=300", "tolerance=0",
    "evaluate-before-use=true", "no-alert=true",
)
MEDIA_REGION_RULES = (
    "DOMAIN-SUFFIX,hulu.com,America-Nodes", "DOMAIN-SUFFIX,hulu.tv,America-Nodes",
    "DOMAIN-SUFFIX,hulu.us,America-Nodes", "DOMAIN-SUFFIX,huluim.com,America-Nodes",
    "DOMAIN-SUFFIX,hulustream.com,America-Nodes", "DOMAIN-SUFFIX,tver.jp,Japan-Nodes",
    "USER-AGENT,TVer-Release*,Japan-Nodes", "DOMAIN-SUFFIX,mytvsuper.com,HongKong-Nodes",
    "DOMAIN-SUFFIX,viu.tv,HongKong-Nodes", "DOMAIN-SUFFIX,viu.now.com,HongKong-Nodes",
    "DOMAIN-SUFFIX,now-ashare.com,HongKong-Nodes", "DOMAIN-SUFFIX,now-tv.com,HongKong-Nodes",
    "DOMAIN-SUFFIX,now.com,HongKong-Nodes", "DOMAIN-SUFFIX,now.com.hk,HongKong-Nodes",
    "DOMAIN-SUFFIX,nowe.com,HongKong-Nodes", "DOMAIN-SUFFIX,nowe.hk,HongKong-Nodes",
)

DOMESTIC_DNS_RULES: tuple[str, ...] = (
    "DOMAIN,dns.pub,Proxy",
    "DOMAIN,doh.pub,Proxy",
    "DOMAIN,dot.pub,Proxy",
    "DOMAIN,dns.360.cn,Proxy",
    "DOMAIN,doh.360.cn,Proxy",
    "DOMAIN-SUFFIX,alibabadns.com,Proxy",
    "DOMAIN-SUFFIX,alidns.com,Proxy",
    "DOMAIN-SUFFIX,bdydns.com,Proxy",
    "DOMAIN-SUFFIX,bytednsdoc.com,Proxy",
    "DOMAIN-SUFFIX,dns.la,Proxy",
    "DOMAIN-SUFFIX,dnspod.cn,Proxy",
    "DOMAIN-SUFFIX,dnspod.com,Proxy",
    "DOMAIN-SUFFIX,dnsv1.com,Proxy",
    "DOMAIN-SUFFIX,jomodns.com,Proxy",
    "DOMAIN-SUFFIX,smtcdns.net,Proxy",
)

# Own encrypted DNS deliberately bypasses outbound rules to avoid a proxy-DNS loop.
SURGE_DNS_PROTOCOL_RULES: tuple[str, ...] = ()

FOREIGN_DNS_RULES: tuple[str, ...] = (
    "DOMAIN,dns.google,Proxy",
    "DOMAIN,one.one.one.one,Proxy",
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
    "DOMAIN,apiintl.biliapi.net,Proxy,extended-matching",
    "DOMAIN,p-bstarstatic.akamaized.net,Proxy,extended-matching",
    "DOMAIN,p.bstarstatic.com,Proxy,extended-matching",
    "DOMAIN,upos-bstar-mirrorakam.akamaized.net,Proxy,extended-matching",
    "DOMAIN,upos-bstar1-mirrorakam.akamaized.net,Proxy,extended-matching",
    "DOMAIN-SUFFIX,bilibili.tv,Proxy,extended-matching",
    "DOMAIN-SUFFIX,biliintl.com,Proxy,extended-matching",
)

REPOSITORY_RULES: tuple[tuple[str, str, str, str], ...] = (
    ("DOMAIN-SET", "Pegasus.list", "Pegasus spyware IOC", "Security"),
    ("RULE-SET", "APNs.list", "APNs", "ApplePush"),
    ("RULE-SET", "AppleCN.list", "AppleCN · Apple", "Apple"),
    ("RULE-SET", "WeChat.list", "WeChat · DIRECT", "DIRECT"),
    ("RULE-SET", "Direct.list", "Direct · DIRECT", "DIRECT"),
    ("RULE-SET", "BiliBili.list", "BiliBili domestic API and video CDN", "DIRECT"),
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

EXTENDED_MATCH_RESOURCES = frozenset(
    filename for _kind, filename, _label, _policy in REPOSITORY_RULES
    if filename != "Ads.list"
)

DYNAMIC_RULES: tuple[dict[str, object], ...] = ()


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
    return [
        repository_line(kind, filename, policy)
        for kind, filename, _label, policy in REPOSITORY_RULES
    ]


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


def validate_remote_profile(text: str, root: Path = ROOT) -> str:
    rules = active_rule_lines(text)
    references = [line for line in rules if line.startswith(("RULE-SET,", "DOMAIN-SET,"))]
    if references != expected_remote_order():
        raise ValueError("external rule URLs, order, policies or options differ from the reviewed inventory")
    if "EMBEDDED-RULES" in text or len(rules) != 157:
        raise ValueError("profile must contain 157 routing rules with 29 external references and no embedded lists")
    return text


def main() -> int:
    text = PROFILE.read_text(encoding="utf-8")
    rules = active_rule_lines(validate_remote_profile(text))
    external = [line for line in rules if line.startswith(("RULE-SET,", "DOMAIN-SET,"))]
    if external != expected_remote_order():
        raise SystemExit("runtime rule inventory or order differs from the reviewed R13.25 inventory")

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

    forbidden = ("reject_phishing.conf", "/domainset/reject.conf", "/surge/main/Rules/", "cdn.jsdelivr.net/gh/")
    if any(marker in text for marker in forbidden):
        raise SystemExit("profile contains a mutable, mobile-heavy or unreviewed runtime source")
    print(
        "PASS: remote_runtime_rules=29 embedded_rule_contents=0 rules=157"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
