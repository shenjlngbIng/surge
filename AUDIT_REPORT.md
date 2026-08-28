# Surge R13.3 Domestic Performance 全量审计报告

审计日期：2026-08-28

## 结论

R13.3 的静态结构、策略引用、循环依赖、规则顺序、R13.2 保留性、本地规则库存、来源锁、故障注入、发布白名单、ZIP 路径安全、清单和双份 SHA-256 检查通过。

可以作为完整候选包发布，但国内软件体感、运营商路径、节点服务端 DNS、APNs、UDP 和 iOS 后台行为仍需 Surge iOS 真机验证。静态审计不能代替设备运行结果。

## R13.2 保留性

| 检查项 | R13.2 | R13.3 | 结果 |
| --- | ---: | ---: | --- |
| 策略组 | 34 | 34 | 34/34 保留 |
| 规则匹配条件 | 130 | 130 | 130/130 保留 |
| 远程运行资源 | 33 | 33 | 33/33 保留 |
| 固定远程 URL | 30 | 30 | 30/30 保留 |
| 动态运行 URL | 3 | 3 | 3/3 保留 |
| 本地 `.list` | 30 | 30 | 30/30 字节保留 |
| `NodePool.policy-path` | 1 处占位符 | 相同 | 保留 |
| `Fail-Closed` | `127.0.0.1:1` | 相同 | 保留 |
| APNs、AI、流媒体、游戏等服务组 | 存在 | 存在 | 保留 |

本版没有删除规则，只改变 17 条现有规则的策略行为或选项，并调整其中 16 条的位置。

- 16 个大陆应用 DNS 主机从 `Proxy` 改为 `Domestic`，移动到通用 DNS 端口拒绝之前。
- `GEOIP,CN,Domestic,no-resolve` 改为 `GEOIP,CN,Domestic`。

## 配置结构

| 检查项 | 结果 |
| --- | ---: |
| 配置节 | 5/5 |
| 策略组 | 34 |
| 活动规则 | 130 |
| 运行时远程资源 | 33 |
| 固定提交资源 | 30 |
| 动态资源 | 3 |
| 本地规则文件 | 30 |
| 未知策略引用 | 0 |
| 策略组循环 | 0 |
| 重复活动规则 | 0 |
| 地区正则编译 | 5/5 |
| `FINAL` | 1 条且位于末尾 |
| 订阅占位符 | 恰好 1 处 |
| 主配置内嵌规则快照 | 0 |

`Surge.conf` 为 UTF-8、LF、无 BOM、无 NUL，并以换行结束。主配置 SHA-256 为 `03439367da4078b16e6a7b9bb94482ef6896ff69f113f66b3da8cefc7d753fe6`。

## 国内性能修正

R13.2 中 16 个大陆 DNS 主机规则位于通用端口拒绝之后并固定进入 `Proxy`。应用自带 DoH 时，这会让国内应用的解析连接绕海外节点，增加握手时延，并可能影响国内 CDN 选路。

R13.3 的顺序为：

1. 局域网与本地主机。
2. Apple Wi-Fi 门户和 STUN。
3. 16 个大陆应用 DNS 主机进入 `Domestic`。
4. 其余公网 53、853、8853 端口拒绝。
5. Apple 引导、出口诊断和 13 个境外应用 DNS 主机。
6. 安全、广告和服务分流。
7. Domestic/China/Global 精确规则。
8. 可解析的 `GEOIP,CN,Domestic`。
9. 公网 IPv4、IPv6 `Proxy` 兜底与唯一 `FINAL`。

审计器要求 16 条大陆 DNS 规则完整、连续、全部指向 `Domestic`，并位于 STUN 与端口拒绝之间。任何一条恢复为 `Proxy`/`DIRECT`、缺失或移动到拒绝之后都会失败。13 条境外 DNS 规则同样要求完整顺序和 `Proxy` 策略。

`Domestic` 默认仍是 `DIRECT`，用户在境外或受限网络中可以整体切到 `Proxy`。未经审阅的公网 DoT 仍被 853 端口规则拒绝。

## GeoIP 行为

末端 CN GeoIP 去掉 `no-resolve` 后，尚未命中域名规则的请求可以先解析，再按中国 IP 进入 `Domestic`。这是国内兜底实际覆盖未收录服务的必要条件。

代价是这类未命中域名可能新增一次 DNS 查询，并依赖当前 DoH 响应与 Surge GeoIP 数据库。非中国 IP 继续落入紧随其后的 `0.0.0.0/0` 或 `::/0` `Proxy` 规则，不会获得新的直连兜底。

