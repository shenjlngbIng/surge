#!/usr/bin/env python3
"""Mutation tests for the R12.17 configuration auditor."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from convert_to_remote_rules import REMOTE_BASE, RULE_SNAPSHOT_TAG, repository_line


ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "tools/audit_config.py"
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


assert run(BASE).returncode == 0, "baseline"

mutations = {
    "attribution_header": (
        "# > Surge Config Make by .ᐣ\n",
        "# > Surge Config Make by unknown\n",
    ),
    "version_header": (
        "# > Surge iOS Privacy + Push R12.17 |",
        "# > Surge iOS Privacy + Push R12.16 |",
    ),
    "final_open": ("\nFINAL,Final,dns-failed\n", "\nFINAL,DIRECT\n"),
    "final_group_direct": ("\nFinal = select, Proxy, REJECT,", "\nFinal = select, Proxy, DIRECT,"),
    "telegram_direct": (f"\n{rr('RULE-SET','Telegram.list','Telegram')}\n", f"\n{rr('RULE-SET','Telegram.list','DIRECT')}\n"),
    "apns_direct": (f"\n{rr('RULE-SET','APNs.list','ApplePush')}\n", f"\n{rr('RULE-SET','APNs.list','DIRECT')}\n"),
    "pegasus_third_party_runtime": (
        f"\n{rr('DOMAIN-SET','Pegasus.list','Security')}\n",
        "\nDOMAIN-SET,https://raw.githubusercontent.com/AmnestyTech/investigations/3d8f248a0d015f183724ae7d096a5c46a8bb5fc7/2021-07-18_nso/domains.txt,Security,update-interval=-1\n",
    ),
    "capture_apns": ("\ninclude-apns = true\n", "\ninclude-apns = false\n"),
    "capture_all": ("\ninclude-all-networks = true\n", "\ninclude-all-networks = false\n"),
    "capture_cellular_services": ("\ninclude-cellular-services = false\n", "\ninclude-cellular-services = true\n"),
    "auto_suspend": ("\nauto-suspend = true\n", "\nauto-suspend = false\n"),
    "encrypted_dns_follow": ("\nencrypted-dns-follow-outbound-mode = false\n", "\nencrypted-dns-follow-outbound-mode = true\n"),
    "encrypted_dns_certificate_verification": ("\nencrypted-dns-skip-cert-verification = false\n", "\nencrypted-dns-skip-cert-verification = true\n"),
    "dns_server": ("\ndns-server = 223.5.5.5, 223.6.6.6\n", "\ndns-server = system, 223.5.5.5\n"),
    "encrypted_dns_server": ("\nencrypted-dns-server = https://dns.alidns.com/dns-query, tls://dns.alidns.com\n", "\nencrypted-dns-server = https://1.1.1.1/dns-query\n"),
    "dns_bootstrap": ("dns.alidns.com = 223.5.5.5, 223.6.6.6, 2400:3200::1", "dns.alidns.com = 1.1.1.1"),
    "duplicate_dns_bootstrap": ("dns.alidns.com = 223.5.5.5, 223.6.6.6, 2400:3200::1\n", "dns.alidns.com = 223.5.5.5, 223.6.6.6, 2400:3200::1\ndns.alidns.com = 1.1.1.1\n"),
    "skip_cgnat": (", 100.64.0.0/10,", ","),
    "macos_hosts_option": ("\n# Access\n", "\nread-etc-hosts = true\n\n# Access\n"),
    "fail_closed_alert": ("Fail-Closed = http, 127.0.0.1, 1, no-error-alert=true", "Fail-Closed = http, 127.0.0.1, 1"),
    "test_timeout": ("\ntest-timeout = 5\n", "\ntest-timeout = 8\n"),
    "proxy_test_url": ("\nproxy-test-url = http://cp.cloudflare.com/generate_204\n", "\nproxy-test-url = http://www.gstatic.com/generate_204\n"),
    "proxy_test_udp": ("\nproxy-test-udp = apple.com@223.5.5.5\n", "\n"),
    "block_quic": ("\nblock-quic = per-policy\n", "\nblock-quic = all-proxy\n"),
    "udp_unsupported": ("\nudp-policy-not-supported-behaviour = REJECT\n", "\nudp-policy-not-supported-behaviour = DIRECT\n"),
    "proxy_default": ("\nProxy = select, AllServer,", "\nProxy = select, HongKong,"),
    "proxy_direct": ("\nProxy = select, AllServer, HongKong,", "\nProxy = select, AllServer, DIRECT, HongKong,"),
    "hbo_forced_america": ("\nHBO = select, Proxy, America,", "\nHBO = select, America, Proxy,"),
    "node_pool_mode": ("\nNodePool = select,", "\nNodePool = url-test,"),
    "node_pool_hidden": ("update-interval=3600, no-alert=0, hidden=1, include-all-proxies=0", "update-interval=3600, no-alert=0, hidden=0, include-all-proxies=0"),
    "node_pool_all_proxies": ("include-all-proxies=0\n\n# Smart groups", "include-all-proxies=true\n\n# Smart groups"),
    "node_pool_direct_member": ("\nProxy = select, AllServer, HongKong,", "\nProxy = select, AllServer, NodePool, HongKong,"),
    "allserver_mode": ("\nAllServer = smart,", "\nAllServer = select,"),
    "allserver_sentinel": ("\nAllServer = smart, Fail-Closed,", "\nAllServer = smart,"),
    "allserver_source": ("include-other-group=NodePool\n\n# Regions", "include-other-group=HongKong\n\n# Regions"),
    "allserver_legacy_probe": ("AllServer = smart, Fail-Closed, no-alert=0", "AllServer = smart, Fail-Closed, interval=60, no-alert=0"),
    "allserver_direct": ("\nAllServer = smart, Fail-Closed,", "\nAllServer = smart, Fail-Closed, DIRECT,"),
    "region_mode": ("\nHongKong = smart,", "\nHongKong = url-test,"),
    "region_sentinel": ("\nJapan = smart, Fail-Closed,", "\nJapan = smart,"),
    "region_filter": ("\nSingapore = smart, Fail-Closed, policy-regex-filter=", "\nSingapore = smart, Fail-Closed, policy-filter="),
    "region_legacy_probe": ("\nTaiWan = smart, Fail-Closed,", "\nTaiWan = smart, Fail-Closed, interval=1800,"),
    "region_source": ("include-other-group=NodePool\nJapan =", "include-other-group=AllServer\nJapan ="),
    "region_direct": ("\nJapan = smart, Fail-Closed,", "\nJapan = smart, Fail-Closed, DIRECT,"),
    "rogue_fallback": ("\nChatGPT = select, America,", "\nChatGPT = fallback, America,"),
    "rogue_policy_path": ("\nGitHub = select, Proxy,", "\nGitHub = select, policy-path=https://example.invalid/nodes, Proxy,"),
    "telegram_direct_member": ("\nTelegram = select, Proxy,", "\nTelegram = select, DIRECT, Proxy,"),
    "public_subscription": ("policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL", "policy-path=https://private.example/subscription"),
    "apple_push_order": ("ApplePush = fallback, Proxy, DIRECT, interval=60, evaluate-before-use=true", "ApplePush = fallback, DIRECT, Proxy, interval=60, evaluate-before-use=true"),
    "apple_push_evaluation": ("ApplePush = fallback, Proxy, DIRECT, interval=60, evaluate-before-use=true", "ApplePush = fallback, Proxy, DIRECT, interval=60"),
    "apple_push_timeout": ("ApplePush = fallback, Proxy, DIRECT, interval=60, evaluate-before-use=true", "ApplePush = fallback, Proxy, DIRECT, interval=60, evaluate-before-use=true, timeout=5"),
    "apple_push_visible": ("ApplePush = fallback, Proxy, DIRECT, interval=60, evaluate-before-use=true, no-alert=0, hidden=1", "ApplePush = fallback, Proxy, DIRECT, interval=60, evaluate-before-use=true, no-alert=0, hidden=0"),
    "adblock_off_switch": ("AdBlock = select, REJECT, REJECT-DROP, DIRECT,", "AdBlock = select, REJECT, REJECT-DROP,"),
    "adblock_visible": ("AdBlock = select, REJECT, REJECT-DROP, DIRECT, no-alert=0, hidden=1", "AdBlock = select, REJECT, REJECT-DROP, DIRECT, no-alert=0, hidden=0"),
    "security_off_switch": ("Security = select, REJECT, REJECT-DROP, DIRECT,", "Security = select, REJECT, REJECT-DROP,"),
    "security_visible": ("Security = select, REJECT, REJECT-DROP, DIRECT, no-alert=0, hidden=1", "Security = select, REJECT, REJECT-DROP, DIRECT, no-alert=0, hidden=0"),
    "udp_choices": ("UDP = select, Proxy, DIRECT, REJECT,", "UDP = select, Proxy, REJECT,"),
    "udp_visible": ("UDP = select, Proxy, DIRECT, REJECT, no-alert=0, hidden=1", "UDP = select, Proxy, DIRECT, REJECT, no-alert=0, hidden=0"),
    "privacy_mode": ("PrivacyAuto = url-test, Fail-Closed,", "PrivacyAuto = smart, Fail-Closed,"),
    "privacy_direct": ("PrivacyAuto = url-test, Fail-Closed,", "PrivacyAuto = url-test, Fail-Closed, DIRECT,"),
    "privacy_legacy_name": ("PrivacyAuto = url-test, Fail-Closed,", "Privacy = url-test, Fail-Closed,"),
    "privacy_visible": ("no-alert=1, hidden=1, include-all-proxies=0, include-other-group=NodePool", "no-alert=1, hidden=0, include-all-proxies=0, include-other-group=NodePool"),
    "privacy_source": ("hidden=1, include-all-proxies=0, include-other-group=NodePool", "hidden=1, include-all-proxies=0"),
    "privacy_evaluation": (", evaluate-before-use=true, no-alert=1, hidden=1", ", no-alert=1, hidden=1"),
    "privacy_interval": ("PrivacyAuto = url-test, Fail-Closed, interval=600,", "PrivacyAuto = url-test, Fail-Closed, interval=60,"),
    "privacy_alert": ("evaluate-before-use=true, no-alert=1, hidden=1", "evaluate-before-use=true, no-alert=0, hidden=1"),
    "privacy_nested_group": ("PrivacyAuto = url-test, Fail-Closed, interval=600,", "PrivacyAuto = url-test, Fail-Closed, Proxy, interval=600,"),
    "stale_encrypted_dns_group": ("\nApplePush = fallback,", "\nEncryptedDNS = fallback, Proxy, DIRECT\nApplePush = fallback,"),
    "inactive_doh_rule": ("\nDOMAIN,dns.alidns.com,Proxy\n", "\nPROTOCOL,DOH,Proxy\nDOMAIN,dns.alidns.com,Proxy\n"),
    "alidns_app_direct": ("\nDOMAIN,dns.alidns.com,Proxy\n", "\nDOMAIN,dns.alidns.com,DIRECT\n"),
    "dnspub_app_direct": ("\nDOMAIN,doh.pub,Proxy\n", "\nDOMAIN,doh.pub,DIRECT\n"),
    "privacy_guard_missing": ("\nDOMAIN-SUFFIX,browserleaks.net,PrivacyAuto\n", "\n"),
    "privacy_guard_smart": ("\nDOMAIN-SUFFIX,ippure.com,PrivacyAuto\n", "\nDOMAIN-SUFFIX,ippure.com,Proxy\n"),
    "unsupported_protocol": ("\nPROTOCOL,STUN,UDP\n", "\nPROTOCOL,BOGUS,UDP\n"),
    "stun_old_policy": ("\nPROTOCOL,STUN,UDP\n", "\nPROTOCOL,STUN,Proxy\n"),
    "cgnat_rule": ("\nIP-CIDR,100.64.0.0/10,DIRECT,no-resolve\n", "\n"),
    "apple_system_direct": ("\nDOMAIN-SUFFIX,ls.apple.com,DIRECT\n", "\nDOMAIN-SUFFIX,ls.apple.com,Proxy\n"),
    "runtime_ruleset": ("\nFINAL,Final,dns-failed\n", "\nRULE-SET,https://example.invalid/a.list,Proxy\nFINAL,Final,dns-failed\n"),
    "node_pool_rule_target": ("\nDOMAIN,sub.store,DIRECT\n", "\nDOMAIN,sub.store,NodePool\n"),
    "remote_host": (f"{REMOTE_BASE}ChatGPT.list", "https://example.invalid/ChatGPT.list"),
    "remote_http": (f"{REMOTE_BASE}ChatGPT.list", REMOTE_BASE.replace("https://", "http://") + "ChatGPT.list"),
    "remote_main_ref": (f"{REMOTE_BASE}ChatGPT.list", "https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@main/Rules/ChatGPT.list"),
    "remote_tag_ref": (f"{REMOTE_BASE}ChatGPT.list", f"https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@{RULE_SNAPSHOT_TAG}/Rules/ChatGPT.list"),
    "missing_update_interval": (rr("RULE-SET", "Claude.list", "Claude"), rr("RULE-SET", "Claude.list", "Claude").replace(",update-interval=-1", "")),
    "bilibili_wrong_policy": (rr("RULE-SET", "BiliBili.list", "DIRECT"), rr("RULE-SET", "BiliBili.list", "Streaming")),
    "bilibili_intl_wrong_policy": (rr("RULE-SET", "BiliBiliIntl.list", "Streaming"), rr("RULE-SET", "BiliBiliIntl.list", "DIRECT")),
    "public_ipv4_direct": ("\nIP-CIDR,0.0.0.0/0,Proxy,no-resolve\n", "\nIP-CIDR,0.0.0.0/0,DIRECT,no-resolve\n"),
    "public_ipv6_missing": ("\nIP-CIDR6,::/0,Proxy,no-resolve\n", "\n"),
    "public_ipv4_resolve": ("\nIP-CIDR,0.0.0.0/0,Proxy,no-resolve\n", "\nIP-CIDR,0.0.0.0/0,Proxy\n"),
    "geoip_direct_restored": ("\n# Public IP literals fail closed through the proxy.", "\nGEOIP,CN,DIRECT,no-resolve\n\n# Public IP literals fail closed through the proxy."),
    "ruleset_local_resolve": (rr("RULE-SET", "Claude.list", "Claude"), rr("RULE-SET", "Claude.list", "Claude").replace(",no-resolve,", ",")),
    "viu_override_missing": ("\nDOMAIN-SUFFIX,viu.now.com,Streaming\n", "\n"),
    "youtube_asset_override_missing": ("\nDOMAIN,yt3.ggpht.com,YouTube\n", "\n"),
    "google_shared_override_missing": ("\nDOMAIN-SUFFIX,ggpht.com,Google\n", "\n"),
    "microsoft_login_override_missing": ("\nDOMAIN,login.live.com,Microsoft\n", "\n"),
    "game_cloud_override_missing": ("\nIP-CIDR,35.192.0.0/12,Proxy,no-resolve\n", "\n"),
    "stun_after_public_ip": (
        "# UDP / STUN / QUIC\nPROTOCOL,STUN,UDP\n\n# Public IP literals fail closed through the proxy. Known local/private ranges and\n# reviewed service IP rules have already matched above; domain requests are skipped.\nIP-CIDR,0.0.0.0/0,Proxy,no-resolve\nIP-CIDR6,::/0,Proxy,no-resolve",
        "# UDP / STUN / QUIC\n# Public IP literals fail closed through the proxy. Known local/private ranges and\n# reviewed service IP rules have already matched above; domain requests are skipped.\nIP-CIDR,0.0.0.0/0,Proxy,no-resolve\nIP-CIDR6,::/0,Proxy,no-resolve\n\nPROTOCOL,STUN,UDP",
    ),
    "game_after_microsoft": (
        f"# Game (before Microsoft so Xbox/Minecraft/Bethesda rules are reachable)\n{rr('RULE-SET','Game.list','Games')}\n# OneDrive\n{rr('RULE-SET','OneDrive.list','Microsoft')}\n# Microsoft\n{rr('RULE-SET','Microsoft.list','Microsoft')}",
        f"# OneDrive\n{rr('RULE-SET','OneDrive.list','Microsoft')}\n# Microsoft\n{rr('RULE-SET','Microsoft.list','Microsoft')}\n# Game (before Microsoft so Xbox/Minecraft/Bethesda rules are reachable)\n{rr('RULE-SET','Game.list','Games')}",
    ),
}

for name, (old, new) in mutations.items():
    assert old in BASE, f"mutation anchor missing: {name}"
    result = run(BASE.replace(old, new, 1))
    assert result.returncode != 0, f"mutation unexpectedly passed: {name}"

print(f"PASS R12.17 mutations={len(mutations)}")
