#!/usr/bin/env python3
"""Regenerate the R13.13 immutable-rules-plus-domestic-dynamic lock."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from convert_to_remote_rules import (
    DOMESTIC_DNS_RULES,
    DOMESTIC_GEOIP_RULE,
    DYNAMIC_RULES,
    EXTENDED_MATCH_RESOURCES,
    FOREIGN_DNS_RULES,
    FUNCTIONAL_GUARDS,
    PROFILE_NAME,
    RELEASE_DATE,
    RELEASE_REF,
    REMOTE_BASE,
    REPOSITORY_RULES,
    RETIRED_BILIBILI_INTL_GUARDS,
    RULE_SNAPSHOT_TAG,
    expected_remote_order,
)


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "Surge.conf"
RULES = ROOT / "Rules"
LOCK = RULES / "r10.lock.json"
REGIONS = ["HongKong", "TaiWan", "Japan", "Singapore", "America"]


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
    raise SystemExit("profile runtime resource order differs from the reviewed R13.13 inventory")
if any(marker in text for marker in ("reject_phishing.conf", "/domainset/reject.conf")):
    raise SystemExit("mobile profile contains a forbidden mutable reject source")

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
        "extended_matching": filename in EXTENDED_MATCH_RESOURCES,
        "update_interval": -1,
        "active_entries": len(rows),
        "sha256": sha256_bytes(path.read_bytes()),
    })

dynamic_sources: list[dict[str, object]] = []
for source in DYNAMIC_RULES:
    item = dict(source)
    item["source_mode"] = "reviewed-dynamic-runtime"
    item["update_interval"] = 86400
    item["release_audited"] = RELEASE_DATE
    dynamic_sources.append(item)

local_lists = sorted(RULES.glob("*.list"))
lock = {
    "schema": 27,
    "mode": "immutable-rules-plus-domestic-dynamic",
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
        "runtime_resource_count": 30,
        "immutable_repository_resource_count": 29,
        "dynamic_runtime_resource_count": 1,
        "local_rule_file_count": 29,
        "embedded_rule_contents": 0,
        "hidden_function_groups": ["ApplePush"],
        "removed_stateful_groups": ["AdBlock", "Security", "UDP", "Domestic", "AllServer", "Smart"],
        "visible_control_groups": ["Final", "Proxy", "Auto", "NodePool"],
        "subscription_policy_path": "https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL",
        "loglevel": "notify",
        "public_embedded_proxy_policies": 0,
        "policy_architecture": {
            "automatic_empty_group_behavior": "DIRECT/SUBSTITUTE",
            "smart_groups": [],
            "auto": {
                "mode": "url-test", "hidden": False, "source": "NodePool",
                "explicit_members": ["REJECT"], "interval_seconds": 600,
                "tolerance_milliseconds": 100, "evaluate_before_use": True,
                "empty_source_behavior": "REJECT/error",
                "direct_substitution_prevented": True,
            },
            "node_pool": {
                "mode": "select", "hidden": False,
                "source": "external-policy-path",
                "explicit_members": ["REJECT"], "include_all_proxies": False,
                "update_interval_seconds": 3600,
                "automatic_fallback": False,
            },
            "proxy": {
                "mode": "select", "default": "Auto",
                "manual_fail_closed_entry": "REJECT",
            },
            "regions": {
                "mode": "url-test", "source": "NodePool",
                "explicit_members": ["REJECT"], "interval_seconds": 600,
                "tolerance_milliseconds": 100,
                "evaluate_before_use": True,
                "empty_source_behavior": "REJECT/error", "names": REGIONS,
            },
            "restricted_service_auto": {
                "mode": "url-test",
                "source_mode": "recursive-include-other-group",
                "explicit_members": ["REJECT"],
                "evaluate_before_use": True,
                "interval_seconds": 600,
                "tolerance_milliseconds": 100,
                "empty_source_behavior": "REJECT/error",
                "groups": {
                    "ChatGPT": ["Japan", "Singapore", "TaiWan", "America"],
                    "Claude": ["Japan", "Singapore", "TaiWan", "America"],
                    "Gemini": ["Japan", "Singapore", "TaiWan", "America"],
                    "TikTok": ["Japan", "Singapore", "TaiWan", "America"],
                },
            },
            "restricted_service_select": {"Bahamut": ["TaiWan", "HongKong"]},
        },
        "security_resources": [
            {"name": "Pegasus.list", "mode": "immutable", "policy": "REJECT", "entries": len(active_rows(RULES / "Pegasus.list"))},
        ],
        "advertising_resources": [
            {"name": "Ads.list", "mode": "immutable", "policy": "REJECT", "entries": len(active_rows(RULES / "Ads.list"))},
        ],
        "mobile_dynamic_reject_sources": [],
        "functional_guards_before_ads": list(FUNCTIONAL_GUARDS),
        "extended_matching_resources": sorted(EXTENDED_MATCH_RESOURCES),
        "domestic_resources": {
            "dynamic_supplement": "domestic.conf",
            "pinned_precise_set": "China.list",
            "policy": "DIRECT",
            "geoip": DOMESTIC_GEOIP_RULE,
            "geoip_resolves_unmatched_domains": False,
            "unmatched_domain_fallback": "Final/Proxy",
        },
        "dns": {
            "dns_server": "223.5.5.5, 223.6.6.6, 2400:3200::1, 2400:3200:baba::1",
            "encrypted_dns_server": "https://dns.alidns.com/dns-query, https://doh.pub/dns-query",
            "follow_outbound_mode": False,
            "certificate_verification": True,
            "domestic_application_resolvers": list(DOMESTIC_DNS_RULES),
            "foreign_application_resolvers": list(FOREIGN_DNS_RULES),
            "domestic_resolver_policy": "DIRECT",
            "foreign_resolver_policy": "Proxy",
            "unmatched_domains_force_local_resolution": False,
            "proxy_hostname_uses_remote_resolution": True,
            "static_bootstrap": {
                "dns.alidns.com": [
                    "223.5.5.5", "223.6.6.6", "2400:3200::1",
                    "2400:3200:baba::1",
                ],
            },
            "dynamic_hostname_bootstrap": ["doh.pub"],
        },
        "capture": {
            "include-all-networks": "true",
            "include-local-networks": "false",
            "include-apns": "true",
            "include-cellular-services": "false",
        },
        "udp_quic": {
            "proxy_test_udp": "apple.com@1.1.1.1",
            "unsupported_behaviour": "REJECT",
            "block_quic": "per-policy",
            "stun_policy": "Proxy",
            "blocked_public_dns_ports": [53, 853, 8853],
        },
        "apple_captive_direct": "DOMAIN,captive.apple.com,DIRECT",
        "apple_bootstrap_direct": "DOMAIN,configuration.ls.apple.com,DIRECT",
        "network_diagnostics": {
            "proxy_policy_source": "NodePool/policy-path",
            "global_proxy_row": "not-enumerated-for-external-policies",
            "global_udp_row": "not-enumerated-for-external-policies",
            "loopback_bridge": False,
            "policy_path": True,
            "real_policy_udp_test": "apple.com@1.1.1.1",
            "udp_requires_policy_and_server_support": True,
        },
        "runtime_rulesets_no_resolve": True,
        "public_ip_literals": {
            "china": DOMESTIC_GEOIP_RULE,
            "ipv4": "IP-CIDR,0.0.0.0/0,Proxy,no-resolve",
            "ipv6": "IP-CIDR6,::/0,Proxy,no-resolve",
        },
        "bilibili": {
            "domestic": {"file": "BiliBili.list", "policy": "DIRECT", "entries": 16},
            "functional_guards": list(FUNCTIONAL_GUARDS[:2]),
            "international_ruleset_retired": True,
            "international_compatibility_policy": "Proxy",
            "international_compatibility_guards": list(RETIRED_BILIBILI_INTL_GUARDS),
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
