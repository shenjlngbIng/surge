#!/usr/bin/env python3
"""Fault-injection regression tests for the R13.13 configuration auditor."""

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


# Header, snapshot and public-source boundary.
replace_once("version", "R13.13 Simple Subscription", "R13.12 Real Proxy Diagnostics")
replace_once("date", "# > Update Date: 2026.09.01", "# > Update Date: 2026.08.31")
replace_once("auto_claim", "# > Auto, regional and restricted-service groups use url-test with an explicit REJECT safety member.\n", "")
replace_once("subscription_claim", "# > Put one Surge-format subscription URL in NodePool; no linked profile or helper script is required.\n", "")
replace_once("capture_warning", "# > include-all-networks stays enabled for APNs/privacy capture; Surge may warn about AirDrop/Xcode.\n", "")
replace_once("snapshot_ref", "2b8fa93901061cf0482b079203630bcd11bfe0b1", "de744020e1a5ecab82a87f0749493f6adf405dd4")
replace_once("token_warning", "# > REQUIRED: replace only NodePool.policy-path locally; never publish subscription tokens.\n", "")
replace_once("missing_policy_path", "policy-path=https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL, ", "")
replace_once("duplicate_policy_path", "NodePool = select, REJECT, policy-path=", "NodePool = select, REJECT, policy-path=https://example.invalid/SECOND, policy-path=")
replace_once("wrong_subscription_placeholder", "https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL", "https://example.invalid/WRONG_SUBSCRIPTION_URL")
replace_once("mutable_main", "# Repository-hosted remote rule sets\n", "RULE-SET,https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@main/Rules/Ads.list,REJECT,no-resolve\n# Repository-hosted remote rule sets\n")
replace_once("mobile_dynamic_ads", "# Artificial intelligence\n", "DOMAIN-SET,https://ruleset.skk.moe/List/domainset/reject.conf,REJECT,update-interval=86400\n# Artificial intelligence\n")

# Complete General and access invariants.
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
replace_once("dns_server", "dns-server = 223.5.5.5, 223.6.6.6, 2400:3200::1, 2400:3200:baba::1", "dns-server = 8.8.8.8")
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
replace_once("udp_probe", "proxy-test-udp = apple.com@1.1.1.1", "proxy-test-udp = apple.com@8.8.8.8")
replace_once("internet_test_url", "internet-test-url = http://connectivitycheck.platform.hicloud.com/generate_204", "internet-test-url = http://example.com/generate_204")
replace_once("proxy_test_url", "proxy-test-url = http://cp.cloudflare.com/generate_204", "proxy-test-url = http://example.com/generate_204")
replace_once("test_timeout", "test-timeout = 5", "test-timeout = 10")
replace_once("compatibility_mode", "compatibility-mode = 3", "compatibility-mode = 2")
replace_once("reject_error_page", "show-error-page-for-reject = false", "show-error-page-for-reject = true")
replace_once("icmp_forwarding", "icmp-forwarding = false", "icmp-forwarding = true")
replace_once("geoip_auto_update", "disable-geoip-db-auto-update = false", "disable-geoip-db-auto-update = true")
replace_once("always_real_ip", "always-real-ip = <simple-hostname>, *.local,", "always-real-ip = <simple-hostname>,")
replace_once("skip_proxy_cgnat", "100.64.0.0/10, 127.0.0.0/8", "127.0.0.0/8")
replace_once("exclude_simple_hostnames", "exclude-simple-hostnames = true", "exclude-simple-hostnames = false")
replace_once("raw_tcp_telegram", "always-raw-tcp-hosts = 149.154.*, 91.108.*,", "always-raw-tcp-hosts = 91.108.*,")
replace_once("dns_svcb", "allow-dns-svcb = false", "allow-dns-svcb = true")
replace_once("local_host_for_proxy", "use-local-host-item-for-proxy = false", "use-local-host-item-for-proxy = true")

