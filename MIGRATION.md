# R13.8 到 R13.9 网络诊断修复迁移说明

R13.9 是根据 Surge iOS 真机复现结果完成的定向修复。R13.8 将 `Fail-Closed = reject` 定义在 `[Proxy]` 中，日常 Smart 路由虽然能够正常使用真实节点，但 Surge 网络诊断会把这个故意拒绝流量的静态条目当成代理策略，导致 TCP 代理测试和 UDP 转发测试固定显示 `Test timeout`。

## 关键差异

| 项目 | R13.8 | R13.9 |
| --- | --- | --- |
| `[Proxy]` | `Fail-Closed = reject` | 不定义静态代理 |
| `NodePool` | `Fail-Closed`＋真实订阅节点 | 仅真实订阅节点 |
| Smart 来源 | 递归导入并过滤 `Fail-Closed` | 直接递归导入全部真实节点 |
| 手动失败关闭 | `Proxy → NodePool → Fail-Closed` | `Proxy → REJECT` |
| 网络诊断 | 可能固定测试 `Fail-Closed` | 不再存在可被误测的拒绝代理 |
| DNS、规则与服务分流 | R13.8 基线 | 不变 |
| 策略组和活动规则 | 30 / 142 | 不变 |
| 运行资源 | 29 固定＋1 动态 | 不变 |
| 运行锁 | schema 22 | schema 23 |
| 完整包 | `Surge-R13.8-Complete-No-Embedded-20260830.zip` | `Surge-R13.9-Complete-No-Embedded-20260830.zip` |

## 为什么必须修改

Surge 将 `[Proxy]` 中定义的条目视为代理策略。网络诊断的代理项会对代理策略执行 HTTP 测试，UDP 项会测试代理 UDP 转发。`Fail-Closed = reject` 本来就是用来主动拒绝连接的安全哨兵，因此被诊断选中后必然超时；这不能反映当前 `Smart` 选择的真实节点状态。

R13.9 删除这个自定义代理别名，让 `NodePool` 只承载 `policy-path` 返回的真实节点。严格手动拒绝改用 Surge 内建 `REJECT`，仍然不会把失败流量静默改为直连。

## 升级步骤

1. 备份私人 `NodePool.policy-path`，不要把地址或令牌提交到公开仓库。
2. 完整导入 R13.9，并只替换 `NodePool.policy-path` 的占位 URL。
3. 确认 `Proxy` 选择 `Smart`，`NodePool` 中能够看到真实节点。
4. 重新运行网络诊断。TCP 项应显示某个真实节点；UDP 是否通过取决于该节点和服务商是否支持 UDP。
5. 在 Wi-Fi 和蜂窝各验证一次 DNS、国内 BiliBili、Telegram、APNs、AI、IPv4/IPv6 与 UDP。

## 保持不变

- `Proxy → Smart` 的日常自动选路、五个地区 Smart 和 AI/TikTok 的允许地区均不变。
- 双 DoH、证书校验、AliDNS 双栈引导和 DNSPod 动态主机名引导均不变。
- 国内 BiliBili 固定 `DIRECT`；国际版专用规则继续删除。
- Telegram、ApplePush、哨兵、Ads/Pegasus、STUN、UDP/QUIC 和双栈公网兜底均不变。
- `AdBlock`、`Security`、`UDP`、`Domestic` 四个隐藏状态组继续不存在。

## 回退

确需回退时，恢复完整 R13.8 包与对应私人订阅地址。不要混用 R13.8 的 `Surge.conf` 与 R13.9 的运行锁、清单、校验和或审计脚本。
