# R13.20 配置复核

复核日期为 2026-09-08。比较基线为 R13.19 辅助组隐藏版，提交 `9e033ed10f5af79767f634917a17af32768d2249`。

## 复核范围

检查主配置的参数、策略组引用、规则顺序、重复匹配与外部资源，同时按最终文件重写 README 和升级说明。第三方规则快照保持原样，不改 Sub-Store 后端，不读取或发布私人节点凭据。

## 删除内容与依据

| 删除项 | 数量 | 保留的有效行为 |
| --- | --- | --- |
| no-alert=0 | 40 处 | 使用默认 false，自动组通知设置不变 |
| hidden=0 | 29 处 | 使用默认可见，隐藏组的 hidden=1 保留 |
| include-all-proxies=0 | 34 处 | 使用默认 false，保留显式成员和 Subscription 引用 |
| 默认全局设置 | 8 项 | 保留暂停、蜂窝辅助、GeoIP 更新及访问限制的默认行为 |
| DNS 精确规则 | 2 条 | alidns.com 与 nextdns.io 后缀继续使用 Proxy |

八项全局设置为 auto-suspend、wifi-assist、all-hybrid、show-error-page-for-reject、disable-geoip-db-auto-update、http-api-web-dashboard、proxy-restricted-to-lan 和 gateway-restricted-to-lan。原值均与官方默认值一致。[全局参数](https://manual.nssurge.com/profile/general.html)、[策略组参数](https://manual.nssurge.com/policy-groups/parameters.html)、[成员导入](https://manual.nssurge.com/policy-groups/policy-including.html)

两条删除规则分别为 `DOMAIN,dns.alidns.com,Proxy` 和 `DOMAIN,dns.nextdns.io,Proxy`。从原精确规则到覆盖它的后缀规则之间，均为同出口 Proxy 的域名规则，没有其他出口或端口规则插入，因此删除后不改变这两个域名的匹配出口。

## 未删除的功能

- 40 个策略组均有业务规则或组间引用，节点池、Auto、五个地区及 20 个服务组完整保留。
- Subscription、Auto 和地区源的保护成员保留，组引用无循环。
- 隐藏辅助组、国内直连例外、APNs 的 DIRECT 回退以及 UDP 控制范围不变。
- 独立直连 DoH、证书校验、DNS 端口规则、ICMP 限制和 no-resolve 保留。
- 29 个外部规则引用继续使用原固定提交 SHA，规则列表内容未内嵌，也未修改。
- BiliBili、Apple 流媒体、Viu、Spotify 和 Microsoft 等冲突例外继续保留。

## 文件与结构

| 指标 | 结果 |
| --- | --- |
| 主配置 | 311 行，17,316 字节 |
| 相比基线 | 减少 76 行、5,186 字节，体积约减少 23.0% |
| 主分流指令 | 142 条 |
| 外部规则引用 | 29 个，26 个 RULE-SET 与 3 个 DOMAIN-SET |
| 策略组 | 40 个，其中 29 个可见、11 个隐藏 |
| 规则语义模型 | 内存中展开 5,659 条，不写入主配置 |
| 内嵌规则列表 | 0 份 |

## 验证项目

- 配置结构、参数清单、组成员与可见性、唯一订阅入口、引用无循环检查。
- 与基线比较，除确认删除的默认值和重复规则外，活动配置内容相同。
- 23 个域名/SNI 分流案例及 6 个损坏资源案例。
- 15 个地区名称、空订阅、全部失效、单地区回退、手动选择和控制开关的离线模型。
- 102 项配置故障注入，包含省略默认值后被显式改为相反值的情况。
- 外部资源 HTTP GET 与 SHA-256、精确域名冲突、来源锁、发布清单和打包校验。

## 验证边界

以上配置检查与模型测试不运行 iOS Surge 内核，不使用真实私人代理，不能证明真实节点 UDP、网站解锁或设备 DNS 检测成功。Fail-Closed 的预期失败不能当作真实节点故障。

地区组可以回退到 Auto，明确的国内直连、Apple 默认直连和 APNs 回退仍存在。哨兵仅保护配置中应走代理的路径，不构成系统级全局断网保证。
