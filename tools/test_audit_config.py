#!/usr/bin/env python3
"""Fault-injection regression tests for the R13.25 configuration auditor."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from convert_to_remote_rules import FOREIGN_DNS_RULES


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
    ("version", "R13.25 Service Regions + Latency + Sentinel", "R13.16 Fail-Closed Sentinel"),
    ("date", "# 更新 2026.09.09", "# 更新 2026.09.01"),
    ("layout_claim", "29 份外置规则", "内嵌规则"),
    ("subscription_claim", "桔子 的订阅地址", "NodePool 的订阅地址"),
    ("attribution", "# 作者 .ᐣ", "# 作者 unknown"),
    ("snapshot_ref", "6e8e1bfbbdda66ee8ad0a5ad3979b6de8b5b7a51", "de744020e1a5ecab82a87f0749493f6adf405dd4"),
    ("token_warning", "勿公开凭据", "可公开凭据"),
    ("missing_policy_path", "policy-path=https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL, ", ""),
    ("duplicate_policy_path", "桔子 = select, REJECT, policy-path=", "桔子 = select, REJECT, policy-path=https://example.invalid/SECOND, policy-path="),
    ("wrong_placeholder", "https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL", "https://example.invalid/WRONG_SUBSCRIPTION_URL"),
):
    replace_once(name, old, new)

replace_once("mutable_main", "[Rule]\n", "[Rule]\nRULE-SET,https://raw.githubusercontent.com/shenjlngbIng/surge/main/Rules/Ads.list,AdBlock,no-resolve\n")
replace_once("mobile_dynamic_ads", "[Rule]\n", "[Rule]\nDOMAIN-SET,https://ruleset.skk.moe/List/domainset/reject.conf,REJECT,update-interval=86400\n")

# General, DNS and access invariants.
for name, old, new in (
    ("loglevel", "loglevel = notify", "loglevel = debug"),
    ("ipv6", "ipv6 = true", "ipv6 = false"),
    ("ipv6_vif", "ipv6-vif = auto", "ipv6-vif = off"),
    ("include_all", "include-all-networks = true", "include-all-networks = false"),
    ("include_apns", "include-apns = true", "include-apns = false"),
    ("dns_server", "dns-server = 223.5.5.5, 223.6.6.6, 2400:3200::1, 2400:3200:baba::1", "dns-server = 8.8.8.8"),
    ("encrypted_dns", "encrypted-dns-server = https://dns.alidns.com/dns-query, https://doh.pub/dns-query", "encrypted-dns-server = https://dns.google/dns-query"),
    ("dns_follow", "encrypted-dns-follow-outbound-mode = false", "encrypted-dns-follow-outbound-mode = true"),
    ("dns_cert", "encrypted-dns-skip-cert-verification = false", "encrypted-dns-skip-cert-verification = true"),
    ("hijack_dns", "hijack-dns = *:53", "hijack-dns = 8.8.8.8:53"),
    ("local_host_proxy", "use-local-host-item-for-proxy = false", "use-local-host-item-for-proxy = true"),
    ("wifi_access", "allow-wifi-access = false", "allow-wifi-access = true"),
    ("hotspot_access", "allow-hotspot-access = false", "allow-hotspot-access = true"),
    ("udp_unsupported", "udp-policy-not-supported-behaviour = REJECT", "udp-policy-not-supported-behaviour = DIRECT"),
    ("quic", "block-quic = per-policy", "block-quic = off"),
    ("udp_probe", "proxy-test-udp = apple.com@1.1.1.1", "proxy-test-udp = apple.com@8.8.8.8"),
):
    replace_once(name, old, new)

for name, option in (
    ("auto_suspend", "auto-suspend = false"),
    ("wifi_assist", "wifi-assist = true"),
    ("proxy_lan", "proxy-restricted-to-lan = false"),
    ("gateway_lan", "gateway-restricted-to-lan = false"),
    ("all_hybrid", "all-hybrid = true"),
    ("error_page", "show-error-page-for-reject = true"),
    ("geoip_update", "disable-geoip-db-auto-update = true"),
    ("web_dashboard", "http-api-web-dashboard = true"),
):
    replace_once(name, "[General]\n", f"[General]\n{option}\n")

# Host, static proxy and restored full-group architecture.
for name, old, new in (
    ("substore_host", "sub.store = 127.0.0.1", "sub.store = 1.1.1.1"),
    ("alidns_bootstrap", "dns.alidns.com = 223.5.5.5, 223.6.6.6, 2400:3200::1, 2400:3200:baba::1", "dns.alidns.com = 8.8.8.8"),
    ("embedded_reject", "[Proxy]\n", "[Proxy]\nFail-Closed = reject\n"),
    ("loopback_diagnostics", "[Proxy]\n", "[Proxy]\nDiagnostics = socks5, 127.0.0.1, 6153, udp-relay=true\n"),
    ("final_members", "Final = select, Proxy, DIRECT\n", "Final = select, Proxy, REJECT\n"),
    ("final_hidden", "Final = select, Proxy, DIRECT\n", "Final = select, Proxy, DIRECT, hidden=1\n"),
    ("applepush_order", "ApplePush = fallback, Proxy, Auto, DIRECT", "ApplePush = fallback, DIRECT, Proxy, Auto"),
    ("applepush_missing_auto", "ApplePush = fallback, Proxy, Auto, DIRECT", "ApplePush = fallback, Proxy, DIRECT"),
    ("applepush_missing_direct", "ApplePush = fallback, Proxy, Auto, DIRECT", "ApplePush = fallback, Proxy, Auto"),
    ("apple_order", "Apple = select, DIRECT, Proxy,", "Apple = select, Proxy, DIRECT,"),
    ("unexpected_allserver", "[Proxy Group]\n", "[Proxy Group]\nAllServer = smart, include-other-group=桔子\n"),
):
    replace_once(name, old, new)

for name, group, old, new in (
    ("proxy_smart", "Proxy", "select", "smart"),
    ("proxy_reject", "Proxy", "Proxy = select,", "Proxy = select, REJECT,"),
    ("proxy_missing_auto", "Proxy", "Auto, ", ""),
    ("proxy_hidden", "Proxy", "\n", ", hidden=1\n"),
    ("proxy_include_all", "Proxy", "\n", ", include-all-proxies=1\n"),
    ("nodepool_reject", "NodePool", "NodePool = select,", "NodePool = select, REJECT,"),
    ("source_update", "桔子", "update-interval=3600", "update-interval=7200"),
    ("nodepool_hidden", "NodePool", "\n", ", hidden=1\n"),
    ("nodepool_include_all", "NodePool", "\n", ", include-all-proxies=1\n"),
    ("auto_select", "Auto", "smart", "select"),
    ("auto_missing_sentinel", "Auto", "smart, Fail-Closed,", "smart,"),
    ("auto_no_evaluate", "Auto", "evaluate-before-use=true", "evaluate-before-use=false"),
    ("auto_hidden", "Auto", "\n", ", hidden=1\n"),
    ("auto_wrong_source", "Auto", "include-other-group=桔子", "include-other-group=America"),
    ("region_empty_guard", "HongKong-Nodes", "url-test, REJECT,", "url-test,"),
    ("region_source_visible", "HongKong-Nodes", "hidden=1", "hidden=0"),
    ("region_source_wrong_group", "HongKong-Nodes", "include-other-group=桔子", "include-other-group=Auto"),
    ("region_fallback_deleted", "HongKong", "HongKong-Nodes, Auto", "HongKong-Nodes"),
    ("chatgpt_hidden", "ChatGPT", "\n", ", hidden=1\n"),
    ("chatgpt_direct", "ChatGPT", "url-test, Fail-Closed,", "url-test, DIRECT, Fail-Closed,"),
    ("bahamut_cross_region", "Bahamut", "TaiWan-Nodes", "HongKong-Nodes"),
    ("telegram_manual", "Telegram", "url-test", "select"),
):
    replace_group_fragment(name, group, old, new)

for name, group, old, new in (
    ("fast_missing_sentinel", "Fast", "url-test, Fail-Closed,", "url-test,"),
    ("fast_old_tolerance", "Fast", "tolerance=0", "tolerance=100"),
    ("fast_wrong_interval", "Fast", "interval=300", "interval=600"),
    ("service_old_tolerance", "ChatGPT", "tolerance=0", "tolerance=100"),
    ("service_missing_sentinel", "ChatGPT", "url-test, Fail-Closed,", "url-test,"),
    ("service_outer_fallback", "ChatGPT", "America-Nodes", "America"),
    ("service_wrong_region", "ChatGPT", "TaiWan-Nodes", "HongKong-Nodes"),
    ("hbo_wrong_region", "HBO", "TaiWan-Nodes", "Japan-Nodes"),
    ("test_url_override", "桔子", "test-url=http://cp.cloudflare.com/generate_204", "test-url=http://example.invalid/"),
    ("test_timeout_override", "桔子", "test-timeout=5", "test-timeout=10"),
):
    replace_group_fragment(name, group, old, new)
replace_once("hulu_wrong_region", "DOMAIN-SUFFIX,hulu.com,America-Nodes", "DOMAIN-SUFFIX,hulu.com,HongKong-Nodes")
replace_once("now_cross_region_fallback", "DOMAIN-SUFFIX,now.com,HongKong-Nodes", "DOMAIN-SUFFIX,now.com,HongKong")

# DNS privacy, rule order and fixed-resource boundary.
for name, old, new in (
    ("final_deleted", "FINAL,Final,dns-failed\n", ""),
    ("final_duplicate", "FINAL,Final,dns-failed\n", "FINAL,Final,dns-failed\nFINAL,Final,dns-failed\n"),
    ("stun_direct", "PROTOCOL,STUN,UDP", "PROTOCOL,STUN,DIRECT"),
    ("resource_transport", "DOMAIN-SUFFIX,jsdelivr.net,Proxy", "DOMAIN-SUFFIX,jsdelivr.net,DIRECT"),
    ("own_dns_rule_returned", "[Rule]\n", "[Rule]\nPROTOCOL,DOH,DIRECT\n"),
    ("domestic_dns_direct", "DOMAIN-SUFFIX,alidns.com,Proxy", "DOMAIN-SUFFIX,alidns.com,DIRECT"),
    ("dns_port_order", "DEST-PORT,853,REJECT\nDEST-PORT,8853,REJECT", "DEST-PORT,8853,REJECT\nDEST-PORT,853,REJECT"),
    ("foreign_dns_direct", "DOMAIN,dns.google,Proxy", "DOMAIN,dns.google,DIRECT"),
    ("pegasus_policy", "Rules/Pegasus.list,Security,extended-matching", "Rules/Pegasus.list,Proxy,extended-matching"),
    ("ads_policy", "Rules/Ads.list,AdBlock,no-resolve", "Rules/Ads.list,Proxy,no-resolve"),
    ("bilibili_guard", "DOMAIN,httpdns.bilivideo.com,DIRECT\n", ""),
    ("openai_guard", "DOMAIN,rum.browser-intake-datadoghq.com,ChatGPT\n", ""),
    ("intl_guard", "DOMAIN,apiintl.biliapi.net,Proxy", "DOMAIN,apiintl.biliapi.net,DIRECT"),
    ("geoip", "GEOIP,CN,Domestic,no-resolve", "GEOIP,CN,Proxy,no-resolve"),
    ("ipv6_tail", "IP-CIDR6,::/0,Proxy,no-resolve", "IP-CIDR6,::/0,DIRECT,no-resolve"),
):
    replace_once(name, old, new)

foreign_block = "\n".join(FOREIGN_DNS_RULES) + "\n"
without_foreign = SOURCE.replace(foreign_block, "", 1)
MUTATIONS.append(("foreign_dns_after_encrypted_reject", without_foreign.replace(
    "DEST-PORT,8853,REJECT\n", "DEST-PORT,8853,REJECT\n" + foreign_block, 1,
)))
MUTATIONS.append(("foreign_dns_before_plaintext_reject", without_foreign.replace(
    "DEST-PORT,53,REJECT\n", foreign_block + "DEST-PORT,53,REJECT\n", 1,
)))

for name, group, old, new in (
    ("source_empty_guard", "桔子", "select, REJECT,", "select,"),
    ("source_udp_flag", "桔子", "udp-relay=true", "udp-relay=false"),
    ("source_visible", "桔子", "hidden=1", "hidden=0"),
    ("manual_default_guard", "NodePool", "select, Auto,", "select,"),
    ("manual_cycle", "NodePool", "include-other-group=桔子", "include-other-group=NodePool"),
    ("adblock_default", "AdBlock", "select, REJECT,", "select, DIRECT,"),
    ("security_default", "Security", "select, REJECT,", "select, DIRECT,"),
):
    replace_group_fragment(name, group, old, new)
replace_once("raw_transport", "DOMAIN,raw.githubusercontent.com,Auto", "DOMAIN,raw.githubusercontent.com,DIRECT")
replace_once("raw_manual_dependency", "DOMAIN,raw.githubusercontent.com,Auto", "DOMAIN,raw.githubusercontent.com,Proxy")
replace_once("udp_control", "PROTOCOL,UDP,UDP", "PROTOCOL,UDP,Proxy")
replace_once("domestic_control", "Rules/China.list,Domestic,", "Rules/China.list,DIRECT,")
replace_once("sentinel_deleted", "Fail-Closed = http, 127.0.0.1, 1, no-error-alert=true\n", "")

for auxiliary in ("AdBlock", "Security", "UDP", "Domestic"):
    replace_group_fragment(f"{auxiliary}_visible", auxiliary, "hidden=1", "hidden=0")

for number, option in enumerate(("no-alert=0", "hidden=0", "include-all-proxies=0"), 1):
    replace_group_fragment(f"redundant_default_{number}", "Proxy", "\n", f", {option}\n")
replace_once("alidns_duplicate_returned", "DOMAIN-SUFFIX,alidns.com,Proxy\n", "DOMAIN,dns.alidns.com,Proxy\nDOMAIN-SUFFIX,alidns.com,Proxy\n")
replace_once("nextdns_suffix_deleted", "DOMAIN-SUFFIX,nextdns.io,Proxy\n", "")

if len(MUTATIONS) < 65:
    raise RuntimeError(f"expected at least 65 mutations, built {len(MUTATIONS)}")

environment = dict(os.environ)
environment["PYTHONDONTWRITEBYTECODE"] = "1"
baseline = subprocess.run(
    [sys.executable, str(AUDITOR)], cwd=ROOT, env=environment,
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False,
)
if baseline.returncode != 0:
    raise AssertionError(f"auditor rejected the valid baseline:\n{baseline.stdout}")
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

print(f"PASS R13.25 mutations={len(MUTATIONS)}")
