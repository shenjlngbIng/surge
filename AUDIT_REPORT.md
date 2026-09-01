# R13.14 回退修复审计报告

审计日期：2026-09-01

## 结论

真机截图已经证明订阅加载成功：`Auto` 与 `America` 能选择真实美国节点。故障来自 R13.13 的多层策略结构和显式 `REJECT` 占位，不来自用户订阅或导入操作。

R13.14 以 R13.9 最后正常的单订阅行为为基线，并参考常见公开 Surge 配置的直接 `policy-path` 用法，删除后来引入的诊断桥、分离配置、空地区组和拒绝占位。

## 回归来源

| 版本 | 改动 | 结果 |
|---|---|---|
| R13.9 | 外置订阅只含真实节点 | 日常节点正常，全球诊断可能不枚举外置节点 |
| R13.10 | 本机 SOCKS5 诊断桥 | TCP 可能经替代路径，UDP 回环不成立 |
| R13.11 | Auto、地区和服务组加入 REJECT | 空地区组在界面显示大量红色失败 |
| R13.12 | `[Proxy]` 分离配置 | iOS 出现分离配置段加载失败，安装复杂 |
| R13.13 | 恢复一条订阅但保留 REJECT 结构 | 节点已加载，界面和选择仍异常 |
| R13.14 | 订阅直接进入唯一 Proxy | 恢复正常使用模型 |

## 当前策略结构

```ini
[Proxy]
# empty

[Proxy Group]
Final = select, Proxy, DIRECT, ..., hidden=1
Proxy = smart, policy-path=<one Surge URL>, update-interval=3600, evaluate-before-use=true, ..., hidden=0
```

- 策略组从 30 个降到 23 个。
- 唯一可见组为 `Proxy`。
- `NodePool`、`Auto` 和五个地区组全部删除。
- 所有显式 `REJECT` 组成员删除；规则层面的广告、安全和 DNS 拒绝继续保留。
- 20 个服务组隐藏并跟随 `Proxy`，Apple 保留 `DIRECT` 默认。

## DNS

- Cloudflare 与 Quad9 DoH，证书校验开启。
- `encrypted-dns-follow-outbound-mode=true`。
- Surge 自身的 DOH、DOH3、DOQ、DOT、DNS 固定进入 `Proxy`。
- 已知大陆与境外应用内 DoH/DoT 端点固定进入 `Proxy`。
- 53 端口接管，53/853/8853 未审阅出口拒绝。
- 固定加密 DNS 引导地址取自 Cloudflare 与 Quad9 官方资料。

## 验证结果

- 主配置审计：23 个策略组、147 条活动规则、30 个运行资源。
- 故障注入：67 项全部被审计器拒绝。
- 固定规则：29 个仓库资源和 1 个动态国内资源通过。
- 精确域名：DIRECT/Proxy 跨策略冲突为 0。
- 公开配置无嵌入节点、订阅、令牌或回环代理。

全局代理/UDP 诊断是否显示仍由 Surge 对 `policy-path` 外置节点的枚举行为决定，不能通过假代理安全地强行填绿。R13.14 的验收对象是唯一 `Proxy` 中的真实节点和真实流量。