# Host, empty static-proxy boundary and fail-closed group architecture.
replace_once("substore_host", "sub.store = 127.0.0.1", "sub.store = 1.1.1.1")
replace_once("alidns_bootstrap", "dns.alidns.com = 223.5.5.5, 223.6.6.6, 2400:3200::1, 2400:3200:baba::1", "dns.alidns.com = 8.8.8.8")
replace_once("dnspod_static_bootstrap", "# AliDNS bootstrap. DNSPod's doh.pub deliberately resolves through dns-server\n", "# AliDNS bootstrap. DNSPod's doh.pub deliberately resolves through dns-server\ndoh.pub = 1.12.12.12, 120.53.53.53\n")
replace_once("fail_closed_proxy", "[Proxy]\n", "[Proxy]\nFail-Closed = reject\n")
replace_once("loopback_diagnostics", "[Proxy]\n", "[Proxy]\nDiagnostics = socks5, 127.0.0.1, 6153, udp-relay=true\n")
replace_once("unexpected_proxy", "[Proxy]\n", "[Proxy]\nUnexpected = direct\n")
replace_once("final_members", "Final = select, Proxy, REJECT,", "Final = select, DIRECT, Proxy,")
replace_once("proxy_default", "Proxy = select, Auto, NodePool, HongKong", "Proxy = select, NodePool, Auto, HongKong")
replace_once("proxy_manual_reject", "America, REJECT, no-alert=0", "America, no-alert=0")
replace_once("allserver_returned", "# Services\n", "AllServer = smart, include-other-group=NodePool\n# Services\n")
replace_once("applepush_direct_first", "ApplePush = fallback, Proxy, DIRECT", "ApplePush = fallback, DIRECT, Proxy")
replace_once("applepush_visible", "hidden=1\n# Services", "hidden=0\n# Services")
replace_group_fragment("auto_smart", "Auto", "url-test", "smart")
replace_group_fragment("auto_select", "Auto", "url-test", "select")
replace_group_fragment("auto_no_reject", "Auto", "url-test, REJECT,", "url-test,")
replace_group_fragment("auto_direct", "Auto", "url-test, REJECT,", "url-test, DIRECT,")
replace_group_fragment("auto_interval", "Auto", "interval=600", "interval=1800")
replace_group_fragment("auto_tolerance", "Auto", "tolerance=100", "tolerance=500")
replace_group_fragment("auto_no_evaluate", "Auto", "evaluate-before-use=true", "evaluate-before-use=false")
replace_group_fragment("auto_alerts_disabled", "Auto", "no-alert=0", "no-alert=1")
replace_group_fragment("auto_hidden", "Auto", "hidden=0", "hidden=1")
replace_group_fragment("auto_include_all", "Auto", "include-all-proxies=0", "include-all-proxies=1")
replace_group_fragment("auto_source", "Auto", "include-other-group=NodePool", "include-other-group=HongKong")
replace_group_fragment("auto_filter", "Auto", "Auto = url-test,", "Auto = url-test, policy-regex-filter=.+,")
replace_group_fragment("auto_extra_direct", "Auto", "url-test, REJECT,", "url-test, REJECT, DIRECT,")
replace_group_fragment("nodepool_automatic", "NodePool", "select", "smart")
replace_group_fragment("nodepool_no_reject", "NodePool", "select, REJECT,", "select,")
replace_group_fragment("nodepool_direct", "NodePool", "select, REJECT,", "select, DIRECT,")
replace_group_fragment("nodepool_hidden", "NodePool", "hidden=0", "hidden=1")
replace_group_fragment("nodepool_update_interval", "NodePool", "update-interval=3600", "update-interval=7200")
replace_group_fragment("nodepool_include_all", "NodePool", "include-all-proxies=0", "include-all-proxies=1")
replace_group_fragment("hongkong_smart", "HongKong", "url-test", "smart")
replace_group_fragment("hongkong_no_reject", "HongKong", "url-test, REJECT,", "url-test,")
replace_group_fragment("hongkong_interval", "HongKong", "interval=600", "interval=1800")
replace_group_fragment("hongkong_filter", "HongKong", "policy-regex-filter=", "removed-filter=")
replace_group_fragment("taiwan_select", "TaiWan", "url-test", "select")
replace_group_fragment("taiwan_tolerance", "TaiWan", "tolerance=100", "tolerance=500")
replace_group_fragment("japan_direct", "Japan", "url-test, REJECT,", "url-test, REJECT, DIRECT,")
replace_group_fragment("singapore_filter", "Singapore", "policy-regex-filter=", "removed-filter=")
replace_group_fragment("america_hidden", "America", "hidden=0", "hidden=1")
replace_group_fragment("america_no_evaluate", "America", "evaluate-before-use=true", "evaluate-before-use=false")
replace_group_fragment("america_filter_case", "America", "policy-regex-filter=(?i).*", "policy-regex-filter=.*")
replace_group_fragment("chatgpt_smart", "ChatGPT", "url-test", "smart")
replace_group_fragment("chatgpt_no_reject", "ChatGPT", "url-test, REJECT,", "url-test,")
replace_group_fragment("claude_hongkong", "Claude", 'include-other-group="Japan,Singapore,TaiWan,America"', 'include-other-group="HongKong,Japan,Singapore,TaiWan,America"')
replace_group_fragment("gemini_direct", "Gemini", "url-test, REJECT,", "url-test, REJECT, DIRECT,")
replace_group_fragment("tiktok_no_evaluate", "TikTok", "evaluate-before-use=true", "evaluate-before-use=false")
replace_group_fragment("chatgpt_unterminated_sources", "ChatGPT", 'include-other-group="Japan,Singapore,TaiWan,America"', 'include-other-group="Japan,Singapore,TaiWan,America')
replace_group_fragment("claude_unquoted_sources", "Claude", 'include-other-group="Japan,Singapore,TaiWan,America"', "include-other-group=Japan,Singapore,TaiWan,America")
replace_group_fragment("gemini_duplicate_source_option", "Gemini", 'include-other-group="Japan,Singapore,TaiWan,America"', 'include-other-group="Japan,Singapore,TaiWan,America", include-other-group="Japan,Singapore,TaiWan,America"')
replace_once("bahamut_japan", "Bahamut = select, TaiWan, HongKong,", "Bahamut = select, TaiWan, HongKong, Japan,")
replace_once("apple_proxy_default", "Apple = select, DIRECT, Proxy,", "Apple = select, Proxy, DIRECT,")
replace_once("github_allserver", "GitHub = select, Proxy, HongKong, Japan, Singapore, America,", "GitHub = select, Proxy, HongKong, Japan, Singapore, America, AllServer,")
replace_group_fragment("telegram_hidden", "Telegram", "hidden=0", "hidden=1")
replace_once("domestic_group_returned", "# Services\n", "Domestic = select, DIRECT, Proxy\n# Services\n")
replace_once("adblock_group_returned", "# Services\n", "AdBlock = select, REJECT, DIRECT\n# Services\n")
replace_once("security_group_returned", "# Services\n", "Security = select, REJECT, DIRECT\n# Services\n")
replace_once("udp_group_returned", "# Services\n", "UDP = select, Proxy, REJECT, DIRECT\n# Services\n")
replace_once("smart_group_returned", "# Subscription\n", "Smart = smart, include-other-group=NodePool\n# Subscription\n")
replace_once("unknown_member", "Games = select, Proxy, HongKong", "Games = select, UnknownPolicy, Proxy, HongKong")
replace_once("policy_cycle", "Proxy = select, Auto, NodePool, HongKong", "Proxy = select, Final, Auto, NodePool, HongKong")

