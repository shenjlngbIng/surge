#!/usr/bin/env python3
"""Fault-injection regression tests for the R13.15 configuration auditor."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "Surge.conf"
AUDITOR = ROOT / "tools" / "audit_config.py"
SOURCE = PROFILE.read_text(encoding="utf-8")
MUTATIONS: list[tuple[str, str]] = []


def replace_once(name: str, old: str, new: str) -> None:
    if SOURCE.count(old) < 1:
        raise RuntimeError(f"mutation anchor {name!r} is missing")
    MUTATIONS.append((name, SOURCE.replace(old, new, 1)))


def replace_group_fragment(name: str, group: str, old: str, new: str) -> None:
    lines = SOURCE.splitlines(keepends=True)
    indexes = [index for index, line in enumerate(lines) if line.startswith(f"{group} = ")]
    if len(indexes) != 1:
        raise RuntimeError(f"group mutation anchor {group!r} is missing or duplicated")
    index = indexes[0]
    if lines[index].count(old) != 1:
        raise RuntimeError(f"group mutation fragment {name!r} is missing or duplicated")
    lines[index] = lines[index].replace(old, new, 1)
    MUTATIONS.append((name, "".join(lines)))


# Header, source and subscription boundary.
for name, old, new in (
    ("version", "R13.15 Restored Groups", "R13.14 Restored Simple"),
    ("date", "# > Update Date: 2026.09.01", "# > Update Date: 2026.08.31"),
    ("layout_claim", "# > Restores NodePool, Auto, region and service groups without visible REJECT placeholders.\n", ""),
    ("subscription_claim", "# > Put one Surge-format Sub-Store URL in NodePool; no linked profile or helper script is required.\n", ""),
    ("capture_warning", "# > include-all-networks stays enabled for APNs/privacy capture; Surge may warn about AirDrop/Xcode.\n", ""),
    ("snapshot_ref", "2b8fa93901061cf0482b079203630bcd11bfe0b1", "de744020e1a5ecab82a87f0749493f6adf405dd4"),
    ("token_warning", "# > REQUIRED: replace only NodePool.policy-path locally; never publish subscription tokens.\n", ""),
    ("missing_policy_path", "policy-path=https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL, ", ""),
    ("duplicate_policy_path", "NodePool = select, policy-path=", "NodePool = select, policy-path=https://example.invalid/SECOND, policy-path="),
    ("wrong_placeholder", "https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL", "https://example.invalid/WRONG_SUBSCRIPTION_URL"),
):
    replace_once(name, old, new)

replace_once("mutable_main", "# Repository-hosted remote rule sets\n", "RULE-SET,https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@main/Rules/Ads.list,REJECT,no-resolve\n# Repository-hosted remote rule sets\n")
replace_once("mobile_dynamic_ads", "# Artificial intelligence\n", "DOMAIN-SET,https://ruleset.skk.moe/List/domainset/reject.conf,REJECT,update-interval=86400\n# Artificial intelligence\n")

# General, DNS and access invariants.
for name, old, new in (
    ("loglevel", "loglevel = notify", "loglevel = debug"),
    ("auto_suspend", "auto-suspend = true", "auto-suspend = false"),
    ("ipv6", "ipv6 = true", "ipv6 = false"),
    ("ipv6_vif", "ipv6-vif = auto", "ipv6-vif = off"),
    ("wifi_assist", "wifi-assist = false", "wifi-assist = true"),
    ("include_all", "include-all-networks = true", "include-all-networks = false"),
    ("include_apns", "include-apns = true", "include-apns = false"),
    ("dns_server", "dns-server = 223.5.5.5, 223.6.6.6, 2400:3200::1, 2400:3200:baba::1", "dns-server = 8.8.8.8"),
    ("encrypted_dns", "encrypted-dns-server = https://cloudflare-dns.com/dns-query, https://dns.quad9.net/dns-query", "encrypted-dns-server = https://dns.google/dns-query"),
    ("dns_follow", "encrypted-dns-follow-outbound-mode = true", "encrypted-dns-follow-outbound-mode = false"),
    ("dns_cert", "encrypted-dns-skip-cert-verification = false", "encrypted-dns-skip-cert-verification = true"),
    ("hijack_dns", "hijack-dns = *:53", "hijack-dns = 8.8.8.8:53"),
    ("local_host_proxy", "use-local-host-item-for-proxy = false", "use-local-host-item-for-proxy = true"),
    ("wifi_access", "allow-wifi-access = false", "allow-wifi-access = true"),
    ("hotspot_access", "allow-hotspot-access = false", "allow-hotspot-access = true"),
    ("proxy_lan", "proxy-restricted-to-lan = true", "proxy-restricted-to-lan = false"),
    ("udp_unsupported", "udp-policy-not-supported-behaviour = REJECT", "udp-policy-not-supported-behaviour = DIRECT"),
    ("quic", "block-quic = per-policy", "block-quic = off"),
    ("udp_probe", "proxy-test-udp = apple.com@1.1.1.1", "proxy-test-udp = apple.com@8.8.8.8"),
):
    replace_once(name, old, new)

# Host, static proxy and restored full-group architecture.
for name, old, new in (
    ("substore_host", "sub.store = 127.0.0.1", "sub.store = 1.1.1.1"),
    ("cloudflare_bootstrap", "cloudflare-dns.com = 1.1.1.1, 1.0.0.1, 2606:4700:4700::1111, 2606:4700:4700::1001", "cloudflare-dns.com = 8.8.8.8"),
    ("quad9_bootstrap", "dns.quad9.net = 9.9.9.9, 149.112.112.112, 2620:fe::fe, 2620:fe::9", "dns.quad9.net = 8.8.8.8"),
    ("embedded_reject", "[Proxy]\n", "[Proxy]\nFail-Closed = reject\n"),
    ("loopback_diagnostics", "[Proxy]\n", "[Proxy]\nDiagnostics = socks5, 127.0.0.1, 6153, udp-relay=true\n"),
    ("final_members", "Final = select, Proxy, DIRECT,", "Final = select, Proxy, REJECT,"),
    ("final_hidden", "Final = select, Proxy, DIRECT, no-alert=0, hidden=0", "Final = select, Proxy, DIRECT, no-alert=0, hidden=1"),
    ("applepush_order", "ApplePush = fallback, Proxy, DIRECT", "ApplePush = fallback, DIRECT, Proxy"),
    ("apple_order", "Apple = select, DIRECT, Proxy,", "Apple = select, Proxy, DIRECT,"),
    ("unexpected_allserver", "# Subscription. This is the only URL the user changes.\n", "AllServer = smart, include-other-group=NodePool\n# Subscription. This is the only URL the user changes.\n"),
):
    replace_once(name, old, new)

for name, group, old, new in (
    ("proxy_smart", "Proxy", "select", "smart"),
    ("proxy_reject", "Proxy", "Proxy = select,", "Proxy = select, REJECT,"),
    ("proxy_missing_auto", "Proxy", "Auto, ", ""),
    ("proxy_hidden", "Proxy", "hidden=0", "hidden=1"),
    ("proxy_include_all", "Proxy", "include-all-proxies=0", "include-all-proxies=1"),
    ("nodepool_reject", "NodePool", "NodePool = select,", "NodePool = select, REJECT,"),
    ("nodepool_update", "NodePool", "update-interval=3600", "update-interval=7200"),
    ("nodepool_hidden", "NodePool", "hidden=0", "hidden=1"),
    ("nodepool_include_all", "NodePool", "include-all-proxies=0", "include-all-proxies=1"),
    ("auto_select", "Auto", "smart", "select"),
    ("auto_no_evaluate", "Auto", "evaluate-before-use=true", "evaluate-before-use=false"),
    ("auto_hidden", "Auto", "hidden=0", "hidden=1"),
    ("auto_wrong_source", "Auto", "include-other-group=NodePool", "include-other-group=America"),
    ("region_source_visible", "HongKong-Nodes", "hidden=1", "hidden=0"),
    ("region_source_wrong_group", "HongKong-Nodes", "include-other-group=NodePool", "include-other-group=Auto"),
    ("region_fallback_deleted", "HongKong", "HongKong-Nodes, Auto", "HongKong-Nodes"),
    ("chatgpt_hidden", "ChatGPT", "hidden=0", "hidden=1"),
    ("chatgpt_direct", "ChatGPT", "select, Proxy,", "select, DIRECT, Proxy,"),
    ("bahamut_no_proxy", "Bahamut", "TaiWan, Proxy,", "TaiWan,"),
    ("telegram_auto", "Telegram", "select", "url-test"),
):
    replace_group_fragment(name, group, old, new)

# DNS privacy, rule order and fixed-resource boundary.
for name, old, new in (
    ("final_deleted", "FINAL,Final,dns-failed\n", ""),
    ("final_duplicate", "FINAL,Final,dns-failed\n", "FINAL,Final,dns-failed\nFINAL,Final,dns-failed\n"),
    ("stun_direct", "PROTOCOL,STUN,Proxy", "PROTOCOL,STUN,DIRECT"),
    ("doh_direct", "PROTOCOL,DOH,Proxy", "PROTOCOL,DOH,DIRECT"),
    ("doh3_deleted", "PROTOCOL,DOH3,Proxy\n", ""),
    ("dns_protocol_direct", "PROTOCOL,DNS,Proxy", "PROTOCOL,DNS,DIRECT"),
    ("domestic_dns_direct", "DOMAIN,dns.alidns.com,Proxy", "DOMAIN,dns.alidns.com,DIRECT"),
    ("dns_port_order", "DEST-PORT,53,REJECT\nDEST-PORT,853,REJECT", "DEST-PORT,853,REJECT\nDEST-PORT,53,REJECT"),
    ("foreign_dns_direct", "DOMAIN,dns.google,Proxy", "DOMAIN,dns.google,DIRECT"),
    ("pegasus_policy", "/Rules/Pegasus.list,REJECT,extended-matching", "/Rules/Pegasus.list,Proxy,extended-matching"),
    ("ads_policy", "/Rules/Ads.list,REJECT,no-resolve", "/Rules/Ads.list,Proxy,no-resolve"),
    ("bilibili_guard", "DOMAIN,httpdns.bilivideo.com,DIRECT\n", ""),
    ("openai_guard", "DOMAIN,rum.browser-intake-datadoghq.com,ChatGPT\n", ""),
    ("intl_guard", "DOMAIN,apiintl.biliapi.net,Proxy", "DOMAIN,apiintl.biliapi.net,DIRECT"),
    ("geoip", "GEOIP,CN,DIRECT,no-resolve", "GEOIP,CN,Proxy,no-resolve"),
    ("ipv6_tail", "IP-CIDR6,::/0,Proxy,no-resolve", "IP-CIDR6,::/0,DIRECT,no-resolve"),
):
    replace_once(name, old, new)

if len(MUTATIONS) < 65:
    raise RuntimeError(f"expected at least 65 mutations, built {len(MUTATIONS)}")

environment = dict(os.environ)
environment["PYTHONDONTWRITEBYTECODE"] = "1"
with tempfile.TemporaryDirectory(prefix="surge-audit-mutations-") as temporary:
    root = Path(temporary)
    for number, (name, mutated) in enumerate(MUTATIONS, 1):
        candidate = root / f"{number:03d}-{name}.conf"
        candidate.write_text(mutated, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(AUDITOR), str(candidate)],
            cwd=ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            raise AssertionError(f"auditor accepted mutation {name}:\n{result.stdout}")

print(f"PASS R13.15 mutations={len(MUTATIONS)}")
