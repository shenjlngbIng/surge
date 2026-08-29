# R13.3 到 R13.4 Strict DNS 迁移说明

R13.4 是 R13.3 基础上的定向 DNS 隐私修正与界面精简。它不删除策略组、规则匹配条件、远程规则来源、本地规则文件、订阅入口或失败关闭逻辑。

主配置、运行锁、审计器、故障注入、README、工作流、清单和哈希必须一起更新。只替换 `Surge.conf` 可以导入设备，但会让仓库中的运行锁和完整性清单停留在旧版本。

## 变化摘要

| 项目 | R13.3 | R13.4 |
| --- | --- | --- |
| 策略组 | 34 | 34 |
| 活动规则 | 130 | 130 |
| 远程运行资源 | 33 | 33 |
| 固定规则文件 | 30 | 30，字节不变 |
| 订阅入口 | `NodePool.policy-path` | 原样保留 |
| 大陆应用 DNS | 16 条规则进入 `Domestic`，位于端口拒绝前 | 原样保留 |
| 境外应用 DNS | 13 条规则进入 `Proxy` | 原样保留 |
| 中国 GeoIP | `GEOIP,CN,Domestic` | `GEOIP,CN,Domestic,no-resolve` |
| BiliBili 国内版 | `BiliBili.list → Domestic` | `BiliBili.list → DIRECT`；国际版仍先进入 `Streaming` |
| 隐藏辅助组 | `ApplePush` | `ApplePush`、`AdBlock`、`Security`、`UDP`、`Domestic` |
| 运行锁 | schema 17 | schema 18 |
| 配置故障注入 | 115 项 | 117 项（含 BiliBili 热修复退化检查） |
| ZIP 安全回归 | 27 项 | 28 项 |
| 完整发布文件 | 66 | 66 |
| 完整包 | `Surge-R13.3-Complete-No-Embedded-20260828.zip` | `Surge-R13.4-Complete-No-Embedded-20260828.zip` |

## 为什么修改

R13.3 为了让未收录的国内服务按 IP 进入 `Domestic`，在末端 CN GeoIP 去掉了 `no-resolve`。这会让尚未匹配的域名先调用 Surge 本地 DNS。配置中的 AliDNS 与 DNSPod DoH 直连，因此代理网页可能出现境外出口与大陆解析器并存的检测结果。

R13.4 恢复 `no-resolve`。已知国内域名继续由 WeChat、Direct、BiliBili、Sukka domestic、China 精确集合、共享云后缀和服务规则匹配；仍未命中的域名不在 CN GeoIP 处解析，而是落入 `Final`，默认由 `Proxy` 以主机名交给代理侧解析。已经解析为中国 IP 的字面量连接仍可进入 `Domestic`。

2026-08-29 热修复将国内 `BiliBili.list` 从 `Domestic` 改为 `DIRECT`。Surge 可能按策略组名称保留升级前的手动选择，而 R13.4 又隐藏了 `Domestic`；旧选择若是 `Proxy`，国内 BiliBili 就会绕海外节点并出现首屏或播放长时间加载。热修复只绕过这一个隐藏选择，国际版规则仍保持更高优先级并进入 `Streaming`。

没有把检测网站单独加到代理规则来伪装结果，也没有把 `encrypted-dns-follow-outbound-mode` 改为 `true`。后者在代理服务器本身使用域名时可能形成启动解析依赖并回退直连，不能作为严格隔离的保证。

`AdBlock`、`Security`、`UDP` 和 `Domestic` 只把 `hidden=0` 改为 `hidden=1`。Surge 仍会执行这些组，所有成员、默认选择和规则引用都在。需要排错时，在私人副本中临时改回 `hidden=0` 即可。

## 保留内容

