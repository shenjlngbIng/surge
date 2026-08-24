#!/usr/bin/env python3
"""Refresh R12.14 metadata for remote RULE-SET sources.

The historical filename is retained for compatibility with older maintenance
commands. It only refreshes metadata and never embeds rule contents into
Surge.conf.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from convert_to_remote_rules import REMOTE_BASE, REPOSITORY_RULES


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "Surge.conf"
LOCK = ROOT / "Rules/r10.lock.json"
RELEASE_DATE = "2026-08-24"


def active_count(path: Path) -> int:
    return sum(
        1
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith(("#", ";", "//"))
    )


text = PROFILE.read_text(encoding="utf-8")
lock = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {}
remote_sources = []
for kind, filename, _label, policy in REPOSITORY_RULES:
    path = ROOT / "Rules" / filename
    if not path.is_file():
        raise SystemExit(f"missing remote source file: {path}")
    remote_sources.append(
        {
            "kind": kind,
            "file": filename,
            "url": f"{REMOTE_BASE}{filename}",
            "policy": policy,
            "active_entries": active_count(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    )

lock.update(
    {
        "schema": 7,
        "mode": "remote-ruleset",
        "profile": "Surge iOS Privacy + Push R12.14",
        "generated": RELEASE_DATE,
        "source_repository": "shenjlngbIng/surge",
        "profile_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "profile_lines": len(text.splitlines()),
        "active_rules": sum(
            1
            for line in text.split("[Rule]", 1)[1].splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ),
        "required_invariants": {
            "final": "FINAL,Final,dns-failed",
            "final_strict_choice": "REJECT",
            "telegram": "forced-proxy",
            "apns_capture": "enabled",
            "apns_fallback": "Proxy_then_DIRECT",
            "encrypted_dns": "direct-bypass-no-protocol-rules",
            "apple_system_direct": "DOMAIN-SUFFIX,ls.apple.com,DIRECT",
            "cgnat_direct": "IP-CIDR,100.64.0.0/10,DIRECT,no-resolve",
            "allserver_probe": {"interval": 600, "timeout": 5},
            "applepush_probe": {"interval": 60, "timeout": 5},
            "fail_closed_alert": "suppressed",
            "dns_server": "223.5.5.5, 223.6.6.6",
            "encrypted_dns_server": "https://dns.alidns.com/dns-query, tls://dns.alidns.com",
            "dns_bootstrap": {
                "dns.alidns.com": ["223.5.5.5", "223.6.6.6", "2400:3200::1"],
            },
            "capture": {
                "include-all-networks": "true",
                "include-local-networks": "false",
                "include-apns": "true",
                "include-cellular-services": "false",
            },
        },
        "remote_sources": remote_sources,
    }
)
lock.pop("embedded_sources", None)
LOCK.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"updated {LOCK}: remote_sources={len(remote_sources)}")
