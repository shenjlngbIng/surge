# R13.21 配置复核

复核日期为 2026-09-08。比较基线为 R13.20，提交 `fdde262b630efe1939c34e34bed8c41699abbabf`。检查依据包括配置内容、离线行为测试和 Surge 官方规则说明。未访问私人订阅或修改 Sub-Store。

## 修正内容

### 广告误拦

移除以下 8 条 DOMAIN-KEYWORD 匹配。它们会覆盖正常业务页面，不能仅凭关键词认定请求属于广告。

| 删除的关键词 | 已核对的业务页面 |
| --- | --- |
| `.footlocker.` | [Foot Locker 商店](https://www.footlocker.com/) |
| `.zooplus.` | [Zooplus 商店](https://www.zooplus.com/) |
| `.bitiba.` | [Bitiba 商店](https://www.bitiba.co.uk/) |
| `.zoohit.` | [Zoohit 商店](https://www.zoohit.cz/) |
| `.stenaline.` | [Stena Line 官网](https://stenaline.com/) |
| `dolce-gusto.` | [Dolce Gusto 官网](https://www.dolce-gusto.com/) |
| `.nimiq.` | [Nimiq 官网及其钱包入口](https://www.nimiq.com/) |
| `seniorliving.` | [SeniorLiving 资讯与服务页面](https://www.seniorliving.org/) |

来源标记 `this_rule_set_is_made_by_sukkaw` 保留为注释，第三方许可文件不变。Ads 活动条目由 152 降至 143，`sanl.footlocker` 等细分匹配保留。未新增整站 DIRECT 或白名单规则，正常网站继续按原有业务规则或 Final 选择出口。[关键词匹配语义](https://manual.nssurge.com/rules/domain.html)

### 加密 DNS 顺序

仅移动原有 12 条境外 DNS 域名规则，使其位于 53 端口拒绝之后、853/8853 端口拒绝之前。原有国内及本地例外不变，不增加域名、公共 IP 或协议放行规则。

| 已识别的域名请求 | 原版 | 本版 |
| --- | --- | --- |
| `dot.pub:853` | Proxy | Proxy |
| `dns.google:853` | REJECT | Proxy |
| `dot.tiar.app:853` | REJECT | Proxy |
| `dns.google:443` | Proxy | Proxy |
| `dns.google:53` | REJECT | REJECT |
| 未知域名的 53/853/8853 请求 | REJECT | REJECT |

此处验证首条命中策略，不代表所有端点都提供全部端口，也不模拟 Surge 的 DNS 接管或协议识别。Surge 自身仍使用独立直连 DoH。[规则顺序](https://manual.nssurge.com/rules/overview.html)、[Google DoT](https://developers.google.com/speed/public-dns/docs/dns-over-tls)

## 保持不变的部分

逐字节比较确认 `[General]`、`[Host]`、`[Proxy]`、`[Proxy Group]` 与 R13.20 一致。29 份列表中只有 Ads 内容变化，其余 28 份未改。主配置仍有 142 条分流指令、40 个策略组和 29 个外部规则引用，没有内嵌规则列表。

节点池、单订阅入口、辅助组隐藏、哨兵及 UDP 参数均保留。地区组仍允许回退 Auto，ChatGPT 的共享登录依赖保持原有归属，这两项作为明确的使用取舍，不作无依据的删改。

规则先作为独立提交 `6e8e1bfbbdda66ee8ad0a5ad3979b6de8b5b7a51` 保存，再由主配置固定引用；运行锁同步到 schema 34。

## 验证项目

本地静态检查、行为及故障注入测试、来源锁和归档检查均通过。29 个运行时规则 URL 实际 GET 均返回 HTTP 200，下载内容的 SHA-256 与本地快照全部一致。

- 23 个既有域名/SNI 案例和 6 个外部资源损坏案例。
- 新增 16 个正常网站、8 个广告及 132 个 DNS 端口正反例，涵盖伪装后缀与未知端点。
- 10 个行为退化案例逐条恢复误拦关键词或错误顺序，均须被行为测试识别，不依赖配置哈希或固定条数。
- 104 项配置故障注入前先检查正常基线，防止审计器全部拒绝却被误判通过。
- 地区筛选、空订阅、全部失效、单地区回退、手动选择及控制开关的原有模型。
- 外部资源 HTTP GET 与 SHA-256、来源锁、精确域名冲突、发布清单及归档检查。

## 验证边界

所有模型均为离线检查，未运行 iOS Surge 内核，未连接私人代理。广告与端口测试验证指定请求的匹配结果，不能证明真实节点 UDP、网站解锁或设备 DNS 检测成功。Fail-Closed 的预期失败不作为真实节点故障。

地区回退、国内直连、Apple 默认直连和 APNs 的 DIRECT 回退继续存在。哨兵仅保护配置中应走代理的路径，不构成系统级全局断网保证。
