#!/usr/bin/env python3
"""Validate the R12.17 repository-hosted runtime rule inventory.

Every static RULE-SET and DOMAIN-SET used by Surge must resolve to the user's
own immutable repository commit. Third-party URLs are maintenance inputs only
and are recorded in lock files; they may not appear in the runtime profile.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "Surge.conf"
PROFILE_NAME = "Surge iOS Privacy + Push R12.17"
RELEASE_DATE = "2026-08-26"
RULE_SNAPSHOT_TAG = "r12.17-20260825"
RELEASE_REF = "d1d714d575d5494ef1a7613238f4f301e1b293df"
REMOTE_BASE = f"https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@{RELEASE_REF}/Rules/"
UPDATE_OPTION = "update-interval=-1"

# Exact runtime order. The profile can contain reviewed inline overrides between
# these entries, but repository resources must retain this relative order.
REPOSITORY_RULES: tuple[tuple[str, str, str, str], ...] = (
    ("DOMAIN-SET", "Pegasus.list", "Pegasus spyware IOC", "Security"),
    ("RULE-SET", "APNs.list", "APNs", "ApplePush"),
    ("RULE-SET", "AppleCN.list", "AppleCN · Apple", "Apple"),
    ("RULE-SET", "WeChat.list", "WeChat · Domestic", "DIRECT"),
    ("RULE-SET", "Direct.list", "Direct · Domestic", "DIRECT"),
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


def repository_line(kind: str, filename: str, policy: str) -> str:
    options = f"no-resolve,{UPDATE_OPTION}" if kind == "RULE-SET" else UPDATE_OPTION
    return f"{kind},{REMOTE_BASE}{filename},{policy},{options}"


def expected_remote_lines() -> set[str]:
    return {
        repository_line(kind, filename, policy)
        for kind, filename, _label, policy in REPOSITORY_RULES
    }


def expected_remote_order() -> list[str]:
    return [
        repository_line(kind, filename, policy)
        for kind, filename, _label, policy in REPOSITORY_RULES
    ]


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
    if "# Embedded rules" in text or "embedded_sources" in text:
        raise SystemExit("embedded rule content is forbidden")
    rules = active_rule_lines(text)
    external = [line for line in rules if line.startswith(("RULE-SET,", "DOMAIN-SET,"))]
    expected = expected_remote_lines()
    if set(external) != expected or len(external) != len(expected):
        missing = sorted(expected - set(external))
        unexpected = sorted(set(external) - expected)
        raise SystemExit(
            f"repository rule inventory mismatch: missing={missing}, unexpected={unexpected}"
        )
    positions = [rules.index(line) for line in expected_remote_order()]
    if positions != sorted(positions):
        raise SystemExit("repository rule relative order does not match the reviewed inventory")
    for line in external:
        fields = [field.strip() for field in line.split(",")]
        expected_fields = 5 if fields[0] == "RULE-SET" else 4
        if len(fields) != expected_fields or fields[-1] != UPDATE_OPTION:
            raise SystemExit(f"repository rule must disable polling of immutable content: {line}")
        if fields[0] == "RULE-SET" and fields[3] != "no-resolve":
            raise SystemExit(f"repository RULE-SET may not trigger local DNS: {line}")
        if not fields[1].startswith(REMOTE_BASE) or ".." in fields[1]:
            raise SystemExit(f"runtime rule is not hosted by the reviewed repository commit: {line}")
    print(
        f"PASS: repository-only runtime resources={len(external)} "
        "third_party_runtime_urls=0 embedded_rule_contents=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
