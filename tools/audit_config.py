#!/usr/bin/env python3
"""Audit the complete Surge iOS Privacy + Push R13.6 profile."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from convert_to_remote_rules import (
    DOMESTIC_DNS_RULES,
    DOMESTIC_GEOIP_RULE,
    DYNAMIC_RULES,
    FOREIGN_DNS_RULES,
    FUNCTIONAL_GUARDS,
    PROFILE_NAME,
    RELEASE_REF,
    REMOTE_BASE,
    REPOSITORY_RULES,
    RETIRED_BILIBILI_INTL_GUARDS,
    expected_remote_order,
    repository_line,
)


ROOT = Path(__file__).resolve().parent.parent
PROFILE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "Surge.conf"
LOCK = ROOT / "Rules" / "r10.lock.json"
PLACEHOLDER = "https://example.invalid/REPLACE_WITH_SUB_STORE_URL"
REGIONS = ("HongKong", "TaiWan", "Japan", "Singapore", "America")
GROUP_ORDER = (
    "Final", "Proxy", "ApplePush", "ChatGPT", "Claude", "Gemini", "GitHub",
    "YouTube", "NETFLIX", "Disney+", "HBO", "PrimeVideo", "Emby", "TikTok",
    "Bahamut", "Spotify", "Streaming", "Telegram", "X", "Apple", "Google",
    "Microsoft", "Games", "Auto", "NodePool", *REGIONS,
)
REMOVED_GROUPS = {"AllServer", "AdBlock", "Security", "UDP", "Domestic"}
AUTO_FILTER = "policy-regex-filter=^(?!Fail-Closed$).+"
AUTO_OPTIONS = (
    "interval=600", "tolerance=100", "evaluate-before-use=true",
    "no-alert=0", "hidden=0", "include-all-proxies=0",
    "include-other-group=NodePool",
)
VISIBLE_SELECT_OPTIONS = ("no-alert=0", "hidden=0", "include-all-proxies=0")
REGION_FILTER_SHA256 = {
    "HongKong": "d73d8aca3f0d3e18d83f9a7250301509f1b1a5bef5c2e6c38e98bc9b39218ea2",
    "TaiWan": "7ebe07a8a85a8ded7cae715491393a674805f836294a4d0357785b4eb9de098f",
    "Japan": "e977bdaae8adda811ce510b3a97cd0980d90a15e16e9c4fb653680d85a22fd46",
    "Singapore": "a7cfc4d2af80513590df01428b8ed41008cc371a86cef4d0fe9dde1c41b92b58",
    "America": "9219ee1ac7b3200e8aade881175e7a7c8b57c2509644130ea599cbe53a18e694",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def parse(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for number, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped[1:-1]
            if current in sections:
                fail(f"duplicate section {current} at line {number}")
            sections[current] = []
        elif current is not None:
            sections[current].append(raw)
    return sections


def active(lines: list[str]) -> list[str]:
    return [
        line.strip() for line in lines
        if line.strip() and not line.lstrip().startswith(("#", ";", "//"))
    ]


def key_values(lines: list[str], section: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in active(lines):
        if "=" not in line:
            fail(f"missing = in [{section}]: {line}")
        key, value = (part.strip() for part in line.split("=", 1))
        if not key or key in values:
            fail(f"empty or duplicate key [{section}] {key!r}")
        values[key] = value
    return values


def group_parts(groups: dict[str, str], name: str) -> list[str]:
    return [part.strip() for part in groups[name].split(",")]


def group_members(groups: dict[str, str], name: str) -> list[str]:
    return [part for part in group_parts(groups, name)[1:] if "=" not in part]


def require_options(parts: list[str], name: str, options: tuple[str, ...]) -> None:
    for option in options:
        if option not in parts:
            fail(f"{name} missing required option: {option}")


def require_exact_options(parts: list[str], name: str, expected: tuple[str, ...]) -> None:
    actual = tuple(part for part in parts[1:] if "=" in part)
    if len(actual) != len(expected) or set(actual) != set(expected):
        fail(f"{name} option inventory changed: {actual}")


payload = PROFILE.read_bytes()
if payload.startswith(b"\xef\xbb\xbf") or b"\r" in payload or not payload.endswith(b"\n"):
    fail("profile must be BOM-free UTF-8, LF-only, and end with a newline")
try:
    text = payload.decode("utf-8")
except UnicodeDecodeError as exc:
    fail(f"profile is not valid UTF-8: {exc}")

expected_header = [
    "# > Surge Config Make by .ᐣ",
    "# > TG Channel: https://t.me/shenjlngbIng",
    "# > GitHub: https://github.com/shenjlngbIng",
    "# > Update Date: 2026.08.30",
    "# > Surge iOS Privacy + Push R13.6 Hybrid Auto | iOS 5.14.6+ (5.21.0+ recommended) | Rule Mode",
    "# > Auto and region url-test groups optimize daily selection; NodePool keeps a manual Fail-Closed entry.",
    "# > Automatic groups may use DIRECT/SUBSTITUTE when empty; read README before enabling Auto.",
    "# > Domestic BiliBili and reviewed functional dependencies precede the fixed mobile ad boundary.",
    f"# > Static repository rules are pinned to commit {RELEASE_REF} (2026.08.29).",
    "# > REQUIRED: replace NodePool.policy-path locally; never publish subscription tokens.",
]
if text.splitlines()[:10] != expected_header:
    fail("profile attribution, version, snapshot or token warning changed")
if not re.fullmatch(r"[0-9a-f]{40}", RELEASE_REF):
    fail("runtime snapshot must be a full lowercase Git SHA")
if text.count(PLACEHOLDER) != 1:
    fail("public subscription placeholder must appear exactly once")
for marker in ("@main/Rules/", "raw.githubusercontent.com", "reject_phishing.conf", "/domainset/reject.conf"):
    if marker in text:
        fail(f"mutable or mobile-heavy runtime source is forbidden: {marker}")

sections = parse(text)
if list(sections) != ["General", "Host", "Proxy", "Proxy Group", "Rule"]:
    fail(f"section order or inventory mismatch: {list(sections)}")

general = key_values(sections["General"], "General")
expected_general = {
    "loglevel": "notify",
    "auto-suspend": "true",
    "ipv6": "true",
    "ipv6-vif": "auto",
    "wifi-assist": "false",
    "all-hybrid": "false",
    "include-all-networks": "true",
    "include-local-networks": "false",
    "include-apns": "true",
    "include-cellular-services": "false",
    "dns-server": "223.5.5.5, 223.6.6.6",
    "encrypted-dns-server": "https://dns.alidns.com/dns-query, https://doh.pub/dns-query",
    "encrypted-dns-follow-outbound-mode": "false",
    "encrypted-dns-skip-cert-verification": "false",
    "hijack-dns": "*:53",
    "allow-wifi-access": "false",
    "allow-hotspot-access": "false",
    "http-api-web-dashboard": "false",
    "proxy-restricted-to-lan": "true",
    "gateway-restricted-to-lan": "true",
    "udp-policy-not-supported-behaviour": "REJECT",
    "block-quic": "per-policy",
    "proxy-test-udp": "apple.com@9.9.9.9",
}
for key, value in expected_general.items():
    if general.get(key) != value:
        fail(f"[General] invariant changed: {key}")

hosts = key_values(sections["Host"], "Host")
if hosts != {
    "sub.store": "127.0.0.1",
    "dns.alidns.com": "223.5.5.5, 223.6.6.6, 2400:3200::1",
    "doh.pub": "1.12.12.12, 120.53.53.53",
}:
    fail("Host bootstrap or fail-closed Sub-Store mapping changed")

proxies = key_values(sections["Proxy"], "Proxy")
if proxies != {"Fail-Closed": "reject"}:
    fail("Fail-Closed must remain the built-in reject alias")

groups = key_values(sections["Proxy Group"], "Proxy Group")
if tuple(groups) != GROUP_ORDER or len(groups) != 30:
    fail(f"policy group order or count mismatch: {tuple(groups)}")
if REMOVED_GROUPS & groups.keys():
    fail("removed automatic or stateful helper group returned")
for name in groups:
    option_keys = [part.split("=", 1)[0] for part in group_parts(groups, name)[1:] if "=" in part]
    if len(option_keys) != len(set(option_keys)):
        fail(f"{name} contains duplicate policy-group options")

if group_parts(groups, "Final")[0] != "select" or group_members(groups, "Final") != ["Proxy", "REJECT"]:
    fail("Final policy changed")
if group_parts(groups, "Proxy")[0] != "select" or group_members(groups, "Proxy") != ["Auto", "NodePool", *REGIONS]:
    fail("Proxy must default to Auto and retain NodePool plus region entries")
if group_parts(groups, "ApplePush")[0] != "fallback" or group_members(groups, "ApplePush") != ["Proxy", "DIRECT"]:
    fail("ApplePush fallback exception changed")
require_exact_options(group_parts(groups, "ApplePush"), "ApplePush", (
    "interval=60", "evaluate-before-use=true", "no-alert=0", "hidden=1",
))

for name in set(groups) - {"ApplePush", "Auto", "NodePool", *REGIONS}:
    require_exact_options(group_parts(groups, name), name, VISIBLE_SELECT_OPTIONS)

node_parts = group_parts(groups, "NodePool")
if node_parts[0] != "select" or group_members(groups, "NodePool") != ["Fail-Closed"]:
    fail("NodePool must be manual and begin with Fail-Closed")
require_exact_options(node_parts, "NodePool", (
    f"policy-path={PLACEHOLDER}", "update-interval=3600", "no-alert=0",
    "hidden=0", "include-all-proxies=0",
))

auto_parts = group_parts(groups, "Auto")
if auto_parts[0] != "url-test" or group_members(groups, "Auto"):
    fail("Auto must be a memberless url-test group fed only by NodePool")
require_exact_options(auto_parts, "Auto", (AUTO_FILTER, *AUTO_OPTIONS))

for region in REGIONS:
    parts = group_parts(groups, region)
    if parts[0] != "url-test" or group_members(groups, region):
        fail(f"{region} must be a memberless url-test group fed only by NodePool")
    filters = [option for option in parts if option.startswith("policy-regex-filter=")]
    if len(filters) != 1:
        fail(f"{region} lost its node-name filter")
    require_exact_options(parts, region, (filters[0], *AUTO_OPTIONS))
    if hashlib.sha256(filters[0].encode()).hexdigest() != REGION_FILTER_SHA256[region]:
        fail(f"{region} node-name filter changed")

restricted = {
    "ChatGPT": ["Japan", "Singapore", "TaiWan", "America"],
    "Claude": ["Japan", "Singapore", "TaiWan", "America"],
    "Gemini": ["Japan", "Singapore", "TaiWan", "America"],
    "TikTok": ["Japan", "Singapore", "TaiWan", "America"],
    "Bahamut": ["TaiWan", "HongKong"],
}
for name, members in restricted.items():
    if group_parts(groups, name)[0] != "select" or group_members(groups, name) != members:
        fail(f"{name} supported-region boundary changed")

generic_members = {
    "GitHub": ["Proxy", "HongKong", "Japan", "Singapore", "America"],
    "YouTube": ["Proxy", *REGIONS], "NETFLIX": ["Proxy", *REGIONS],
    "Disney+": ["Proxy", *REGIONS],
    "HBO": ["Proxy", "America", "Singapore", "Japan", "HongKong", "TaiWan"],
    "PrimeVideo": ["Proxy", "America", "Japan", "Singapore", "HongKong", "TaiWan"],
    "Emby": ["Proxy", *REGIONS], "Spotify": ["Proxy", *REGIONS],
    "Streaming": ["Proxy", *REGIONS], "Telegram": ["Proxy", *REGIONS],
    "X": ["Proxy", *REGIONS], "Apple": ["DIRECT", "Proxy", *REGIONS],
    "Google": ["Proxy", *REGIONS], "Microsoft": ["Proxy", *REGIONS],
    "Games": ["Proxy", *REGIONS],
}
for name, members in generic_members.items():
    if group_parts(groups, name)[0] != "select" or group_members(groups, name) != members:
        fail(f"{name} member order changed")

automatic = {name: group_parts(groups, name)[0] for name in groups if group_parts(groups, name)[0] in {"smart", "url-test", "load-balance"}}
expected_automatic = {"Auto": "url-test", **{region: "url-test" for region in REGIONS}}
if automatic != expected_automatic:
    fail(f"automatic node-group boundary changed: {automatic}")

# Validate group references and reject cycles.
builtins = {"DIRECT", "REJECT", "REJECT-DROP", "Fail-Closed"}
for name in groups:
    unknown = [member for member in group_members(groups, name) if member not in groups and member not in builtins]
    if unknown:
        fail(f"{name} contains unknown policy members: {unknown}")

visiting: set[str] = set()
visited: set[str] = set()
def visit(name: str) -> None:
    if name in visiting:
        fail(f"policy group cycle detected at {name}")
    if name in visited:
        return
    visiting.add(name)
    for member in group_members(groups, name):
        if member in groups:
            visit(member)
    visiting.remove(name)
    visited.add(name)
for group in groups:
    visit(group)

rules = active(sections["Rule"])
if len(rules) != 142 or rules[-1] != "FINAL,Final,dns-failed" or rules.count("FINAL,Final,dns-failed") != 1:
    fail("reviewed rule count or unique FINAL changed")
external = [rule for rule in rules if rule.startswith(("RULE-SET,", "DOMAIN-SET,"))]
if external != expected_remote_order():
    fail("runtime resource order differs from reviewed inventory")
if len(external) != 30:
    fail("runtime resource count changed")

for kind, filename, _label, policy in REPOSITORY_RULES:
    line = repository_line(kind, filename, policy)
    if rules.count(line) != 1:
        fail(f"immutable resource line changed: {filename}")
    if f"@{RELEASE_REF}/Rules/{filename}" not in line:
        fail(f"immutable resource is not pinned: {filename}")

dynamic_line = "RULE-SET,https://ruleset.skk.moe/List/non_ip/domestic.conf,DIRECT,extended-matching,no-resolve,update-interval=86400"
if external.count(dynamic_line) != 1 or len(DYNAMIC_RULES) != 1:
    fail("dynamic domestic supplement boundary changed")

def index(line: str) -> int:
    if rules.count(line) != 1:
        fail(f"required rule is missing or duplicated: {line}")
    return rules.index(line)

guard_start = index(FUNCTIONAL_GUARDS[0])
if rules[guard_start:guard_start + len(FUNCTIONAL_GUARDS)] != list(FUNCTIONAL_GUARDS):
    fail("functional guards must be complete and contiguous")
ads_line = repository_line("RULE-SET", "Ads.list", "REJECT")
if any(index(line) >= index(ads_line) for line in FUNCTIONAL_GUARDS):
    fail("functional guard appears after Ads")
intl_start = index(RETIRED_BILIBILI_INTL_GUARDS[0])
if rules[intl_start:intl_start + len(RETIRED_BILIBILI_INTL_GUARDS)] != list(RETIRED_BILIBILI_INTL_GUARDS):
    fail("retired BiliBili international compatibility guards changed")
if index(RETIRED_BILIBILI_INTL_GUARDS[0]) >= index(repository_line("RULE-SET", "BiliBili.list", "DIRECT")):
    fail("international compatibility guard must precede domestic BiliBili parent suffixes")

stun = index("PROTOCOL,STUN,Proxy")
domestic_dns_start = index(DOMESTIC_DNS_RULES[0])
if rules[domestic_dns_start:domestic_dns_start + len(DOMESTIC_DNS_RULES)] != list(DOMESTIC_DNS_RULES):
    fail("mainland application DNS block changed")
port_rules = ["DEST-PORT,53,REJECT", "DEST-PORT,853,REJECT", "DEST-PORT,8853,REJECT"]
port_start = index(port_rules[0])
if rules[port_start:port_start + 3] != port_rules or not stun < domestic_dns_start < port_start:
    fail("STUN, mainland DNS and public DNS-port order changed")
foreign_start = index(FOREIGN_DNS_RULES[0])
if rules[foreign_start:foreign_start + len(FOREIGN_DNS_RULES)] != list(FOREIGN_DNS_RULES) or foreign_start <= port_start:
    fail("foreign application DNS block or order changed")

diagnostics = (
    "DOMAIN-SUFFIX,net.coffee,Proxy", "DOMAIN-SUFFIX,ippure.com,Proxy",
    "DOMAIN-SUFFIX,browserleaks.net,Proxy", "DOMAIN-SUFFIX,surfsharkdns.com,Proxy",
    "DOMAIN-SUFFIX,fastly-analytics.com,Proxy", "DOMAIN-SUFFIX,icanhazip.com,Proxy",
    "DOMAIN-SUFFIX,ipinfo.io,Proxy", "DOMAIN-SUFFIX,ipapi.co,Proxy",
    "DOMAIN-SUFFIX,ipip.net,Proxy", "IP-CIDR,1.1.1.1/32,Proxy,no-resolve",
)
for line in diagnostics:
    index(line)

shared_domestic = (
    "DOMAIN-SUFFIX,alibabausercontent.com,DIRECT", "DOMAIN-SUFFIX,aliyuncs.com,DIRECT",
    "DOMAIN-SUFFIX,bcebos.com,DIRECT", "DOMAIN-SUFFIX,coding.net,DIRECT",
    "DOMAIN-SUFFIX,gitee.io,DIRECT", "DOMAIN-SUFFIX,jdcloud.com,DIRECT",
    "DOMAIN-SUFFIX,myqcloud.com,DIRECT", "DOMAIN-SUFFIX,qcloudimg.com,DIRECT",
    "DOMAIN-SUFFIX,qiniu.com,DIRECT", "DOMAIN-SUFFIX,tencentcs.com,DIRECT",
    "DOMAIN-SUFFIX,volccdn.com,DIRECT", "DOMAIN-SUFFIX,volcengine.com,DIRECT",
)
shared_start = index(shared_domestic[0])
if rules[shared_start:shared_start + len(shared_domestic)] != list(shared_domestic):
    fail("bounded domestic fallback block changed")
if not shared_start < index(dynamic_line) < index(repository_line("DOMAIN-SET", "China.list", "DIRECT")):
    fail("domestic fixed/dynamic precedence changed")

tail = [
    DOMESTIC_GEOIP_RULE,
    "IP-CIDR,0.0.0.0/0,Proxy,no-resolve",
    "IP-CIDR6,::/0,Proxy,no-resolve",
    "FINAL,Final,dns-failed",
]
if rules[-4:] != tail:
    fail("CN GeoIP, dual-stack public literals or FINAL tail changed")

ordered_overlap_guards = (
    "DOMAIN,hls-amt.itunes.apple.com,Streaming", "DOMAIN,hls.itunes.apple.com,Streaming",
    "DOMAIN,np-edge.itunes.apple.com,Streaming", "DOMAIN,play-edge.itunes.apple.com,Streaming",
    "DOMAIN,uts-api.itunes.apple.com,Streaming",
)
if max(index(line) for line in ordered_overlap_guards) >= index(repository_line("RULE-SET", "AppleCN.list", "Apple")):
    fail("Apple streaming exceptions must precede AppleCN")
if index("DOMAIN-SUFFIX,viu.now.com,Streaming") >= index(repository_line("RULE-SET", "HBO.list", "HBO")):
    fail("Viu exception must precede HBO parent suffix")
for line in ("DOMAIN,img-prod-cms-rt-microsoft-com.akamaized.net,Microsoft", "DOMAIN,login.live.com,Microsoft", "DOMAIN,logincdn.msauth.net,Microsoft", "DOMAIN,store-images.s-microsoft.com,Microsoft", "IP-CIDR,35.192.0.0/12,Proxy,no-resolve"):
    if index(line) >= index(repository_line("RULE-SET", "Game.list", "Games")):
        fail("Microsoft/shared cloud guard must precede Game")

valid_policies = set(groups) | {"DIRECT", "REJECT", "REJECT-DROP", "Fail-Closed"}
for rule in rules:
    fields = [field.strip() for field in rule.split(",")]
    policy = fields[1] if fields[0] == "FINAL" else fields[2]
    if policy not in valid_policies:
        fail(f"rule references unknown policy: {rule}")

if PROFILE == ROOT / "Surge.conf":
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    expected_counts = (142, 30, 29, 1, 29)
    actual_counts = tuple(lock.get(key) for key in (
        "active_rules", "runtime_resources", "immutable_repository_resources",
        "dynamic_runtime_resources", "local_rule_files",
    ))
    if lock.get("schema") != 20 or lock.get("mode") != "immutable-rules-plus-domestic-dynamic":
        fail("runtime lock schema or mode mismatch")
    if actual_counts != expected_counts or lock.get("profile") != PROFILE_NAME:
        fail("runtime lock profile or counts mismatch")
    if lock.get("profile_sha256") != hashlib.sha256(payload).hexdigest():
        fail("runtime lock profile hash is stale")

print(
    f"PASS R13.6 groups={len(groups)} rules={len(rules)} runtime_resources={len(external)} "
    f"immutable_resources={len(REPOSITORY_RULES)} dynamic_resources={len(DYNAMIC_RULES)} "
    f"embedded_rule_contents=0 sha256={hashlib.sha256(payload).hexdigest()}"
)
