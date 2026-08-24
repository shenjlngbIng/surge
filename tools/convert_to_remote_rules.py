#!/usr/bin/env python3
"""Validate the R12.15 profile's curated and upstream-hosted rule sources.

The repository remains the source of truth for curated rule snapshots. The
Surge profile loads those snapshots through jsDelivr. Broad upstream domain
collections are deliberately replaced with two bounded, repository-maintained
DOMAIN-SET files. No broad upstream routing collection is loaded at runtime.

This maintenance command deliberately never writes rule contents into
``Surge.conf``.  The historical filename is retained so existing maintenance
commands continue to work.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "Surge.conf"
REMOTE_BASE = "https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@main/Rules/"

# Keep this order aligned with the remote profile. Earlier rules
# intentionally win over broader domestic/geoip fallbacks later in the file.
REMOTE_RULES: tuple[tuple[str, str, str], ...] = (
    ("AppleCN.list", "AppleCN · Apple", "Apple"),
    ("WeChat.list", "WeChat · Domestic", "DIRECT"),
    ("Direct.list", "Direct · Domestic", "DIRECT"),
    ("Ads.list", "Ads · AdBlock", "AdBlock"),
    ("ChatGPT.list", "ChatGPT", "ChatGPT"),
    ("Claude.list", "Claude", "Claude"),
    ("Gemini.list", "Gemini", "Gemini"),
    ("YouTube.list", "YouTube", "YouTube"),
    ("Netflix.list", "Netflix", "NETFLIX"),
    ("Disney.list", "Disney+", "Disney+"),
    ("HBO.list", "HBO", "HBO"),
    ("PrimeVideo.list", "PrimeVideo", "PrimeVideo"),
    ("Emby.list", "Emby", "Emby"),
    ("TikTok.list", "TikTok", "TikTok"),
    ("Bahamut.list", "Bahamut", "Bahamut"),
    ("BiliBiliIntl.list", "BiliBiliIntl · Streaming", "Streaming"),
    ("Spotify.list", "Spotify", "Spotify"),
    ("ProxyMedia.list", "ProxyMedia · Streaming", "Streaming"),
    ("Telegram.list", "Telegram", "Telegram"),
    ("Github.list", "Github", "GitHub"),
    ("Twitter.list", "Twitter", "X"),
    ("Google.list", "Google", "Google"),
    ("OneDrive.list", "OneDrive", "Microsoft"),
    ("Microsoft.list", "Microsoft", "Microsoft"),
    ("Game.list", "Game", "Games"),
    ("APNs.list", "APNs", "ApplePush"),
)

PRECISE_DOMAIN_RULES: tuple[tuple[str, str, str], ...] = (
    ("China.list", "China domains · precise", "DIRECT"),
    ("Global.list", "Global domains · precise", "Proxy"),
)

REPOSITORY_RULES: tuple[tuple[str, str, str, str], ...] = tuple(
    ("RULE-SET", filename, label, policy)
    for filename, label, policy in REMOTE_RULES
) + tuple(
    ("DOMAIN-SET", filename, label, policy)
    for filename, label, policy in PRECISE_DOMAIN_RULES
)


def remote_line(filename: str, policy: str) -> str:
    return f"RULE-SET,{REMOTE_BASE}{filename},{policy}"


def repository_line(kind: str, filename: str, policy: str) -> str:
    return f"{kind},{REMOTE_BASE}{filename},{policy}"


def render_remote_block() -> str:
    lines = [
        "# Repository-hosted remote rule sets",
        "# The CDN URLs point to the curated files in this repository.",
        "# Aegis-style modular security feeds are intentionally not enabled here",
        "# until their threat-intelligence sources are independently reviewed.",
        "",
        "# Apple / domestic precedence",
    ]
    filename, label, policy = REMOTE_RULES[25]
    lines[5:5] = ["# APNs", f"# {label}", remote_line(filename, policy), ""]
    for filename, label, policy in REMOTE_RULES[:3]:
        lines.append(f"# {label}")
        lines.append(remote_line(filename, policy))

    lines.extend(("", "# Advertising", f"# {REMOTE_RULES[3][1]}", remote_line(*REMOTE_RULES[3][::2])))

    lines.extend(("", "# Artificial intelligence"))
    for filename, label, policy in REMOTE_RULES[4:7]:
        lines.extend((f"# {label}", remote_line(filename, policy)))

    lines.extend(("", "# Streaming"))
    for filename, label, policy in REMOTE_RULES[7:18]:
        lines.extend((f"# {label}", remote_line(filename, policy)))

    lines.extend(("", "# International services"))
    for filename, label, policy in REMOTE_RULES[18:25]:
        lines.extend((f"# {label}", remote_line(filename, policy)))

    lines.extend(("", "# Bounded repository-maintained domain fallbacks"))
    for filename, label, policy in PRECISE_DOMAIN_RULES:
        lines.extend((f"# {label}", repository_line("DOMAIN-SET", filename, policy)))

    return "\n".join(lines)


def expected_remote_lines() -> set[str]:
    lines = {
        repository_line(kind, filename, policy)
        for kind, filename, _label, policy in REPOSITORY_RULES
    }
    return lines


def active_rule_lines(text: str) -> list[str]:
    if "[Rule]" not in text:
        raise SystemExit("[Rule] section not found")
    return [
        line.strip()
        for line in text.split("[Rule]", 1)[1].splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def main() -> int:
    text = PROFILE.read_text(encoding="utf-8")
    if "# Embedded rules" in text or "embedded_sources" in text:
        raise SystemExit("embedded rule content is forbidden; use remote RULE-SET/DOMAIN-SET references")
    rules = active_rule_lines(text)
    external = {
        line for line in rules if line.startswith(("RULE-SET,", "DOMAIN-SET,"))
    }
    expected = expected_remote_lines()
    if external != expected:
        missing = sorted(expected - external)
        unexpected = sorted(external - expected)
        raise SystemExit(
            f"remote rule inventory mismatch: missing={missing}, unexpected={unexpected}"
        )
    print(
        f"PASS: remote-only profile; external_rules={len(external)} "
        f"embedded_rule_contents=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
