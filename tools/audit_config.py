#!/usr/bin/env python3
"""Audit the complete Surge iOS Privacy + Push R13.23 profile."""

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
    SURGE_DNS_PROTOCOL_RULES,
    expected_remote_order,
    repository_line,
    validate_remote_profile,
)


ROOT = Path(__file__).resolve().parent.parent
READY_MODE = "--ready" in sys.argv[1:]
POSITIONAL = [argument for argument in sys.argv[1:] if not argument.startswith("--")]
if len(POSITIONAL) > 1 or any(argument != "--ready" for argument in sys.argv[1:] if argument.startswith("--")):
    raise SystemExit("usage: audit_config.py [PROFILE] [--ready]")
PROFILE = Path(POSITIONAL[0]).resolve() if POSITIONAL else ROOT / "Surge.conf"
LOCK = ROOT / "Rules" / "r10.lock.json"
SUBSCRIPTION_PLACEHOLDER = "https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL"
GROUP_ORDER = (
    "Final", "Proxy", "ApplePush", "AdBlock", "Security", "UDP", "Domestic",
    "ChatGPT", "Claude", "Gemini", "GitHub",
    "YouTube", "NETFLIX", "Disney+", "HBO", "PrimeVideo", "Emby", "TikTok",
    "Bahamut", "Spotify", "Streaming", "Telegram", "X", "Apple", "Google",
    "Microsoft", "Games", "桔子", "NodePool", "Auto",
    "HongKong-Nodes", "TaiWan-Nodes", "Japan-Nodes", "Singapore-Nodes", "America-Nodes",
    "HongKong", "TaiWan", "Japan", "Singapore", "America",
)
SERVICE_GROUPS = (
    "ChatGPT", "Claude", "Gemini", "GitHub", "YouTube", "NETFLIX", "Disney+",
    "HBO", "PrimeVideo", "Emby", "TikTok", "Bahamut", "Spotify", "Streaming",
    "Telegram", "X", "Apple", "Google", "Microsoft", "Games",
)
SERVICE_MEMBERS = {
    "ChatGPT": ["Proxy", "America", "Japan", "Singapore", "HongKong", "TaiWan", "Auto"],
    "Claude": ["Proxy", "America", "Japan", "Singapore", "HongKong", "TaiWan", "Auto"],
    "Gemini": ["Proxy", "America", "Japan", "Singapore", "HongKong", "TaiWan", "Auto"],
    "GitHub": ["Proxy", "HongKong", "Japan", "Singapore", "America", "Auto"],
    "YouTube": ["Proxy", "HongKong", "TaiWan", "Japan", "Singapore", "America", "Auto"],
    "NETFLIX": ["Proxy", "HongKong", "TaiWan", "Japan", "Singapore", "America", "Auto"],
    "Disney+": ["Proxy", "HongKong", "TaiWan", "Japan", "Singapore", "America", "Auto"],
    "HBO": ["Proxy", "America", "Singapore", "Japan", "HongKong", "TaiWan", "Auto"],
    "PrimeVideo": ["Proxy", "America", "Japan", "Singapore", "HongKong", "TaiWan", "Auto"],
    "Emby": ["Proxy", "HongKong", "TaiWan", "Japan", "Singapore", "America", "Auto"],
    "TikTok": ["Proxy", "HongKong", "TaiWan", "Japan", "Singapore", "America", "Auto"],
    "Bahamut": ["TaiWan", "Proxy", "HongKong", "Japan", "Auto"],
    "Spotify": ["Proxy", "HongKong", "TaiWan", "Japan", "Singapore", "America", "Auto"],
    "Streaming": ["Proxy", "HongKong", "TaiWan", "Japan", "Singapore", "America", "Auto"],
    "Telegram": ["Proxy", "HongKong", "TaiWan", "Japan", "Singapore", "America", "Auto"],
    "X": ["Proxy", "HongKong", "TaiWan", "Japan", "Singapore", "America", "Auto"],
    "Apple": ["DIRECT", "Proxy", "HongKong", "TaiWan", "Japan", "Singapore", "America", "Auto"],
    "Google": ["Proxy", "HongKong", "TaiWan", "Japan", "Singapore", "America", "Auto"],
    "Microsoft": ["Proxy", "HongKong", "TaiWan", "Japan", "Singapore", "America", "Auto"],
    "Games": ["Proxy", "HongKong", "TaiWan", "Japan", "Singapore", "America", "Auto"],
}
REGIONS = ("HongKong", "TaiWan", "Japan", "Singapore", "America")
VISIBLE_SELECT_OPTIONS: tuple[str, ...] = ()


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
    """Split a group line while preserving commas inside quoted option values."""

    parts: list[str] = []
    current: list[str] = []
    quoted = False
    escaped = False
    for character in groups[name]:
        if escaped:
            current.append(character)
            escaped = False
        elif character == "\\" and quoted:
            current.append(character)
            escaped = True
        elif character == '"':
            current.append(character)
            quoted = not quoted
        elif character == "," and not quoted:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    if quoted or escaped:
        fail(f"{name} contains an unterminated quoted option")
    parts.append("".join(current).strip())
    return parts


