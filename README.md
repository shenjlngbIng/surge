# Surge iOS Privacy + Push R13.19

外部规则版。主配置包含 144 条分流指令、29 个外部规则文件引用、40 个策略组，**没有内嵌规则列表**。节点池、Smart、五个地区、20 个服务策略和哨兵均保留。

## 使用

1. [下载 Surge.conf](https://raw.githubusercontent.com/shenjlngbIng/surge/main/Surge.conf)，作为新配置导入。
2. 搜索 `REPLACE_WITH_SURGE_SUBSCRIPTION_URL`，把完整占位地址替换为已经可用的 Surge 格式订阅地址。全配置只有一个 `policy-path`，位于隐藏的 `Subscription` 组。
3. 保存并启用。`Proxy` 默认选择 `Auto`；`NodePool` 默认也是 `Auto`，并列出所有真实节点供手动选择。

沿用手机上已经正常工作的 Sub-Store 模块、订阅和设置。无需新增分离配置或脚本。旧私人副本可能保存旧订阅地址，升级时以自己当前已修好的地址为准。

主配置的外部资源应有 **29 份规则和 1 个 Subscription 订阅**。规则使用本仓库固定提交的 GitHub 原始文件；不依赖 jsDelivr。规则内容随配置版本更新，已下载的资源由 Surge 缓存。

## 策略与保护

| 项目 | 行为 |
| --- | --- |
| Auto / Smart | 从订阅节点中自动选择，保留 `Fail-Closed` 空池保护 |
| NodePool | 默认 Auto，也可手动选择真实节点；不直接路由隐藏订阅源 |
| 五个地区 | 地区内测速；没有可用地区节点时回退 Auto |
| AdBlock | 控制 Ads.list，默认 REJECT |
| Security | 控制 Pegasus.list，默认 REJECT；该表是历史 IOC，不代表完整威胁检测 |
| Domestic | 控制 China.list 和 CN GeoIP，默认 DIRECT；国内 BiliBili、局域网等明确直连例外保留 |
| UDP | 控制 STUN 和未被前置业务/国内规则命中的 UDP，默认 Proxy |
| ApplePush | 优先 Proxy，失败后 DIRECT，保留推送可用性的例外 |

`Fail-Closed` 是刻意不可连接的本机保护项，它单独显示“失败”是预期状态。它使 Smart 始终保留一个代理类型成员，避免空 Smart 被替换为 DIRECT。隐藏订阅源和隐藏地区源另有原生 REJECT 保护。哨兵保护的是应走代理的流量；明确直连的国内/LAN/APNs 例外和用户手动选择的 DIRECT 不属于全局断网保护。

## DNS 与 UDP

Surge 自身使用 AliDNS/DNSPod 独立直连 DoH，开启证书校验，避免解析节点域名时形成代理启动循环。应用内已知解析器仍按规则代理，公共 53/853/8853 边界和 `no-resolve` 保留。DNS 检测不保证显示与代理出口完全相同的运营商；DoH 引导、连通性检测及远端节点 DNS 仍有各自的边界。

订阅导入时统一启用 `udp-relay=true`，补齐 Shadowsocks/SOCKS5 需要的客户端开关。服务端仍必须支持 UDP；不支持或转发失败时不会自动转为直连。TCP 测速成功不等于 UDP 已通过。主配置不包含本机 SOCKS 诊断桥，也不以假成功填充诊断页面。

依据：[Smart](https://manual.nssurge.com/policy-groups/smart.html)、[策略导入](https://manual.nssurge.com/policy-groups/policy-including.html)、[加密 DNS](https://manual.nssurge.com/dns/encrypted-dns.html)、[UDP 转发](https://manual.nssurge.com/policies/udp.html)。外部订阅与规则的基本结构也对照了 [开发者参考配置](https://github.com/Rabbit-Spec/Surge/blob/Master/Conf/Spec/Surge-Developer.conf) 和 [Lucky 配置](https://github.com/As-Lucky/Lucky/blob/main/Lucky-Surge.conf)。

## 验证与维护

发布前检查全部外部文件的 HTTP 状态和 SHA-256，并运行分流案例、空池/地区回退模型、故障注入和打包校验。这些检查不等同于用户 iPhone 或实际节点的运行测试。

```bash
python3 tools/convert_to_remote_rules.py
python3 tools/audit_config.py
python3 tools/audit_rules.py --check-runtime-remote
python3 tools/test_runtime_rules.py
python3 tools/test_policy_failover.py
python3 tools/test_audit_config.py
```

`Rules/` 是维护和校验用的来源副本；主配置仍通过 URL 加载。已删除内嵌生成工具，避免维护时误把规则再次写入配置。公开仓库不保存私人订阅或节点凭据。
