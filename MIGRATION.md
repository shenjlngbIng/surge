# R13.10 到 R13.11 安全纠错迁移说明

R13.11 撤回 R13.10 的本机 `Diagnostics` SOCKS5 诊断桥。真机已经证明该桥的 TCP 请求可以完成，但本机 SOCKS5 服务不支持诊断要求的 UDP relay；更严重的是，旧 `Proxy → Smart` 在订阅未加载时会被 Surge 自动替换为 `DIRECT/SUBSTITUTE`，因此 TCP 绿色结果不一定代表真实代理。

这不是通过修改测速地址就能解决的问题。R13.11 恢复诚实的空白全局代理诊断，并把所有 Smart 自动组改成带显式 `REJECT` 的 `url-test`。

## 关键差异

| 项目 | R13.10 | R13.11 |
| --- | --- | --- |
| `[Proxy]` | 本机 `Diagnostics` SOCKS5 桥 | 空；不伪造静态代理 |
| 全局代理/UDP 诊断 | 强制显示 `Diagnostics`，TCP 可能假绿，UDP 必败 | 因节点仅存在于 `policy-path` 而保持空白 |
| 默认自动入口 | `Smart` | `Auto = url-test, REJECT, ...` |
| 空订阅或更新失败 | Smart 可能 `DIRECT/SUBSTITUTE` | 显式 `REJECT`，评估失败即报错 |
| `NodePool` | 只含导入节点 | 第一项固定 `REJECT`，随后才是导入节点 |
| 地区与 AI/TikTok | Smart | 带 `REJECT` 的 `url-test` |
| 自动测试 | Smart 固定调度与真实流量学习 | 600 秒结果有效期、100 ms 切换容差、首次使用前评估 |
| 活动规则 | 143 | 142；删除 Cloudflare 回环探针，`1.1.1.1` 恢复原出口诊断位置 |
| 策略组 | 30 | 30 |
| 运行资源 | 29 固定＋1 动态 | 不变 |
| 运行锁 | schema 24 | schema 25 |
| 故障注入 | 128 | 133 |
| 完整包 | `Surge-R13.10-Complete-No-Embedded-20260831.zip` | `Surge-R13.11-Complete-No-Embedded-20260831.zip` |

## 升级步骤

1. 先复制保存私人 `NodePool.policy-path`。公开仓库不会也不能保存订阅令牌。
2. 完整导入 R13.11，不要只刷新旧规则。
3. 把私人地址重新填入 `NodePool` 的 `policy-path`。公开占位 URL 本身不会返回节点。
4. 打开 `NodePool`，确认除第一项 `REJECT` 外还能看到真实节点。
5. 打开 `Proxy`，确认选择第一项 `Auto`。旧的 `Smart` 已删除。
6. 清理旧配置缓存并重新加载。事件中不应再出现“Smart组中没有可用的子策略”。
7. 全局网络诊断的代理与 UDP 两行应为空白。DNS 与直连测试仍正常；空白是外置节点架构的限制，不是错误。
8. 进入具体真实节点的详情或策略测试入口分别检查 TCP 和 UDP。UDP 失败时检查节点协议、订阅是否含 `udp-relay=true` 以及服务端能力。
9. 在 Wi-Fi 和蜂窝各验证 BiliBili、Telegram、APNs、AI、IPv4/IPv6、DNS 与实际 UDP 应用。

## 预期事件

- `include-all-networks` 警告仍会出现。为 APNs 和全网络接管继续保留该选项；它可能影响 AirDrop、Xcode 或 USB Dashboard。
- 本机 HTTP/SOCKS5 监听的 INFO 事件仍可能出现，这是 Surge 自身服务，不是 R13.10 的诊断桥。
- 私人订阅未加载时，`Auto` 会评估失败或落到 `REJECT`。此时没有网络是预期安全结果。
- `Smart ... SUBSTITUTE` 不应再出现，因为 R13.11 没有 Smart 组。

## 保持不变

- 双 DoH、证书校验、AliDNS 双栈引导和 DNSPod 动态主机名引导。
- 国内 BiliBili 固定 `DIRECT`，国际版专用规则继续删除。
- Telegram、ApplePush、哨兵、Ads/Pegasus、STUN、QUIC 和双栈公网兜底。
- `AdBlock`、`Security`、`UDP`、`Domestic` 四个隐藏状态组继续不存在。
- `udp-policy-not-supported-behaviour=REJECT`，不支持 UDP 时绝不退回直连。
- `include-all-networks=true`、`include-apns=true` 与 ApplePush 的代理优先、直连后备顺序。

## 回退

不建议回退到 R13.10，因为它同时存在 UDP 假桥和 Smart 空组直连风险。若必须回退，应恢复整套对应版本文件与私人订阅地址，不能混用不同版本的 `Surge.conf`、运行锁、审计器、清单或校验和。