def group_members(groups: dict[str, str], name: str) -> list[str]:
    return [part for part in group_parts(groups, name)[1:] if "=" not in part]


def included_groups(groups: dict[str, str], name: str) -> list[str]:
    values = [
        part.split("=", 1)[1]
        for part in group_parts(groups, name)[1:]
        if part.startswith("include-other-group=")
    ]
    if len(values) > 1:
        fail(f"{name} contains duplicate include-other-group options")
    if not values:
        return []
    value = values[0]
    if value.startswith('"') or value.endswith('"'):
        if len(value) < 2 or not (value.startswith('"') and value.endswith('"')):
            fail(f"{name} contains malformed include-other-group quoting")
        value = value[1:-1]
    names = [item.strip() for item in value.split(",")]
    if not names or any(not item for item in names) or len(names) != len(set(names)):
        fail(f"{name} contains an invalid include-other-group list")
    return names


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
    f"# {PROFILE_NAME}",
    "# 作者 .ᐣ | https://t.me/shenjlngbIng",
    "# 仓库 https://github.com/shenjlngbIng/surge",
    "# 更新 2026.09.08 | Surge iOS 5.14.6+，建议 5.21.0+ | 规则模式",
    "# 29 份外置规则；仅替换 桔子 的订阅地址，勿公开凭据。",
]
if text.splitlines()[:len(expected_header)] != expected_header:
    fail("profile attribution, version, snapshot or token warning changed")
if not re.fullmatch(r"[0-9a-f]{40}", RELEASE_REF):
    fail("runtime snapshot must be a full lowercase Git SHA")
if text.count("policy-path=") != 1:
    fail("exactly one subscription policy-path is required")
if "#!include" in text:
    fail("the simple profile must not require a linked configuration")
for marker in ("/surge/main/Rules/", "cdn.jsdelivr.net/gh/", "reject_phishing.conf", "/domainset/reject.conf"):
    if marker in text:
        fail(f"mutable or mobile-heavy runtime source is forbidden: {marker}")

sections = parse(text)
if list(sections) != ["General", "Host", "Proxy", "Proxy Group", "Rule"]:
    fail(f"section order or inventory mismatch: {list(sections)}")
