# 贡献说明

R13.14 把主配置、规则快照、来源锁、运行锁、审计器、故障注入和发布清单视为一个整体。行为变化必须同步更新并完成全套验证。

## 不变量

- 公开 `Surge.conf` 只保留一个 `Proxy.policy-path=https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL`，不得提交真实订阅、节点或令牌。
- `[Proxy]` 保持为空，不得添加回环诊断、静态假代理或拒绝别名。
- `Proxy` 保持唯一可见的 `smart` 组，直接加载外置订阅，不得恢复 `NodePool`、`Auto`、地区组或显式 `REJECT` 成员。
- 服务策略保持隐藏并跟随 `Proxy`，Apple 保留 `DIRECT, Proxy` 顺序。
- 加密 DNS 必须跟随规则；`DOH`、`DOH3`、`DOQ`、`DOT`、`DNS` 和已知应用内 DNS 端点保持 `Proxy`。
- `hijack-dns=*:53`、53/853/8853 拒绝、证书校验、UDP 不支持时拒绝和 `block-quic=per-policy` 不得放松。
- 固定运行资源继续钉住完整提交，动态资源必须有来源、范围、更新频率和失败边界。

## 验证

```bash
python3 tools/audit_config.py
python3 tools/test_audit_config.py
python3 tools/convert_to_remote_rules.py
python3 tools/audit_rules.py
python3 tools/audit_precise_domains.py
python3 tools/test_release_inventory.py
python3 tools/test_stage_surge_zip.py
python3 tools/package_release.py --output ../Surge-R13.14-Complete-No-Embedded-20260901.zip
```

不要在 Issue、提交、测试夹具或截图中包含真实订阅 URL、节点认证信息或私人日志。
