# Surge iOS Privacy + Push R13.18

R13.18 将 29 份已审阅规则直接放进一个 `Surge.conf`，消除导入和规则更新对 jsDelivr 的依赖。主配置包含 5,664 条活动规则、39 个策略组；仍只需要维护一个节点订阅地址。

## 使用

1. [下载 Surge.conf](https://raw.githubusercontent.com/shenjlngbIng/surge/main/Surge.conf)，在 Surge 中作为新配置导入。
2. 在文本模式搜索 `REPLACE_WITH_SURGE_SUBSCRIPTION_URL`，把完整占位地址替换为自己当前的 Surge 格式订阅地址。
3. 保存并启用。主配置的“外部资源”中只应剩下 `NodePool` 订阅，规则列表不再需要下载。

如果使用已填订阅的私人副本，不必重复修改地址。该副本只保留用户提供过的地址，不代表订阅服务当前已验证可用。

`sub.store` 地址由手机上原有的 Sub-Store 模块处理。保留该模块及其已有设置；无需新增分离配置、额外转换脚本或替换模块。此地址不能在另一台服务器上验证手机内的订阅。

## 保留的功能

NodePool、Auto/Smart、五个地区入口、20 个服务策略，以及 AdBlock、Security、UDP、Domestic 全部保留。APNs、BiliBili、AI、流媒体、Telegram、广告及 Pegasus 规则的原顺序和策略不变。

五个隐藏地区源各含一个原生 `REJECT`，使无节点的地区源仍有明确的拒绝成员，供可见地区组回退到 Auto。它不建立任何回环代理连接。

## 尚不能承诺的行为

- **Sub-Store 500 与节点全部失败需要手机端日志才能确认原因。** 规则改为内置只解决规则资源下载依赖；旧节点名称、旧到期日期均不能证明当前订阅状态。
- **Smart 空池不是自动断网哨兵。** Surge 官方记录了空组使用 `DIRECT/SUBSTITUTE` 的行为。本版保留 Smart，但不宣称在整个订阅为空时严格失败关闭。隐藏地区的 REJECT 只保护地区空源。
- Surge 自身使用 AliDNS/DNSPod 的独立直连 DoH，证书校验开启。它不会保证 DNS 检测结果与代理出口一致；普通 DNS 仍可用于 DoH 域名引导和连通性检测。
- `PROTOCOL,DOH/DOH3/DOQ/DOT/DNS` 只匹配 Surge 自身的 DNS，请勿把它们当成所有应用的 DoH 检测器。本配置的这几条协议规则在 `encrypted-dns-follow-outbound-mode=false` 时不参与自身 DNS 分流；已知应用解析器由域名规则处理。
- 离线校验不等同于 iPhone 真机、真实代理或 UDP 测试。网络诊断页空白的具体原因也未在本环境验证。

依据：[策略组行为](https://manual.nssurge.com/policy-groups/overview.html)、[Smart](https://manual.nssurge.com/policy-groups/smart.html)、[加密 DNS](https://manual.nssurge.com/dns/encrypted-dns.html)、[DNS 协议匹配](https://manual.nssurge.com/rules/protocol-and-network.html)。

## 维护

`Rules/` 保存原始维护副本和来源锁，用户日常导入无需这些文件。维护者更新来源后运行 `tools/embed_runtime_rules.py` 生成主配置。主配置内的规则随配置版本更新。

```bash
python3 tools/embed_runtime_rules.py --check
python3 tools/test_embed_runtime_rules.py
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/test_audit_config.py
python3 tools/package_release.py --output ../Surge-R13.18-Single-File-20260907.zip
```

公开仓库不包含私人订阅、节点凭据或私人日志。
