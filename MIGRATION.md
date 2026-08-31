# R13.9 到 R13.10 真实网络诊断迁移说明

R13.9 删除了会被 Surge 网络诊断误选的 `Fail-Closed = reject`，所以原来的固定超时消失了。但真实订阅节点仍只由 `policy-path` 加载到 `NodePool` 外置策略组，并不会变成主配置 `[Proxy]` 中的代理实体；网络诊断找不到测试对象，就把“测试代理策略”和“UDP 代理转发”两行直接留空。

R13.10 增加一个不含凭据、只绑定本机的 `Diagnostics` SOCKS5 诊断桥。网络诊断测试该桥时，请求会重新进入 Surge 规则系统，再由当前 `Proxy → Smart/手选节点` 送出。它不属于任何策略组，规则也不能指回它，因此不会形成代理递归。

## 关键差异

| 项目 | R13.9 | R13.10 |
| --- | --- | --- |
| `[Proxy]` | 无静态代理 | 唯一 `Diagnostics = socks5, 127.0.0.1, 6153, udp-relay=true` |
| 全局代理诊断 | 因无测试对象而空白 | 测试 `Diagnostics`，内层走当前 `Proxy` |
| UDP 诊断 | 因无测试对象而空白 | `apple.com@1.1.1.1` 经当前 `Proxy` 测试真实节点 UDP |
| 防回环 | 不适用 | `Diagnostics` 禁止进入任何组或规则；全部组保持 `include-all-proxies=0` |
| 本机 SOCKS5 端口 | 使用 Surge 默认值 | 显式锁定 `wifi-access-socks5-port=6153` |
| 诊断目标规则 | 依赖普通分流 | `cp.cloudflare.com` 与 `1.1.1.1` 在 DNS 端口拒绝前固定进入 `Proxy` |
| Smart、NodePool 与地区组 | R13.9 基线 | 不变 |
| DNS、Telegram、APNs、BiliBili、哨兵 | R13.9 基线 | 不变 |
| 策略组和活动规则 | 30 / 142 | 30 / 143 |
| 运行资源 | 29 固定＋1 动态 | 不变 |
| 运行锁 | schema 23 | schema 24 |
| 故障注入 | 119 | 128 |
| 完整包 | `Surge-R13.9-Complete-No-Embedded-20260830.zip` | `Surge-R13.10-Complete-No-Embedded-20260831.zip` |

## 诊断链路

TCP 诊断链路如下。

`网络诊断 → Diagnostics → 本机 SOCKS5 127.0.0.1:6153 → DOMAIN,cp.cloudflare.com,Proxy → 当前 Smart/手选真实节点`

UDP 诊断链路如下。

`网络诊断 → Diagnostics UDP relay → 本机 SOCKS5 127.0.0.1:6153 → IP-CIDR,1.1.1.1/32,Proxy → 当前 Smart/手选真实节点`

TCP 通过表示当前 `Proxy` 路径能够建立真实代理连接。UDP 通过还要求最终真实节点及服务商支持 UDP；配置继续使用 `udp-policy-not-supported-behaviour=REJECT`，不支持时会明确失败，不会静默直连。

## 升级步骤

1. 备份私人 `NodePool.policy-path`，不要把地址或令牌提交到公开仓库。
2. 完整导入 R13.10，并只替换 `NodePool.policy-path` 的占位 URL。
3. 确认 `Proxy` 选择 `Smart`，`NodePool` 中能够看到真实节点。
4. 重新运行网络诊断。“测试代理策略”和“UDP 代理转发”应显示 `Diagnostics`，不能空白，也不能显示 `REJECT`。
5. TCP 应通过。UDP 若失败，进入 `NodePool` 切换到服务商明确标注支持 UDP 的节点，再运行一次；这类失败不能用 `DIRECT` 伪装通过。
6. 在 Wi-Fi 和蜂窝各验证一次 DNS、国内 BiliBili、Telegram、APNs、AI、IPv4/IPv6 与 UDP。

## 保持不变

- `Proxy → Smart` 的日常自动选路、五个地区 Smart 和 AI/TikTok 的允许地区均不变。
- 双 DoH、证书校验、AliDNS 双栈引导和 DNSPod 动态主机名引导均不变。
- 国内 BiliBili 固定 `DIRECT`；国际版专用规则继续删除。
- Telegram、ApplePush、哨兵、Ads/Pegasus、STUN、QUIC 和双栈公网兜底均不变。
- `AdBlock`、`Security`、`UDP`、`Domestic` 四个隐藏状态组继续不存在。
- `allow-wifi-access=false` 和 `allow-hotspot-access=false` 继续阻止其他设备使用代理服务；显式 6153 端口只供本机回环。

## 回退

确需回退时，恢复完整 R13.9 包与对应私人订阅地址。不要混用 R13.9 的 `Surge.conf` 与 R13.10 的运行锁、清单、校验和或审计脚本。回退后网络诊断的两个代理行会重新变为空白，这是 R13.9 的已知限制。
