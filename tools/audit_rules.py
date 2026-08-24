#!/usr/bin/env python3
"""Validate the R12.16 remote RULE-SET inventory and published rule sources."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from convert_to_remote_rules import RELEASE_REF, REMOTE_BASE, REPOSITORY_RULES


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "Surge.conf"
DEFAULT_RULES = ROOT / "Rules"
RULES = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_RULES
LOCK = RULES / "r10.lock.json"


def active_lines(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith(("#", ";", "//"))
    ]


def fail(message: str) -> None:
    raise AssertionError(message)


if not LOCK.is_file():
    fail(f"lock file not found: {LOCK}")

lock = json.loads(LOCK.read_text(encoding="utf-8"))
if lock.get("schema") != 8:
    fail(f"unsupported lock schema: {lock.get('schema')!r}")
if lock.get("mode") != "remote-ruleset":
    fail("lock mode must be remote-ruleset")
if lock.get("profile") != "Surge iOS Privacy + Push R12.16":
    fail("lock profile name mismatch")
invariants = lock.get("required_invariants", {})
if invariants.get("release_ref") != RELEASE_REF:
    fail("lock release reference mismatch")
if invariants.get("apns_capture") != "enabled":
    fail("lock APNs capture invariant mismatch")
if invariants.get("apns_fallback") != "Proxy_then_DIRECT":
    fail("lock APNs fallback invariant mismatch")
if invariants.get("encrypted_dns") != "direct-bypass-no-protocol-rules":
    fail("lock encrypted DNS invariant mismatch")
if invariants.get("apple_system_direct") != "DOMAIN-SUFFIX,ls.apple.com,DIRECT":
    fail("lock Apple system direct invariant mismatch")
if invariants.get("cgnat_direct") != "IP-CIDR,100.64.0.0/10,DIRECT,no-resolve":
    fail("lock CGNAT invariant mismatch")
if invariants.get("policy_architecture") != {
    "node_pool": {"mode": "select", "hidden": True, "source": "policy-path"},
    "all_server": {"mode": "smart", "source": "NodePool", "fail_closed": True},
    "regions": {
        "mode": "smart",
        "source": "NodePool",
        "fail_closed": True,
        "names": ["HongKong", "TaiWan", "Japan", "Singapore", "America"],
    },
}:
    fail("lock policy architecture invariant mismatch")
if invariants.get("applepush_probe") != {"interval": 60, "timeout": 5}:
    fail("lock ApplePush probe invariant mismatch")
if invariants.get("fail_closed_alert") != "suppressed":
    fail("lock Fail-Closed alert invariant mismatch")
if invariants.get("dns_server") != "223.5.5.5, 223.6.6.6":
    fail("lock DNS server invariant mismatch")
if invariants.get("encrypted_dns_server") != "https://dns.alidns.com/dns-query, tls://dns.alidns.com":
    fail("lock encrypted DNS server invariant mismatch")
if invariants.get("dns_bootstrap") != {"dns.alidns.com": ["223.5.5.5", "223.6.6.6", "2400:3200::1"]}:
    fail("lock DNS bootstrap invariant mismatch")
if invariants.get("capture") != {
    "include-all-networks": "true",
    "include-local-networks": "false",
    "include-apns": "true",
    "include-cellular-services": "false",
}:
    fail("lock capture invariant mismatch")
if invariants.get("bilibili") != {
    "domestic": {"file": "BiliBili.list", "policy": "DIRECT"},
    "international": {"file": "BiliBiliIntl.list", "policy": "Streaming"},
    "international_precedes_domestic": True,
}:
    fail("lock BiliBili split-routing invariant mismatch")
if invariants.get("stun_before_geoip") is not True:
    fail("lock STUN ordering invariant mismatch")

expected_sources = {
    filename: {"kind": kind, "url": f"{REMOTE_BASE}{filename}", "policy": policy}
    for kind, filename, _label, policy in REPOSITORY_RULES
}
raw_sources = lock.get("remote_sources")
if not isinstance(raw_sources, list):
    fail("remote_sources is missing")
if len(raw_sources) != len(expected_sources):
    fail(f"expected {len(expected_sources)} remote sources, found {len(raw_sources)}")

seen: set[str] = set()
for raw in raw_sources:
    item = dict(raw)
    filename = str(item.get("file", ""))
    if filename in seen:
        fail(f"duplicate remote source: {filename}")
    seen.add(filename)
    expected = expected_sources.get(filename)
    if expected is None:
        fail(f"remote source is not declared by the profile: {filename}")
    if item.get("url") != expected["url"]:
        fail(f"remote URL mismatch for {filename}")
    if item.get("kind") != expected["kind"]:
        fail(f"remote kind mismatch for {filename}")
    if item.get("policy") != expected["policy"]:
        fail(f"remote policy mismatch for {filename}")
    if not isinstance(item.get("active_entries"), int) or item["active_entries"] < 1:
        fail(f"invalid active entry count for {filename}")
    if not isinstance(item.get("sha256"), str) or len(item["sha256"]) != 64:
        fail(f"invalid SHA-256 for {filename}")

if seen != set(expected_sources):
    fail(f"remote source inventory mismatch: missing={sorted(set(expected_sources) - seen)}")

# A staged ZIP may contain Rules without Surge.conf. In that mode validate the
# remote source inventory only. The repository checkout additionally validates
# profile metadata and the exact RULE-SET references.
profile = PROFILE if RULES == DEFAULT_RULES else RULES.parent / "Surge.conf"
if profile.is_file():
    text = profile.read_text(encoding="utf-8")
    rule_text = text.split("[Rule]", 1)[1]
    active_rules = [
        line.strip()
        for line in rule_text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if lock.get("profile_sha256") != hashlib.sha256(text.encode()).hexdigest():
        fail("profile hash mismatch")
    if lock.get("profile_lines") != len(text.splitlines()):
        fail("profile line count mismatch")
    if lock.get("active_rules") != len(active_rules):
        fail("active rule count mismatch")
    actual_remote = {
        (line.split(",", 2)[0], line.split(",", 2)[1]): line.split(",", 2)[2]
        for line in active_rules
        if line.startswith((f"RULE-SET,{REMOTE_BASE}", f"DOMAIN-SET,{REMOTE_BASE}"))
        and len(line.split(",", 2)) == 3
    }
    expected_remote = {
        (item["kind"], item["url"]): item["policy"] for item in raw_sources
    }
    if actual_remote != expected_remote:
        fail("profile remote RULE-SET references do not match the lock")

errors: list[str] = []
for raw in raw_sources:
    item = dict(raw)
    filename = str(item["file"])
    path = RULES / filename
    if not path.is_file():
        errors.append(f"missing source: {filename}")
        continue
    actual_count = len(active_lines(path))
    expected_count = int(item["active_entries"])
    if actual_count != expected_count:
        errors.append(f"{filename}: expected {expected_count} active entries, got {actual_count}")
    actual_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_sha256 != item["sha256"]:
        errors.append(f"{filename}: source SHA-256 mismatch")

if errors:
    raise AssertionError("\n".join(errors))

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
missing_apns = apns_required - set(active_lines(RULES / "APNs.list"))
if missing_apns:
    fail(f"APNs source is missing Apple-published endpoints: {sorted(missing_apns)}")

telegram_required = {
    "DOMAIN-SUFFIX,t.me",
    "DOMAIN-SUFFIX,telegram.org",
    "IP-CIDR,149.154.160.0/20,no-resolve",
    "IP-CIDR,91.108.4.0/22,no-resolve",
    "IP-CIDR6,2001:b28:f23c::/48,no-resolve",
}
missing_telegram = telegram_required - set(active_lines(RULES / "Telegram.list"))
if missing_telegram:
    fail(f"Telegram source is missing core endpoints: {sorted(missing_telegram)}")

bilibili_domestic_required = {
    "DOMAIN-SUFFIX,acgvideo.com",
    "DOMAIN-SUFFIX,b23.tv",
    "DOMAIN-SUFFIX,biliapi.com",
    "DOMAIN-SUFFIX,biliapi.net",
    "DOMAIN-SUFFIX,bilibili.cn",
    "DOMAIN-SUFFIX,bilibili.com",
    "DOMAIN-SUFFIX,bilicdn1.com",
    "DOMAIN-SUFFIX,bilicomics.com",
    "DOMAIN-SUFFIX,biligame.com",
    "DOMAIN-SUFFIX,biliimg.com",
    "DOMAIN-SUFFIX,bilivideo.com",
    "DOMAIN-SUFFIX,hdslb.com",
}
bilibili_intl_required = {
    "DOMAIN,apiintl.biliapi.net",
    "DOMAIN,p-bstarstatic.akamaized.net",
    "DOMAIN,p.bstarstatic.com",
    "DOMAIN,upos-bstar-mirrorakam.akamaized.net",
    "DOMAIN,upos-bstar1-mirrorakam.akamaized.net",
    "DOMAIN-SUFFIX,bilibili.tv",
    "DOMAIN-SUFFIX,biliintl.com",
}
if set(active_lines(RULES / "BiliBili.list")) != bilibili_domestic_required:
    fail("BiliBili domestic rules do not match the reviewed DIRECT set")
if set(active_lines(RULES / "BiliBiliIntl.list")) != bilibili_intl_required:
    fail("BiliBili international rules do not match the reviewed Streaming set")

forbidden_rules = {
    "Bahamut.list": {
        "DOMAIN-SUFFIX,digicert.com",
        "DOMAIN-SUFFIX,gvt1.com",
        "DOMAIN-SUFFIX,hinet.net",
    },
    "Disney.list": {
        "DOMAIN-SUFFIX,adobedtm.com",
        "DOMAIN-SUFFIX,bam.nr-data.net",
        "DOMAIN-SUFFIX,braze.com",
        "DOMAIN-SUFFIX,cdn.optimizely.com",
        "DOMAIN-SUFFIX,conviva.com",
        "DOMAIN-SUFFIX,d9.flashtalking.com",
        "DOMAIN-SUFFIX,js-agent.newrelic.com",
    },
    "Game.list": {"DOMAIN-SUFFIX,helpshift.com"},
    "HBO.list": {
        "DOMAIN-SUFFIX,manifest.prod.boltdns.net",
        "DOMAIN-SUFFIX,players.brightcove.net",
    },
    "Microsoft.list": {
        "DOMAIN-SUFFIX,azurefd.net",
        "DOMAIN-SUFFIX,azureedge.net",
        "DOMAIN-SUFFIX,azurewebsites.net",
        "DOMAIN-SUFFIX,edgesuite.net",
        "DOMAIN-SUFFIX,helpshift.com",
        "DOMAIN-SUFFIX,optimizely.com",
        "DOMAIN-SUFFIX,windows.net",
    },
    "TikTok.list": {"DOMAIN-SUFFIX,snssdk.com"},
    "ProxyMedia.list": {
        "DOMAIN,apm-misaka.biliapi.net",
        "DOMAIN,cache.video.iqiyi.com",
    },
}
for filename, forbidden in forbidden_rules.items():
    leaked = forbidden & set(active_lines(RULES / filename))
    if leaked:
        fail(f"{filename} contains intentionally excluded shared/domestic rules: {sorted(leaked)}")

direct_rules = set(active_lines(RULES / "Direct.list"))
google_bypasses = sorted(
    rule for rule in direct_rules if "google" in rule.lower() or "gvt1.com" in rule.lower()
)
if google_bypasses:
    fail(f"Direct.list bypasses the Google policy: {google_bypasses}")

netflix_rules = set(active_lines(RULES / "Netflix.list"))
if "IP-ASN,2906,no-resolve" not in netflix_rules:
    fail("Netflix.list must use the reviewed Netflix AS2906 route")
wide_netflix_cidrs = sorted(
    rule for rule in netflix_rules if rule.startswith(("IP-CIDR,", "IP-CIDR6,"))
)
if wide_netflix_cidrs:
    fail(f"Netflix.list must not import broad cloud CIDRs: {wide_netflix_cidrs[:3]}")

print(
    f"PASS R12.16 remote_sources={len(raw_sources)} "
    f"rules={lock.get('active_rules')}"
)
