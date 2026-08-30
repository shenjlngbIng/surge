# R13.6 到 R13.7 Smart Hybrid 迁移说明

R13.7 只升级节点选择架构。国内外软件规则、BiliBili 国内版修复、DNS、Telegram、APNs、UDP/QUIC、双栈兜底、固定快照和四个已删除的隐藏开关保持不变。建议完整导入新配置、运行锁、审计器和文档，不要只复制策略组片段。

## 关键差异

| 项目 | R13.6 | R13.7 |
| --- | --- | --- |
| 默认代理 | `Auto` 固定测速选优 | `Smart` 根据真实连接质量动态选路 |
| 手动安全入口 | `NodePool` | 保留不变 |
| 地区入口 | `url-test` | Smart |
| 选路依据 | 固定测试地址延迟 | 首包时间、TCP 重传、连接失败、测速和站点记忆 |
| 自动参数 | 600 秒、100 毫秒、首次使用前评估 | 首次使用前评估；Smart 固定五分钟测试调度 |
| 自动空组行为 | 可能 `DIRECT/SUBSTITUTE` | 不变 |
| 四个隐藏开关 | 已删除 | 继续删除 |
| 运行资源 | 29 固定＋1 动态 | 不变 |
| 策略组和规则 | 30 / 142 | 30 / 142 |
| 运行锁 | schema 20 | schema 21 |
| 完整包 | `Surge-R13.6-Complete-No-Embedded-20260830.zip` | `Surge-R13.7-Complete-No-Embedded-20260830.zip` |

## 为什么升级为 Smart

`url-test` 主要根据一个固定测试地址的延迟选择节点，可能出现测速很快但真实网站首包慢、丢包高或连接失败的情况。Smart 会持续综合实际连接的首包时间、TCP 重传、失败记录和测速结果；它还会记忆特定站点近期成功或失败的节点，并在当前连接失败时尝试其他候选。Surge iOS 5.21.0 及以上还会把 UDP 响应和静默中继失败纳入评分。

R13.7 的 `Smart` 与五个地区组都通过 `include-other-group=NodePool` 递归取得真实订阅代理。Smart 只接受代理策略，因此配置不会显式加入 `DIRECT`、`REJECT` 或 `Fail-Closed`；总入口使用精确过滤再次排除 `Fail-Closed`。Smart 使用固定五分钟测试调度，`interval` 对它无效，`tolerance` 也不属于 Smart 选路参数，所以两项都被删除。六个 Smart 组保留 `evaluate-before-use=true`。

Surge 官方说明，自动组没有可用成员时会以 `DIRECT` 替代，并在日志中显示 `SUBSTITUTE`。R13.7 继续明确披露这项风险。自动便利和全局严格失败关闭无法同时由当前 Surge 自动组机制保证。

## 升级步骤

1. 备份私人订阅地址和当前节点名称。备份不要提交到公开仓库。
2. 完整导入 R13.7。
3. 只替换 `NodePool.policy-path` 的占位 URL。
4. 在 Surge 中重新下载并加载配置，随后清理旧规则缓存。
5. 打开 `Proxy`，确认选择为 `Smart`。旧配置中的 `Auto` 已移除，Surge 也可能保留此前的 `NodePool` 选择。
6. 首次发起代理请求，等待 Smart 完成初始评估；之后让它根据真实流量逐步学习。
7. 检查香港、台湾、日本、新加坡、美国五个组是否能看到名称匹配的节点。
8. 按 README 的 Wi-Fi 与蜂窝真机清单验收。

地区组平时无需逐个手动选择。需要临时指定时，可在 Surge iOS 的策略组界面长按对应策略启用临时覆盖。Smart 界面显示的是近期最常用节点，不代表每条新连接必然使用同一个节点。

## 手动安全入口

需要禁止自动空组替代时，按下面顺序操作。

1. 将 `Proxy` 从 `Smart` 切到 `NodePool`。
2. 在 `NodePool` 选择一个已知可用节点。
3. 需要主动封闭代理流量时，选择 `Fail-Closed`。

`NodePool` 仍是手动 `select`，首项仍是内建 `reject` 的别名 `Fail-Closed`。它不会自动选最快节点，也不会经过 Smart。

## 旧策略状态

`Auto`、`AllServer`、`AdBlock`、`Security`、`UDP` 和 `Domestic` 继续不存在。R13.7 不会恢复旧隐藏选择，也不会改变 Ads 固定 `REJECT`、Pegasus 固定 `REJECT`、STUN 固定 `Proxy` 和国内规则固定 `DIRECT` 的行为。

升级后应检查一次 `Proxy` 的当前选择。只有明确切到 `Smart` 后，日常流量才会使用真实连接质量驱动的自动选路。

## 保持不变的功能

- 国内 BiliBili 继续使用 16 个精确后缀、两条 Ads 前置功能护栏和 `extended-matching`，策略固定为 `DIRECT`。
- 国际版专用规则和策略继续删除，七条历史域名只走通用 `Proxy` 兼容护栏。
- 152 条固定 Ads 与 1,438 条固定 Pegasus 历史 IOC 继续 `REJECT`。
- Telegram 继续使用同名策略组并默认继承 `Proxy`。
- AliDNS、DNSPod 双 DoH、固定引导、证书校验和 DNS 端口边界保持不变。
- `ApplePush = fallback, Proxy, DIRECT` 保持不变。
- `udp-policy-not-supported-behaviour=REJECT`、`block-quic=per-policy` 和 STUN 代理保持不变。

## 回退

确需回退时，恢复完整 R13.6 包和私人订阅地址。不要混用两个版本的 `Surge.conf`、`Rules/r10.lock.json`、清单、哈希或审计脚本。回到 R13.6 后，默认入口恢复为 `Auto = url-test`，地区组也恢复固定测速选优。
