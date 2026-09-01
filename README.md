# Surge iOS Privacy + Push R13.14

R13.14 回到正常的一条订阅地址用法。订阅直接放进唯一可见的 `Proxy` 策略组，不再经过 `NodePool → Auto → 地区组`，也不再用 `REJECT` 填充空组。

## 使用

1. 下载或导入 `Surge.conf`。
2. 进入文本模式，搜索 `REPLACE_WITH_SURGE_SUBSCRIPTION_URL`。
3. 把完整占位地址替换为自己的 Surge 格式订阅地址，只替换这一处。
4. 保存并重新加载。打开“策略”，应只看到一个主要入口 `Proxy`，其中直接显示或选择真实节点。

配置中的订阅入口只有一行：

```ini
Proxy = smart, policy-path=https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL, update-interval=3600, evaluate-before-use=true, no-alert=0, hidden=0, include-all-proxies=0
```

Sub-Store 输出必须选择 Surge 格式。不要把 Clash、Mihomo、Shadowrocket 或通用 Base64 输出放进 `policy-path`。

## 本版修复

- 以 R13.9 之前的单订阅可用行为为基线，撤回 R13.10 的本机 SOCKS5 诊断桥、R13.12 的分离配置以及 R13.13 的显式 `REJECT` 占位。
- 删除可见的 `NodePool`、`Auto`、香港、台湾、日本、新加坡、美国空组。服务分流仍然存在，但全部隐藏并跟随 `Proxy`。
- `Final` 隐藏并默认跟随 `Proxy`，不再在策略页显示红色 `REJECT` 卡片。
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

1. `Proxy` 显示真实节点名称和延迟，不出现 `NodePool`、空地区组或成排红色 `REJECT`。
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
python3 tools/package_release.py --output ../Surge-R13.14-Complete-No-Embedded-20260901.zip
```

公开仓库不包含私人订阅、节点、令牌或日志。规则来源、许可、发布边界和迁移说明见仓库内对应文档。
