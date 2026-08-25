#!/usr/bin/env python3
"""Refresh R12.17 metadata for repository-hosted runtime resources.

The historical filename is retained for compatibility. It updates the lock
file and never embeds rule contents into ``Surge.conf``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from convert_to_remote_rules import (
    PROFILE_NAME,
    RELEASE_DATE,
    RELEASE_REF,
    REMOTE_BASE,
    REPOSITORY_RULES,
    repository_line,
)


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "Surge.conf"
LOCK = ROOT / "Rules/r10.lock.json"


def active_count(path: Path) -> int:
    return sum(
        1
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith(("#", ";", "//"))
    )


text = PROFILE.read_text(encoding="utf-8")
remote_sources = []
for kind, filename, _label, policy in REPOSITORY_RULES:
    path = ROOT / "Rules" / filename
    if not path.is_file():
        raise SystemExit(f"missing runtime source file: {path}")
    remote_sources.append(
        {
            "kind": kind,
            "file": filename,
            "url": f"{REMOTE_BASE}{filename}",
            "policy": policy,
            "update_interval": -1,
            "active_entries": active_count(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    )

active_rules = [
    line.strip()
    for line in text.split("[Rule]", 1)[1].splitlines()
    if line.strip() and not line.lstrip().startswith(("#", ";", "//"))
]

lock = {
    "schema": 9,
    "mode": "repository-ruleset",
    "profile": PROFILE_NAME,
    "generated": RELEASE_DATE,
    "source_repository": "shenjlngbIng/surge",
    "profile_sha256": hashlib.sha256(text.encode()).hexdigest(),
    "profile_lines": len(text.splitlines()),
    "active_rules": len(active_rules),
    "required_invariants": {
        "final": "FINAL,Final,dns-failed",
        "release_ref": RELEASE_REF,
        "runtime_static_resources": "repository-only",
        "runtime_resource_count": len(REPOSITORY_RULES),
        "final_strict_choice": "REJECT",
        "telegram": "forced-proxy",
        "apns_capture": "enabled",
        "apns_fallback": "Proxy_then_DIRECT",
        "applepush_probe": {
            "interval": 60,
            "evaluate_before_use": True,
            "global_test_timeout": 5,
        },
        "security_resource": {
            "file": "Pegasus.list",
            "policy": "Security",
            "entries": 1438,
        },
        "encrypted_dns": "direct-bypass-no-protocol-rules",
        "apple_system_direct": "DOMAIN-SUFFIX,ls.apple.com,DIRECT",
        "cgnat_direct": "IP-CIDR,100.64.0.0/10,DIRECT,no-resolve",
        "policy_architecture": {
            "node_pool": {"mode": "select", "hidden": True, "source": "policy-path"},
            "all_server": {"mode": "smart", "source": "NodePool", "fail_closed": True},
            "regions": {
                "mode": "smart",
                "source": "NodePool",
                "fail_closed": True,
                "names": ["HongKong", "TaiWan", "Japan", "Singapore", "America"],
            },
        },
        "fail_closed_alert": "suppressed",
        "dns_server": "223.5.5.5, 223.6.6.6",
        "encrypted_dns_server": "https://dns.alidns.com/dns-query, tls://dns.alidns.com",
        "dns_bootstrap": {
            "dns.alidns.com": ["223.5.5.5", "223.6.6.6", "2400:3200::1"]
        },
        "capture": {
            "include-all-networks": "true",
            "include-local-networks": "false",
            "include-apns": "true",
            "include-cellular-services": "false",
        },
        "udp_quic": {
            "proxy_test_udp": "apple.com@223.5.5.5",
            "unsupported_behaviour": "REJECT",
            "block_quic": "per-policy",
            "stun_policy": "UDP",
        },
        "bilibili": {
            "domestic": {"file": "BiliBili.list", "policy": "DIRECT"},
            "international": {"file": "BiliBiliIntl.list", "policy": "Streaming"},
            "international_precedes_domestic": True,
        },
        "shared_infrastructure_overrides": {
            "youtube_google": True,
            "game_microsoft": True,
            "game_google_cloud": "IP-CIDR,35.192.0.0/12,Proxy,no-resolve",
            "viu_hbo": "DOMAIN-SUFFIX,viu.now.com,Streaming",
        },
        "stun_before_geoip": True,
        "geoip_no_resolve": True,
    },
    "remote_sources": remote_sources,
}

expected_lines = {
    repository_line(kind, filename, policy)
    for kind, filename, _label, policy in REPOSITORY_RULES
}
actual_lines = {line for line in active_rules if line.startswith(("RULE-SET,", "DOMAIN-SET,"))}
if actual_lines != expected_lines:
    raise SystemExit("profile runtime resource inventory differs from the generated lock")

LOCK.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"updated {LOCK}: remote_sources={len(remote_sources)} rules={len(active_rules)}")
