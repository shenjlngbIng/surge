# Surge iOS Privacy + Push R13.16

R13.16 恢复旧版完整策略结构和 `Fail-Closed` 哨兵，同时仍然只维护一条订阅地址。节点由 `NodePool` 从 Sub-Store 加载，`Auto` 自动选择，Proxy、地区与服务策略均保留。

## 使用

1. 下载或导入 `Surge.conf`。
2. 进入文本模式，搜索 `REPLACE_WITH_SURGE_SUBSCRIPTION_URL`。
3. 把完整占位地址替换为自己的 Surge 格式订阅地址，只替换这一处。
4. 保存并重新加载。打开“策略”，应看到 `Proxy`、`NodePool`、`Auto`、地区组和服务策略。

配置中的订阅入口只有一行：

```ini
NodePool = select, policy-path=https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL, update-interval=3600, no-alert=0, hidden=0, include-all-proxies=0
```

Sub-Store 输出必须选择 Surge 格式。不要把 Clash、Mihomo、Shadowrocket 或通用 Base64 输出放进 `policy-path`。

## 本版修复

- 恢复 `NodePool → Auto → Proxy`，并恢复香港、台湾、日本、新加坡、美国与全部服务策略。
- `NodePool` 不再把 `REJECT` 设为默认节点；订阅成功后直接显示真实节点。
- `[Proxy]` 恢复唯一的 `Fail-Closed = http, 127.0.0.1, 1, no-error-alert=true` 哨兵；它只作为 `Auto` 的失败兜底，不直接放入 NodePool、Proxy 或可见地区组。
- 每个地区使用隐藏的严格筛选源；订阅没有该地区节点时，可见地区组自动回退到 `Auto`，不再显示红色失败卡片。
- 保留 Smart 自动选点；需要固定出口时可在 `NodePool` 手动选择真实节点。
- 保留 APNs、国内 BiliBili、AI、流媒体、Telegram、广告与 Pegasus、STUN、UDP/QUIC 和双栈兜底规则。

## DNS 防泄漏

- Surge 加密 DNS 使用 Cloudflare DoH 与 Quad9 DoH，并开启 `encrypted-dns-follow-outbound-mode=true`。
- Surge 自身的 `DOH`、`DOH3`、`DOQ`、`DOT`、`DNS` 请求固定进入 `Proxy`。
- 已知应用内大陆及境外 DoH/DoT 域名均进入 `Proxy`。
- 系统及应用的 53 端口 DNS 由 `hijack-dns=*:53` 接管；未审阅的 53、853、8853 出口拒绝。
- 证书校验保持开启，代理目标仍使用远端解析。

传统 `dns-server` 仅用于连通性测试和必要引导。网络诊断页面显示对这些服务器的测试，不等于日常域名查询绕过加密 DNS。

## 网络诊断边界

`policy-path` 是 Surge iOS 常用的一条订阅接入方式。外置节点不一定出现在全局“测试代理策略”和“UDP 代理转发”的枚举列表中；这两块空白不是订阅未导入。实际节点能否工作，以 `Proxy` 中真实节点的延迟、网页访问和真实 UDP 能力为准。

配置不会再用本机回环代理或假代理伪造绿色诊断。UDP 是否可用仍取决于节点协议、订阅参数和服务端支持，且不支持时保持 `REJECT`，不会偷偷直连。

## 验收

导入后确认：

1. `NodePool` 显示真实节点，`Auto` 自动选点；可见地区组没有红色 `REJECT` 占位。
2. 常用网页、ChatGPT、Telegram、流媒体和国内应用可正常访问。
3. DNS 泄漏检测只显示 Cloudflare、Quad9 或代理出口附近解析器，不出现运营商 DNS。
4. Surge 事件中没有 `DIRECT/SUBSTITUTE`、循环代理或分离配置加载失败。
5. UDP 用实际支持 UDP 的节点和应用测试，不用全局空白行判断。

## 维护验证

```bash
python3 tools/audit_config.py
python3 tools/test_audit_config.py
python3 tools/convert_to_remote_rules.py
python3 tools/audit_rules.py
python3 tools/audit_precise_domains.py
python3 tools/test_release_inventory.py
python3 tools/test_stage_surge_zip.py
python3 tools/package_release.py --output ../Surge-R13.16-Complete-No-Embedded-20260901.zip
```

公开仓库不包含私人订阅、节点、令牌或日志。规则来源、许可、发布边界和迁移说明见仓库内对应文档。
