# R13.16 Fail-Closed 哨兵恢复审计报告

审计日期：2026-09-01

## 结论

真机截图已经证明订阅加载成功：`Auto` 与 `America` 能选择真实美国节点。故障来自 R13.13 的多层策略结构和显式 `REJECT` 占位，不来自用户订阅或导入操作。

R13.16 在完整 NodePool、Auto、地区和服务策略上恢复唯一 `Fail-Closed` 静态哨兵。哨兵只由 Auto 引用；NodePool、Proxy 和可见地区组不直接暴露它。

## 回归来源

| 版本 | 改动 | 结果 |
|---|---|---|
| R13.9 | 外置订阅只含真实节点 | 日常节点正常，全球诊断可能不枚举外置节点 |
| R13.10 | 本机 SOCKS5 诊断桥 | TCP 可能经替代路径，UDP 回环不成立 |
| R13.11 | Auto、地区和服务组加入 REJECT | 空地区组在界面显示大量红色失败 |
| R13.12 | `[Proxy]` 分离配置 | iOS 出现分离配置段加载失败，安装复杂 |
| R13.13 | 恢复一条订阅但保留 REJECT 结构 | 节点已加载，界面和选择仍异常 |
| R13.14 | 订阅直接进入唯一 Proxy | 恢复正常使用模型 |
| R13.15 | 订阅回到 NodePool，恢复完整分组 | 保留功能并消除可见空组失败 |
| R13.16 | Auto 恢复 Fail-Closed 哨兵 | 订阅整体失效时明确失败关闭 |

## 当前策略结构

```ini
[Proxy]
Fail-Closed = http, 127.0.0.1, 1, no-error-alert=true

[Proxy Group]
Final = select, Proxy, DIRECT, ..., hidden=0
Proxy = select, Auto, NodePool, HongKong, TaiWan, Japan, Singapore, America, ...
NodePool = select, policy-path=<one Surge URL>, update-interval=3600, ...
Auto = smart, Fail-Closed, include-other-group=NodePool, ...
```

- 共 39 个策略组，其中 5 个严格地区源隐藏。
- `NodePool`、`Auto`、五个可见地区组和 20 个服务策略全部恢复。
- NodePool、Auto、Proxy 和可见地区组不含 `REJECT` 默认占位。
- 唯一 `Fail-Closed` 哨兵为不可达本机 HTTP 代理，只在所有真实节点不可用时承接 Auto。
- 地区没有匹配节点时回退 `Auto`；规则层面的广告、安全和 DNS 拒绝继续保留。

## DNS

- Cloudflare 与 Quad9 DoH，证书校验开启。
- `encrypted-dns-follow-outbound-mode=true`。
- Surge 自身的 DOH、DOH3、DOQ、DOT、DNS 固定进入 `Proxy`。
- 已知大陆与境外应用内 DoH/DoT 端点固定进入 `Proxy`。
- 53 端口接管，53/853/8853 未审阅出口拒绝。
- 固定加密 DNS 引导地址取自 Cloudflare 与 Quad9 官方资料。

## 验证结果

- 主配置审计：39 个策略组、147 条活动规则、30 个运行资源。
- 故障注入覆盖完整策略结构、DNS、规则与发布边界。
- 固定规则：29 个仓库资源和 1 个动态国内资源通过。
- 精确域名：DIRECT/Proxy 跨策略冲突为 0。
- 公开配置无嵌入节点、订阅、令牌或回环代理。

全局代理/UDP 诊断是否显示仍由 Surge 对 `policy-path` 外置节点的枚举行为决定，不能通过哨兵伪造绿色结果。R13.16 的验收对象是 `NodePool`、`Auto` 中的真实节点和真实流量。
