#!/usr/bin/env python3
"""Audit the complete Surge iOS Privacy + Push R13.3 Domestic Performance profile."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import sys
from pathlib import Path

from convert_to_remote_rules import (
    DOMESTIC_DNS_RULES,
    DOMESTIC_GEOIP_RULE,
    DYNAMIC_RULES,
    FOREIGN_DNS_RULES,
    PROFILE_NAME,
    RELEASE_REF,
    REMOTE_BASE,
    REPOSITORY_RULES,
    dynamic_line,
    expected_remote_order,
    repository_line,
)


ROOT = Path(__file__).resolve().parent.parent
PROFILE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "Surge.conf"
LOCK = ROOT / "Rules" / "r10.lock.json"
PLACEHOLDER = "https://example.invalid/REPLACE_WITH_SUB_STORE_URL"
REGIONS = ("HongKong", "TaiWan", "Japan", "Singapore", "America")
GROUP_ORDER = (
    "Final", "Proxy", "ApplePush", "AdBlock", "Security", "UDP", "Domestic",
    "ChatGPT", "Claude", "Gemini", "GitHub", "YouTube", "NETFLIX",
    "Disney+", "HBO", "PrimeVideo", "Emby", "TikTok", "Bahamut",
    "Spotify", "Streaming", "Telegram", "X", "Apple", "Google",
    "Microsoft", "Games", "NodePool", "AllServer", *REGIONS,
)


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
    "# > Update Date: 2026.08.28",
    "# > Surge iOS Privacy + Push R13.3 Domestic Performance | iOS 5.14.6+ (5.21.0+ recommended) | Rule Mode",
    "# > Feature-preserving performance correction based on R13.2; no original service group or remote rule resource was removed.",
    "# > Static repository rules remain pinned to commit d1d714d575d5494ef1a7613238f4f301e1b293df (2026.08.25).",
    "# > REQUIRED: replace NodePool.policy-path locally; never publish subscription tokens.",
]
if text.splitlines()[:8] != expected_header:
    fail("profile attribution, version, date, preservation statement, snapshot disclosure, or token warning changed")
if not re.fullmatch(r"[0-9a-f]{40}", RELEASE_REF) or "@main/Rules/" in text:
    fail("repository runtime URLs must use the full immutable rule-snapshot commit")

sections = parse(text)
if list(sections) != ["General", "Host", "Proxy", "Proxy Group", "Rule"]:
    fail(f"section order or inventory mismatch: {list(sections)}")

general = key_values(sections["General"], "General")
required_general = {
    "loglevel": "notify",
    "auto-suspend": "true",
    "internet-test-url": "http://connectivitycheck.platform.hicloud.com/generate_204",
    "proxy-test-url": "http://cp.cloudflare.com/generate_204",
    "test-timeout": "5",
    "proxy-test-udp": "apple.com@9.9.9.9",
    "ipv6": "true",
    "ipv6-vif": "auto",
    "compatibility-mode": "3",
    "wifi-assist": "false",
    "all-hybrid": "false",
    "include-all-networks": "true",
    "include-local-networks": "false",
    "include-apns": "true",
    "include-cellular-services": "false",
    "show-error-page-for-reject": "false",
    "icmp-forwarding": "false",
    "disable-geoip-db-auto-update": "false",
    "exclude-simple-hostnames": "true",
    "dns-server": "223.5.5.5, 223.6.6.6",
    "encrypted-dns-server": "https://dns.alidns.com/dns-query, https://doh.pub/dns-query",
    "encrypted-dns-follow-outbound-mode": "false",
    "encrypted-dns-skip-cert-verification": "false",
    "hijack-dns": "*:53",
    "allow-dns-svcb": "false",
    "use-local-host-item-for-proxy": "false",
    "allow-wifi-access": "false",
    "allow-hotspot-access": "false",
    "http-api-web-dashboard": "false",
    "proxy-restricted-to-lan": "true",
    "gateway-restricted-to-lan": "true",
    "udp-policy-not-supported-behaviour": "REJECT",
    "block-quic": "per-policy",
}
for key, expected in required_general.items():
    if general.get(key) != expected:
        fail(f"[General] {key}: expected {expected!r}, got {general.get(key)!r}")
for required_key in ("always-real-ip", "skip-proxy", "always-raw-tcp-hosts"):
    if not general.get(required_key):
        fail(f"[General] missing {required_key}")
if set(general) != set(required_general) | {"always-real-ip", "skip-proxy", "always-raw-tcp-hosts"}:
    fail("[General] contains an unreviewed or missing option")
if "system" in general["dns-server"].lower() or "read-etc-hosts" in general:
    fail("system DNS or macOS-only hosts loading is forbidden")
if "100.64.0.0/10" not in {part.strip() for part in general["skip-proxy"].split(",")}:
    fail("skip-proxy must include CGNAT 100.64.0.0/10")

host = key_values(sections["Host"], "Host")
if host != {
    "sub.store": "127.0.0.1",
    "dns.alidns.com": "223.5.5.5, 223.6.6.6, 2400:3200::1",
    "doh.pub": "1.12.12.12, 120.53.53.53",
}:
    fail("[Host] fail-closed synthetic host or DNS bootstrap mappings changed")

proxies = key_values(sections["Proxy"], "Proxy")
if proxies != {"Fail-Closed": "http, 127.0.0.1, 1, no-error-alert=true"}:
    fail("Fail-Closed sentinel changed")

groups = key_values(sections["Proxy Group"], "Proxy Group")
if tuple(groups) != GROUP_ORDER:
    fail(f"policy group order or inventory mismatch: {tuple(groups)}")
expected_members = {
    "Final": ["Proxy", "REJECT"],
    "Proxy": ["AllServer", "NodePool", *REGIONS],
    "ApplePush": ["Proxy", "DIRECT"],
    "AdBlock": ["REJECT", "REJECT-DROP", "DIRECT"],
    "Security": ["REJECT", "REJECT-DROP", "DIRECT"],
    "UDP": ["Proxy", "NodePool", "REJECT", "DIRECT"],
    "Domestic": ["DIRECT", "Proxy"],
}
for name, expected in expected_members.items():
    if group_members(groups, name) != expected:
        fail(f"{name} member order changed: {group_members(groups, name)}")

for name in GROUP_ORDER:
    parts = group_parts(groups, name)
    expected_mode = "fallback" if name == "ApplePush" else "smart" if name in {"AllServer", *REGIONS} else "select"
    if parts[0] != expected_mode:
        fail(f"{name} must use {expected_mode}, got {parts[0]}")
    expected_hidden = "hidden=1" if name == "ApplePush" else "hidden=0"
    if expected_hidden not in parts:
        fail(f"{name} visibility must remain {expected_hidden}")
    if any(part.startswith("policy-path=") for part in parts) != (name == "NodePool"):
        fail(f"only NodePool may own policy-path: {name}")
    if "include-all-proxies=true" in parts or "include-all-proxies=1" in parts:
        fail(f"{name} bypasses the explicit NodePool architecture")

apple_push = group_parts(groups, "ApplePush")
require_options(apple_push, "ApplePush", ("interval=60", "evaluate-before-use=true", "no-alert=0", "hidden=1"))

node_pool = group_parts(groups, "NodePool")
if group_members(groups, "NodePool") != ["Fail-Closed"]:
    fail("NodePool must contain only Fail-Closed before imported nodes")
require_options(node_pool, "NodePool", (
    f"policy-path={PLACEHOLDER}", "update-interval=3600", "no-alert=0", "hidden=0", "include-all-proxies=0",
))
if any(part.startswith(("interval=", "tolerance=", "evaluate-before-use=", "timeout=")) for part in node_pool):
    fail("manual NodePool must not run automatic latency tests")

for name in ("AllServer", *REGIONS):
    parts = group_parts(groups, name)
    if group_members(groups, name) != ["Fail-Closed"]:
        fail(f"{name} may declare only Fail-Closed before importing NodePool")
    require_options(parts, name, (
        "evaluate-before-use=true", "no-alert=0", "hidden=0", "include-all-proxies=0", "include-other-group=NodePool",
    ))
    if any(part.startswith(("policy-path=", "interval=", "tolerance=", "timeout=")) for part in parts):
        fail(f"{name} contains an option that is invalid or meaningless for Smart")
for name in REGIONS:
    patterns = [part.split("=", 1)[1] for part in group_parts(groups, name) if part.startswith("policy-regex-filter=")]
    if len(patterns) != 1:
        fail(f"{name} must have exactly one regional regex")
    try:
        re.compile(patterns[0])
    except re.error as exc:
        fail(f"{name} has an invalid regional regex: {exc}")

service_groups = set(GROUP_ORDER) - {
    "Final", "Proxy", "ApplePush", "AdBlock", "Security", "UDP", "Domestic",
    "NodePool", "AllServer", *REGIONS,
}
for name in service_groups:
    members = group_members(groups, name)
    if name == "Apple":
        if members[:2] != ["DIRECT", "Proxy"]:
            fail("Apple must retain the DIRECT default and Proxy fallback")
    elif not members or members[0] != "Proxy" or "DIRECT" in members:
        fail(f"{name} must default to Proxy and cannot expose DIRECT")

# Resolve explicit and included policy references, then reject cycles.
builtins = {"DIRECT", "REJECT", "REJECT-DROP", "Fail-Closed"}
graph: dict[str, list[str]] = {name: [] for name in groups}
for name in GROUP_ORDER:
    unknown = [member for member in group_members(groups, name) if member not in groups and member not in builtins]
    if unknown:
        fail(f"{name} references undefined policies: {unknown}")
    graph[name].extend(member for member in group_members(groups, name) if member in groups)
    for part in group_parts(groups, name):
        if part.startswith("include-other-group="):
            include = part.split("=", 1)[1].strip('"')
            for target in (item.strip() for item in include.split(",")):
                if target not in groups:
                    fail(f"{name} includes undefined policy group: {target}")
                graph[name].append(target)
visiting: set[str] = set()
visited: set[str] = set()


def visit(name: str) -> None:
    if name in visiting:
        fail(f"policy group cycle detected at {name}")
    if name in visited:
        return
    visiting.add(name)
    for child in graph[name]:
        visit(child)
    visiting.remove(name)
    visited.add(name)


for group in groups:
    visit(group)

if text.count(PLACEHOLDER) != 1 or text.count("policy-path=") != 1:
    fail("public build must contain exactly one safe NodePool subscription placeholder")
for marker in ("access-token=", "authorization=", "token=", "password="):
    if marker in text.lower():
        fail(f"possible published secret marker: {marker}")

rules = active(sections["Rule"])
if len(rules) != 130:
    fail(f"active rule count changed: {len(rules)}")
if rules[-1] != "FINAL,Final,dns-failed" or rules.count("FINAL,Final,dns-failed") != 1:
    fail("FINAL must appear exactly once as the last rule")
if len(rules) != len(set(rules)):
    fail("duplicate active rules detected")

external = [rule for rule in rules if rule.startswith(("RULE-SET,", "DOMAIN-SET,"))]
if external != expected_remote_order():
    fail("runtime resource inventory or relative order changed")
if len(external) != 33:
    fail("R13.3 must contain 30 pinned and 3 dynamic runtime resources")
if sum(REMOTE_BASE in line for line in external) != 30:
    fail("all 30 original immutable repository resources must remain present")
if sum(str(item["url"]) in line for item in DYNAMIC_RULES for line in external) != 3:
    fail("the exact three reviewed dynamic resources must remain present")
if any(marker in text for marker in ("raw.githubusercontent.com", "@main/Rules/", "reject_extra.conf")):
    fail("unreviewed or mutable runtime source leaked into Surge.conf")

phishing, dynamic_ads, dynamic_domestic = (dynamic_line(item) for item in DYNAMIC_RULES)
pegasus = repository_line("DOMAIN-SET", "Pegasus.list", "Security")
ads = repository_line("RULE-SET", "Ads.list", "AdBlock")
security_rules = [rule for rule in rules if len(rule.split(",")) > 2 and rule.split(",")[2].strip() == "Security"]
adblock_rules = [rule for rule in rules if len(rule.split(",")) > 2 and rule.split(",")[2].strip() == "AdBlock"]
if security_rules != [phishing, pegasus]:
    fail("Security must contain maintained phishing first and pinned Pegasus second")
if adblock_rules != [ads, dynamic_ads]:
    fail("AdBlock must contain pinned Ads first and maintained base Ads second")
if any(
    rule.endswith((",Security", ",AdBlock"))
    and not rule.startswith(("RULE-SET,", "DOMAIN-SET,"))
    for rule in rules
):
    fail("embedded Security or AdBlock rule content is forbidden")

allowed_policies = set(groups) | builtins
supported = {
    "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-WILDCARD", "RULE-SET", "DOMAIN-SET",
    "IP-CIDR", "IP-CIDR6", "GEOIP", "DEST-PORT", "PROTOCOL", "FINAL",
}
for rule in rules:
    fields = [field.strip() for field in rule.split(",")]
    rule_type = fields[0]
    if rule_type not in supported:
        fail(f"unsupported active profile rule type: {rule_type}")
    policy = fields[1] if rule_type == "FINAL" else fields[2] if len(fields) >= 3 else ""
    if policy not in allowed_policies:
        fail(f"undefined policy {policy!r} in rule: {rule}")
    if rule_type in {"IP-CIDR", "IP-CIDR6"}:
        try:
            network = ipaddress.ip_network(fields[1], strict=False)
        except ValueError as exc:
            fail(f"invalid network {fields[1]!r}: {exc}")
        if (rule_type == "IP-CIDR") != (network.version == 4) or "no-resolve" not in fields[3:]:
            fail(f"CIDR family or no-resolve mismatch: {rule}")


def position(rule: str) -> int:
    try:
        return rules.index(rule)
    except ValueError:
        fail(f"required rule missing: {rule}")
        return -1


captive = position("DOMAIN,captive.apple.com,DIRECT")
stun = position("PROTOCOL,STUN,UDP")
dns_ports = [position(f"DEST-PORT,{port},REJECT") for port in (53, 853, 8853)]
domestic_dns = [position(rule) for rule in DOMESTIC_DNS_RULES]
bootstrap = position("DOMAIN,configuration.ls.apple.com,DIRECT")
diagnostics = [position(f"DOMAIN-SUFFIX,{domain},Proxy") for domain in (
    "net.coffee", "ippure.com", "browserleaks.net", "surfsharkdns.com",
    "fastly-analytics.com", "icanhazip.com", "ipinfo.io", "ipapi.co", "ipip.net",
)]
diagnostic_ip = position("IP-CIDR,1.1.1.1/32,Proxy,no-resolve")
foreign_dns = [position(rule) for rule in FOREIGN_DNS_RULES]
if rules[stun + 1:min(dns_ports)] != list(DOMESTIC_DNS_RULES):
    fail("the reviewed mainland resolver block must be contiguous between STUN and DNS-port rejects")
if rules[min(foreign_dns):max(foreign_dns) + 1] != list(FOREIGN_DNS_RULES):
    fail("the reviewed foreign application DNS block changed or was reordered")
old_domestic_proxy_rules = {rule.rsplit(",", 1)[0] + ",Proxy" for rule in DOMESTIC_DNS_RULES}
if old_domestic_proxy_rules & set(rules):
    fail("a reviewed mainland resolver regressed to the Proxy policy")
if not (
    captive < stun < min(domestic_dns) <= max(domestic_dns) < min(dns_ports)
    < bootstrap < min(diagnostics) <= max(diagnostics) < diagnostic_ip
    < min(foreign_dns) <= max(foreign_dns) < position(phishing) < position(pegasus)
):
    fail("captive, STUN, DNS, diagnostics, phishing, or Pegasus precedence changed")

ordered_pairs = (
    (pegasus, repository_line("RULE-SET", "APNs.list", "ApplePush")),
    ("DOMAIN,hls-amt.itunes.apple.com,Streaming", repository_line("RULE-SET", "AppleCN.list", "Apple")),
    (repository_line("RULE-SET", "AppleCN.list", "Apple"), repository_line("RULE-SET", "WeChat.list", "Domestic")),
    (repository_line("RULE-SET", "Direct.list", "Domestic"), ads),
    (ads, dynamic_ads),
    (dynamic_ads, repository_line("RULE-SET", "ChatGPT.list", "ChatGPT")),
    ("DOMAIN,yt3.ggpht.com,YouTube", repository_line("RULE-SET", "YouTube.list", "YouTube")),
    ("DOMAIN-SUFFIX,viu.now.com,Streaming", repository_line("RULE-SET", "HBO.list", "HBO")),
    (repository_line("RULE-SET", "BiliBiliIntl.list", "Streaming"), repository_line("RULE-SET", "BiliBili.list", "Domestic")),
    ("DOMAIN,login.live.com,Microsoft", repository_line("RULE-SET", "Game.list", "Games")),
    ("IP-CIDR,35.192.0.0/12,Proxy,no-resolve", repository_line("RULE-SET", "Game.list", "Games")),
    (repository_line("RULE-SET", "Game.list", "Games"), repository_line("RULE-SET", "OneDrive.list", "Microsoft")),
    (repository_line("RULE-SET", "OneDrive.list", "Microsoft"), repository_line("RULE-SET", "Microsoft.list", "Microsoft")),
    (repository_line("RULE-SET", "Microsoft.list", "Microsoft"), "DOMAIN-SUFFIX,alibabausercontent.com,Domestic"),
    ("DOMAIN-SUFFIX,volcengine.com,Domestic", dynamic_domestic),
    (dynamic_domestic, repository_line("DOMAIN-SET", "China.list", "Domestic")),
    (repository_line("DOMAIN-SET", "China.list", "Domestic"), repository_line("DOMAIN-SET", "Global.list", "Proxy")),
    (repository_line("DOMAIN-SET", "Global.list", "Proxy"), DOMESTIC_GEOIP_RULE),
)
for before, after in ordered_pairs:
    if position(before) >= position(after):
        fail(f"precedence regression: {before} must precede {after}")

if "DOMAIN-SUFFIX,ls.apple.com,DIRECT" in rules:
    fail("broad ls.apple.com DIRECT bypass is forbidden")
for domain in (
    "alibabausercontent.com", "aliyuncs.com", "bcebos.com", "coding.net", "gitee.io",
    "jdcloud.com", "myqcloud.com", "qcloudimg.com", "qiniu.com", "tencentcs.com",
    "volccdn.com", "volcengine.com",
):
    position(f"DOMAIN-SUFFIX,{domain},Domestic")
if rules[-4:] != [
    DOMESTIC_GEOIP_RULE,
    "IP-CIDR,0.0.0.0/0,Proxy,no-resolve",
    "IP-CIDR6,::/0,Proxy,no-resolve",
    "FINAL,Final,dns-failed",
]:
    fail("Domestic GEOIP and public IPv4/IPv6 fail-closed catchalls must immediately precede FINAL")

if PROFILE == (ROOT / "Surge.conf").resolve():
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if lock.get("schema") != 17 or lock.get("mode") != "repository-plus-reviewed-dynamic-no-embedded-content":
        fail("runtime lock schema or mode mismatch")
    if lock.get("profile") != PROFILE_NAME:
        fail("runtime lock profile name mismatch")
    if lock.get("profile_sha256") != hashlib.sha256(payload).hexdigest():
        fail("runtime lock profile SHA-256 is stale")
    if lock.get("profile_lines") != len(text.splitlines()) or lock.get("active_rules") != len(rules):
        fail("runtime lock profile counts are stale")

print(
    f"PASS R13.3 groups={len(groups)} rules={len(rules)} runtime_resources={len(external)} "
    "immutable_resources=30 dynamic_resources=3 embedded_rule_contents=0 "
    f"sha256={hashlib.sha256(payload).hexdigest()}"
)
