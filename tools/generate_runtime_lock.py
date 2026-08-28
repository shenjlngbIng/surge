#!/usr/bin/env python3
"""Regenerate the R13.4 no-embedded-content runtime lock.

The lock records 30 immutable repository snapshots, three reviewed dynamic
runtime supplements and the configuration invariants enforced by the auditors.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from convert_to_remote_rules import (
    DOMESTIC_DNS_RULES,
    DOMESTIC_GEOIP_RULE,
    DYNAMIC_RULES,
    FOREIGN_DNS_RULES,
    PROFILE_NAME,
    RELEASE_DATE,
    RELEASE_REF,
    REMOTE_BASE,
    REPOSITORY_RULES,
    RULE_SNAPSHOT_TAG,
    expected_remote_order,
)


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "Surge.conf"
RULES = ROOT / "Rules"
LOCK = RULES / "r10.lock.json"


def active_rows(path: Path) -> list[str]:
    return [
        row.strip() for row in path.read_text(encoding="utf-8-sig").splitlines()
        if row.strip() and not row.lstrip().startswith(("#", ";", "//"))
    ]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


payload = PROFILE.read_bytes()
text = payload.decode("utf-8")
if "[Rule]" not in text:
    raise SystemExit("Surge.conf has no [Rule] section")
profile_rules = [
    row.strip() for row in text.split("[Rule]", 1)[1].splitlines()
    if row.strip() and not row.lstrip().startswith(("#", ";", "//"))
]
external = [row for row in profile_rules if row.startswith(("RULE-SET,", "DOMAIN-SET,"))]
if external != expected_remote_order():
    raise SystemExit("profile runtime resource order differs from the reviewed R13.4 inventory")

embedded = [
    row for row in profile_rules
    if row.endswith((",Security", ",AdBlock"))
    and not row.startswith(("RULE-SET,", "DOMAIN-SET,"))
]
if embedded:
    raise SystemExit(f"embedded Security/AdBlock rule content is forbidden: {embedded[:3]}")

repository_sources: list[dict[str, object]] = []
for kind, filename, _label, policy in REPOSITORY_RULES:
    path = RULES / filename
    rows = active_rows(path)
    repository_sources.append({
        "source_mode": "immutable-repository-snapshot",
        "kind": kind,
        "file": filename,
        "url": f"{REMOTE_BASE}{filename}",
        "policy": policy,
        "update_interval": -1,
        "active_entries": len(rows),
        "sha256": sha256_bytes(path.read_bytes()),
    })

dynamic_sources = []
for source in DYNAMIC_RULES:
    item = dict(source)
    item["source_mode"] = "reviewed-dynamic-runtime"
    item["update_interval"] = 86400
    item["release_audited"] = RELEASE_DATE
    dynamic_sources.append(item)

local_lists = sorted(RULES.glob("*.list"))
lock = {
    "schema": 18,
    "mode": "repository-plus-reviewed-dynamic-no-embedded-content",
    "profile": PROFILE_NAME,
    "generated": RELEASE_DATE,
    "source_repository": "shenjlngbIng/surge",
    "profile_sha256": sha256_bytes(payload),
    "profile_lines": len(text.splitlines()),
    "active_rules": len(profile_rules),
    "runtime_resources": len(external),
    "immutable_repository_resources": len(repository_sources),
    "dynamic_runtime_resources": len(dynamic_sources),
    "local_rule_files": len(local_lists),
    "required_invariants": {
        "final": "FINAL,Final,dns-failed",
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
        "policy_architecture": {
            "node_pool": {
                "mode": "select",
                "hidden": False,
                "source": "policy-path",
                "fail_closed": True,
                "manual_default": False,
            },
            "proxy": {"mode": "select", "default": "AllServer"},
            "all_server": {
                "mode": "smart",
                "source": "NodePool",
                "fail_closed": True,
                "evaluate_before_use": True,
            },
            "regions": {
                "mode": "smart",
                "source": "NodePool",
                "fail_closed": True,
                "names": ["HongKong", "TaiWan", "Japan", "Singapore", "America"],
            },
            "domestic": {"mode": "select", "default": "DIRECT", "fallback": "Proxy", "hidden": True},
        },
        "security_resources": [
            {"name": "reject_phishing.conf", "mode": "dynamic", "policy": "Security"},
            {"name": "Pegasus.list", "mode": "immutable", "policy": "Security", "entries": len(active_rows(RULES / "Pegasus.list"))},
        ],
        "advertising_resources": [
            {"name": "Ads.list", "mode": "immutable", "policy": "AdBlock", "entries": len(active_rows(RULES / "Ads.list"))},
            {"name": "reject.conf", "mode": "dynamic", "policy": "AdBlock"},
        ],
        "domestic_resources": {
            "dynamic_supplement": "domestic.conf",
            "pinned_precise_set": "China.list",
            "policy": "Domestic",
            "geoip": DOMESTIC_GEOIP_RULE,
            "geoip_resolves_unmatched_domains": False,
            "unmatched_domain_fallback": "Final/Proxy",
        },
        "dns": {
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
        },
        "capture": {
            "include-all-networks": "true",
            "include-local-networks": "false",
            "include-apns": "true",
            "include-cellular-services": "false",
        },
        "udp_quic": {
            "proxy_test_udp": "apple.com@9.9.9.9",
            "unsupported_behaviour": "REJECT",
            "block_quic": "per-policy",
            "stun_policy": "UDP",
            "udp_default": "Proxy",
            "blocked_public_dns_ports": [53, 853, 8853],
        },
        "apple_captive_direct": "DOMAIN,captive.apple.com,DIRECT",
        "apple_bootstrap_direct": "DOMAIN,configuration.ls.apple.com,DIRECT",
        "diagnostic_policy": "Proxy",
        "runtime_rulesets_no_resolve": True,
        "public_ip_literals": {
            "china": DOMESTIC_GEOIP_RULE,
            "ipv4": "IP-CIDR,0.0.0.0/0,Proxy,no-resolve",
            "ipv6": "IP-CIDR6,::/0,Proxy,no-resolve",
        },
        "bilibili": {
            "domestic": {"file": "BiliBili.list", "policy": "Domestic"},
            "international": {"file": "BiliBiliIntl.list", "policy": "Streaming"},
            "international_precedes_domestic": True,
        },
    },
    "runtime_order": external,
    "embedded_sources": [],
    "remote_sources": repository_sources,
    "dynamic_sources": dynamic_sources,
}

LOCK.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(
    f"updated {LOCK}: runtime_sources={len(external)} immutable={len(repository_sources)} "
    f"dynamic={len(dynamic_sources)} local_rule_files={len(local_lists)} "
    f"rules={len(profile_rules)} embedded_rule_contents=0"
)
