# Contributing

R13.13 把主配置、固定规则快照、来源锁、运行锁、审计器、故障注入和发布清单视为一个整体。行为变化必须同步更新这些文件，并完成全套验证。

## 配置边界

- 公开 `Surge.conf` 只保留 `NodePool.policy-path=https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL`，不得提交真实订阅、节点或令牌。
- `[Proxy]` 必须保持为空；禁止静态拒绝别名、本机 SOCKS5 回环诊断桥和公开节点。
- `NodePool` 必须保持手动 `select`，显式第一项为 `REJECT`，只包含一个 `policy-path`，更新间隔 3,600 秒。
- `Auto` 与五个地区组必须为可见 `url-test`，显式第一项为 `REJECT`，并保持 `interval=600`、`tolerance=100`、`evaluate-before-use=true` 和唯一 `NodePool` 来源。
- ChatGPT、Claude、Gemini 与 TikTok 只递归导入日本、新加坡、台湾、美国；Bahamut 保持台湾、香港顺序。
- 禁止恢复 Smart、load-balance、本机 `Diagnostics` 或第二套总自动入口。自动组不得加入 `DIRECT`。
- DNS、APNs、BiliBili、Ads/Pegasus、STUN、UDP/QUIC 和规则顺序的审计边界不得在未验证真机行为时改变。

## 验证

```bash
export PYTHONDONTWRITEBYTECODE=1
python3 -m compileall -q tools
python3 tools/convert_to_remote_rules.py
python3 tools/generate_runtime_lock.py
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/audit_precise_domains.py
python3 tools/update_external_resources.py --verify-lock
python3 tools/update_service_rules.py --verify-lock
python3 tools/test_audit_config.py
python3 tools/test_release_inventory.py
python3 tools/test_stage_surge_zip.py
python3 tools/package_release.py --output ../Surge-R13.13-Complete-No-Embedded-20260901.zip
```

需要联网时再运行：

```bash
python3 tools/audit_rules.py --check-dynamic
python3 tools/audit_rules.py --check-runtime-remote
```

发布前确认 `git diff --check` 无误，重新生成运行锁、清单与校验和，并确保 ZIP 中不含真实订阅或临时文件。