所有 `IP-CIDR` 和 `IP-CIDR6` 规则仍通过地址族与语法检查，并保留 `no-resolve`。

## 策略与 DNS 边界

- `Proxy` 默认选择 `AllServer`，`NodePool` 仍是唯一订阅入口和可见手动节点池。
- `AllServer` 与五个地区组仍为 Smart，只从 `NodePool` 导入代理，并保留 `Fail-Closed`。
- `AdBlock`、`Security`、`UDP` 和 `Domestic` 可见；`ApplePush` 隐藏并按 Proxy、DIRECT 后备。
- Surge 自身仍使用 AliDNS 与 DNSPod 两个 DoH，`encrypted-dns-follow-outbound-mode=false`，证书校验开启。
- 两个 DoH 可能同时看到查询，这不是匿名 DNS 设计。
- `hijack-dns=*:53`、Host 引导、IPv6 VIF、局域网限制和公网端口控制保持不变。

## 规则来源

30 个固定 URL 全部指向：

```text
https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@d1d714d575d5494ef1a7613238f4f301e1b293df/Rules/
```

包内 30 份 `.list` 与 R13.2 字节一致。Pegasus、19 份服务规则和 10 份仓库维护规则的来源锁继续通过。

三个动态运行资源的发布基线保持不变：

| 资源 | 类型 | 策略 | 条目 | SHA-256 |
| --- | --- | --- | ---: | --- |
| `reject_phishing.conf` | DOMAIN-SET | Security | 147,468 | `c7dd0c7429e1f11168b1e1923a54defbca6403f13ba7e10246b3b87b5c367f4e` |
| `reject.conf` | DOMAIN-SET | AdBlock | 135,304 | `5ceb8c9903e4fc967722eab763a91e7d5ef91fcbe9bad71d1c378cf5ad800e4d` |
| `domestic.conf` | RULE-SET | Domestic | 869 | `56809cd8399666433acb1229c3a472667a32c86fc2a0b9861a5dca54020564aa` |

动态内容不随 ZIP 分发。在线审计检查 HTTP、UTF-8、类型格式、重复行和 8 MiB 大小边界，不要求上游未来一直保持发布哈希。

## 自动化测试

| 测试 | 结果 |
| --- | ---: |
| 配置故障注入 | 115/115 被拒绝 |
| ZIP 安全回归 | 27/27 通过 |
| 发布清单回归 | 15/15 通过 |
| Python 编译 | 15/15 工具通过 |
| 运行锁再生成 | 与受审配置一致 |
| Pegasus 固定来源锁 | 通过 |
| 19 份服务规则来源锁 | 通过 |
| China/Global 精确集合 | Domestic 306、Proxy 116、冲突 0 |
| 严格发布目录 | 66/66 文件 |
| 双份 SHA-256 | 一致并全部校验通过 |
| 确定性打包 | 相同输入两次 ZIP 字节一致 |

故障注入新增大陆 DNS 策略回退、规则块错位、境外 DNS 绕过和 CN GeoIP 恢复 `no-resolve` 等场景。运行锁升级为 schema 17，并记录两组应用 DNS 清单与 GeoIP 解析不变量。

## 剩余风险与真机项目

| 风险 | 实际影响 | 当前处理 |
| --- | --- | --- |
| 无 Surge iOS 原生解析器 | 私有语义差异只能在应用中发现 | 导入后执行配置检查与真机验收 |
| 大陆 DNS 端点网络差异 | 境外或受限网络可能不可达 | `Domestic` 可切到 `Proxy` |
| CN GeoIP 触发解析 | 未命中域名多一次查询，可能受错误 DNS/GeoIP 影响 | 双 DoH、可见 Domestic、最近请求排查 |
| 动态列表变化 | 可能误报、撤回或上游故障 | 精确 URL、可见策略、在线检查和定期监控 |
| 固定规则陈旧 | 稳定但不会自动获得新提交 | 固定快照并人工审阅新版本 |
| 节点服务端 DNS | 客户端无法替节点决定递归解析器 | 更换节点或由服务方修复 |
| Smart 结果非固定 | 不同站点可能选择不同节点 | 可把 Proxy 切到 NodePool 手动固定 |

真机至少测试常用国内软件首屏、登录、图片和视频 CDN；查看大陆 DNS 主机是否命中 `Domestic`；在 Wi-Fi 与蜂窝分别检查 APNs、DNS、IPv4、IPv6、UDP、AI 和流媒体；确认日志没有持续规则下载、解析循环或代理循环错误。
