#!/usr/bin/env python3
"""Validate the complete R12.17 repository rule and resource inventory."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import sys
from pathlib import Path

from convert_to_remote_rules import (
    PROFILE_NAME,
    RELEASE_REF,
    REMOTE_BASE,
    REPOSITORY_RULES,
    RULE_SNAPSHOT_TAG,
    repository_line,
)


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "Surge.conf"
DEFAULT_RULES = ROOT / "Rules"
RULES = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_RULES
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
        line.strip()
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith(("#", ";", "//"))
    ]


if not LOCK.is_file():
    fail(f"runtime lock not found: {LOCK}")
lock = json.loads(LOCK.read_text(encoding="utf-8"))
if lock.get("schema") != 13 or lock.get("mode") != "repository-ruleset":
    fail("runtime lock schema/mode mismatch")
if lock.get("profile") != PROFILE_NAME:
    fail("runtime lock profile mismatch")
invariants = dict(lock.get("required_invariants", {}))
if invariants.get("rule_snapshot_tag") != RULE_SNAPSHOT_TAG:
    fail("runtime lock rule snapshot tag mismatch")
if invariants.get("rule_snapshot_commit") != RELEASE_REF:
    fail("runtime lock rule snapshot commit mismatch")
if invariants.get("runtime_static_resources") != "repository-only":
    fail("runtime resources are not locked to the repository")
if invariants.get("runtime_resource_count") != len(REPOSITORY_RULES):
    fail("runtime resource count invariant mismatch")
if invariants.get("hidden_function_groups") != ["ApplePush", "AdBlock", "Security", "UDP"]:
    fail("hidden functional policy group invariant mismatch")
if invariants.get("security_resource") != {
    "file": "Pegasus.list", "policy": "Security", "entries": 1438
}:
    fail("security resource invariant mismatch")
if invariants.get("udp_quic") != {
    "proxy_test_udp": "apple.com@223.5.5.5",
    "unsupported_behaviour": "REJECT",
    "block_quic": "per-policy",
    "stun_policy": "UDP",
}:
    fail("UDP/QUIC invariant mismatch")
privacy = dict(dict(invariants.get("policy_architecture", {})).get("privacy", {}))
if privacy != {
    "name": "PrivacyAuto",
    "mode": "url-test",
    "hidden": True,
    "source": "NodePool",
    "fail_closed": True,
    "automatic_single_policy": True,
    "interval": 600,
    "tolerance": 100,
    "evaluate_before_use": True,
}:
    fail("privacy hidden automatic-selection invariant mismatch")
if invariants.get("encrypted_dns_certificate_verification") is not True:
    fail("encrypted DNS certificate verification invariant mismatch")
if invariants.get("runtime_rulesets_no_resolve") is not True:
    fail("runtime RULE-SET local-DNS suppression invariant mismatch")
if invariants.get("public_ip_literals") != {
    "ipv4": "IP-CIDR,0.0.0.0/0,Proxy,no-resolve",
    "ipv6": "IP-CIDR6,::/0,Proxy,no-resolve",
}:
    fail("public IP literal fail-closed invariant mismatch")
if invariants.get("privacy_diagnostic_ip_literals") != ["1.1.1.1/32"]:
    fail("privacy diagnostic IP literal invariant mismatch")

expected_sources = {
    filename: {
        "kind": kind,
        "url": f"{REMOTE_BASE}{filename}",
        "policy": policy,
        "update_interval": -1,
    }
    for kind, filename, _label, policy in REPOSITORY_RULES
}
raw_sources = lock.get("remote_sources")
if not isinstance(raw_sources, list) or len(raw_sources) != len(expected_sources):
    fail(f"expected {len(expected_sources)} runtime sources")
seen: set[str] = set()
for raw in raw_sources:
    item = dict(raw)
    filename = str(item.get("file", ""))
    if filename in seen:
        fail(f"duplicate runtime source: {filename}")
    seen.add(filename)
    expected = expected_sources.get(filename)
    if expected is None:
        fail(f"unexpected runtime source: {filename}")
    for key, value in expected.items():
        if item.get(key) != value:
            fail(f"runtime source {filename} has incorrect {key}")
    if not isinstance(item.get("active_entries"), int) or item["active_entries"] < 1:
        fail(f"invalid entry count for {filename}")
    if not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", ""))):
        fail(f"invalid SHA-256 for {filename}")
if seen != set(expected_sources):
    fail(f"runtime inventory is incomplete: {sorted(set(expected_sources)-seen)}")

# In a staged ZIP the profile lives next to Rules. Validate it when present.
profile = PROFILE if RULES == DEFAULT_RULES else RULES.parent / "Surge.conf"
if profile.is_file():
    text = profile.read_text(encoding="utf-8")
    active_rules = [
        line.strip()
        for line in text.split("[Rule]", 1)[1].splitlines()
        if line.strip() and not line.lstrip().startswith(("#", ";", "//"))
    ]
    if lock.get("profile_sha256") != hashlib.sha256(text.encode()).hexdigest():
        fail("profile hash mismatch")
    if lock.get("profile_lines") != len(text.splitlines()):
        fail("profile line count mismatch")
    if lock.get("active_rules") != len(active_rules):
        fail("profile rule count mismatch")
    external = {line for line in active_rules if line.startswith(("RULE-SET,", "DOMAIN-SET,"))}
    expected_external = {
        repository_line(kind, filename, policy)
        for kind, filename, _label, policy in REPOSITORY_RULES
    }
    if external != expected_external:
        fail("profile runtime resource references do not match the lock")

errors: list[str] = []
domain_set_files = {"Pegasus.list", "China.list", "Global.list"}
for raw in raw_sources:
    item = dict(raw)
    filename = str(item["file"])
    path = RULES / filename
    if not path.is_file():
        errors.append(f"missing source: {filename}")
        continue
    rows = active_lines(path)
    if len(rows) != int(item["active_entries"]):
        errors.append(f"{filename}: entry count mismatch")
    if len(rows) != len(set(rows)):
        errors.append(f"{filename}: duplicate active rows")
    if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
        errors.append(f"{filename}: SHA-256 mismatch")
    if filename in domain_set_files:
        for row in rows:
            value = row[1:] if row.startswith(".") else row
            if "," in row or not DOMAIN_RE.fullmatch(value):
                errors.append(f"{filename}: invalid DOMAIN-SET row {row!r}")
                break
    else:
        for row in rows:
            rule_type = row.split(",", 1)[0].upper()
            if rule_type not in RULE_TYPES:
                errors.append(f"{filename}: unsupported rule type {rule_type}")
                break
            if rule_type == "PROCESS-NAME":
                errors.append(f"{filename}: PROCESS-NAME is not valid for the iOS runtime bundle")
                break
            if rule_type in {"IP-CIDR", "IP-CIDR6"}:
                try:
                    ipaddress.ip_network(row.split(",", 2)[1], strict=False)
                except ValueError:
                    errors.append(f"{filename}: invalid network {row!r}")
                    break
if errors:
    fail("\n".join(errors))

if not RESOURCE_LOCK.is_file():
    fail("pinned resource provenance lock is missing")
resource_lock = json.loads(RESOURCE_LOCK.read_text(encoding="utf-8"))
resources = list(resource_lock.get("resources", []))
if resource_lock.get("schema") != 1 or len(resources) != 1:
    fail("pinned resource provenance lock is invalid")
pegasus_meta = dict(resources[0])
pegasus = RULES / "Pegasus.list"
if pegasus_meta.get("local_file") != "Pegasus.list":
    fail("Pegasus local resource name mismatch")
if pegasus_meta.get("active_entries") != 1438:
    fail("Pegasus entry count in provenance lock is stale")
if pegasus_meta.get("local_sha256") != hashlib.sha256(pegasus.read_bytes()).hexdigest():
    fail("Pegasus provenance local SHA-256 mismatch")
if len(active_lines(pegasus)) != 1438:
    fail("Pegasus local snapshot must contain exactly 1438 domains")

if not SERVICE_LOCK.is_file():
    fail("pinned service provenance lock is missing")
service_lock = json.loads(SERVICE_LOCK.read_text(encoding="utf-8"))
if service_lock.get("schema") != 2 or len(service_lock.get("services", [])) != 19:
    fail("pinned service provenance inventory is invalid")
if dict(service_lock.get("local_additions_policy", {})).get("undeclared_rows") != "forbidden":
    fail("service lock does not forbid undeclared local rows")
review = dict(service_lock.get("upstream", {})).get("last_review", {})
if review != {
    "date": "2026-08-25",
    "compared_commit": "f42be99379fcd1a1dd03469e8b56dcb46888fcea",
    "services_compared": 19,
    "active_additions": 0,
    "active_deletions": 0,
    "decision": "保留当前固定提交；19 个文件的活动规则一致，Game.list 仅有注释或元数据差异。",
}:
    fail("pinned service comparison review is missing or stale")

for raw_service in service_lock["services"]:
    service = dict(raw_service)
    target = RULES / str(service["local_file"])
    if service.get("local_active_entries") != len(active_lines(target)):
        fail(f"service local entry count mismatch: {target.name}")
    if service.get("local_sha256") != hashlib.sha256(target.read_bytes()).hexdigest():
        fail(f"service local SHA-256 mismatch: {target.name}")
    additions = list(service.get("add", []))
    if additions and dict(service.get("add_source", {})).get("type") != "repository-maintained-curation":
        fail(f"service local additions have no disclosure: {target.name}")

if not MAINTAINED_LOCK.is_file():
    fail("repository-maintained source disclosure lock is missing")
maintained_lock = json.loads(MAINTAINED_LOCK.read_text(encoding="utf-8"))
maintained_files = {
    "APNs.list", "Ads.list", "AppleCN.list", "BiliBili.list", "China.list",
    "Direct.list", "Global.list", "ProxyMedia.list", "Telegram.list", "WeChat.list",
}
maintained_items = list(maintained_lock.get("files", []))
if maintained_lock.get("schema") != 1 or len(maintained_items) != len(maintained_files):
    fail("repository-maintained source disclosure inventory is invalid")
if maintained_lock.get("policy", {}).get("automatic_refresh") != "forbidden unless a fixed source and reviewed diff are recorded":
    fail("repository-maintained automatic refresh policy is missing")
seen_maintained: set[str] = set()
for raw_item in maintained_items:
    item = dict(raw_item)
    filename = str(item.get("file", ""))
    if filename not in maintained_files or filename in seen_maintained:
        fail(f"unexpected repository-maintained source item: {filename}")
    seen_maintained.add(filename)
    target = RULES / filename
    if item.get("active_entries") != len(active_lines(target)):
        fail(f"repository-maintained entry count mismatch: {filename}")
    if item.get("sha256") != hashlib.sha256(target.read_bytes()).hexdigest():
        fail(f"repository-maintained SHA-256 mismatch: {filename}")
    if not item.get("maintenance") or not item.get("license_status") or not item.get("notes"):
        fail(f"repository-maintained disclosure is incomplete: {filename}")
if seen_maintained != maintained_files:
    fail("repository-maintained source disclosure is incomplete")

apns_required = {
    "DOMAIN-SUFFIX,push.apple.com",
    "DOMAIN-SUFFIX,push-apple.com.akadns.net",
    "IP-CIDR,17.249.0.0/16,no-resolve",
    "IP-CIDR,17.252.0.0/16,no-resolve",
    "IP-CIDR,17.57.144.0/22,no-resolve",
    "IP-CIDR,17.188.128.0/18,no-resolve",
    "IP-CIDR,17.188.20.0/23,no-resolve",
    "IP-CIDR6,2620:149:a44::/48,no-resolve",
    "IP-CIDR6,2403:300:a42::/48,no-resolve",
    "IP-CIDR6,2403:300:a51::/48,no-resolve",
    "IP-CIDR6,2a01:b740:a42::/48,no-resolve",
}
if not apns_required <= set(active_lines(RULES / "APNs.list")):
    fail("APNs source is missing Apple-published endpoints")

telegram_required = {
    "DOMAIN-SUFFIX,t.me", "DOMAIN-SUFFIX,telegram.org",
    "IP-CIDR,149.154.160.0/20,no-resolve",
    "IP-CIDR,91.108.4.0/22,no-resolve",
    "IP-CIDR6,2001:b28:f23c::/48,no-resolve",
}
if not telegram_required <= set(active_lines(RULES / "Telegram.list")):
    fail("Telegram source is missing core endpoints")

bilibili_domestic = {
    "DOMAIN-SUFFIX,acgvideo.com", "DOMAIN-SUFFIX,b23.tv",
    "DOMAIN-SUFFIX,biliapi.com", "DOMAIN-SUFFIX,biliapi.net",
    "DOMAIN-SUFFIX,bilibili.cn", "DOMAIN-SUFFIX,bilibili.com",
    "DOMAIN-SUFFIX,bilicdn1.com", "DOMAIN-SUFFIX,bilicomics.com",
    "DOMAIN-SUFFIX,biligame.com", "DOMAIN-SUFFIX,biliimg.com",
    "DOMAIN-SUFFIX,bilivideo.com", "DOMAIN-SUFFIX,hdslb.com",
}
bilibili_international = {
    "DOMAIN,apiintl.biliapi.net", "DOMAIN,p-bstarstatic.akamaized.net",
    "DOMAIN,p.bstarstatic.com", "DOMAIN,upos-bstar-mirrorakam.akamaized.net",
    "DOMAIN,upos-bstar1-mirrorakam.akamaized.net",
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

direct_rules = set(active_lines(RULES / "Direct.list"))
if any("google" in rule.lower() or "gvt1.com" in rule.lower() for rule in direct_rules):
    fail("Direct.list bypasses the Google policy")
netflix_rules = set(active_lines(RULES / "Netflix.list"))
if "IP-ASN,2906,no-resolve" not in netflix_rules:
    fail("Netflix must use AS2906")
if any(rule.startswith(("IP-CIDR,", "IP-CIDR6,")) for rule in netflix_rules):
    fail("Netflix must not import broad cloud CIDRs")

print(
    f"PASS R12.17 runtime_sources={len(raw_sources)} local_rule_files={len(list(RULES.glob('*.list')))} "
    f"rules={lock.get('active_rules')} pegasus=1438"
)
