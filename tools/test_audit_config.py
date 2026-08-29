#!/usr/bin/env python3
"""Fault-injection regression tests for the R13.5 configuration auditor."""

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


# Header, snapshot and public-source boundary (1-8).
replace_once("version", "R13.5 Strict Fail-Closed", "R13.4 Strict DNS")
replace_once("date", "# > Update Date: 2026.08.29", "# > Update Date: 2026.08.28")
replace_once("header_claim", "Manual proxy and region groups prevent", "Automatic groups allegedly prevent")
replace_once("snapshot_ref", "2b8fa93901061cf0482b079203630bcd11bfe0b1", "de744020e1a5ecab82a87f0749493f6adf405dd4")
replace_once("token_warning", "# > REQUIRED: replace NodePool.policy-path locally; never publish subscription tokens.\n", "")
replace_once("subscription_placeholder", "https://example.invalid/REPLACE_WITH_SUB_STORE_URL", "https://example.com/private-subscription")
replace_once("mutable_main", "# Repository-hosted remote rule sets\n", "RULE-SET,https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@main/Rules/Ads.list,REJECT,no-resolve\n# Repository-hosted remote rule sets\n")
replace_once("mobile_dynamic_ads", "# Artificial intelligence\n", "DOMAIN-SET,https://ruleset.skk.moe/List/domainset/reject.conf,REJECT,update-interval=86400\n# Artificial intelligence\n")

# General and access invariants (9-31).
replace_once("loglevel", "loglevel = notify", "loglevel = debug")
replace_once("auto_suspend", "auto-suspend = true", "auto-suspend = false")
replace_once("ipv6", "ipv6 = true", "ipv6 = false")
replace_once("ipv6_vif", "ipv6-vif = auto", "ipv6-vif = off")
replace_once("wifi_assist", "wifi-assist = false", "wifi-assist = true")
replace_once("all_hybrid", "all-hybrid = false", "all-hybrid = true")
replace_once("include_all", "include-all-networks = true", "include-all-networks = false")
replace_once("include_local", "include-local-networks = false", "include-local-networks = true")
replace_once("include_apns", "include-apns = true", "include-apns = false")
replace_once("include_cellular", "include-cellular-services = false", "include-cellular-services = true")
replace_once("dns_server", "dns-server = 223.5.5.5, 223.6.6.6", "dns-server = 8.8.8.8")
replace_once("encrypted_dns", "encrypted-dns-server = https://dns.alidns.com/dns-query, https://doh.pub/dns-query", "encrypted-dns-server = https://dns.google/dns-query")
replace_once("dns_follow_outbound", "encrypted-dns-follow-outbound-mode = false", "encrypted-dns-follow-outbound-mode = true")
replace_once("dns_cert", "encrypted-dns-skip-cert-verification = false", "encrypted-dns-skip-cert-verification = true")
replace_once("hijack_dns", "hijack-dns = *:53", "hijack-dns = 8.8.8.8:53")
replace_once("wifi_access", "allow-wifi-access = false", "allow-wifi-access = true")
replace_once("hotspot_access", "allow-hotspot-access = false", "allow-hotspot-access = true")
replace_once("dashboard", "http-api-web-dashboard = false", "http-api-web-dashboard = true")
replace_once("proxy_lan", "proxy-restricted-to-lan = true", "proxy-restricted-to-lan = false")
replace_once("gateway_lan", "gateway-restricted-to-lan = true", "gateway-restricted-to-lan = false")
replace_once("udp_unsupported", "udp-policy-not-supported-behaviour = REJECT", "udp-policy-not-supported-behaviour = DIRECT")
replace_once("quic", "block-quic = per-policy", "block-quic = off")
replace_once("udp_probe", "proxy-test-udp = apple.com@9.9.9.9", "proxy-test-udp = apple.com@8.8.8.8")