- 34 个策略组的名称、类型、成员结构和默认选择全部保留。
- `Proxy → AllServer → NodePool`、五个 Smart 地区组和 `Fail-Closed` 保留。
- `Domestic` 成员顺序仍是 `DIRECT`、`Proxy`，只是从控制面板隐藏；国内 BiliBili 专用规则不再引用该组。
- 30 个固定远程 URL 仍固定到提交 `d1d714d575d5494ef1a7613238f4f301e1b293df`。
- 三个 Sukka 动态运行 URL、策略和 86,400 秒更新间隔保留。
- 30 份 `.list`、四份来源锁、APNs、UDP、广告、钓鱼、Pegasus、AI、流媒体和服务分流保留。
- `encrypted-dns-follow-outbound-mode=false`、两个 DoH、Host 引导、证书校验和 `hijack-dns=*:53` 保留。
- 16 个大陆应用 DNS 主机位于端口拒绝前的 R13.3 性能修正保留。
- 公开订阅占位符保留，真实订阅仍由用户在私人副本中填写。

## 推荐迁移步骤

1. 备份私人副本中的真实 `NodePool.policy-path`，不要把含令牌的副本上传到公开仓库。
2. Surge 可能按组名保留旧选择。覆盖升级前或在私人副本中临时取消隐藏后，确认 `AdBlock=REJECT`、`Security=REJECT`、`UDP=Proxy`、`Domestic=DIRECT`；再恢复四组的 `hidden=1`。
3. 解压 R13.4 完整包，用全部 66 个文件替换旧发布文件并保留目录层级。
4. 在私人 `Surge.conf` 中只恢复自己的 `NodePool.policy-path`，不要覆盖 R13.4 的 `[Rule]` 顺序。
5. 重新载入配置，刷新外部资源并清理 Surge DNS 缓存与检测网站数据。
6. 在无额外模块的状态下，使用至少两个检测站点复核网页出口和 DNS；再切换一个已知节点对比。
7. 测试常用国内软件首屏、登录、图片和视频 CDN。若某个未知国内域名因严格兜底改走代理，从最近请求提取精确域名，人工审阅后补到国内规则，而不要去掉全局 `no-resolve`。
8. 需要检查广告、安全、UDP 或国内总开关时，只在私人副本中把对应组临时改为 `hidden=0`，完成后恢复隐藏。
9. 分别在 Wi-Fi 和蜂窝网络检查 APNs、IPv4、IPv6、UDP、AI 与流媒体，不要删除 `Fail-Closed` 或把 `Final` 改成 `DIRECT` 来掩盖节点问题。

## DNS 行为边界

已审阅的大陆解析器主机可以在通用端口拒绝之前进入 `Domestic`。其余公网 53、853 和 8853 仍被拒绝。局域网私有地址在它们之前直连，本地路由器解析不受影响。

境外 DNS 域名规则位于端口拒绝之后，因此 HTTPS DoH 可以进入 `Proxy`，未审阅的 DoT 仍会先被 853 端口规则拒绝。Surge 自身的两个加密 DNS 继续由内部链路直连，不跟随普通应用规则，以避免域名型代理节点形成解析环。

严格边界只针对未命中且尚未解析的域名。明确的 `Domestic` 连接、本地网络、代理节点启动和 Surge 自身功能仍可能使用配置的本地 DNS。网页出口与解析器完全一致还取决于代理节点服务端的递归 DNS，客户端无法替远端节点决定该解析器。

## 性能取舍

恢复 `no-resolve` 会牺牲 R13.3 的“未知中国域名按解析 IP 直连”能力。现有国内域名规则覆盖常见服务，但不可能覆盖全部新域名，因此少量国内软件可能走代理并增加延迟。该代价换来更明确的代理域名 DNS 边界；若出现实例，应补充经过审阅的精确域名，不建议重新开启全局解析式 CN GeoIP。

## 回退

需要回退时，重新使用完整的 R13.3 包，并恢复当时的私人订阅地址。不要把 R13.4 的 `Rules/r10.lock.json`、清单、哈希或审计工具留在 R13.3 目录中。

回退会重新让末端 CN GeoIP 为未命中域名触发本地 DNS，也会让四个辅助策略组重新显示。16 个大陆应用 DNS 主机仍保持 R13.3 的 `Domestic` 性能修正。
