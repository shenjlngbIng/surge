# R13.7 到 R13.8 Smart 与 DNS 韧性迁移说明

R13.8 是一次全盘复核后的定向修复。BiliBili 国内版、Telegram、APNs、UDP/QUIC、哨兵、四个已删除的隐藏开关、规则内容、首条命中顺序和固定快照都不变；本版调整 Surge 自身 DoH 的启动解析，并补全 AI/TikTok 在允许地区内的自动容错。

## 关键差异

| 项目 | R13.7 | R13.8 |
| --- | --- | --- |
| 传统引导 DNS | AliDNS 双 IPv4 | AliDNS 双 IPv4＋双 IPv6 |
| `dns.alidns.com` 静态引导 | 2 IPv4＋1 IPv6 | 2 IPv4＋2 IPv6 |
| `doh.pub` 引导 | 固定 `1.12.12.12`、`120.53.53.53` | 由引导 DNS 动态解析主机名 |
| AI/TikTok 默认选路 | 手动 `select`，首项日本 Smart | 服务自身 Smart，汇总四个允许地区的真实节点 |
| 双 DoH 与证书校验 | 开启 | 不变 |
| 策略组和活动规则 | 30 / 142 | 不变 |
| 运行资源 | 29 固定＋1 动态 | 不变 |
| 运行锁 | schema 21 | schema 22 |
| 完整包 | `Surge-R13.7-Complete-No-Embedded-20260830.zip` | `Surge-R13.8-Complete-No-Embedded-20260830.zip` |

## 为什么要改 DNS 引导

DNSPod 已公告不再公开推荐通过免费 DoH/DoT 的旧 IP 接入，建议使用 `https://doh.pub/dns-query`，以便服务方调整后端并提高稳定性。R13.7 的 DoH URL 虽然使用主机名，但 `[Host]` 又把该主机名冻结到旧 IP，长期会失去动态调度能力。

Surge 在配置加密 DNS 后，只把传统 `dns-server` 用于连通性测试和解析 DoH URL 中的主机名。R13.8 因此保留双 DoH、直连启动和证书校验，同时让 `doh.pub` 通过 AliDNS 引导动态解析。AliDNS 自身仍使用官方静态引导，并补齐第二条官方 IPv6 地址。

## 升级步骤

1. 备份私人 `NodePool.policy-path`，不要把地址或令牌提交到公开仓库。
2. 完整导入 R13.8，不要只复制 `[General]` 或 `[Host]` 片段。
3. 只替换 `NodePool.policy-path` 的占位 URL。
4. 重新下载配置并清理旧规则缓存。
5. 确认 `Proxy` 仍选择 `Smart`；升级不需要手动选择具体节点。
6. ChatGPT、Claude、Gemini 与 TikTok 会在允许地区内自动选优；需要临时固定时，长按对应策略并选择一个真实节点。
7. 在 Wi-Fi 和蜂窝各测试一次 DNS、国内 BiliBili、Telegram、APNs、AI、IPv4/IPv6 和 UDP。

## 保持不变

- `Proxy → Smart` 日常自动选路和 `NodePool → Fail-Closed` 手动安全入口不变。
- 香港、台湾、日本、新加坡、美国五个地区组仍为 Smart。
- AI/TikTok 的允许地区仍是日本、新加坡、台湾、美国，香港与通用 Proxy 仍不进入候选池；变化只是由手动首项改为跨允许地区 Smart。
- 国内 BiliBili 仍使用 16 个精确后缀、两条 Ads 前置护栏和固定 `DIRECT`。
- 国际版专用规则继续删除，七条历史域名只保留通用 `Proxy` 防串线护栏。
- Telegram 当前官方 CIDR、Apple APNs 当前网段、ApplePush 的 `Proxy → DIRECT` 后备顺序都不变。
- 152 条固定 Ads、1,438 条 Pegasus、STUN 代理、UDP 不支持即拒绝、QUIC 按策略和双栈公网代理兜底都不变。
- `AdBlock`、`Security`、`UDP`、`Domestic` 四个隐藏状态组继续不存在。

## 回退

确需回退时，恢复完整 R13.7 包与对应私人订阅地址。不要混用 R13.7 的 `Surge.conf` 与 R13.8 的 `Rules/r10.lock.json`、清单、校验和或审计脚本。
