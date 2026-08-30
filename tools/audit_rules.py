#!/usr/bin/env python3
"""Validate R13.6 rule snapshots, locks and optional online resources."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from convert_to_remote_rules import (
    DOMESTIC_DNS_RULES,
    DOMESTIC_GEOIP_RULE,
    DYNAMIC_RULES,
    EXTENDED_MATCH_RESOURCES,
    FOREIGN_DNS_RULES,
    FUNCTIONAL_GUARDS,
    PROFILE_NAME,
    RELEASE_REF,
    REMOTE_BASE,
    REPOSITORY_RULES,
    RETIRED_BILIBILI_INTL_GUARDS,
    RULE_SNAPSHOT_TAG,
    expected_remote_order,
)


ROOT = Path(__file__).resolve().parent.parent
CHECK_DYNAMIC = "--check-dynamic" in sys.argv[1:]
CHECK_RUNTIME_REMOTE = "--check-runtime-remote" in sys.argv[1:]
positional = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
if len(positional) > 1:
    raise SystemExit("usage: audit_rules.py [RULES_DIR] [--check-dynamic] [--check-runtime-remote]")
RULES = Path(positional[0]).resolve() if positional else ROOT / "Rules"
LOCK = RULES / "r10.lock.json"
RESOURCE_LOCK = RULES / "resources.lock.json"
SERVICE_LOCK = RULES / "upstreams.lock.json"
MAINTAINED_LOCK = RULES / "maintained_sources.lock.json"
DOMAIN_RE = re.compile(
    r"(?=.{1,253}\Z)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z",
    re.IGNORECASE,
)
HOST_RE = re.compile(
    r"(?=.{1,253}\Z)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)(?:\."
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*\Z",
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
    payload = path.read_bytes()
    if payload.startswith(b"\xef\xbb\xbf") or b"\r" in payload or not payload.endswith(b"\n"):
        fail(f"{path.name} must be BOM-free UTF-8, LF-only and newline-terminated")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"{path.name} is not UTF-8: {exc}")
    return [
        line.strip() for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith(("#", ";", "//"))
    ]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_rule_row(filename: str, row: str) -> None:
    parts = [part.strip() for part in row.split(",")]
    if not parts or parts[0] not in RULE_TYPES:
        fail(f"unsupported rule type in {filename}: {row}")
    kind = parts[0]
    if kind in {"DOMAIN", "DOMAIN-SUFFIX"}:
        if len(parts) != 2 or not HOST_RE.fullmatch(parts[1]):
            fail(f"invalid domain row in {filename}: {row}")
    elif kind in {"IP-CIDR", "IP-CIDR6"}:
        if len(parts) not in {2, 3} or (len(parts) == 3 and parts[2] != "no-resolve"):
            fail(f"invalid IP rule shape in {filename}: {row}")
        try:
            network = ipaddress.ip_network(parts[1], strict=False)
        except ValueError as exc:
            fail(f"invalid IP network in {filename}: {row}: {exc}")
        if (kind == "IP-CIDR") != (network.version == 4):
            fail(f"IP family mismatch in {filename}: {row}")
    elif len(parts) < 2 or not parts[1]:
        fail(f"empty rule value in {filename}: {row}")


lock = json.loads(LOCK.read_text(encoding="utf-8"))
if lock.get("schema") != 20 or lock.get("mode") != "immutable-rules-plus-domestic-dynamic":
    fail("runtime lock schema or mode mismatch")
if lock.get("profile") != PROFILE_NAME:
    fail("runtime lock profile mismatch")
counts = tuple(lock.get(key) for key in (
    "active_rules", "runtime_resources", "immutable_repository_resources",
    "dynamic_runtime_resources", "local_rule_files",
))
if counts != (142, 30, 29, 1, 29):
    fail(f"runtime lock counts mismatch: {counts}")

invariants = dict(lock.get("required_invariants", {}))
expected_invariants = {
    "rule_snapshot_tag": RULE_SNAPSHOT_TAG,
    "rule_snapshot_commit": RELEASE_REF,
    "runtime_resource_count": 30,
    "immutable_repository_resource_count": 29,
    "dynamic_runtime_resource_count": 1,
    "local_rule_file_count": 29,
    "embedded_rule_contents": 0,
    "hidden_function_groups": ["ApplePush"],
    "removed_stateful_groups": ["AdBlock", "Security", "UDP", "Domestic", "AllServer"],
    "visible_control_groups": ["Final", "Proxy", "Auto", "NodePool"],
    "public_subscription_placeholder": "https://example.invalid/REPLACE_WITH_SUB_STORE_URL",
    "loglevel": "notify",
    "fail_closed_alias": "reject",
    "mobile_dynamic_reject_sources": [],
    "functional_guards_before_ads": list(FUNCTIONAL_GUARDS),
    "extended_matching_resources": sorted(EXTENDED_MATCH_RESOURCES),
    "apple_captive_direct": "DOMAIN,captive.apple.com,DIRECT",
    "apple_bootstrap_direct": "DOMAIN,configuration.ls.apple.com,DIRECT",
    "diagnostic_policy": "Proxy",
    "runtime_rulesets_no_resolve": True,
}
for key, expected in expected_invariants.items():
    if invariants.get(key) != expected:
        fail(f"runtime invariant mismatch: {key}")

architecture = dict(invariants.get("policy_architecture", {}))
if architecture.get("automatic_empty_group_behavior") != "DIRECT/SUBSTITUTE":
    fail("automatic empty-group behavior invariant mismatch")
if architecture.get("auto") != {
    "mode": "url-test", "hidden": False, "source": "NodePool",
    "excluded_policy": "Fail-Closed", "interval": 600,
    "tolerance": 100, "evaluate_before_use": True,
}:
    fail("Auto architecture invariant mismatch")
if architecture.get("proxy") != {
    "mode": "select", "default": "Auto", "manual_fail_closed_entry": "NodePool",
}:
    fail("Proxy architecture invariant mismatch")
if architecture.get("node_pool") != {
    "mode": "select", "hidden": False, "source": "policy-path",
    "first_member": "Fail-Closed", "automatic_fallback": False,
}:
    fail("NodePool architecture invariant mismatch")
regions = dict(architecture.get("regions", {}))
if regions != {
    "mode": "url-test", "source": "NodePool", "interval": 600,
    "tolerance": 100, "evaluate_before_use": True,
    "empty_group_behavior": "DIRECT/SUBSTITUTE",
    "names": ["HongKong", "TaiWan", "Japan", "Singapore", "America"],
}:
    fail("region architecture invariant mismatch")
if invariants.get("domestic_resources") != {
    "dynamic_supplement": "domestic.conf",
    "pinned_precise_set": "China.list",
    "policy": "DIRECT",
    "geoip": DOMESTIC_GEOIP_RULE,
    "geoip_resolves_unmatched_domains": False,
    "unmatched_domain_fallback": "Final/Proxy",
}:
    fail("domestic resource invariant mismatch")
if invariants.get("dns") != {
    "dns_server": "223.5.5.5, 223.6.6.6",
    "encrypted_dns_server": "https://dns.alidns.com/dns-query, https://doh.pub/dns-query",
    "follow_outbound_mode": False,
    "certificate_verification": True,
    "domestic_application_resolvers": list(DOMESTIC_DNS_RULES),
    "foreign_application_resolvers": list(FOREIGN_DNS_RULES),
    "domestic_resolver_policy": "DIRECT",
    "foreign_resolver_policy": "Proxy",
    "unmatched_domains_force_local_resolution": False,
    "proxy_hostname_uses_remote_resolution": True,
    "bootstrap": {
        "dns.alidns.com": ["223.5.5.5", "223.6.6.6", "2400:3200::1"],
        "doh.pub": ["1.12.12.12", "120.53.53.53"],
    },
}:
    fail("DNS invariant mismatch")
if invariants.get("udp_quic") != {
    "proxy_test_udp": "apple.com@9.9.9.9", "unsupported_behaviour": "REJECT",
    "block_quic": "per-policy", "stun_policy": "Proxy",
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
        "extended_matching": filename in EXTENDED_MATCH_RESOURCES,
        "update_interval": -1,
    }
    for kind, filename, _label, policy in REPOSITORY_RULES
}
raw_sources = list(lock.get("remote_sources", []))
if len(raw_sources) != 29:
    fail("expected 29 immutable repository sources")
seen_remote: set[str] = set()
for raw in raw_sources:
    item = dict(raw)
    filename = str(item.get("file", ""))
    if filename in seen_remote or filename not in expected_sources:
        fail(f"duplicate or unexpected runtime source: {filename}")
    seen_remote.add(filename)
    for key, expected in expected_sources[filename].items():
        if item.get(key) != expected:
            fail(f"runtime source {filename} has incorrect {key}")
    path = RULES / filename
    rows = active_lines(path)
    if item.get("active_entries") != len(rows) or item.get("sha256") != digest(path):
        fail(f"runtime source metadata mismatch: {filename}")
if seen_remote != set(expected_sources):
    fail("immutable runtime inventory is incomplete")

dynamic_sources = list(lock.get("dynamic_sources", []))
if len(dynamic_sources) != 1:
    fail("expected one reviewed dynamic runtime source")
for expected, raw in zip(DYNAMIC_RULES, dynamic_sources, strict=True):
    item = dict(raw)
    for key, value in expected.items():
        if item.get(key) != value:
            fail(f"dynamic release observation mismatch for {expected['name']}: {key}")
    if item.get("source_mode") != "reviewed-dynamic-runtime" or item.get("update_interval") != 86400:
        fail("dynamic source control metadata mismatch")

if list(lock.get("runtime_order", [])) != expected_remote_order():
    fail("runtime order in lock is stale")
if list(lock.get("embedded_sources", [])):
    fail("runtime lock may not declare embedded rule sources")

expected_local = set(expected_sources)
actual_local = {path.name for path in RULES.glob("*.list")}
if actual_local != expected_local:
    fail(f"local rule file inventory mismatch: {sorted(actual_local ^ expected_local)}")

for filename in sorted(expected_local):
    path = RULES / filename
    rows = active_lines(path)
    if not rows or len(rows) != len(set(rows)):
        fail(f"empty or duplicate active rules in {filename}")
    if filename in {"China.list", "Global.list", "Pegasus.list"}:
        invalid = [row for row in rows if not DOMAIN_RE.fullmatch(row.removeprefix("."))]
        if invalid:
            fail(f"invalid DOMAIN-SET row in {filename}: {invalid[:3]}")
    else:
        for row in rows:
            validate_rule_row(filename, row)

exact_bilibili = {
    "DOMAIN-SUFFIX,acgvideo.com", "DOMAIN-SUFFIX,b23.tv",
    "DOMAIN-SUFFIX,biliapi.com", "DOMAIN-SUFFIX,biliapi.net",
    "DOMAIN-SUFFIX,bilibili.cn", "DOMAIN-SUFFIX,bilibili.com",
    "DOMAIN-SUFFIX,bilicdn1.com", "DOMAIN-SUFFIX,bilicomic.com",
    "DOMAIN-SUFFIX,bilicomics.com", "DOMAIN-SUFFIX,biligame.com",
    "DOMAIN-SUFFIX,biligame.net", "DOMAIN-SUFFIX,biliimg.com",
    "DOMAIN-SUFFIX,bilivideo.cn", "DOMAIN-SUFFIX,bilivideo.com",
    "DOMAIN-SUFFIX,bilivideo.net", "DOMAIN-SUFFIX,hdslb.com",
}
if set(active_lines(RULES / "BiliBili.list")) != exact_bilibili:
    fail("BiliBili domestic exact set changed")
if (RULES / "BiliBiliIntl.list").exists():
    fail("retired BiliBili international ruleset returned")
intl_markers = ("apiintl.biliapi.net", "bilibili.tv", "biliintl.com", "bstarstatic")
for path in RULES.glob("*.list"):
    if any(marker in "\n".join(active_lines(path)).lower() for marker in intl_markers):
        fail(f"retired BiliBili international marker leaked into {path.name}")

required_chatgpt = {
    "DOMAIN,cdn.workos.com", "DOMAIN,challenges.cloudflare.com",
    "DOMAIN,forwarder.workos.com", "DOMAIN,images.workoscdn.com",
    "DOMAIN,js.stripe.com", "DOMAIN,o207216.ingest.sentry.io",
    "DOMAIN,o33249.ingest.sentry.io", "DOMAIN,rum.browser-intake-datadoghq.com",
    "DOMAIN,setup.workos.com", "DOMAIN,workos.imgix.net",
    "DOMAIN-SUFFIX,ct.sendgrid.net",
}
chatgpt_rows = set(active_lines(RULES / "ChatGPT.list"))
if len(chatgpt_rows) != 63 or not required_chatgpt <= chatgpt_rows:
    fail("ChatGPT official runtime dependencies are incomplete")
if len(active_lines(RULES / "Ads.list")) != 152 or len(active_lines(RULES / "Pegasus.list")) != 1438:
    fail("fixed Ads or Pegasus count changed")

resource_lock = json.loads(RESOURCE_LOCK.read_text(encoding="utf-8"))
resources = list(resource_lock.get("resources", []))
if len(resources) != 1:
    fail("Pegasus resource lock inventory changed")
pegasus = dict(resources[0])
if pegasus.get("policy") != "REJECT" or pegasus.get("local_sha256") != digest(RULES / "Pegasus.list") or pegasus.get("active_entries") != 1438:
    fail("Pegasus resource lock metadata mismatch")

service_lock = json.loads(SERVICE_LOCK.read_text(encoding="utf-8"))
services = list(service_lock.get("services", []))
if len(services) != 18:
    fail("service provenance inventory changed")
for raw in services:
    item = dict(raw)
    path = RULES / str(item["local_file"])
    if item.get("local_active_entries") != len(active_lines(path)) or item.get("local_sha256") != digest(path):
        fail(f"service provenance metadata mismatch: {path.name}")
precise = {str(item["path"]): dict(item) for item in dict(service_lock.get("precise_domains", {})).get("sources", [])}
if precise.get("Rules/China.list", {}).get("policy") != "DIRECT" or precise.get("Rules/Global.list", {}).get("policy") != "Proxy":
    fail("precise-domain policies are stale")

maintained = json.loads(MAINTAINED_LOCK.read_text(encoding="utf-8"))
maintained_files = list(maintained.get("files", []))
if len(maintained_files) != 10:
    fail("maintained-source inventory changed")
for raw in maintained_files:
    item = dict(raw)
    path = RULES / str(item["file"])
    if item.get("active_entries") != len(active_lines(path)) or item.get("sha256") != digest(path):
        fail(f"maintained-source metadata mismatch: {path.name}")


def download(url: str, limit: int = 8 * 1024 * 1024) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "surge-r13.5-auditor/1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read(limit + 1)
    if len(payload) > limit:
        fail(f"remote resource exceeds size limit: {url}")
    return payload


if CHECK_DYNAMIC:
    source = DYNAMIC_RULES[0]
    payload = download(str(source["url"]), 2 * 1024 * 1024)
    try:
        text_dynamic = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        fail(f"dynamic domestic resource is not UTF-8: {exc}")
    rows = [line.strip() for line in text_dynamic.splitlines() if line.strip() and not line.lstrip().startswith(("#", ";", "//"))]
    if len(rows) < 100 or len(rows) != len(set(rows)):
        fail("dynamic domestic resource is empty, too small or duplicated")
    for row in rows:
        validate_rule_row("domestic.conf", row)
    print(
        f"PASS dynamic domestic.conf entries={len(rows)} bytes={len(payload)} "
        f"sha256={hashlib.sha256(payload).hexdigest()}"
    )

if CHECK_RUNTIME_REMOTE:
    checked = 0
    for item in raw_sources:
        source = dict(item)
        payload = download(str(source["url"]))
        actual = hashlib.sha256(payload).hexdigest()
        if actual != source["sha256"]:
            fail(f"immutable CDN copy mismatch: {source['file']}")
        checked += 1
    print(f"PASS immutable CDN copies={checked} commit={RELEASE_REF}")

print(
    f"PASS R13.6 runtime_sources=30 immutable_sources=29 dynamic_sources=1 "
    f"local_rule_files=29 rules=142 embedded_rule_contents=0"
)
