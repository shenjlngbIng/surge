#!/usr/bin/env python3
"""Execute the Sub-Store managed-profile transformer against hostile cases."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "Scripts" / "SubStore-Surge-Profile.js"


def run_case(*, body: str, query: dict[str, str], url: str) -> dict[str, object]:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("node is required to test the Sub-Store transformer")
    payload = json.dumps({"body": body, "query": query, "url": url})
    harness = f"""
const fs = require('fs');
const vm = require('vm');
const input = {payload};
global.$options = {{_req: {{query: input.query, url: input.url}}}};
vm.runInThisContext(fs.readFileSync({json.dumps(str(SCRIPT))}, 'utf8'));
const response = {{status: 200, header: {{}}, body: input.body}};
try {{
  const output = transformFunction(response);
  process.stdout.write(JSON.stringify({{ok: true, output}}));
}} catch (error) {{
  process.stdout.write(JSON.stringify({{ok: false, error: String(error.message || error)}}));
}}
"""
    result = subprocess.run(
        [node, "-"],
        input=harness,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


raw = "HK-01 = trojan, hk.example.com, 443, password=secret"
normal = run_case(body=raw, query={"target": "Surge"}, url="/download/collection/Surge/Surge")
assert normal["ok"] is True and normal["output"]["body"] == raw

wrong_target = run_case(
    body=raw,
    query={"target": "JSON", "surge-profile": "1"},
    url="/download/collection/Surge/JSON?target=JSON&surge-profile=1",
)
assert wrong_target["ok"] is False and "requires target=Surge" in wrong_target["error"]

empty = run_case(
    body="",
    query={"target": "Surge", "surge-profile": "1"},
    url="/download/collection/Surge/Surge?surge-profile=1",
)
assert empty["ok"] is False and "empty" in empty["error"]

direct_only = run_case(
    body="Only-Direct = direct",
    query={"target": "Surge", "surge-profile": "1"},
    url="/download/collection/Surge/Surge?surge-profile=1",
)
assert direct_only["ok"] is False and "without a real proxy" in direct_only["error"]

section_injection = run_case(
    body=f"{raw}\n[Rule]\nFINAL,DIRECT",
    query={"target": "Surge", "surge-profile": "1"},
    url="/download/collection/Surge/Surge?surge-profile=1",
)
assert section_injection["ok"] is False and "unexpected profile sections" in section_injection["error"]

wrapped = run_case(
    body=f"\ufeff{raw}\r\n",
    query={"target": "Surge", "surge-profile": "true"},
    url="/download/collection/Surge/Surge?target=Surge&surge-profile=true",
)
assert wrapped["ok"] is True
expected = (
    "#!MANAGED-CONFIG http://sub.store/download/collection/Surge/Surge?"
    "target=Surge&surge-profile=true interval=3600 strict=true\n"
    f"[Proxy]\n{raw}\n"
)
assert wrapped["output"]["body"] == expected
assert wrapped["output"]["header"]["Content-Type"] == "text/plain; charset=utf-8"

already_wrapped = run_case(
    body=f"[Proxy]\n{raw}",
    query={"target": "SurgeMac", "surgeProfile": "on"},
    url="https://sub.store/download/collection/Surge/SurgeMac?target=SurgeMac&surgeProfile=on",
)
assert already_wrapped["ok"] is True
assert already_wrapped["output"]["body"].count("[Proxy]") == 1
assert already_wrapped["output"]["body"].startswith(
    "#!MANAGED-CONFIG http://sub.store/download/collection/Surge/SurgeMac?"
)

print("PASS R13.12 Sub-Store managed-profile transformer cases=7")