general = key_values(sections["General"], "General")
expected_general = {
    "loglevel": "notify",
    "internet-test-url": "http://connectivitycheck.platform.hicloud.com/generate_204",
    "proxy-test-url": "http://cp.cloudflare.com/generate_204",
    "test-timeout": "5",
    "proxy-test-udp": "apple.com@1.1.1.1",
    "ipv6": "true",
    "ipv6-vif": "auto",
    "compatibility-mode": "3",
    "include-all-networks": "true",
    "include-local-networks": "false",
    "include-apns": "true",
    "include-cellular-services": "false",
    "icmp-forwarding": "false",
    "always-real-ip": "<simple-hostname>, *.local, *.cmpassport.com, id6.me, open.e.189.cn, mdn.open.wo.cn, opencloud.wostore.cn, auth.wosms.cn, *.10099.com.cn, *.srv.nintendo.net, *.stun.playstation.net, xbox.*.microsoft.com, *.xboxlive.com",
    "skip-proxy": "192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, localhost, *.local, ::1/128, fc00::/7, fe80::/10",
    "exclude-simple-hostnames": "true",
    "always-raw-tcp-hosts": "149.154.*, 91.108.*, *.push.apple.com:443, *push-apple.com.akadns.net:443, *.apple.com.edgekey.net:443",
    "dns-server": "223.5.5.5, 223.6.6.6, 2400:3200::1, 2400:3200:baba::1",
    "encrypted-dns-server": "https://dns.alidns.com/dns-query, https://doh.pub/dns-query",
    "encrypted-dns-follow-outbound-mode": "false",
    "encrypted-dns-skip-cert-verification": "false",
    "hijack-dns": "*:53",
    "allow-dns-svcb": "false",
    "use-local-host-item-for-proxy": "false",
    "allow-wifi-access": "false",
    "allow-hotspot-access": "false",
    "udp-policy-not-supported-behaviour": "REJECT",
    "block-quic": "per-policy",
}
for key, value in expected_general.items():
    if general.get(key) != value:
        fail(f"[General] invariant changed: {key}")
if set(general) != set(expected_general):
    fail(f"[General] key inventory changed: {sorted(set(general) ^ set(expected_general))}")

hosts = key_values(sections["Host"], "Host")
if hosts != {
    "sub.store": "127.0.0.1",
    "dns.alidns.com": "223.5.5.5, 223.6.6.6, 2400:3200::1, 2400:3200:baba::1",
}:
    fail("Host bootstrap or fail-closed Sub-Store mapping changed")

proxies = key_values(sections["Proxy"], "Proxy")
if proxies != {"Fail-Closed": "http, 127.0.0.1, 1, no-error-alert=true"}:
    fail("the only local proxy must be the unavailable Fail-Closed guard")
proxy_includes = [
    line.strip() for line in sections["Proxy"]
    if line.strip().startswith("#!include")
]
if proxy_includes:
    fail("[Proxy] must not use detached or remote includes")

groups = key_values(sections["Proxy Group"], "Proxy Group")
if tuple(groups) != GROUP_ORDER or len(groups) != 40:
    fail(f"policy group order or count mismatch: {tuple(groups)}")
if "AllServer" in groups:
    fail("retired duplicate automatic group returned")
for name in groups:
    options = [part for part in group_parts(groups, name)[1:] if "=" in part]
    option_keys = [part.split("=", 1)[0] for part in options]
    if len(option_keys) != len(set(option_keys)):
        fail(f"{name} contains duplicate policy-group options")
    if set(options) & {"no-alert=0", "hidden=0", "include-all-proxies=0"}:
        fail(f"{name} repeats an omitted default option")

if group_parts(groups, "Final")[0] != "select" or group_members(groups, "Final") != ["Proxy", "DIRECT"]:
    fail("Final policy changed")
require_exact_options(group_parts(groups, "Final"), "Final", VISIBLE_SELECT_OPTIONS)

proxy_parts = group_parts(groups, "Proxy")
if proxy_parts[0] != "select" or group_members(groups, "Proxy") != ["Auto", "NodePool", *REGIONS]:
    fail("Proxy must expose Auto, NodePool and the five visible region groups")
require_exact_options(proxy_parts, "Proxy", VISIBLE_SELECT_OPTIONS)