# Rule order, fixed policies and mobile source boundary.
replace_once("final_deleted", "FINAL,Final,dns-failed\n", "")
replace_once("final_duplicated", "FINAL,Final,dns-failed\n", "FINAL,Final,dns-failed\nFINAL,Final,dns-failed\n")
replace_once("stun_direct", "PROTOCOL,STUN,Proxy", "PROTOCOL,STUN,DIRECT")
replace_once("diagnostics_proxy_returned", "[Proxy]\n", "[Proxy]\nDiagnostics = socks5, 127.0.0.1, 6153, udp-relay=true\n")
replace_once("diagnostics_tcp_rule_returned", "# Reviewed mainland resolver hostnames", "DOMAIN,cp.cloudflare.com,Proxy\n# Reviewed mainland resolver hostnames")
replace_once("domestic_dns_proxy", "DOMAIN,dns.alidns.com,DIRECT", "DOMAIN,dns.alidns.com,Proxy")
replace_once("dns_port_order", "DEST-PORT,53,REJECT\nDEST-PORT,853,REJECT", "DEST-PORT,853,REJECT\nDEST-PORT,53,REJECT")
replace_once("foreign_dns_direct", "DOMAIN,dns.google,Proxy", "DOMAIN,dns.google,DIRECT")
replace_once("udp_probe_ip_deleted", "IP-CIDR,1.1.1.1/32,Proxy,no-resolve\n", "")
MUTATIONS.append((
    "udp_probe_ip_before_dns_reject",
    SOURCE.replace("IP-CIDR,1.1.1.1/32,Proxy,no-resolve\n", "", 1).replace(
        "# Reviewed mainland resolver hostnames",
        "IP-CIDR,1.1.1.1/32,Proxy,no-resolve\n# Reviewed mainland resolver hostnames",
        1,
    ),
))
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

EXPECTED_MUTATIONS = 135
if len(MUTATIONS) != EXPECTED_MUTATIONS:
    raise RuntimeError(f"expected {EXPECTED_MUTATIONS} mutations, built {len(MUTATIONS)}")

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

print(f"PASS R13.13 mutations={len(MUTATIONS)}")