# Host, built-in alias and group architecture (32-60).
replace_once("substore_host", "sub.store = 127.0.0.1", "sub.store = 1.1.1.1")
replace_once("alidns_bootstrap", "dns.alidns.com = 223.5.5.5, 223.6.6.6, 2400:3200::1", "dns.alidns.com = 8.8.8.8")
replace_once("dnspod_bootstrap", "doh.pub = 1.12.12.12, 120.53.53.53", "doh.pub = 8.8.4.4")
replace_once("fail_closed_proxy", "Fail-Closed = reject", "Fail-Closed = direct")
replace_once("extra_proxy", "Fail-Closed = reject\n\n[Proxy Group]", "Fail-Closed = reject\nUnexpected = direct\n\n[Proxy Group]")
replace_once("final_members", "Final = select, Proxy, REJECT,", "Final = select, DIRECT, Proxy,")
replace_once("proxy_default", "Proxy = select, NodePool, HongKong", "Proxy = select, HongKong, NodePool")
replace_once("allserver_returned", "# Services\n", "AllServer = smart, Fail-Closed, include-other-group=NodePool\n# Services\n")
replace_once("applepush_direct_first", "ApplePush = fallback, Proxy, DIRECT", "ApplePush = fallback, DIRECT, Proxy")
replace_once("applepush_visible", "hidden=1\n# Services", "hidden=0\n# Services")
replace_once("nodepool_automatic", "NodePool = select, Fail-Closed", "NodePool = url-test, Fail-Closed")
replace_once("nodepool_no_fail", "NodePool = select, Fail-Closed, policy-path", "NodePool = select, policy-path")
replace_once("nodepool_hidden", "update-interval=3600, no-alert=0, hidden=0, include-all-proxies=0\n\n# Regions", "update-interval=3600, no-alert=0, hidden=1, include-all-proxies=0\n\n# Regions")
replace_once("hongkong_smart", "HongKong = select, Fail-Closed", "HongKong = smart, Fail-Closed")
replace_once("taiwan_no_fail", "TaiWan = select, Fail-Closed,", "TaiWan = select,")
replace_once("japan_source", "Japan = select, Fail-Closed,", "Japan = select, Fail-Closed, NodePool,")
replace_once("singapore_filter", "Singapore = select, Fail-Closed, policy-regex-filter=", "Singapore = select, Fail-Closed, removed-filter=")
replace_once("america_hidden", "America = select, Fail-Closed,", "America = select, Fail-Closed, hidden=1,")
replace_once("chatgpt_proxy", "ChatGPT = select, Japan, Singapore, TaiWan, America,", "ChatGPT = select, Japan, Singapore, TaiWan, America, Proxy,")
replace_once("claude_hongkong", "Claude = select, Japan, Singapore, TaiWan, America,", "Claude = select, Japan, Singapore, TaiWan, America, HongKong,")
replace_once("gemini_hongkong", "Gemini = select, Japan, Singapore, TaiWan, America,", "Gemini = select, HongKong, Japan, Singapore, TaiWan, America,")
replace_once("tiktok_hongkong", "TikTok = select, Japan, Singapore, TaiWan, America,", "TikTok = select, HongKong, Japan, Singapore, TaiWan, America,")
replace_once("bahamut_japan", "Bahamut = select, TaiWan, HongKong,", "Bahamut = select, TaiWan, HongKong, Japan,")
replace_once("apple_proxy_default", "Apple = select, DIRECT, Proxy,", "Apple = select, Proxy, DIRECT,")
replace_once("github_allserver", "GitHub = select, Proxy, HongKong, Japan, Singapore, America,", "GitHub = select, Proxy, HongKong, Japan, Singapore, America, AllServer,")
replace_once("domestic_group_returned", "# Services\n", "Domestic = select, DIRECT, Proxy\n# Services\n")
replace_once("adblock_group_returned", "# Services\n", "AdBlock = select, REJECT, DIRECT\n# Services\n")
replace_once("unknown_member", "Games = select, Proxy, HongKong", "Games = select, UnknownPolicy, Proxy, HongKong")
replace_once("policy_cycle", "Proxy = select, NodePool, HongKong", "Proxy = select, Final, NodePool, HongKong")

# Rule order, fixed policies and mobile source boundary (61-82).
replace_once("final_deleted", "FINAL,Final,dns-failed\n", "")
replace_once("final_duplicated", "FINAL,Final,dns-failed\n", "FINAL,Final,dns-failed\nFINAL,Final,dns-failed\n")
replace_once("stun_direct", "PROTOCOL,STUN,Proxy", "PROTOCOL,STUN,DIRECT")
replace_once("domestic_dns_proxy", "DOMAIN,dns.alidns.com,DIRECT", "DOMAIN,dns.alidns.com,Proxy")
replace_once("dns_port_order", "DEST-PORT,53,REJECT\nDEST-PORT,853,REJECT", "DEST-PORT,853,REJECT\nDEST-PORT,53,REJECT")
replace_once("foreign_dns_direct", "DOMAIN,dns.google,Proxy", "DOMAIN,dns.google,DIRECT")
replace_once("mobile_dynamic_phishing", "# Historical Pegasus IOC defense-in-depth", "DOMAIN-SET,https://ruleset.skk.moe/List/domainset/reject_phishing.conf,REJECT,update-interval=86400\n# Historical Pegasus IOC defense-in-depth")
replace_once("pegasus_policy", "/Rules/Pegasus.list,REJECT,extended-matching", "/Rules/Pegasus.list,Security,extended-matching")
replace_once("apns_extended", "/Rules/APNs.list,ApplePush,extended-matching,no-resolve", "/Rules/APNs.list,ApplePush,no-resolve")
replace_once("ads_extended", "/Rules/Ads.list,REJECT,no-resolve", "/Rules/Ads.list,REJECT,extended-matching,no-resolve")
replace_once("ads_policy", "/Rules/Ads.list,REJECT,no-resolve", "/Rules/Ads.list,AdBlock,no-resolve")
replace_once("bilibili_httpdns", "DOMAIN,httpdns.bilivideo.com,DIRECT\n", "")
replace_once("bilibili_h5", "DOMAIN,line3-h5-mobile-api.biligame.com,DIRECT\n", "")
replace_once("spotify_audio", "DOMAIN,audio-ak.cdn.spotify.com,Spotify\n", "")
replace_once("google_gvt2", "DOMAIN-SUFFIX,gvt2.com,Google\n", "")
replace_once("openai_rum", "DOMAIN,rum.browser-intake-datadoghq.com,ChatGPT\n", "")
replace_once("intl_guard", "DOMAIN,apiintl.biliapi.net,Proxy", "DOMAIN,apiintl.biliapi.net,DIRECT")
replace_once("bilibili_policy", "/Rules/BiliBili.list,DIRECT,extended-matching", "/Rules/BiliBili.list,Domestic,extended-matching")
replace_once("dynamic_domestic_policy", "domestic.conf,DIRECT,extended-matching", "domestic.conf,Domestic,extended-matching")
replace_once("china_policy", "/Rules/China.list,DIRECT,extended-matching", "/Rules/China.list,Domestic,extended-matching")
replace_once("geoip_policy", "GEOIP,CN,DIRECT,no-resolve", "GEOIP,CN,Domestic,no-resolve")
replace_once("ipv6_direct", "IP-CIDR6,::/0,Proxy,no-resolve", "IP-CIDR6,::/0,DIRECT,no-resolve")

if len(MUTATIONS) != 82:
    raise RuntimeError(f"expected 82 mutations, built {len(MUTATIONS)}")

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

print(f"PASS R13.5 mutations={len(MUTATIONS)}")