source = group_parts(groups, "桔子")
if source[0] != "select" or group_members(groups, "桔子") != ["REJECT"]:
    fail("桔子 must contain a native REJECT guard and imported policies")
policy_paths = [part for part in source[1:] if part.startswith("policy-path=")]
if len(policy_paths) != 1:
    fail("桔子 must contain exactly one policy-path")
if READY_MODE:
    subscription = policy_paths[0].split("=", 1)[1]
    if not subscription.startswith("https://") or "example.invalid" in subscription:
        fail("ready profile must contain one real HTTPS subscription URL")
elif policy_paths[0] != f"policy-path={SUBSCRIPTION_PLACEHOLDER}":
    fail("public profile must contain the reviewed subscription placeholder")
require_exact_options(source, "桔子", (
    policy_paths[0], "update-interval=3600", 'external-policy-modifier="udp-relay=true"',
    "hidden=1",
))
node_pool = group_parts(groups, "NodePool")
if node_pool[0] != "select" or group_members(groups, "NodePool") != ["Auto"]:
    fail("manual NodePool must default to guarded Auto")
require_exact_options(node_pool, "NodePool", (
    *VISIBLE_SELECT_OPTIONS, "include-other-group=桔子", "policy-regex-filter=^(?!REJECT$).+",
))
auto = group_parts(groups, "Auto")
if auto[0] != "smart" or group_members(groups, "Auto") != ["Fail-Closed"] or included_groups(groups, "Auto") != ["桔子"]:
    fail("Auto must retain a proxy-policy guard and include the 桔子 members")
require_exact_options(auto, "Auto", (
    "evaluate-before-use=true",
    "include-other-group=桔子",
))
for name, members in {
    "AdBlock": ["REJECT", "REJECT-DROP", "DIRECT"],
    "Security": ["REJECT", "REJECT-DROP", "DIRECT"],
    "UDP": ["Proxy", "NodePool", "REJECT", "DIRECT"],
    "Domestic": ["DIRECT", "Proxy"],
}.items():
    if group_parts(groups, name)[0] != "select" or group_members(groups, name) != members:
        fail(f"{name} control defaults or choices changed")
    require_exact_options(group_parts(groups, name), name, ("hidden=1",))

if group_parts(groups, "ApplePush")[0] != "fallback" or group_members(groups, "ApplePush") != ["Proxy", "Auto", "DIRECT"]:
    fail("ApplePush fallback exception changed")
require_exact_options(group_parts(groups, "ApplePush"), "ApplePush", (
    "interval=60", "evaluate-before-use=true", "hidden=1",
))

for name in SERVICE_GROUPS:
    parts = group_parts(groups, name)
    if parts[0] != "select" or group_members(groups, name) != SERVICE_MEMBERS[name]:
        fail(f"{name} visible service policy membership changed")
    require_exact_options(parts, name, VISIBLE_SELECT_OPTIONS)

for name in REGIONS:
    source = f"{name}-Nodes"
    source_parts = group_parts(groups, source)
    if source_parts[0] != "url-test" or group_members(groups, source) != ["REJECT"]:
        fail(f"{source} must contain a REJECT guard plus filtered 桔子 policies")
    require_options(source_parts, source, (
        "interval=600", "tolerance=100", "evaluate-before-use=true",
        "hidden=1", "include-other-group=桔子",
    ))
    if not any(part.startswith("policy-regex-filter=") for part in source_parts):
        fail(f"{source} missing regional policy filter")
    visible = group_parts(groups, name)
    if visible[0] != "fallback" or group_members(groups, name) != [source, "Auto"]:
        fail(f"{name} must fall back from its strict source to Auto")
    require_exact_options(visible, name, (
        "interval=600", "evaluate-before-use=true",
    ))

