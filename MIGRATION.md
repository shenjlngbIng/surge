# R13.5 到 R13.6 Hybrid Auto 迁移说明

R13.6 只调整节点选择架构。国内外软件规则、BiliBili 国内版修复、DNS、Telegram、APNs、UDP/QUIC、双栈兜底、固定快照和四个已删除的隐藏开关保持不变。建议完整导入新配置、运行锁、审计器和文档，不要只复制策略组片段。

## 关键差异

| 项目 | R13.5 | R13.6 |
| --- | --- | --- |
| 默认代理 | 手动 `NodePool` | `Auto` 自动测速选优 |
| 手动安全入口 | `NodePool` | 保留不变 |
| 地区入口 | 手动 `select` | `url-test` 自动选优 |
| Smart | 无 | 无 |
| 自动参数 | 无 | 600 秒、100 毫秒、首次使用前评估 |
| 自动空组行为 | 不适用 | 可能 `DIRECT/SUBSTITUTE` |
| 四个隐藏开关 | 已删除 | 继续删除 |
| 运行资源 | 29 固定＋1 动态 | 不变 |
| 策略组和规则 | 29 / 142 | 30 / 142 |
| 运行锁 | schema 19 | schema 20 |
| 完整包 | `Surge-R13.5-Complete-No-Embedded-20260829.zip` | `Surge-R13.6-Complete-No-Embedded-20260830.zip` |

## 为什么选择 url-test

`url-test` 会从通过测试的成员中选择延迟最低者，适合一组用途相近的订阅节点。R13.6 的 `Auto` 从 `NodePool` 导入节点，并用 `policy-regex-filter` 排除 `Fail-Closed`。五个地区组继续使用原有名称过滤，只在对应地区节点中测试。

Smart 会忽略嵌套策略组和内建策略，无法直接复用当前 `NodePool` 架构。R13.6 因此不恢复 Smart。六个自动组都使用 `interval=600`、`tolerance=100` 和 `evaluate-before-use=true`。测试结果过期或网络变化后，Surge 会在组再次使用时重新评估，100 毫秒容差用于减少延迟相近节点之间的频繁切换。

Surge 官方说明，自动组没有可用成员时会以 `DIRECT` 替代，并在日志中显示 `SUBSTITUTE`。R13.6 明确保留这项风险说明。自动便利和全局严格失败关闭无法同时由当前 Surge 组机制保证。

## 升级步骤

1. 备份私人订阅地址和当前节点名称。备份不要提交到公开仓库。
2. 完整导入 R13.6。
3. 只替换 `NodePool.policy-path` 的占位 URL。
4. 在 Surge 中重新下载并加载配置，随后清理旧规则缓存。
5. 打开 `Proxy`，确认选择为 `Auto`。旧配置可能保留 R13.5 的 `NodePool` 选择。
6. 首次发起代理请求，等待 `Auto` 完成一轮测试。
7. 检查香港、台湾、日本、新加坡、美国五个组是否能看到名称匹配的节点。
8. 按 README 的 Wi-Fi 与蜂窝真机清单验收。

地区组平时无需逐个手动选择。需要临时指定时，可在 Surge iOS 的策略组界面长按对应策略启用临时覆盖。

## 手动安全入口

需要禁止自动空组替代时，按下面顺序操作。

1. 将 `Proxy` 从 `Auto` 切到 `NodePool`。
2. 在 `NodePool` 选择一个已知可用节点。
3. 需要主动封闭代理流量时，选择 `Fail-Closed`。

`NodePool` 仍是手动 `select`，首项仍是内建 `reject` 的别名 `Fail-Closed`。它不会自动选最快节点，也不会经过 `Auto`。

## 旧策略状态

`AllServer`、`AdBlock`、`Security`、`UDP` 和 `Domestic` 继续不存在。R13.6 不会恢复旧隐藏选择，也不会改变 Ads 固定 `REJECT`、Pegasus 固定 `REJECT`、STUN 固定 `Proxy` 和国内规则固定 `DIRECT` 的行为。

升级后应检查一次 `Proxy` 的当前选择。Surge 可能保留同名策略组的历史选择，只有用户明确切到 `Auto` 后，日常流量才会使用自动选优。

## 保持不变的功能

- 国内 BiliBili 继续使用 16 个精确后缀、两条 Ads 前置功能护栏和 `extended-matching`，策略固定为 `DIRECT`。
- 国际版专用规则和策略继续删除，七条历史域名只走通用 `Proxy` 兼容护栏。
- 152 条固定 Ads 与 1,438 条固定 Pegasus 历史 IOC 继续 `REJECT`。
- Telegram 继续使用同名策略组并默认继承 `Proxy`。
- AliDNS、DNSPod 双 DoH、固定引导、证书校验和 DNS 端口边界保持不变。
- `ApplePush = fallback, Proxy, DIRECT` 保持不变。
- `udp-policy-not-supported-behaviour=REJECT`、`block-quic=per-policy` 和 STUN 代理保持不变。

## 回退

确需回退时，恢复完整 R13.5 包和私人订阅地址。不要混用两个版本的 `Surge.conf`、`Rules/r10.lock.json`、清单、哈希或审计脚本。回到 R13.5 后，`Proxy` 和五个地区组重新变成手动选择，自动空组的 `DIRECT/SUBSTITUTE` 风险随之移除。
