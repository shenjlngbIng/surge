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


def main() -> int:
    assert GROUPS["桔子"][1] == ["REJECT"]
    assert GROUPS["桔子"][2]["hidden"] == "1"
    assert GROUPS["桔子"][2]["external-policy-modifier"] == '"udp-relay=true"'
    for name, (_kind, explicit, _options) in GROUPS.items():
        assert "桔子" not in explicit, f"raw subscription source is routed by {name}"
    for row in TEXT.split("[Rule]", 1)[1].splitlines():
        if row.strip() and not row.lstrip().startswith("#"):
            assert ",桔子" not in row

    fixtures = {
        "HongKong": ["🇭🇰 香港-1", "Hong Kong 2", "HKG-3"],
        "TaiWan": ["🇹🇼 台灣-1", "台湾 2", "TPE-3"],
        "Japan": ["🇯🇵 日本-1", "Tokyo 2", "NRT-3"],
        "Singapore": ["🇸🇬 新加坡-1", "Lion City 2", "SIN-3"],
        "America": ["🇺🇸 美国-1", "Los Angeles 2", "JFK-3"],
    }
    nodes = [node for group in fixtures.values() for node in group] + ["Germany-1", "NOTHKWORD"]
    for region, expected in fixtures.items():
        actual = members(f"{region}-Nodes", nodes)
        assert actual == ["REJECT", *expected], (region, actual)
    assert members("NodePool", nodes) == ["Auto", *nodes]
    assert members("Auto", []) == ["Fail-Closed"]
    assert members("NodePool", []) == ["Auto"]
    assert members("桔子", []) == ["REJECT"]

    protected = ["Final", "Proxy", "Auto", "NodePool", "UDP", *REGIONS]
    protected += ["ChatGPT", "Claude", "Gemini", "GitHub", "YouTube", "NETFLIX",
                  "Disney+", "HBO", "PrimeVideo", "Emby", "TikTok", "Bahamut",
                  "Spotify", "Streaming", "Telegram", "X", "Google", "Microsoft", "Games"]
    for imported in ([], nodes):
        for group in protected:
            assert resolve(group, imported, set()) in {"FAILED", "REJECT"}, group
        assert resolve("ApplePush", imported, set()) == "DIRECT"  # Deliberate APNs exception.
        assert resolve("Domestic", imported, set()) == "DIRECT"

    for only in (fixtures["HongKong"][0], fixtures["Japan"][0]):
        for group in protected:
            assert resolve(group, [only], {only}) == only, (group, only)
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
    print(f"PASS policy model: 15 region names, empty/failed sources, single-region fallback, manual selection and control switches; delivery_cases={delivery_cases} delivery_mutations=1; no device claim")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