automatic = {
    name: group_parts(groups, name)[0]
    for name in groups
    if group_parts(groups, name)[0] in {"smart", "url-test", "load-balance"}
}
expected_automatic = {"Auto": "smart", **{f"{name}-Nodes": "url-test" for name in REGIONS}}
if automatic != expected_automatic:
    fail(f"automatic node-source inventory changed: {automatic}")

# Validate group references and reject cycles.
builtins = {"DIRECT", "REJECT", "REJECT-DROP"}
for name in groups:
    unknown = [
        member for member in [*group_members(groups, name), *included_groups(groups, name)]
        if member not in groups and member not in proxies and member not in builtins
    ]
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
    for member in [*group_members(groups, name), *included_groups(groups, name)]:
        if member in groups:
            visit(member)
    visiting.remove(name)
    visited.add(name)
for group in groups:
    visit(group)

expanded_rules = active(sections["Rule"])
rules = active(parse(validate_remote_profile(text))["Rule"])
if len(rules) != 142 or rules[-1] != "FINAL,Final,dns-failed" or rules.count("FINAL,Final,dns-failed") != 1:
    fail("reviewed rule count or unique FINAL changed")
external = [rule for rule in rules if rule.startswith(("RULE-SET,", "DOMAIN-SET,"))]
if external != expected_remote_order():
    fail("runtime resource order differs from reviewed inventory")
if len(external) != 29:
    fail("runtime resource count changed")

for kind, filename, _label, policy in REPOSITORY_RULES:
    line = repository_line(kind, filename, policy)
    if rules.count(line) != 1:
        fail(f"immutable resource line changed: {filename}")
    if f"/{RELEASE_REF}/Rules/{filename}" not in line:
        fail(f"immutable resource is not pinned: {filename}")

if DYNAMIC_RULES:
    fail("R13.23 must not load mutable runtime supplements")

def index(line: str) -> int:
    if rules.count(line) != 1:
        fail(f"required rule is missing or duplicated: {line}")
    return rules.index(line)

guard_start = index(FUNCTIONAL_GUARDS[0])
if rules[guard_start:guard_start + len(FUNCTIONAL_GUARDS)] != list(FUNCTIONAL_GUARDS):
    fail("functional guards must be complete and contiguous")
ads_line = repository_line("RULE-SET", "Ads.list", "AdBlock")
if any(index(line) >= index(ads_line) for line in FUNCTIONAL_GUARDS):
    fail("functional guard appears after Ads")
intl_start = index(RETIRED_BILIBILI_INTL_GUARDS[0])
if rules[intl_start:intl_start + len(RETIRED_BILIBILI_INTL_GUARDS)] != list(RETIRED_BILIBILI_INTL_GUARDS):
    fail("retired BiliBili international compatibility guards changed")
if index(RETIRED_BILIBILI_INTL_GUARDS[0]) >= index(repository_line("RULE-SET", "BiliBili.list", "DIRECT")):
    fail("international compatibility guard must precede domestic BiliBili parent suffixes")

stun = index("PROTOCOL,STUN,UDP")
resource_transport = index("DOMAIN,raw.githubusercontent.com,Auto")
index("DOMAIN-SUFFIX,jsdelivr.net,Proxy")
if SURGE_DNS_PROTOCOL_RULES or any(rule.startswith(tuple(f"PROTOCOL,{kind}," for kind in ("DOH", "DOH3", "DOQ", "DOT", "DNS"))) for rule in rules):
    fail("inactive own-DNS protocol rules must not return")
domestic_dns_start = index(DOMESTIC_DNS_RULES[0])
if rules[domestic_dns_start:domestic_dns_start + len(DOMESTIC_DNS_RULES)] != list(DOMESTIC_DNS_RULES):
    fail("mainland application DNS proxy block changed")
port_start = index("DEST-PORT,53,REJECT")
foreign_start = index(FOREIGN_DNS_RULES[0])
encrypted_ports = ["DEST-PORT,853,REJECT", "DEST-PORT,8853,REJECT"]
encrypted_start = index(encrypted_ports[0])
if not stun < resource_transport < domestic_dns_start < port_start < foreign_start < encrypted_start:
    fail("DNS exceptions must follow plaintext rejection and precede encrypted-port rejection")
