#!/usr/bin/env python3
"""Exercise documented group semantics with synthetic nodes, not live Surge I/O."""

from __future__ import annotations

import re
from pathlib import Path

from test_runtime_rules import domain_route, reference_records

ROOT = Path(__file__).resolve().parent.parent
TEXT = (ROOT / "Surge.conf").read_text()
GROUPS: dict[str, tuple[str, list[str], dict[str, str]]] = {}
for row in TEXT.split("[Proxy Group]", 1)[1].split("[Rule]", 1)[0].splitlines():
    if not row.strip() or row.lstrip().startswith("#"):
        continue
    name, value = row.split(" = ", 1)
    parts = [part.strip() for part in re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', value)]
    members = [part for part in parts[1:] if "=" not in part]
    options = dict(part.split("=", 1) for part in parts[1:] if "=" in part)
    GROUPS[name] = (parts[0], members, options)

BUILTINS = {"DIRECT", "REJECT", "REJECT-DROP"}
REGIONS = ("HongKong", "TaiWan", "Japan", "Singapore", "America")
AI_REGIONS = {"America", "Japan", "Singapore", "TaiWan"}
SERVICE_REGIONS = {
    "ChatGPT": AI_REGIONS, "Claude": AI_REGIONS, "Gemini": AI_REGIONS,
    "NETFLIX": set(REGIONS), "Disney+": set(REGIONS), "PrimeVideo": set(REGIONS), "Spotify": set(REGIONS),
    "HBO": {"America", "Singapore", "HongKong", "TaiWan"},
    "TikTok": AI_REGIONS, "Bahamut": {"TaiWan"},
}


def members(name: str, nodes: list[str], visiting: tuple[str, ...] = ()) -> list[str]:
    assert name not in visiting, f"recursive policy inclusion: {visiting + (name,)}"
    kind, explicit, options = GROUPS[name]
    imported: list[str] = []
    for source in options.get("include-other-group", "").strip('"').split(","):
        if source:
            imported.extend(members(source, nodes, visiting + (name,)))
    if "policy-path" in options:
        imported.extend(nodes)
    if "policy-regex-filter" in options:
        pattern = re.compile(options["policy-regex-filter"])
        imported = [member for member in imported if pattern.search(member)]
    result = list(dict.fromkeys(explicit + imported))
    if kind == "smart":
        # Built-ins and nested groups are ignored by Smart; a real proxy-policy
        # sentinel is therefore essential even though the source has REJECT.
        result = [member for member in result if member in nodes or member == "Fail-Closed"]
    return result


def resolve(name: str, nodes: list[str], healthy: set[str], choices: dict[str, str] | None = None) -> str:
    if name in BUILTINS:
        return name
    if name == "Fail-Closed":
        return "FAILED"
    if name in nodes:
        return name if name in healthy else "FAILED"
    kind, _explicit, options = GROUPS[name]
    candidates = members(name, nodes)
    if not candidates:
        return "DIRECT"  # Official empty-group SUBSTITUTE behavior.
    if kind == "select" or name in (choices or {}):
        selected = (choices or {}).get(name, candidates[0])
        assert selected in candidates, (name, selected, candidates)
        return resolve(selected, nodes, healthy, choices)
    results = [resolve(candidate, nodes, healthy, choices) for candidate in candidates]
    available = [result for result in results if result == "DIRECT" or result in healthy]
    if available:
        return available[0]  # Exact score ordering is immaterial to these safety cases.
    if kind == "fallback":
        return results[0]
    assert options.get("evaluate-before-use") == "true"
    return "FAILED"


def check_delivery_recovery() -> int:
    """Do not let a failed manual exit strand downloads or bypass healthy proxies.

    This models fresh availability results, not APNs-specific reachability or
    delivery. A temporary Smart override deliberately disables its recovery.
    """
    nodes = ["Hong Kong healthy", "Japan unavailable"]
    healthy, failed = nodes
    pinned = {"Proxy": "NodePool", "NodePool": failed}
    transport = domain_route(reference_records(TEXT), "raw.githubusercontent.com", port=443)
    assert transport == "Auto", ("resource download depends on manual exit", transport)
    assert resolve("Proxy", nodes, {healthy}, pinned) == "FAILED"
    assert resolve(transport, nodes, {healthy}, pinned) == healthy
    assert resolve("ApplePush", nodes, {healthy}, pinned) == healthy
    # Healthy manual choices are still preferred for APNs.
    assert resolve("ApplePush", nodes, set(nodes), pinned) == failed
    assert resolve("ApplePush", [], set()) == "DIRECT"
    assert resolve("ApplePush", nodes, set(), pinned) == "DIRECT"
    assert resolve(transport, [], set()) == "FAILED"
    assert resolve(transport, nodes, set(), pinned) == "FAILED"
    # A user override is an explicit limitation, not silently ignored by tests.
    override = {**pinned, "Auto": failed}
    assert resolve(transport, nodes, {healthy}, override) == "FAILED"
    assert resolve("ApplePush", nodes, {healthy}, override) == "DIRECT"
    return 11


def check_service_regions(fixtures: dict[str, list[str]]) -> int:
    """Check country isolation even when excluded nodes are the healthy ones."""
    unclassified = ["Germany-1", "NOTHKWORD", "RUSSIAN-1", "🇨🇳 上海-01", "英国-01", "剩余流量 500GB",
                    "South America-1", "Latin America", "North America", "LatinAmerican", "新西兰-01"]
    ambiguous = ["HK JP-01", "🇭🇰 美国-01", "日本/台湾 01", "新加坡-美国", "🇺🇸 日本-01",
                 "香港->日本", "香港→美国", "美国中转01", "日本中轉01", "US=>UK-01"]
    pool = [node for names in fixtures.values() for node in names] + unclassified + ambiguous
    checks = 0
    for region, expected in fixtures.items():
        assert members(region + "-Nodes", pool) == ["REJECT", *expected], region
        checks += 1
    for service, allowed in SERVICE_REGIONS.items():
        eligible = {node for region in allowed for node in fixtures[region]}
        assert set(members(service, pool)) == {"Fail-Closed", *eligible}, service
        assert resolve(service, [], set()) == "FAILED", service
        assert resolve(service, pool, set()) == "FAILED", service
        wrong = [node for node in pool if node not in eligible]
        assert members(service, wrong) == ["Fail-Closed"], service
        assert resolve(service, wrong, set(wrong)) == "FAILED", service
        assert resolve(service, pool, set(wrong)) == "FAILED", service
        checks += 6
        for region in allowed:
            only = fixtures[region][0]
            assert resolve(service, [only, *wrong], {only, *wrong}) == only, (service, region)
            # Changing the global exit cannot widen a service's eligible pool.
            assert resolve(service, [only, *wrong], {only, *wrong}, {"Proxy": "NodePool", "NodePool": wrong[0]}) == only
            checks += 2
    return checks


def main() -> int:
    assert GROUPS["桔子"][1] == ["REJECT"]
    assert GROUPS["桔子"][2]["hidden"] == "1"
    assert GROUPS["桔子"][2]["external-policy-modifier"] == '"udp-relay=true,test-url=http://cp.cloudflare.com/generate_204,test-timeout=5"'
    for name, (_kind, explicit, _options) in GROUPS.items():
        assert "桔子" not in explicit, f"raw subscription source is routed by {name}"
    for row in TEXT.split("[Rule]", 1)[1].splitlines():
        if row.strip() and not row.lstrip().startswith("#"):
            assert ",桔子" not in row

    fixtures = {
        "HongKong": ["🇭🇰 香港-1", "Hong Kong 2", "HKG-3", "香港-优化", "香港-优化 2", "香港 WAP-优化 2"],
        "TaiWan": ["🇹🇼 台灣-1", "台湾 2", "TPE-3", "台湾-优化", "臺灣-优化", "Taipei-01"],
        "Japan": ["🇯🇵 日本-1", "Tokyo 2", "NRT-3", "日本-优化", "日本-优化 2", "日本-优化 3"],
        "Singapore": ["🇸🇬 新加坡-1", "Lion City 2", "SIN-3", "新加坡-优化-GPT", "新加坡-优化 2-GPT", "新加坡-优化 3"],
        "America": ["🇺🇸 美国-1", "Los Angeles 2", "JFK-3", "美国-优化", "美國-优化 2", "Seattle-4"],
    }
    nodes = [node for group in fixtures.values() for node in group] + ["Germany-1", "NOTHKWORD"]
    for region, expected in fixtures.items():
        actual = members(f"{region}-Nodes", nodes)
        assert actual == ["REJECT", *expected], (region, actual)
    assert members("NodePool", nodes) == ["Auto", *nodes]
    assert members("Auto", []) == ["Fail-Closed"]
    assert members("NodePool", []) == ["Auto"]
    assert members("桔子", []) == ["REJECT"]

    protected = ["Final", "Proxy", "Auto", "Fast", "NodePool", "UDP", *REGIONS]
    protected += ["ChatGPT", "Claude", "Gemini", "GitHub", "YouTube", "NETFLIX",
                  "Disney+", "HBO", "PrimeVideo", "Emby", "TikTok", "Bahamut",
                  "Spotify", "Streaming", "Telegram", "X", "Google", "Microsoft", "Games"]
    for imported in ([], nodes):
        for group in protected:
            assert resolve(group, imported, set()) in {"FAILED", "REJECT"}, group
        assert resolve("ApplePush", imported, set()) == "DIRECT"  # Deliberate APNs exception.
        assert resolve("Domestic", imported, set()) == "DIRECT"

    for region in ("HongKong", "Japan"):
        only = fixtures[region][0]
        for group in protected:
            expected = only if group not in SERVICE_REGIONS or region in SERVICE_REGIONS[group] else "FAILED"
            assert resolve(group, [only], {only}) == expected, (group, only)
    hongkong, japan = fixtures["HongKong"][0], fixtures["Japan"][0]
    assert resolve("NodePool", [hongkong, japan], {hongkong, japan}, {"NodePool": japan}) == japan
    assert resolve("NodePool", [hongkong, japan], {hongkong}, {"NodePool": japan}) == "FAILED"
    for switch in ("AdBlock", "Security"):
        assert resolve(switch, nodes, set(nodes)) == "REJECT"
        assert resolve(switch, nodes, set(nodes), {switch: "DIRECT"}) == "DIRECT"
    assert resolve("Domestic", [japan], {japan}, {"Domestic": "Proxy"}) == japan
    assert resolve("UDP", nodes, set(nodes), {"UDP": "REJECT"}) == "REJECT"
    delivery_cases = check_delivery_recovery()
    current_push = GROUPS["ApplePush"]
    try:
        GROUPS["ApplePush"] = (current_push[0], ["Proxy", "DIRECT"], current_push[2])
        try:
            check_delivery_recovery()
        except AssertionError:
            pass
        else:
            raise AssertionError("delivery cases accepted the old premature DIRECT fallback")
    finally:
        GROUPS["ApplePush"] = current_push
    region_cases = check_service_regions(fixtures)
    mutations = [
        ("ChatGPT", "include-other-group", '"HongKong-Nodes,America-Nodes,Japan-Nodes,Singapore-Nodes,TaiWan-Nodes"'),
        ("HBO", "include-other-group", '"Japan-Nodes,America-Nodes,Singapore-Nodes,HongKong-Nodes,TaiWan-Nodes"'),
        ("Bahamut", "include-other-group", "Auto"),
    ]
    for group, option, wrong in mutations:
        original = GROUPS[group]
        GROUPS[group] = (original[0], original[1], {**original[2], option: wrong})
        try:
            try:
                check_service_regions(fixtures)
            except AssertionError:
                pass
            else:
                raise AssertionError(f"country boundary tests accepted {group} cross-region regression")
        finally:
            GROUPS[group] = original
    print(f"PASS policy model: 30 region names, 21 negative/ambiguous names, empty/failed sources, single-region fallback, manual selection and control switches; service_region_cases={region_cases} service_mutations={len(mutations)} delivery_cases={delivery_cases} delivery_mutations=1; no device claim")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
