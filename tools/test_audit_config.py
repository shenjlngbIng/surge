#!/usr/bin/env python3
"""Mutation regression tests for the R13.4 configuration auditor."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from convert_to_remote_rules import (
    DYNAMIC_RULES,
    REMOTE_BASE,
    RULE_SNAPSHOT_TAG,
    dynamic_line,
    repository_line,
)


ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "tools" / "audit_config.py"
BASE = (ROOT / "Surge.conf").read_text(encoding="utf-8")


def run(text: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        profile = Path(directory) / "Surge.conf"
        profile.write_text(text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(AUDIT), str(profile)],
            capture_output=True,
            text=True,
            check=False,
        )


def rr(kind: str, filename: str, policy: str) -> str:
    return repository_line(kind, filename, policy)


baseline = run(BASE)
if baseline.returncode != 0:
    raise AssertionError(f"baseline failed:\n{baseline.stdout}{baseline.stderr}")

cases: list[tuple[str, str]] = []


def replace_once(name: str, old: str, new: str) -> None:
    count = BASE.count(old)
    if count != 1:
        raise AssertionError(f"mutation anchor count for {name}: expected 1, got {count}")
    cases.append((name, BASE.replace(old, new, 1)))


def swap_once(name: str, left: str, right: str) -> None:
    if BASE.count(left) != 1 or BASE.count(right) != 1:
        raise AssertionError(f"swap anchor missing or duplicated: {name}")
    marker = f"__R13_MUTATION_{name}__"
    changed = BASE.replace(left, marker, 1).replace(right, left, 1).replace(marker, right, 1)
    cases.append((name, changed))


# Header, section, global privacy, DNS, and access invariants.
replace_once("author", "# > Surge Config Make by .ᐣ", "# > Surge Config Make by unknown")
replace_once("date", "# > Update Date: 2026.08.28", "# > Update Date: 2026.08.27")
replace_once("version", "Surge iOS Privacy + Push R13.4 Strict DNS", "Surge iOS Privacy + Push R13.3 Domestic Performance")
replace_once("preservation_header", "# > Privacy-hardening correction based on R13.3; no policy group, rule, remote resource, or subscription entry was removed.\n", "")
replace_once("snapshot_header", "# > Static repository rules remain pinned to commit d1d714d575d5494ef1a7613238f4f301e1b293df (2026.08.25).\n", "")
replace_once("token_warning", "# > REQUIRED: replace NodePool.policy-path locally; never publish subscription tokens.\n", "")
replace_once("duplicate_section", "[Host]\n", "[Host]\n[Host]\n")
replace_once("loglevel", "loglevel = notify", "loglevel = warning")
replace_once("auto_suspend", "auto-suspend = true", "auto-suspend = false")
replace_once("internet_probe", "internet-test-url = http://connectivitycheck.platform.hicloud.com/generate_204", "internet-test-url = http://example.com/")
replace_once("proxy_probe", "proxy-test-url = http://cp.cloudflare.com/generate_204", "proxy-test-url = http://example.com/")
replace_once("test_timeout", "test-timeout = 5", "test-timeout = 10")
replace_once("udp_probe", "proxy-test-udp = apple.com@9.9.9.9", "proxy-test-udp = apple.com@223.5.5.5")
replace_once("ipv6", "ipv6 = true", "ipv6 = false")
replace_once("wifi_assist", "wifi-assist = false", "wifi-assist = true")
replace_once("capture_all", "include-all-networks = true", "include-all-networks = false")
replace_once("capture_apns", "include-apns = true", "include-apns = false")
replace_once("capture_cellular", "include-cellular-services = false", "include-cellular-services = true")
replace_once("cgnat_skip", ", 100.64.0.0/10,", ",")
replace_once("dns_server", "dns-server = 223.5.5.5, 223.6.6.6", "dns-server = system")
replace_once("encrypted_dns", "encrypted-dns-server = https://dns.alidns.com/dns-query, https://doh.pub/dns-query", "encrypted-dns-server = https://dns.alidns.com/dns-query")
replace_once("dns_follow", "encrypted-dns-follow-outbound-mode = false", "encrypted-dns-follow-outbound-mode = true")
replace_once("dns_cert", "encrypted-dns-skip-cert-verification = false", "encrypted-dns-skip-cert-verification = true")
replace_once("hijack_dns", "hijack-dns = *:53", "hijack-dns = false")
replace_once("wifi_access", "allow-wifi-access = false", "allow-wifi-access = true")
replace_once("hotspot_access", "allow-hotspot-access = false", "allow-hotspot-access = true")
replace_once("dashboard", "http-api-web-dashboard = false", "http-api-web-dashboard = true")
replace_once("udp_unsupported", "udp-policy-not-supported-behaviour = REJECT", "udp-policy-not-supported-behaviour = DIRECT")
replace_once("block_quic", "block-quic = per-policy", "block-quic = all-proxy")
replace_once("mac_hosts", "# Access\n", "read-etc-hosts = true\n\n# Access\n")
replace_once("substore_host", "sub.store = 127.0.0.1", "sub.store = 1.1.1.1")
replace_once("alidns_bootstrap", "dns.alidns.com = 223.5.5.5, 223.6.6.6, 2400:3200::1", "dns.alidns.com = 223.5.5.5")
replace_once("dnspub_bootstrap", "doh.pub = 1.12.12.12, 120.53.53.53", "doh.pub = 1.1.1.1")
replace_once("fail_closed", "Fail-Closed = http, 127.0.0.1, 1, no-error-alert=true", "Fail-Closed = http, 127.0.0.1, 1")

# Policy architecture, defaults, visibility, and source ownership.
replace_once("final_direct", "Final = select, Proxy, REJECT, no-alert=0", "Final = select, Proxy, DIRECT, no-alert=0")
replace_once("proxy_default", "Proxy = select, AllServer, NodePool", "Proxy = select, NodePool, AllServer")
replace_once("proxy_cycle", "Proxy = select, AllServer, NodePool", "Proxy = select, Final, NodePool")
replace_once("applepush_order", "ApplePush = fallback, Proxy, DIRECT, interval=60", "ApplePush = fallback, DIRECT, Proxy, interval=60")
replace_once("applepush_mode", "ApplePush = fallback, Proxy, DIRECT", "ApplePush = select, Proxy, DIRECT")
replace_once("applepush_eval", "interval=60, evaluate-before-use=true, no-alert=0, hidden=1", "interval=60, no-alert=0, hidden=1")
replace_once("adblock_off", "AdBlock = select, REJECT, REJECT-DROP, DIRECT,", "AdBlock = select, REJECT, REJECT-DROP,")
replace_once("security_off", "Security = select, REJECT, REJECT-DROP, DIRECT,", "Security = select, REJECT, REJECT-DROP,")
replace_once("adblock_visible", "AdBlock = select, REJECT, REJECT-DROP, DIRECT, no-alert=0, hidden=1", "AdBlock = select, REJECT, REJECT-DROP, DIRECT, no-alert=0, hidden=0")
replace_once("security_visible", "Security = select, REJECT, REJECT-DROP, DIRECT, no-alert=0, hidden=1", "Security = select, REJECT, REJECT-DROP, DIRECT, no-alert=0, hidden=0")
replace_once("udp_order", "UDP = select, Proxy, NodePool, REJECT, DIRECT,", "UDP = select, NodePool, Proxy, REJECT, DIRECT,")
replace_once("udp_visible", "UDP = select, Proxy, NodePool, REJECT, DIRECT, no-alert=0, hidden=1", "UDP = select, Proxy, NodePool, REJECT, DIRECT, no-alert=0, hidden=0")
replace_once("domestic_default", "Domestic = select, DIRECT, Proxy,", "Domestic = select, Proxy, DIRECT,")
replace_once("domestic_visible", "Domestic = select, DIRECT, Proxy, no-alert=0, hidden=1", "Domestic = select, DIRECT, Proxy, no-alert=0, hidden=0")
replace_once("domestic_missing", "Domestic = select, DIRECT, Proxy, no-alert=0, hidden=1, include-all-proxies=0\n", "")
replace_once("service_direct", "ChatGPT = select, Proxy, America", "ChatGPT = select, DIRECT, America")
replace_once("apple_default", "Apple = select, DIRECT, Proxy", "Apple = select, Proxy, DIRECT")
replace_once("nodepool_mode", "NodePool = select, Fail-Closed,", "NodePool = url-test, Fail-Closed,")
replace_once("nodepool_sentinel", "NodePool = select, Fail-Closed,", "NodePool = select,")
replace_once("nodepool_hidden", "policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL, update-interval=3600, no-alert=0, hidden=0", "policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL, update-interval=3600, no-alert=0, hidden=1")
replace_once("private_subscription", "policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL", "policy-path=https://private.example/user-token")
replace_once("subscription_secret", "policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL", "policy-path=https://example.invalid/nodes?token=secret")
replace_once("nodepool_probe", "NodePool = select, Fail-Closed, policy-path=", "NodePool = select, Fail-Closed, interval=60, policy-path=")
replace_once("allserver_mode", "AllServer = smart, Fail-Closed,", "AllServer = url-test, Fail-Closed,")
replace_once("allserver_sentinel", "AllServer = smart, Fail-Closed,", "AllServer = smart,")
replace_once("allserver_interval", "AllServer = smart, Fail-Closed, evaluate-before-use=true,", "AllServer = smart, Fail-Closed, interval=1800, evaluate-before-use=true,")
replace_once("allserver_source", "include-other-group=NodePool\n\n# Regions", "include-other-group=HongKong\n\n# Regions")
replace_once("region_mode", "HongKong = smart, Fail-Closed,", "HongKong = select, Fail-Closed,")
replace_once("region_filter", "Singapore = smart, Fail-Closed, evaluate-before-use=true, policy-regex-filter=", "Singapore = smart, Fail-Closed, evaluate-before-use=true, policy-filter=")
replace_once("region_source", "include-other-group=NodePool\nJapan =", "include-other-group=AllServer\nJapan =")
replace_once("rogue_policy_path", "GitHub = select, Proxy,", "GitHub = select, policy-path=https://example.invalid/nodes, Proxy,")
replace_once("undefined_group", "Claude = select, Proxy, America", "Claude = select, MissingPolicy, America")

# Embedded content, immutable remote resources, policies, and precedence.
pegasus_remote = rr("DOMAIN-SET", "Pegasus.list", "Security")
ads_remote = rr("RULE-SET", "Ads.list", "AdBlock")
phishing_remote, dynamic_ads_remote, dynamic_domestic_remote = (dynamic_line(item) for item in DYNAMIC_RULES)
replace_once("phishing_policy", phishing_remote, phishing_remote.replace(",Security,", ",DIRECT,"))
replace_once("phishing_polling", phishing_remote, phishing_remote.replace("update-interval=86400", "update-interval=-1"))
replace_once("pegasus_policy", pegasus_remote, rr("DOMAIN-SET", "Pegasus.list", "DIRECT"))
replace_once("pegasus_embedded", pegasus_remote, "DOMAIN-SUFFIX,123tramites.com,Security\n" + pegasus_remote)
swap_once("pegasus_order", pegasus_remote, rr("RULE-SET", "APNs.list", "ApplePush"))
replace_once("ad_policy", ads_remote, rr("RULE-SET", "Ads.list", "DIRECT"))
replace_once("ad_embedded", ads_remote, "DOMAIN-SUFFIX,doubleclick.net,AdBlock\n" + ads_remote)
replace_once("ad_no_resolve", ads_remote, ads_remote.replace(",no-resolve,", ","))
replace_once("apns_policy", rr("RULE-SET", "APNs.list", "ApplePush"), rr("RULE-SET", "APNs.list", "DIRECT"))
replace_once("telegram_policy", rr("RULE-SET", "Telegram.list", "Telegram"), rr("RULE-SET", "Telegram.list", "DIRECT"))
replace_once("bili_policy", rr("RULE-SET", "BiliBili.list", "Domestic"), rr("RULE-SET", "BiliBili.list", "Streaming"))
replace_once("bili_intl_policy", rr("RULE-SET", "BiliBiliIntl.list", "Streaming"), rr("RULE-SET", "BiliBiliIntl.list", "DIRECT"))
replace_once("remote_host", f"{REMOTE_BASE}ChatGPT.list", "https://example.invalid/ChatGPT.list")
replace_once("remote_http", f"{REMOTE_BASE}Claude.list", REMOTE_BASE.replace("https://", "http://") + "Claude.list")
replace_once("remote_main", f"{REMOTE_BASE}Gemini.list", "https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@main/Rules/Gemini.list")
replace_once("remote_tag", f"{REMOTE_BASE}Netflix.list", f"https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@{RULE_SNAPSHOT_TAG}/Rules/Netflix.list")
replace_once("ruleset_no_resolve", rr("RULE-SET", "Microsoft.list", "Microsoft"), rr("RULE-SET", "Microsoft.list", "Microsoft").replace(",no-resolve,", ","))
replace_once("ruleset_polling", rr("RULE-SET", "OneDrive.list", "Microsoft"), rr("RULE-SET", "OneDrive.list", "Microsoft").replace(",update-interval=-1", ""))
replace_once("dynamic_ad_policy", dynamic_ads_remote, dynamic_ads_remote.replace(",AdBlock,", ",DIRECT,"))
replace_once("dynamic_domestic_no_resolve", dynamic_domestic_remote, dynamic_domestic_remote.replace(",no-resolve,", ","))
replace_once("dynamic_domestic_policy", dynamic_domestic_remote, dynamic_domestic_remote.replace(",Domestic,", ",DIRECT,"))
swap_once("remote_order", rr("RULE-SET", "ChatGPT.list", "ChatGPT"), rr("RULE-SET", "Claude.list", "Claude"))
replace_once("stun_policy", "PROTOCOL,STUN,UDP", "PROTOCOL,STUN,Proxy")
replace_once("dns53_open", "DEST-PORT,53,REJECT", "DEST-PORT,53,DIRECT")
replace_once("dns853_open", "DEST-PORT,853,REJECT", "DEST-PORT,853,Proxy")
replace_once("domestic_dns_proxy", "DOMAIN,dns.alidns.com,Domestic", "DOMAIN,dns.alidns.com,Proxy")
replace_once("domestic_dns_direct", "DOMAIN,doh.pub,Domestic", "DOMAIN,doh.pub,DIRECT")
replace_once("foreign_dns_direct", "DOMAIN,dns.google,Proxy", "DOMAIN,dns.google,DIRECT")
swap_once("domestic_dns_after_reject", "DOMAIN-SUFFIX,smtcdns.net,Domestic", "DEST-PORT,53,REJECT")
replace_once("apple_bootstrap_broad", "DOMAIN,configuration.ls.apple.com,DIRECT", "DOMAIN-SUFFIX,ls.apple.com,DIRECT")
replace_once("diagnostic_direct", "DOMAIN-SUFFIX,browserleaks.net,Proxy", "DOMAIN-SUFFIX,browserleaks.net,DIRECT")
replace_once("cloud_direct", "DOMAIN-SUFFIX,aliyuncs.com,Domestic", "DOMAIN-SUFFIX,aliyuncs.com,DIRECT")
replace_once("viu_policy", "DOMAIN-SUFFIX,viu.now.com,Streaming", "DOMAIN-SUFFIX,viu.now.com,HBO")
replace_once("youtube_override", "DOMAIN,yt3.ggpht.com,YouTube", "DOMAIN,yt3.ggpht.com,Google")
replace_once("microsoft_override", "DOMAIN,login.live.com,Microsoft", "DOMAIN,login.live.com,Games")
replace_once("game_cloud", "IP-CIDR,35.192.0.0/12,Proxy,no-resolve", "IP-CIDR,35.192.0.0/12,Games,no-resolve")
replace_once("geoip_resolve", "GEOIP,CN,Domestic,no-resolve", "GEOIP,CN,Domestic")
replace_once("geoip_proxy", "GEOIP,CN,Domestic,no-resolve", "GEOIP,CN,Proxy,no-resolve")
replace_once("ipv4_catchall", "IP-CIDR,0.0.0.0/0,Proxy,no-resolve", "IP-CIDR,0.0.0.0/0,DIRECT,no-resolve")
replace_once("ipv6_catchall", "IP-CIDR6,::/0,Proxy,no-resolve", "IP-CIDR6,::/0,DIRECT,no-resolve")
replace_once("cidr_resolve", "IP-CIDR,1.1.1.1/32,Proxy,no-resolve", "IP-CIDR,1.1.1.1/32,Proxy")
replace_once("invalid_cidr", "IP-CIDR,35.192.0.0/12,Proxy,no-resolve", "IP-CIDR,999.1.1.1/12,Proxy,no-resolve")
replace_once("final_open", "FINAL,Final,dns-failed", "FINAL,DIRECT")
swap_once("final_not_last", "IP-CIDR6,::/0,Proxy,no-resolve", "FINAL,Final,dns-failed")
swap_once("stun_after_dns", "PROTOCOL,STUN,UDP", "DEST-PORT,53,REJECT")
swap_once("bili_precedence", rr("RULE-SET", "BiliBiliIntl.list", "Streaming"), rr("RULE-SET", "BiliBili.list", "Domestic"))
swap_once("game_precedence", rr("RULE-SET", "Game.list", "Games"), rr("RULE-SET", "Microsoft.list", "Microsoft"))
replace_once("extra_rule", "FINAL,Final,dns-failed\n", "DOMAIN,unexpected.example,DIRECT\nFINAL,Final,dns-failed\n")
replace_once("missing_rule", "DOMAIN-SUFFIX,ipip.net,Proxy\n", "")
replace_once("duplicate_rule", "DOMAIN-SUFFIX,ipip.net,Proxy\n", "DOMAIN-SUFFIX,ipip.net,Proxy\nDOMAIN-SUFFIX,ipip.net,Proxy\n")

for name, changed in cases:
    result = run(changed)
    if result.returncode == 0:
        raise AssertionError(f"mutation unexpectedly passed: {name}")

print(f"PASS R13.4 mutations={len(cases)}")
