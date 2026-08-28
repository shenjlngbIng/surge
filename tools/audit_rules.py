#!/usr/bin/env python3
"""Validate the R13.4 local rule, runtime lock and provenance inventory.

Use ``--check-dynamic`` to download and format-check the three reviewed dynamic
runtime supplements without requiring their content to remain byte-identical.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import sys
import urllib.request
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
    RULE_SNAPSHOT_TAG,
    expected_remote_order,
)


ROOT = Path(__file__).resolve().parent.parent
CHECK_DYNAMIC = "--check-dynamic" in sys.argv[1:]
positional = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
DEFAULT_RULES = ROOT / "Rules"
RULES = Path(positional[0]).resolve() if positional else DEFAULT_RULES
LOCK = RULES / "r10.lock.json"
RESOURCE_LOCK = RULES / "resources.lock.json"
SERVICE_LOCK = RULES / "upstreams.lock.json"
MAINTAINED_LOCK = RULES / "maintained_sources.lock.json"
DOMAIN_RE = re.compile(
    r"(?=.{1,253}\Z)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z",
    re.IGNORECASE,
)
RULE_TYPES = {
    "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-WILDCARD",
    "USER-AGENT", "URL-REGEX", "AND", "OR", "NOT", "IP-CIDR",
    "IP-CIDR6", "IP-ASN",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def active_lines(path: Path) -> list[str]:
    return [
        line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith(("#", ";", "//"))
    ]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


lock = json.loads(LOCK.read_text(encoding="utf-8"))
if lock.get("schema") != 18 or lock.get("mode") != "repository-plus-reviewed-dynamic-no-embedded-content":
    fail("runtime lock schema or mode mismatch")
if lock.get("profile") != PROFILE_NAME:
    fail("runtime lock profile mismatch")
if (lock.get("active_rules"), lock.get("runtime_resources"), lock.get("immutable_repository_resources"), lock.get("dynamic_runtime_resources"), lock.get("local_rule_files")) != (130, 33, 30, 3, 30):
    fail("runtime lock counts mismatch")

invariants = dict(lock.get("required_invariants", {}))
expected_invariants = {
    "rule_snapshot_tag": RULE_SNAPSHOT_TAG,
    "rule_snapshot_commit": RELEASE_REF,
    "runtime_resource_count": 33,
    "immutable_repository_resource_count": 30,
    "dynamic_runtime_resource_count": 3,
    "local_rule_file_count": 30,
    "embedded_rule_contents": 0,
    "hidden_function_groups": ["ApplePush", "AdBlock", "Security", "UDP", "Domestic"],
    "visible_control_groups": ["Final", "Proxy", "NodePool"],
    "public_subscription_placeholder": "https://example.invalid/REPLACE_WITH_SUB_STORE_URL",
    "loglevel": "notify",
    "apple_captive_direct": "DOMAIN,captive.apple.com,DIRECT",
    "apple_bootstrap_direct": "DOMAIN,configuration.ls.apple.com,DIRECT",
    "diagnostic_policy": "Proxy",
    "runtime_rulesets_no_resolve": True,
}
for key, expected in expected_invariants.items():
    if invariants.get(key) != expected:
        fail(f"runtime invariant mismatch: {key}")

architecture = dict(invariants.get("policy_architecture", {}))
if architecture.get("node_pool") != {
    "mode": "select", "hidden": False, "source": "policy-path",
    "fail_closed": True, "manual_default": False,
}:
    fail("NodePool architecture invariant mismatch")
if architecture.get("proxy") != {"mode": "select", "default": "AllServer"}:
    fail("Proxy default architecture invariant mismatch")
if dict(architecture.get("all_server", {})).get("mode") != "smart":
    fail("AllServer must remain Smart")
if dict(architecture.get("regions", {})).get("mode") != "smart":
    fail("regional groups must remain Smart")
if architecture.get("domestic") != {"mode": "select", "default": "DIRECT", "fallback": "Proxy", "hidden": True}:
    fail("Domestic architecture invariant mismatch")
if invariants.get("domestic_resources") != {
    "dynamic_supplement": "domestic.conf",
    "pinned_precise_set": "China.list",
    "policy": "Domestic",
    "geoip": DOMESTIC_GEOIP_RULE,
    "geoip_resolves_unmatched_domains": False,
    "unmatched_domain_fallback": "Final/Proxy",
}:
    fail("Domestic resource invariant mismatch")
if invariants.get("dns") != {
    "dns_server": "223.5.5.5, 223.6.6.6",
    "encrypted_dns_server": "https://dns.alidns.com/dns-query, https://doh.pub/dns-query",
    "follow_outbound_mode": False,
    "certificate_verification": True,
    "domestic_application_resolvers": list(DOMESTIC_DNS_RULES),
    "foreign_application_resolvers": list(FOREIGN_DNS_RULES),
    "domestic_resolver_policy": "Domestic",
    "foreign_resolver_policy": "Proxy",
    "unmatched_domains_force_local_resolution": False,
    "proxy_hostname_uses_remote_resolution": True,
    "bootstrap": {
        "dns.alidns.com": ["223.5.5.5", "223.6.6.6", "2400:3200::1"],
        "doh.pub": ["1.12.12.12", "120.53.53.53"],
    },
}:
    fail("DNS routing invariant mismatch")
if invariants.get("udp_quic") != {
    "proxy_test_udp": "apple.com@9.9.9.9",
    "unsupported_behaviour": "REJECT",
    "block_quic": "per-policy",
    "stun_policy": "UDP",
    "udp_default": "Proxy",
    "blocked_public_dns_ports": [53, 853, 8853],
}:
    fail("UDP/QUIC invariant mismatch")
if invariants.get("public_ip_literals") != {
    "china": DOMESTIC_GEOIP_RULE,
    "ipv4": "IP-CIDR,0.0.0.0/0,Proxy,no-resolve",
    "ipv6": "IP-CIDR6,::/0,Proxy,no-resolve",
}:
    fail("public IP literal invariant mismatch")

expected_sources = {
    filename: {
        "source_mode": "immutable-repository-snapshot",
        "kind": kind,
        "url": f"{REMOTE_BASE}{filename}",
        "policy": policy,
        "update_interval": -1,
    }
    for kind, filename, _label, policy in REPOSITORY_RULES
}
raw_sources = list(lock.get("remote_sources", []))
if len(raw_sources) != len(expected_sources):
    fail("expected 30 immutable repository runtime sources")
seen_remote: set[str] = set()
for raw in raw_sources:
    item = dict(raw)
    filename = str(item.get("file", ""))
    if filename in seen_remote or filename not in expected_sources:
        fail(f"duplicate or unexpected repository runtime source: {filename}")
    seen_remote.add(filename)
    for key, expected in expected_sources[filename].items():
        if item.get(key) != expected:
            fail(f"repository runtime source {filename} has incorrect {key}")
    path = RULES / filename
    if item.get("active_entries") != len(active_lines(path)) or item.get("sha256") != digest(path):
        fail(f"repository runtime metadata mismatch: {filename}")
if seen_remote != set(expected_sources):
    fail("repository runtime inventory is incomplete")

dynamic_sources = list(lock.get("dynamic_sources", []))
if len(dynamic_sources) != 3:
    fail("expected three reviewed dynamic runtime sources")
for expected, raw in zip(DYNAMIC_RULES, dynamic_sources, strict=True):
    item = dict(raw)
    for key, value in expected.items():
        if item.get(key) != value:
            fail(f"dynamic release observation mismatch for {expected['name']}: {key}")
    if item.get("source_mode") != "reviewed-dynamic-runtime" or item.get("update_interval") != 86400:
        fail(f"dynamic source control metadata mismatch: {expected['name']}")

if list(lock.get("runtime_order", [])) != expected_remote_order():
    fail("runtime order in the lock is stale")
if list(lock.get("embedded_sources", [])):
    fail("runtime lock may not declare embedded rule sources")

expected_local = set(expected_sources)
actual_local = {path.name for path in RULES.glob("*.list")}
if actual_local != expected_local or len(actual_local) != 30:
    fail(f"local rule inventory mismatch: missing={sorted(expected_local-actual_local)}, unexpected={sorted(actual_local-expected_local)}")
domain_set_files = {"Pegasus.list", "China.list", "Global.list"}
errors: list[str] = []
for filename in sorted(actual_local):
    path = RULES / filename
    rows = active_lines(path)
    if not rows:
        errors.append(f"{filename}: empty rule source")
        continue
    if len(rows) != len(set(rows)):
        errors.append(f"{filename}: duplicate active rows")
    if filename in domain_set_files:
        for row in rows:
            value = row[1:] if row.startswith(".") else row
            if "," in row or not DOMAIN_RE.fullmatch(value):
                errors.append(f"{filename}: invalid DOMAIN-SET row {row!r}")
                break
    else:
        for row in rows:
            fields = [part.strip() for part in row.split(",")]
            rule_type = fields[0].upper()
            if rule_type not in RULE_TYPES or rule_type == "PROCESS-NAME":
                errors.append(f"{filename}: unsupported rule type {rule_type}")
                break
            if rule_type in {"IP-CIDR", "IP-CIDR6"}:
                try:
                    network = ipaddress.ip_network(fields[1], strict=False)
                except (IndexError, ValueError):
                    errors.append(f"{filename}: invalid network {row!r}")
                    break
                if (rule_type == "IP-CIDR") != (network.version == 4) or "no-resolve" not in fields[2:]:
                    errors.append(f"{filename}: CIDR family or no-resolve mismatch {row!r}")
                    break
if errors:
    fail("\n".join(errors))

# In a staged ZIP the profile is the parent of Rules. Validate it when present.
profile = ROOT / "Surge.conf" if RULES == DEFAULT_RULES else RULES.parent / "Surge.conf"
if profile.is_file():
    profile_text = profile.read_text(encoding="utf-8")
    profile_rules = [
        line.strip() for line in profile_text.split("[Rule]", 1)[1].splitlines()
        if line.strip() and not line.lstrip().startswith(("#", ";", "//"))
    ]
    if lock.get("profile_sha256") != hashlib.sha256(profile.read_bytes()).hexdigest():
        fail("profile hash mismatch")
    if lock.get("profile_lines") != len(profile_text.splitlines()) or lock.get("active_rules") != len(profile_rules):
        fail("profile line or rule count mismatch")
    external = [line for line in profile_rules if line.startswith(("RULE-SET,", "DOMAIN-SET,"))]
    if external != expected_remote_order():
        fail("profile runtime references do not match the lock")
    inline = [
        line for line in profile_rules
        if line.endswith((",Security", ",AdBlock"))
        and not line.startswith(("RULE-SET,", "DOMAIN-SET,"))
    ]
    if inline:
        fail("profile contains embedded Security or AdBlock rules")

# Existing provenance locks and reviewed local curation remain byte-identical.
resource_lock = json.loads(RESOURCE_LOCK.read_text(encoding="utf-8"))
resources = list(resource_lock.get("resources", []))
if resource_lock.get("schema") != 1 or len(resources) != 1:
    fail("pinned Pegasus provenance lock is invalid")
pegasus_path = RULES / "Pegasus.list"
pegasus_meta = dict(resources[0])
if pegasus_meta.get("local_file") != "Pegasus.list" or pegasus_meta.get("active_entries") != 1438 or pegasus_meta.get("local_sha256") != digest(pegasus_path):
    fail("Pegasus provenance identity, count, or hash mismatch")

service_lock = json.loads(SERVICE_LOCK.read_text(encoding="utf-8"))
services = list(service_lock.get("services", []))
if service_lock.get("schema") != 2 or len(services) != 19:
    fail("pinned service provenance inventory is invalid")
if dict(service_lock.get("local_additions_policy", {})).get("undeclared_rows") != "forbidden":
    fail("service lock does not forbid undeclared local rows")
for raw_service in services:
    service = dict(raw_service)
    target = RULES / str(service["local_file"])
    if service.get("local_active_entries") != len(active_lines(target)) or service.get("local_sha256") != digest(target):
        fail(f"service local metadata mismatch: {target.name}")
    additions = list(service.get("add", []))
    if additions and dict(service.get("add_source", {})).get("type") != "repository-maintained-curation":
        fail(f"service local additions have no disclosure: {target.name}")

maintained_lock = json.loads(MAINTAINED_LOCK.read_text(encoding="utf-8"))
maintained_files = {
    "APNs.list", "Ads.list", "AppleCN.list", "BiliBili.list", "China.list",
    "Direct.list", "Global.list", "ProxyMedia.list", "Telegram.list", "WeChat.list",
}
maintained_items = list(maintained_lock.get("files", []))
if maintained_lock.get("schema") != 1 or len(maintained_items) != len(maintained_files):
    fail("repository-maintained source disclosure inventory is invalid")
seen_maintained: set[str] = set()
for raw_item in maintained_items:
    item = dict(raw_item)
    filename = str(item.get("file", ""))
    if filename not in maintained_files or filename in seen_maintained:
        fail(f"unexpected repository-maintained source item: {filename}")
    seen_maintained.add(filename)
    target = RULES / filename
    if item.get("active_entries") != len(active_lines(target)) or item.get("sha256") != digest(target):
        fail(f"repository-maintained metadata mismatch: {filename}")
    if not item.get("maintenance") or not item.get("license_status") or not item.get("notes"):
        fail(f"repository-maintained disclosure is incomplete: {filename}")
if seen_maintained != maintained_files:
    fail("repository-maintained source disclosure is incomplete")

apns_required = {
    "DOMAIN-SUFFIX,push.apple.com", "DOMAIN-SUFFIX,push-apple.com.akadns.net",
    "IP-CIDR,17.249.0.0/16,no-resolve", "IP-CIDR,17.252.0.0/16,no-resolve",
    "IP-CIDR,17.57.144.0/22,no-resolve", "IP-CIDR,17.188.128.0/18,no-resolve",
    "IP-CIDR,17.188.20.0/23,no-resolve", "IP-CIDR6,2620:149:a44::/48,no-resolve",
    "IP-CIDR6,2403:300:a42::/48,no-resolve", "IP-CIDR6,2403:300:a51::/48,no-resolve",
    "IP-CIDR6,2a01:b740:a42::/48,no-resolve",
}
if not apns_required <= set(active_lines(RULES / "APNs.list")):
    fail("APNs source is missing Apple-published endpoints")
telegram_required = {
    "DOMAIN-SUFFIX,t.me", "DOMAIN-SUFFIX,telegram.org",
    "IP-CIDR,149.154.160.0/20,no-resolve", "IP-CIDR,91.108.4.0/22,no-resolve",
    "IP-CIDR6,2001:b28:f23c::/48,no-resolve",
}
if not telegram_required <= set(active_lines(RULES / "Telegram.list")):
    fail("Telegram source is missing core endpoints")

bilibili_domestic = {
    "DOMAIN-SUFFIX,acgvideo.com", "DOMAIN-SUFFIX,b23.tv", "DOMAIN-SUFFIX,biliapi.com",
    "DOMAIN-SUFFIX,biliapi.net", "DOMAIN-SUFFIX,bilibili.cn", "DOMAIN-SUFFIX,bilibili.com",
    "DOMAIN-SUFFIX,bilicdn1.com", "DOMAIN-SUFFIX,bilicomics.com", "DOMAIN-SUFFIX,biligame.com",
    "DOMAIN-SUFFIX,biliimg.com", "DOMAIN-SUFFIX,bilivideo.com", "DOMAIN-SUFFIX,hdslb.com",
}
bilibili_international = {
    "DOMAIN,apiintl.biliapi.net", "DOMAIN,p-bstarstatic.akamaized.net", "DOMAIN,p.bstarstatic.com",
    "DOMAIN,upos-bstar-mirrorakam.akamaized.net", "DOMAIN,upos-bstar1-mirrorakam.akamaized.net",
    "DOMAIN-SUFFIX,bilibili.tv", "DOMAIN-SUFFIX,biliintl.com",
}
if set(active_lines(RULES / "BiliBili.list")) != bilibili_domestic:
    fail("BiliBili domestic rules differ from the reviewed set")
if set(active_lines(RULES / "BiliBiliIntl.list")) != bilibili_international:
    fail("BiliBili international rules differ from the reviewed set")

forbidden_rules = {
    "Bahamut.list": {"DOMAIN-SUFFIX,digicert.com", "DOMAIN-SUFFIX,gvt1.com", "DOMAIN-SUFFIX,hinet.net"},
    "Disney.list": {"DOMAIN-SUFFIX,adobedtm.com", "DOMAIN-SUFFIX,bam.nr-data.net", "DOMAIN-SUFFIX,braze.com", "DOMAIN-SUFFIX,cdn.optimizely.com", "DOMAIN-SUFFIX,conviva.com", "DOMAIN-SUFFIX,d9.flashtalking.com", "DOMAIN-SUFFIX,js-agent.newrelic.com"},
    "Game.list": {"DOMAIN-SUFFIX,helpshift.com"},
    "HBO.list": {"DOMAIN-SUFFIX,manifest.prod.boltdns.net", "DOMAIN-SUFFIX,players.brightcove.net"},
    "Microsoft.list": {"DOMAIN-SUFFIX,azurefd.net", "DOMAIN-SUFFIX,azureedge.net", "DOMAIN-SUFFIX,azurewebsites.net", "DOMAIN-SUFFIX,edgesuite.net", "DOMAIN-SUFFIX,helpshift.com", "DOMAIN-SUFFIX,optimizely.com", "DOMAIN-SUFFIX,windows.net"},
    "TikTok.list": {"DOMAIN-SUFFIX,snssdk.com"},
    "ProxyMedia.list": {"DOMAIN,apm-misaka.biliapi.net", "DOMAIN,cache.video.iqiyi.com"},
}
for filename, forbidden in forbidden_rules.items():
    leaked = forbidden & set(active_lines(RULES / filename))
    if leaked:
        fail(f"{filename} contains intentionally excluded rules: {sorted(leaked)}")
if any("google" in rule.lower() or "gvt1.com" in rule.lower() for rule in active_lines(RULES / "Direct.list")):
    fail("Direct.list bypasses the Google policy")
netflix_rules = set(active_lines(RULES / "Netflix.list"))
if "IP-ASN,2906,no-resolve" not in netflix_rules or any(rule.startswith(("IP-CIDR,", "IP-CIDR6,")) for rule in netflix_rules):
    fail("Netflix must use AS2906 without broad cloud CIDRs")


def fetch_dynamic(source: dict[str, object]) -> tuple[int, int, str]:
    request = urllib.request.Request(str(source["url"]), headers={"User-Agent": "Surge-R13.4-Audit/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            fail(f"dynamic source HTTP {response.status}: {source['url']}")
        data = response.read(8 * 1024 * 1024 + 1)
    if len(data) > 8 * 1024 * 1024:
        fail(f"dynamic source exceeds 8 MiB: {source['url']}")
    text = data.decode("utf-8-sig")
    rows = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith(("#", ";", "//"))]
    if not rows or len(rows) != len(set(rows)):
        fail(f"dynamic source is empty or has duplicate active rows: {source['url']}")
    if source["kind"] == "DOMAIN-SET":
        if any("," in row or any(ch.isspace() for ch in row) for row in rows):
            fail(f"invalid dynamic DOMAIN-SET row: {source['url']}")
    else:
        if any("," not in row or row.split(",", 1)[0] == "FINAL" for row in rows):
            fail(f"invalid dynamic RULE-SET row: {source['url']}")
    return len(rows), len(data), hashlib.sha256(data).hexdigest()


if CHECK_DYNAMIC:
    for source in DYNAMIC_RULES:
        entries, size, sha256 = fetch_dynamic(source)
        print(f"PASS dynamic {source['name']} entries={entries} bytes={size} sha256={sha256}")

print(
    f"PASS R13.4 runtime_sources=33 immutable_sources=30 dynamic_sources=3 "
    f"local_rule_files={len(actual_local)} rules={lock.get('active_rules')} embedded_rule_contents=0"
)
