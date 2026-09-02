# Surge iOS Privacy + Push R13.17

R13.17 是一次真机故障恢复版。R13.16 的回环假代理会被 Smart 当成真实节点，同时加密 DNS 又依赖 `Proxy → Auto`，最终造成节点测试与外部资源一起超时。本版移除该回环依赖，恢复一条 Sub-Store 订阅即可使用的结构。

## 使用

1. 导入 `Surge.conf`。
2. 在文本模式搜索 `REPLACE_WITH_SURGE_SUBSCRIPTION_URL`。
3. 只把这一处替换为自己的 Surge 格式 Sub-Store 地址。
4. 保存并重新加载；`NodePool` 应显示真实节点，`Auto` 应自动选出可用节点。

```ini
NodePool = select, policy-path=https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL, update-interval=3600, no-alert=0, hidden=0, include-all-proxies=0
Auto = smart, evaluate-before-use=true, include-other-group=NodePool, ...
```

Sub-Store 必须输出 Surge 节点格式，不能使用 Clash、Mihomo、Shadowrocket 或通用 Base64 输出。

## 本版修复

- 删除 `127.0.0.1:1` 回环假代理，Smart 只接收 `NodePool` 的真实节点。
- 订阅为空或全部节点失效时，`Auto` 没有 `DIRECT` 或伪代理兜底，按原生行为失败关闭。
- 加密 DNS 改回 AliDNS DoH 与 DNSPod DoH 的直连引导，避免节点尚未加载时出现 DNS 循环依赖；证书校验保持开启。
- `cdn.jsdelivr.net` 明确经过 `Proxy` 更新，避免中国移动直连路径超时。
- 删除唯一的动态国内补充资源，运行时只保留 29 个固定提交资源，减少一个 HTTP 500 来源。
- NodePool、Auto、五地区、20 个服务策略、AdBlock、Security、UDP、Domestic 均保留。
- APNs、国内 BiliBili、AI、流媒体、Telegram、广告与 Pegasus、STUN、UDP/QUIC 和双栈兜底规则均保留。

## DNS 与诊断边界

`hijack-dns=*:53`、应用内 DoH/DoT 代理分流和 53/853/8853 未审阅出口拒绝仍然生效。Surge 自身的 AliDNS/DNSPod 加密查询采用直连引导，这是为了保证域名型代理节点能够启动；它不会向运营商发送明文查询，但 DNS 检测页可能显示这两个解析服务。

`policy-path` 导入的节点不一定出现在 Surge 全局“测试代理策略”和“UDP 代理转发”枚举中。不要再用回环或假代理填充这两栏；以 `NodePool`/`Auto` 的真实节点延迟、实际网页和真实 UDP 流量验收。

## 维护验证

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

公开仓库不包含私人订阅、节点、令牌或日志。
