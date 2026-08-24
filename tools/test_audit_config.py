#!/usr/bin/env python3
"""Mutation tests for the R12.14 configuration auditor."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

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


assert run(BASE).returncode == 0, "baseline"

mutations = {
    "final_open": ("\nFINAL,Final,dns-failed\n", "\nFINAL,DIRECT\n"),
    "telegram_direct": (
        "\nRULE-SET,https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@main/Rules/Telegram.list,Telegram\n",
        "\nRULE-SET,https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@main/Rules/Telegram.list,DIRECT\n",
    ),
    "apns_direct": (
        "\nRULE-SET,https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@main/Rules/APNs.list,ApplePush\n",
        "\nRULE-SET,https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@main/Rules/APNs.list,DIRECT\n",
    ),
    "capture_apns": ("\ninclude-apns = true\n", "\ninclude-apns = false\n"),
    "capture_all": ("\ninclude-all-networks = true\n", "\ninclude-all-networks = false\n"),
    "capture_cellular_services": (
        "\ninclude-cellular-services = false\n",
        "\ninclude-cellular-services = true\n",
    ),
    "auto_suspend": ("\nauto-suspend = true\n", "\nauto-suspend = false\n"),
    "encrypted_dns_follow": (
        "\nencrypted-dns-follow-outbound-mode = false\n",
        "\nencrypted-dns-follow-outbound-mode = true\n",
    ),
    "dns_server": (
        "\ndns-server = 223.5.5.5, 223.6.6.6\n",
        "\ndns-server = system, 223.5.5.5, 119.29.29.29\n",
    ),
    "encrypted_dns_server": (
        "\nencrypted-dns-server = https://dns.alidns.com/dns-query, tls://dns.alidns.com\n",
        "\nencrypted-dns-server = https://1.1.1.1/dns-query, https://9.9.9.9/dns-query\n",
    ),
    "dns_bootstrap": (
        "dns.alidns.com = 223.5.5.5, 223.6.6.6, 2400:3200::1",
        "dns.alidns.com = 1.1.1.1",
    ),
    "duplicate_dns_bootstrap": (
        "dns.alidns.com = 223.5.5.5, 223.6.6.6, 2400:3200::1\n",
        "dns.alidns.com = 223.5.5.5, 223.6.6.6, 2400:3200::1\ndns.alidns.com = 1.1.1.1\n",
    ),
    "skip_cgnat": (", 100.64.0.0/10,", ","),
    "macos_hosts_option": ("\n# Access\n", "\nread-etc-hosts = true\n\n# Access\n"),
    "fail_closed_alert": (
        "Fail-Closed = http, 127.0.0.1, 1, no-error-alert=true",
        "Fail-Closed = http, 127.0.0.1, 1",
    ),
    "test_timeout": ("\ntest-timeout = 8\n", "\ntest-timeout = 5\n"),
    "proxy_default": ("\nProxy = select, AllServer,", "\nProxy = select, HongKong,"),
    "allserver_mode": ("\nAllServer = fallback,", "\nAllServer = select,"),
    "allserver_interval": ("interval=600, timeout=5", "interval=60, timeout=5"),
    "allserver_timeout": ("interval=600, timeout=5", "interval=600, timeout=300"),
    "public_subscription": (
        "policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL",
        "policy-path=https://private.example/subscription",
    ),
    "apple_push_order": (
        "ApplePush = fallback, Proxy, DIRECT, interval=60, timeout=5",
        "ApplePush = fallback, DIRECT, Proxy, interval=60, timeout=5",
    ),
    "apple_push_timeout": (
        "ApplePush = fallback, Proxy, DIRECT, interval=60, timeout=5",
        "ApplePush = fallback, Proxy, DIRECT, interval=60, timeout=300",
    ),
    "stale_encrypted_dns_group": (
        "\nApplePush = fallback,",
        "\nEncryptedDNS = fallback, Proxy, DIRECT\nApplePush = fallback,",
    ),
    "inactive_doh_rule": (
        "\nDOMAIN,dns.alidns.com,DIRECT\n",
        "\nPROTOCOL,DOH,Proxy\nDOMAIN,dns.alidns.com,DIRECT\n",
    ),
    "unsupported_protocol": (
        "\nPROTOCOL,STUN,Proxy\n",
        "\nPROTOCOL,BOGUS,Proxy\n",
    ),
    "cgnat_rule": (
        "\nIP-CIDR,100.64.0.0/10,DIRECT,no-resolve\n",
        "\n",
    ),
    "apple_system_direct": (
        "\nDOMAIN-SUFFIX,ls.apple.com,DIRECT\n",
        "\nDOMAIN-SUFFIX,ls.apple.com,Proxy\n",
    ),
    "runtime_ruleset": (
        "\nFINAL,Final,dns-failed\n",
        "\nRULE-SET,https://example.invalid/a.list,Proxy\nFINAL,Final,dns-failed\n",
    ),
    "remote_host": (
        "https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@main/Rules/ChatGPT.list",
        "https://example.invalid/ChatGPT.list",
    ),
    "remote_http": (
        "https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@main/Rules/ChatGPT.list",
        "http://cdn.jsdelivr.net/gh/shenjlngbIng/surge@main/Rules/ChatGPT.list",
    ),
}

for name, (old, new) in mutations.items():
    assert old in BASE, f"mutation anchor missing: {name}"
    result = run(BASE.replace(old, new, 1))
    assert result.returncode != 0, f"mutation unexpectedly passed: {name}"

print(f"PASS mutations={len(mutations)}")
