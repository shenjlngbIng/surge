# R13.2 到 R13.3 Domestic Performance 迁移说明

R13.3 是 R13.2 基础上的定向性能修正。它不删除策略组、规则匹配条件、远程规则来源、本地规则文件、订阅入口或失败关闭逻辑。

主配置、运行锁、审计器、故障注入、README、工作流、清单和哈希必须一起更新。只替换 `Surge.conf` 可以导入设备，但会让仓库中的运行锁和完整性清单停留在旧版本。

## 变化摘要

| 项目 | R13.2 | R13.3 |
| --- | --- | --- |
| 策略组 | 34 | 34 |
| 活动规则 | 130 | 130 |
| 远程运行资源 | 33 | 33 |
| 固定规则文件 | 30 | 30，字节不变 |
| 订阅入口 | `NodePool.policy-path` | 原样保留 |
| 大陆应用 DNS | 16 条规则进入 `Proxy`，且位于端口拒绝后 | 16 条规则进入 `Domestic`，位于端口拒绝前 |
| 境外应用 DNS | `Proxy` | 原样保留在端口拒绝后 |
| 中国 GeoIP | `GEOIP,CN,Domestic,no-resolve` | `GEOIP,CN,Domestic` |
| 运行锁 | schema 16 | schema 17 |
| 配置故障注入 | 110 项 | 115 项 |
| ZIP 安全回归 | 26 项 | 27 项 |
| 完整发布文件 | 66 | 66 |
| 完整包 | `Surge-R13.2-Complete-No-Embedded-20260828.zip` | `Surge-R13.3-Complete-No-Embedded-20260828.zip` |

## 为什么修改

R13.2 把 AliDNS、DNSPod、360 DNS 等大陆解析入口固定到 `Proxy`。应用自带 DoH 时，即使应用本身属于国内服务，解析连接也可能先绕海外节点，增加握手、丢包和 CDN 选路异常的概率。

R13.3 把这 16 个已审阅主机名放在通用 DNS 端口拒绝之前，并统一交给可见的 `Domestic`。该组默认 `DIRECT`，因此国内应用不再无条件绕海外节点；在境外、校园网或受限网络中仍可把 `Domestic` 切到 `Proxy`。

R13.2 末端 CN GeoIP 带 `no-resolve`，只能判断已经有 IP 的请求，无法为尚未命中域名表的域名主动取得 IP。R13.3 去掉这一选项，使末端国内兜底能对未命中域名实际生效。非中国 IP 继续进入紧随其后的 IPv4/IPv6 `Proxy` 兜底。

## 保留内容

- 34 个策略组名称、成员结构和默认选择全部保留。
- `Proxy → AllServer → NodePool`、五个 Smart 地区组和 `Fail-Closed` 保留。
- `Domestic` 仍为可见 `select`，成员顺序仍是 `DIRECT`、`Proxy`。
- 30 个固定远程 URL 仍固定到提交 `d1d714d575d5494ef1a7613238f4f301e1b293df`。
- 三个 Sukka 动态运行 URL、策略和 86,400 秒更新间隔保留。
- 30 份 `.list`、四份来源锁、APNs、UDP、广告、钓鱼、Pegasus、AI、流媒体和服务分流保留。
- `encrypted-dns-follow-outbound-mode=false`、两个 DoH、Host 引导、证书校验和 `hijack-dns=*:53` 保留。
- 公开订阅占位符保留，真实订阅仍由用户在私人副本中填写。

## 推荐迁移步骤

1. 备份私人副本中的真实 `NodePool.policy-path` 和当前手动策略选择，不要把含令牌的副本上传到公开仓库。
2. 解压 R13.3 完整包，用全部 66 个文件替换旧发布文件并保留目录层级。
3. 在私人 `Surge.conf` 中只恢复自己的 `NodePool.policy-path`，不要覆盖 R13.3 的 `[Rule]` 顺序。
4. 重新载入配置，并确认 `Proxy`、`UDP`、`Domestic` 和各服务组仍选中预期成员。
5. 保持 `Domestic=DIRECT` 测试常用国内软件；若当前网络限制大陆解析端点，再临时切到 `Domestic=Proxy` 对比。
6. 查看最近请求，确认 `dns.alidns.com`、`doh.pub` 或其他清单内大陆解析主机命中 `Domestic`，而 Google、Cloudflare、Quad9 等境外 DoH 命中 `Proxy`。
7. 分别在 Wi-Fi 和蜂窝网络测试国内软件首屏、图片/视频 CDN、登录、APNs、IPv4、IPv6、UDP、AI 与流媒体。
8. 完成测试后保存策略选择；不要删除 `Fail-Closed` 或把 `Final` 改成 `DIRECT` 来掩盖节点问题。

## DNS 行为边界

已审阅的大陆解析器主机可以在通用端口拒绝之前进入 `Domestic`。其余公网 53、853 和 8853 仍被拒绝。局域网私有地址在它们之前直连，本地路由器解析不受影响。

境外 DNS 域名规则位于端口拒绝之后，因此 HTTPS DoH 可以进入 `Proxy`，未审阅的 DoT 仍会先被 853 端口规则拒绝。Surge 自身的两个加密 DNS 继续由内部链路直连，不跟随普通应用规则。

末端 CN GeoIP 现在可能为一个尚未匹配、尚未解析的域名触发解析。这是国内兜底能够生效的必要代价。若解析质量差，应检查两个 DoH、Host 引导、GeoIP 数据库和私人模块，不要恢复 `no-resolve` 后把国内未命中流量全部推给公网 `Proxy` 兜底。

## 回退

需要回退时，重新使用完整的 R13.2 包，并恢复当时的私人订阅地址。不要把 R13.3 的 `Rules/r10.lock.json`、清单、哈希或审计工具留在 R13.2 目录中。

回退会让 16 个大陆应用 DNS 主机重新固定走 `Proxy`，并让末端 CN GeoIP 停止为未命中域名解析。若国内软件卡顿因此恢复，问题很可能正来自这两个旧行为。
