# R13.13 单订阅与失败关闭审计报告

审计日期：2026-09-01

## 结论

R13.13 撤回 R13.12 的 `Private-Proxies.conf` 双配置流程，恢复为一个公开主配置加一个本机私人订阅 URL。用户只需要替换 `NodePool.policy-path`，不需要 Sub-Store 自定义脚本、额外配置文件或导入顺序。

节点来源变简单后，R13.12 已验证的分流、DNS、BiliBili、APNs、固定规则快照与失败关闭结构保持不变。10 个自动组继续使用显式 `REJECT` 的 `url-test`，没有 Smart、DIRECT 自动后备或本机回环诊断代理。

## 公开配置对照

| 配置 | 节点接入方式 | 采纳内容 | 未照搬内容 |
| --- | --- | --- | --- |
| [Rabbit-Spec Surge](https://github.com/Rabbit-Spec/Surge/blob/Master/Conf/Spec/Surge.conf) | `select + policy-path=你的订阅地址` | 单 URL、地区组递归复用节点池 | 空 Smart 可能产生替代行为 |
| [Rabbit-Spec Surge-EN](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-EN.conf) | 单个外置节点组 | 地区过滤、UDP 不支持时拒绝 | 额外地区和不适用的默认项 |
| [Lucky Surge](https://github.com/As-Lucky/Lucky/blob/main/Lucky-Surge.conf) | 手动节点组直接使用 `policy-path` | 一处订阅地址、自动组复用节点池 | DIRECT 混入多个服务组和宽泛过滤 |
| 本仓库 R13.11 | `NodePool.policy-path` | 已真机使用过的单订阅结构 | R13.11 文档不够强调诊断显示边界 |

对照配置共同采用外置 `policy-path`，说明这是 Surge 日用配置最常见、最易部署的订阅接入方式。R13.13 在此基础上保留显式 `REJECT`，避免订阅为空或自动组无成员时静默直连。

## 关键结构

```ini
[Proxy]
# intentionally empty

[Proxy Group]
Auto = url-test, REJECT, ..., include-other-group=NodePool
NodePool = select, REJECT, policy-path=https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL, update-interval=3600, ...
HongKong = url-test, REJECT, policy-regex-filter=..., ..., include-other-group=NodePool
```

该结构保证：

- 只出现一个订阅入口，用户只改一处；
- `NodePool` 第一项是 `REJECT`，旧节点消失时不会默认直连；
- `Auto`、地区和受限服务组均显式包含 `REJECT`；
- `policy-regex-filter` 只筛选导入成员，不会移除显式 `REJECT`；
- 没有真实订阅被提交到公开仓库。

## 全局诊断边界

`policy-path` 向策略组导入外置节点，但不会把它们声明为主配置 `[Proxy]` 的静态代理。因此 Surge iOS 全局“测试代理策略”和“UDP 代理转发”可能不枚举这些节点。

R13.13 接受这个显示边界，禁止以下伪修复：

- 本机 `Diagnostics = socks5, 127.0.0.1,...`；
- 伪造可达静态代理只为让诊断变绿；
- 把 `udp-policy-not-supported-behaviour` 改成 `DIRECT`；
- 将 `REJECT` 或其他非真实策略冒充节点测试结果。

真实 TCP 应在 `NodePool` 内对具体节点测试。真实 UDP 需要节点协议、订阅参数和服务端共同支持，应使用具体节点能力测试或真实 UDP 流量验收。

## DNS、规则与供应链

- AliDNS 与 DNSPod DoH 同时启用，证书校验开启。
- 大陆应用 DNS 位于公网 DNS 端口拒绝前并固定 `DIRECT`；境外应用 DNS 位于其后并固定 `Proxy`。
- STUN 在通用公网与国内规则前固定进入 `Proxy`。
- 公网 IPv4、IPv6 最终进入 `Proxy`，唯一 `FINAL` 为 `FINAL,Final,dns-failed`。
- 29 个仓库规则资源固定到提交 `2b8fa93901061cf0482b079203630bcd11bfe0b1`。
- 唯一动态资源为 `https://ruleset.skk.moe/List/non_ip/domestic.conf`。
- Ads 与 Pegasus 位于固定边界，BiliBili 和必要功能护栏按审阅顺序加载。

## 验证范围

自动化验证覆盖配置头、General 全量键、唯一订阅入口、空 `[Proxy]`、策略组顺序、自动组失败关闭、地区过滤摘要、策略循环、规则数量和顺序、DNS/UDP 边界、固定资源、运行锁、发布清单、校验和与 ZIP 安全边界。

静态审计不能证明私人订阅在线、节点标签真实、服务端支持 UDP、远端递归 DNS 不泄漏或运营商链路稳定。最终仍需在真实设备的 Wi-Fi 和蜂窝网络分别验收。