if rules[foreign_start:foreign_start + len(FOREIGN_DNS_RULES)] != list(FOREIGN_DNS_RULES):
    fail("foreign application DNS block changed")
if foreign_start != port_start + 1 or encrypted_start != foreign_start + len(FOREIGN_DNS_RULES):
    fail("unexpected rule inserted into the reviewed DNS-port boundary")
if rules[encrypted_start:encrypted_start + 2] != encrypted_ports:
    fail("encrypted DNS port rejection block changed")

diagnostics = (
    "DOMAIN-SUFFIX,net.coffee,Proxy", "DOMAIN-SUFFIX,ippure.com,Proxy",
    "DOMAIN-SUFFIX,browserleaks.net,Proxy", "DOMAIN-SUFFIX,surfsharkdns.com,Proxy",
    "DOMAIN-SUFFIX,fastly-analytics.com,Proxy", "DOMAIN-SUFFIX,icanhazip.com,Proxy",
    "DOMAIN-SUFFIX,ipinfo.io,Proxy", "DOMAIN-SUFFIX,ipapi.co,Proxy",
    "DOMAIN-SUFFIX,ipip.net,Proxy", "IP-CIDR,1.1.1.1/32,Proxy,no-resolve",
)
for line in diagnostics:
    index(line)
diagnostics_start = index(diagnostics[0])
if rules[diagnostics_start:diagnostics_start + len(diagnostics)] != list(diagnostics):
    fail("public egress diagnostic block changed")
if not foreign_start < encrypted_start < diagnostics_start < index(ads_line):
    fail("public egress diagnostic block order changed")

if index(repository_line("RULE-SET", "APNs.list", "ApplePush")) >= index(repository_line("RULE-SET", "AppleCN.list", "Apple")):
    fail("APNs must precede ordinary Apple routing")

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
if not shared_start < index(repository_line("DOMAIN-SET", "China.list", "Domestic")):
    fail("domestic fixed/snapshot precedence changed")

tail = [
    DOMESTIC_GEOIP_RULE,
    "PROTOCOL,UDP,UDP",
    "IP-CIDR,0.0.0.0/0,Proxy,no-resolve",
    "IP-CIDR6,::/0,Proxy,no-resolve",
    "FINAL,Final,dns-failed",
]
if rules[-5:] != tail:
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

valid_policies = set(groups) | set(proxies) | {"DIRECT", "REJECT", "REJECT-DROP"}
for rule in expanded_rules:
    fields = [field.strip() for field in rule.split(",")]
    policy = fields[1] if fields[0] == "FINAL" else fields[2]
    if policy not in valid_policies:
        fail(f"rule references unknown policy: {rule}")

if PROFILE == ROOT / "Surge.conf":
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    expected_counts = (142, 29, 29, 0, 29)
    actual_counts = tuple(lock.get(key) for key in (
        "active_rules", "runtime_resources", "immutable_repository_resources",
        "dynamic_runtime_resources", "local_rule_files",
    ))
    if lock.get("schema") != 35 or lock.get("mode") != "remote-rules-guarded-single-subscription":
        fail("runtime lock schema or mode mismatch")
    if actual_counts != expected_counts or lock.get("profile") != PROFILE_NAME:
        fail("runtime lock profile or counts mismatch")
    if lock.get("profile_sha256") != hashlib.sha256(payload).hexdigest():
        fail("runtime lock profile hash is stale")

print(
    f"PASS R13.23 groups={len(groups)} rules={len(expanded_rules)} remote_rule_resources=29 "
    f"local_sources={len(REPOSITORY_RULES)} "
    f"embedded_rule_contents=0 sha256={hashlib.sha256(payload).hexdigest()}"
)
