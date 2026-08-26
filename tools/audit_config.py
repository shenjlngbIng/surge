#!/usr/bin/env python3
"""Audit the complete Surge iOS Privacy + Push R12.17 profile."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import sys
from pathlib import Path

from convert_to_remote_rules import (
    PROFILE_NAME,
    RELEASE_REF,
    REMOTE_BASE,
    REPOSITORY_RULES,
    expected_remote_order,
    repository_line,
)


ROOT = Path(__file__).resolve().parent.parent
PROFILE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "Surge.conf"
LOCK = ROOT / "Rules/r10.lock.json"


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
        line.strip()
        for line in lines
        if line.strip() and not line.lstrip().startswith(("#", ";", "//"))
    ]


def key_values(lines: list[str], section: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in active(lines):
        if "=" not in line:
            fail(f"missing = in [{section}]: {line}")
        key, value = (part.strip() for part in line.split("=", 1))
        if key in values:
            fail(f"duplicate key [{section}] {key}")
        values[key] = value
    return values


def target(rule: str) -> str:
    fields = [field.strip() for field in rule.split(",")]
    return fields[1] if fields[0] == "FINAL" else fields[2]


text = PROFILE.read_text(encoding="utf-8")
if not text.endswith("\n") or "\r" in text or "\ufeff" in text:
    fail("profile must be UTF-8 LF and end with newline")
expected_header = [
    "# > Surge Config Make by .ᐣ",
    "# > TG Channel: https://t.me/shenjlngbIng",
    "# > GitHub: https://github.com/shenjlngbIng",
    "# > Update Date: 2026.08.26",
    "# > Surge iOS Privacy + Push R12.17 | iOS 5.14.6+ (5.21.0+ recommended) | Rule Mode",
]
if text.splitlines()[:5] != expected_header:
    fail("profile attribution/version header mismatch")
if RELEASE_REF != "d1d714d575d5494ef1a7613238f4f301e1b293df" or "@main/Rules/" in text:
    fail("runtime rule URLs must use the immutable R12.17 rule-snapshot commit")
if len(RELEASE_REF) != 40 or any(char not in "0123456789abcdef" for char in RELEASE_REF):
    fail("runtime rule reference must be a full lowercase Git commit SHA")

sections = parse(text)
if list(sections) != ["General", "Host", "Proxy", "Proxy Group", "Rule"]:
    fail(f"section order mismatch: {list(sections)}")

general = key_values(sections["General"], "General")
required_general = {
    "auto-suspend": "true",
    "internet-test-url": "http://connectivitycheck.platform.hicloud.com/generate_204",
    "proxy-test-url": "http://cp.cloudflare.com/generate_204",
    "test-timeout": "5",
    "proxy-test-udp": "apple.com@223.5.5.5",
    "ipv6": "true",
    "ipv6-vif": "auto",
    "compatibility-mode": "3",
    "wifi-assist": "false",
    "all-hybrid": "false",
    "include-all-networks": "true",
    "include-local-networks": "false",
    "include-apns": "true",
    "include-cellular-services": "false",
    "icmp-forwarding": "false",
    "hijack-dns": "*:53",
    "allow-dns-svcb": "false",
    "use-local-host-item-for-proxy": "false",
    "dns-server": "223.5.5.5, 223.6.6.6",
    "encrypted-dns-server": "https://dns.alidns.com/dns-query, tls://dns.alidns.com",
    "encrypted-dns-follow-outbound-mode": "false",
    "encrypted-dns-skip-cert-verification": "false",
    "allow-wifi-access": "false",
    "allow-hotspot-access": "false",
    "http-api-web-dashboard": "false",
    "proxy-restricted-to-lan": "true",
    "gateway-restricted-to-lan": "true",
    "udp-policy-not-supported-behaviour": "REJECT",
    "block-quic": "per-policy",
}
for key, value in required_general.items():
    if general.get(key) != value:
        fail(f"[General] {key}: expected {value!r}, got {general.get(key)!r}")
if "system" in general.get("dns-server", "").lower():
    fail("system DNS is forbidden in the public privacy profile")
if "read-etc-hosts" in general:
    fail("read-etc-hosts is a macOS-only option")
skip_proxy = {item.strip() for item in general.get("skip-proxy", "").split(",")}
if "100.64.0.0/10" not in skip_proxy:
    fail("skip-proxy must include 100.64.0.0/10")

host = key_values(sections["Host"], "Host")
if host != {"dns.alidns.com": "223.5.5.5, 223.6.6.6, 2400:3200::1"}:
    fail("DNS bootstrap must be one dns.alidns.com mapping with all three addresses")

proxies = key_values(sections["Proxy"], "Proxy")
if proxies != {"Fail-Closed": "http, 127.0.0.1, 1, no-error-alert=true"}:
    fail("Fail-Closed sentinel changed")

groups = key_values(sections["Proxy Group"], "Proxy Group")
expected_groups = {
    "Final", "Proxy", "ApplePush", "AdBlock", "Security", "UDP", "PrivacyAuto",
    "ChatGPT", "Claude", "Gemini", "GitHub", "YouTube", "NETFLIX",
    "Disney+", "HBO", "PrimeVideo", "Emby", "TikTok", "Bahamut",
    "Spotify", "Streaming", "Telegram", "X", "Apple", "Google",
    "Microsoft", "Games", "NodePool", "AllServer", "HongKong", "TaiWan",
    "Japan", "Singapore", "America",
}
if set(groups) != expected_groups:
    fail(f"policy group inventory mismatch: missing={sorted(expected_groups-set(groups))}, unexpected={sorted(set(groups)-expected_groups)}")


def group_members(name: str) -> list[str]:
    parts = [part.strip() for part in groups.get(name, "").split(",")]
    return [part for part in parts[1:] if "=" not in part]


if group_members("Final") != ["Proxy", "REJECT"]:
    fail("Final must contain only Proxy and REJECT")
if group_members("Proxy") != ["AllServer", "HongKong", "TaiWan", "Japan", "Singapore", "America"]:
    fail("Proxy members or default order changed")
if group_members("ApplePush") != ["Proxy", "DIRECT"]:
    fail("ApplePush must contain exactly Proxy then DIRECT")
apple_push = [part.strip() for part in groups["ApplePush"].split(",")]
if apple_push[0] != "fallback" or "interval=60" not in apple_push or "evaluate-before-use=true" not in apple_push:
    fail("ApplePush must use reviewed fallback evaluation settings")
if any(part.startswith("timeout=") for part in apple_push):
    fail("ApplePush must use the global test timeout, not a misleading group timeout")
if group_members("AdBlock") != ["REJECT", "REJECT-DROP", "DIRECT"]:
    fail("AdBlock must preserve its emergency DIRECT off-switch")
if group_members("Security") != ["REJECT", "REJECT-DROP", "DIRECT"]:
    fail("Security must preserve its emergency DIRECT off-switch")
if group_members("UDP") != ["Proxy", "DIRECT", "REJECT"]:
    fail("UDP must preserve Proxy, DIRECT and REJECT choices")
if group_members("PrivacyAuto") != ["Fail-Closed"]:
    fail("PrivacyAuto may only declare Fail-Closed before importing NodePool")
privacy_parts = [part.strip() for part in groups["PrivacyAuto"].split(",")]
for option in (
    "interval=600", "tolerance=100", "evaluate-before-use=true",
    "no-alert=1", "hidden=1", "include-all-proxies=0",
    "include-other-group=NodePool",
):
    if option not in privacy_parts:
        fail(f"PrivacyAuto missing hidden automatic-selection option: {option}")
if any(part.startswith(("timeout=", "policy-path=")) for part in privacy_parts):
    fail("PrivacyAuto must use the global test timeout and the reviewed NodePool source")
for name in ("ApplePush", "AdBlock", "Security", "UDP"):
    parts = [part.strip() for part in groups[name].split(",")]
    if "hidden=1" not in parts:
        fail(f"{name} must remain hidden from the policy selection view")
if group_members("HBO")[:2] != ["Proxy", "America"]:
    fail("HBO must default to Proxy")

node_pool_parts = [part.strip() for part in groups["NodePool"].split(",")]
if node_pool_parts[0] != "select":
    fail("NodePool must remain a passive select container")
for option in (
    "policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL",
    "update-interval=3600", "no-alert=0", "hidden=1", "include-all-proxies=0",
):
    if option not in node_pool_parts:
        fail(f"NodePool missing designed option: {option}")
if group_members("NodePool"):
    fail("NodePool cannot contain an explicit routing member")
for forbidden in ("Fail-Closed", "interval=", "timeout=", "evaluate-before-use=", "tolerance=", "include-all-proxies=true"):
    if any(part == forbidden or part.startswith(forbidden) for part in node_pool_parts):
        fail(f"NodePool may not test or route imported nodes: {forbidden}")

regions = ("HongKong", "TaiWan", "Japan", "Singapore", "America")
smart_groups = {"AllServer", *regions}
for name, value in groups.items():
    parts = [part.strip() for part in value.split(",")]
    mode = parts[0]
    expected_mode = (
        "smart" if name in smart_groups
        else "fallback" if name == "ApplePush"
        else "url-test" if name == "PrivacyAuto"
        else "select"
    )
    if mode != expected_mode:
        fail(f"{name} must use {expected_mode}, got {mode}")
    if "policy-path=" in value and name != "NodePool":
        fail(f"only NodePool may own policy-path: {name}")
    if "include-all-proxies=true" in value:
        fail(f"group bypasses the explicit NodePool architecture: {name}")
    if any(part == "NodePool" for part in parts):
        fail(f"NodePool cannot be a directly selectable member: {name}")

for name in smart_groups:
    parts = [part.strip() for part in groups[name].split(",")]
    if parts[:2] != ["smart", "Fail-Closed"]:
        fail(f"{name} must start with smart and Fail-Closed")
    if "include-other-group=NodePool" not in parts or "include-all-proxies=0" not in parts:
        fail(f"{name} must import only NodePool")
    if group_members(name) != ["Fail-Closed"]:
        fail(f"{name} may only declare Fail-Closed before importing NodePool")
    if any(part.startswith(("interval=", "timeout=", "evaluate-before-use=", "tolerance=", "policy-path=")) for part in parts):
        fail(f"{name} restored eager whole-subscription testing")
for region in regions:
    if "policy-regex-filter=" not in groups[region]:
        fail(f"{region} is missing its regional filter")

proxy_only_groups = {
    "ChatGPT", "Claude", "Gemini", "GitHub", "YouTube", "NETFLIX", "Disney+",
    "HBO", "PrimeVideo", "Emby", "TikTok", "Bahamut", "Spotify", "Streaming",
    "Telegram", "X", "Google", "Microsoft", "Games", "PrivacyAuto",
}
for name in proxy_only_groups:
    if "DIRECT" in group_members(name):
        fail(f"{name} cannot expose a DIRECT member")

rules = active(sections["Rule"])
if rules[-1] != "FINAL,Final,dns-failed":
    fail("FINAL invariant failed")
if len(rules) != len(set(rules)):
    fail("duplicate active rules detected")

expected_external = {
    repository_line(kind, filename, policy)
    for kind, filename, _label, policy in REPOSITORY_RULES
}
actual_external = {rule for rule in rules if rule.startswith(("RULE-SET,", "DOMAIN-SET,"))}
if actual_external != expected_external:
    fail(f"runtime resource inventory mismatch: missing={sorted(expected_external-actual_external)}, unexpected={sorted(actual_external-expected_external)}")
for rule in actual_external:
    fields = [field.strip() for field in rule.split(",")]
    expected_fields = 5 if fields[0] == "RULE-SET" else 4
    if len(fields) != expected_fields or not fields[1].startswith(REMOTE_BASE) or fields[-1] != "update-interval=-1":
        fail(f"runtime resource is not an immutable repository URL: {rule}")
    if fields[0] == "RULE-SET" and fields[3] != "no-resolve":
        fail(f"runtime RULE-SET may not trigger local DNS: {rule}")
if "raw.githubusercontent.com" in text or "blackmatrix7/ios_rule_script" in text:
    fail("third-party runtime rule URL leaked into Surge.conf")
if "# Embedded rules" in text or "embedded_sources" in text:
    fail("embedded rule content is forbidden")

snapshot_rules = {
    line.strip()
    for path in (ROOT / "Rules").glob("*.list")
    for line in path.read_text(encoding="utf-8-sig").splitlines()
    if line.strip() and not line.lstrip().startswith(("#", ";", "//"))
}
embedded = sorted(set(rules) & snapshot_rules)
if embedded:
    fail(f"profile contains embedded snapshot content: {embedded[:3]}")

defined_policies = set(groups) | set(proxies) | {"DIRECT", "REJECT", "REJECT-DROP", "REJECT-TINYGIF", "REJECT-NO-DROP"}
valid_protocols = {"HTTP", "HTTPS", "TCP", "UDP", "DNS", "DOH", "DOH3", "DOQ", "DOT", "QUIC", "STUN"}
for rule in rules:
    fields = [field.strip() for field in rule.split(",")]
    if fields[0] in {"RULE-SET", "DOMAIN-SET", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-WILDCARD", "IP-CIDR", "IP-CIDR6", "IP-ASN", "GEOIP", "PROTOCOL", "DEST-PORT", "FINAL"}:
        policy = target(rule)
        if policy not in defined_policies:
            fail(f"rule targets an undefined policy: {rule}")
    if fields[0] in {"IP-CIDR", "IP-CIDR6"}:
        ipaddress.ip_network(fields[1], strict=False)
        if "no-resolve" not in fields[3:]:
            fail(f"inline IP rule may not trigger local DNS: {rule}")
    if fields[0] == "PROTOCOL":
        protocol = fields[1].upper()
        if protocol not in valid_protocols:
            fail(f"unsupported PROTOCOL rule: {rule}")
        if protocol in {"DOH", "DOH3", "DOQ"}:
            fail(f"encrypted DNS protocol rules are inactive in this DNS mode: {rule}")


def rule_position(prefix: str) -> int:
    for index, rule in enumerate(rules):
        if rule.startswith(prefix):
            return index
    fail(f"missing ordering anchor: {prefix}")


external_positions = [rules.index(line) for line in expected_remote_order()]
if external_positions != sorted(external_positions):
    fail("repository resource relative order changed")
pegasus_pos = rule_position(f"DOMAIN-SET,{REMOTE_BASE}Pegasus.list,")
apns_pos = rule_position(f"RULE-SET,{REMOTE_BASE}APNs.list,")
youtube_pos = rule_position(f"RULE-SET,{REMOTE_BASE}YouTube.list,")
hbo_pos = rule_position(f"RULE-SET,{REMOTE_BASE}HBO.list,")
bilibili_intl_pos = rule_position(f"RULE-SET,{REMOTE_BASE}BiliBiliIntl.list,")
bilibili_domestic_pos = rule_position(f"RULE-SET,{REMOTE_BASE}BiliBili.list,")
proxy_media_pos = rule_position(f"RULE-SET,{REMOTE_BASE}ProxyMedia.list,")
google_pos = rule_position(f"RULE-SET,{REMOTE_BASE}Google.list,")
game_pos = rule_position(f"RULE-SET,{REMOTE_BASE}Game.list,")
onedrive_pos = rule_position(f"RULE-SET,{REMOTE_BASE}OneDrive.list,")
microsoft_pos = rule_position(f"RULE-SET,{REMOTE_BASE}Microsoft.list,")
china_pos = rule_position(f"DOMAIN-SET,{REMOTE_BASE}China.list,")
global_pos = rule_position(f"DOMAIN-SET,{REMOTE_BASE}Global.list,")
stun_pos = rule_position("PROTOCOL,STUN,UDP")
public_ipv4_pos = rule_position("IP-CIDR,0.0.0.0/0,Proxy,no-resolve")
public_ipv6_pos = rule_position("IP-CIDR6,::/0,Proxy,no-resolve")
diagnostic_rules = {
    "DOMAIN-SUFFIX,net.coffee,PrivacyAuto",
    "DOMAIN-SUFFIX,ippure.com,PrivacyAuto",
    "DOMAIN-SUFFIX,browserleaks.net,PrivacyAuto",
    "DOMAIN-SUFFIX,surfsharkdns.com,PrivacyAuto",
    "DOMAIN-SUFFIX,fastly-analytics.com,PrivacyAuto",
    "DOMAIN-SUFFIX,icanhazip.com,PrivacyAuto",
    "DOMAIN-SUFFIX,ipinfo.io,PrivacyAuto",
    "DOMAIN-SUFFIX,ipapi.co,PrivacyAuto",
    "DOMAIN-SUFFIX,ipip.net,PrivacyAuto",
    "IP-CIDR,1.1.1.1/32,PrivacyAuto,no-resolve",
}
if not diagnostic_rules <= set(rules):
    fail(f"privacy diagnostic guard is incomplete: {sorted(diagnostic_rules-set(rules))}")
if max(rules.index(rule) for rule in diagnostic_rules) >= rule_position("DOMAIN,dns.alidns.com,Proxy"):
    fail("privacy diagnostic guard must precede DNS and repository rules")
for dns_host in ("DOMAIN,dns.alidns.com,Proxy", "DOMAIN,doh.pub,Proxy"):
    if dns_host not in rules:
        fail(f"application encrypted DNS endpoint may not be DIRECT: {dns_host}")
if not (rule_position("DEST-PORT,8853,REJECT") < pegasus_pos < apns_pos):
    fail("security/APNs order changed")
if not (
    rule_position("DOMAIN,yt3.ggpht.com,YouTube")
    < rule_position("DOMAIN-SUFFIX,ggpht.com,Google")
    < youtube_pos
    < google_pos
):
    fail("YouTube/Google shared infrastructure overrides are out of order")
if not (rule_position("DOMAIN-SUFFIX,viu.now.com,Streaming") < hbo_pos < proxy_media_pos):
    fail("Viu must be protected from HBO's broader now.com suffix")
if not (bilibili_intl_pos < bilibili_domestic_pos < proxy_media_pos < china_pos):
    fail("BiliBili specialized routing order changed")
for inline in (
    "DOMAIN,img-prod-cms-rt-microsoft-com.akamaized.net,Microsoft",
    "DOMAIN,login.live.com,Microsoft",
    "DOMAIN,logincdn.msauth.net,Microsoft",
    "DOMAIN,store-images.s-microsoft.com,Microsoft",
    "IP-CIDR,35.192.0.0/12,Proxy,no-resolve",
):
    if rule_position(inline) >= game_pos:
        fail(f"shared Game/Microsoft override must precede Game.list: {inline}")
if not (game_pos < onedrive_pos < microsoft_pos < china_pos < global_pos < stun_pos < public_ipv4_pos < public_ipv6_pos):
    fail("Game/Microsoft/fallback/STUN/public-IP fail-closed order changed")

required_rules = {
    "IP-CIDR,100.64.0.0/10,DIRECT,no-resolve",
    "DOMAIN-SUFFIX,ls.apple.com,DIRECT",
    "DOMAIN-SUFFIX,viu.now.com,Streaming",
    "PROTOCOL,STUN,UDP",
    "IP-CIDR,0.0.0.0/0,Proxy,no-resolve",
    "IP-CIDR6,::/0,Proxy,no-resolve",
    *diagnostic_rules,
    *expected_external,
}
missing_required = required_rules - set(rules)
if missing_required:
    fail(f"missing required rules: {sorted(missing_required)}")
if any(("telegram" in rule.lower() or ",t.me," in rule.lower()) and target(rule) == "DIRECT" for rule in rules):
    fail("Telegram traffic cannot be DIRECT")
if any(target(rule) == "NodePool" for rule in rules):
    fail("rules cannot target NodePool")
if any(rule.startswith("GEOIP,CN,") and target(rule) == "DIRECT" for rule in rules):
    fail("China GEOIP may not expose public IP literals through DIRECT")

if LOCK.exists() and PROFILE.resolve() == (ROOT / "Surge.conf").resolve():
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if lock.get("profile") != PROFILE_NAME:
        fail("lock profile name is stale")
    if lock.get("profile_sha256") != hashlib.sha256(text.encode()).hexdigest():
        fail("lock hash is stale")
    if lock.get("active_rules") != len(rules):
        fail("lock active rule count is stale")

print(
    f"PASS R12.17 groups={len(groups)} rules={len(rules)} "
    f"runtime_resources={len(actual_external)} sha256={hashlib.sha256(text.encode()).hexdigest()}"
)
