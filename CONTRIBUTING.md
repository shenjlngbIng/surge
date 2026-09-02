# 贡献说明

R13.17 把主配置、规则快照、来源锁、运行锁、审计器、故障注入和发布清单视为一个整体。行为变化必须同步更新并完成全套验证。

## 不变量

- 公开 `Surge.conf` 只保留一个 `NodePool.policy-path` 占位地址，不得提交真实订阅、节点或令牌。
- `[Proxy]` 保持为空，不得添加回环诊断、静态假代理或拒绝代理。
- `NodePool` 只负责订阅；`Auto` 只递归导入 NodePool 的真实代理。
- Proxy、五地区、20 个服务策略、AdBlock、Security、UDP、Domestic 不得擅自删除。
- Surge 自身加密 DNS 保持独立直连引导；应用内 DoH/DoT 仍进入 Proxy。
- `hijack-dns=*:53`、53/853/8853 拒绝、证书校验、UDP 不支持时拒绝和 `block-quic=per-policy` 不得放松。
- 29 个运行资源继续固定到完整提交；不得新增未经锁定和审阅的动态资源。

## 验证

```bash
python3 tools/generate_runtime_lock.py
python3 tools/audit_config.py
python3 tools/test_audit_config.py
python3 tools/convert_to_remote_rules.py
python3 tools/audit_rules.py
python3 tools/audit_precise_domains.py
python3 tools/test_release_inventory.py
python3 tools/test_stage_surge_zip.py
python3 tools/package_release.py --output ../Surge-R13.17-Complete-No-Embedded-20260902.zip
```

不要在 Issue、提交、测试夹具或截图中包含真实订阅 URL、节点认证信息或私人日志。
