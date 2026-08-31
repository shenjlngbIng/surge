# R13.11 全盘分流与失败关闭审计报告

审计日期为 2026-08-31。审计对象包括 `Surge.conf`、29 份本地规则、四份锁文件、维护脚本、发布清单、ZIP、GitHub Actions，以及用户提供的 Surge 真机网络诊断和事件截图。

## 结论

本次是全配置复核，不是只改 UDP。30 个策略组、142 条活动规则、DNS、UDP、APNs、Telegram、国内 BiliBili、AI/流媒体地区、Ads/Pegasus、双栈兜底、外部资源和发布链均已检查。

R13.10 的 `Diagnostics` 回环方案被真机证伪并已全部撤回。R13.11 没有静态 `[Proxy]` 策略，也没有 Smart 组。10 个自动组统一改为带显式 `REJECT` 的 `url-test`；订阅为空、资源失败或地区无匹配节点时不能再被 Surge 替换为 `DIRECT`。

## 真机发现与修复

| 严重度 | 发现 | 影响 | R13.11 处理 |
| --- | --- | --- | --- |
| 严重 | `Diagnostics` 指向 Surge 本机 SOCKS5，服务不支持 UDP relay | UDP 诊断固定报 `The SOCKS proxy server doesn't support UDP relay` | 删除代理、端口依赖和回环探针规则 |
| 严重 | `Smart` 没有可用子策略时变为 `SUBSTITUTE/DIRECT` | 代理诊断或业务流量可能直连，绿色 TCP 结果不可信 | 删除全部 Smart；自动组显式加入 `REJECT` |
| 高 | 外置 `policy-path` 节点不会进入主配置 `[Proxy]` | 全局网络诊断无法直接选择真实节点 | 接受代理/UDP 两行空白；只测试具体真实节点 |
| 高 | 把 UDP 不支持回退改成 DIRECT 可以制造假绿 | UDP 绕过代理并泄漏真实出口 | 继续锁定 `udp-policy-not-supported-behaviour=REJECT` |
| 中 | `include-all-networks=true` 触发兼容性警告 | 可能影响 AirDrop、Xcode 或 USB Dashboard | 为 APNs/防旁路保留并明确披露，不误判为节点故障 |
| 中 | 自动入口只按固定测速 URL 可能选到业务质量一般的节点 | 低延迟不等于所有站点体验最佳 | 使用 600 秒有效期、100 ms 容差；保留手动 `NodePool` 固定节点入口 |

## 失败关闭证明

[Surge 策略组文档](https://manual.nssurge.com/policy-groups/overview.html)说明，策略组没有可用成员时会替换为 `DIRECT`，日志显示为 `SUBSTITUTE`；Smart 还会忽略内建策略和嵌套组。因而无法靠给 Smart 写一个 `REJECT` 来解决空组问题。

[URL Test 文档](https://manual.nssurge.com/policy-groups/url-test.html)说明，`url-test` 会从测试通过的成员中选择最低延迟策略；`evaluate-before-use=true` 会在第一次请求前等待测试，评估失败时请求直接报错。

[策略导入文档](https://manual.nssurge.com/policy-groups/policy-including.html)说明，显式成员排在导入成员之前，且 `policy-regex-filter` 只过滤 `policy-path`、`include-all-proxies` 和 `include-other-group` 的导入成员，不过滤显式成员。因此 R13.11 的设计是可验证的。

```ini
Auto = url-test, REJECT, interval=600, tolerance=100, evaluate-before-use=true, ..., include-other-group=NodePool
NodePool = select, REJECT, policy-path=<private-url>, ...
HongKong = url-test, REJECT, policy-regex-filter=<reviewed-regex>, ..., include-other-group=NodePool
```

- 真实节点存在并通过测试时，`REJECT` 测试失败，真实节点胜出。
- 订阅为空时，显式 `REJECT` 仍在，组不为空，不触发 `DIRECT/SUBSTITUTE`。
- 第一次评估全失败时，请求报错；旧结果失效或节点消失后不会改成直连。
- `NodePool` 选择项消失时，第一项是 `REJECT`，手动池也保持安全。
- 五个地区组和四个受限服务组使用相同保护，共 10 个自动组。

ApplePush 是唯一刻意保留的可用性例外，顺序仍为 `Proxy → DIRECT`。这不是隐蔽泄漏，而是明确的 APNs 送达取舍。

## 公开配置对照

用户指定的公开配置用于比较设计，不复制私人节点、脚本或未经审阅的大表。

| 来源 | 观察到的架构 | 可借鉴点 | 未直接采用的原因 |
| --- | --- | --- | --- |
| [Rabbit-Spec Developer](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-Developer.conf) | 外置 `policy-path` 与地区组 | 单 URL 导入、地区过滤 | 外置节点不能填充全局诊断；空 Smart 仍有替代风险 |
| [Lucky](https://raw.githubusercontent.com/As-Lucky/Lucky/main/Lucky-Surge.conf) | `[Proxy]` 为空、节点由策略组加载 | 公开配置不暴露节点 | 同样不能让全局诊断直接测试真实节点 |
| [Rabbit-Spec Surge-EN](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-EN.conf) | Smart 地区组、`policy-path` 节点池、UDP 不支持时拒绝 | 地区分层与 UDP `REJECT` 边界 | Smart 地区为空仍可能 `SUBSTITUTE` |
| [Coldvvater Surge.conf](https://gist.githubusercontent.com/Coldvvater/8093bc6be4340b5324b4a343493becfe/raw/Surge,conf) | 外置节点与服务分组 | 服务边界参考 | 不能解决私人外置节点的全局诊断限制 |
| [Thoseyearsbrian/Aegis](https://github.com/Thoseyearsbrian/Aegis) | 安全基线、UDP 探针、外置节点 | 安全开关与审计思路 | 探针参数不能给不支持 UDP 的服务端增加能力 |
| [blackmatrix7 规则库](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule) | 大量按服务分类的规则 | 服务域名对照与来源追踪 | 规则库不负责节点装载、空组行为或 UDP 服务端能力 |

公开配置普遍接受全局代理/UDP 诊断空白，没有用本机 SOCKS5 回环伪造真实代理。R13.11 回到这一诚实边界，同时额外加入显式 `REJECT` 解决空源直连风险。

## 国内外软件分流

| 范围 | 审计结果 |
| --- | --- |
| 国内 BiliBili | 16 个固定后缀 `DIRECT`；HTTPDNS/H5 功能护栏位于 Ads 前；国际版专组继续删除 |
| 微信与国内基础服务 | 固定 `DIRECT`，不经过已删除的 `Domestic` 状态组 |
| ChatGPT、Claude、Gemini、TikTok | 日本、新加坡、台湾、美国自动选优；每组空源失败关闭 |
| Bahamut | 仅台湾、香港 |
| Telegram | 固定进入 Telegram 选择组，默认继承 `Proxy`；官方 CIDR 与 raw TCP 边界不变 |
| 流媒体 | 各服务组默认继承 `Proxy`，保留地区手选能力 |
| Apple | 国内服务默认直连；流媒体例外先匹配；APNs 代理优先、直连后备 |
| 未匹配公网流量 | IPv4/IPv6 字面量先进入 `Proxy`，最后唯一 `FINAL,Final,dns-failed` |

## BiliBili、广告与安全

国内 BiliBili 卡顿的既有修复继续保留。

- `BiliBili.list` 含 16 个审阅后缀，使用 `DIRECT,extended-matching`。
- `httpdns.bilivideo.com` 与 `line3-h5-mobile-api.biligame.com` 在 Ads 前固定直连。
- 七条退役国际版域名先进入通用 `Proxy`，不会被国内父后缀覆盖。
- 动态 `reject.conf` 与 `reject_phishing.conf` 继续禁用，避免 iOS 内存压力和功能误杀。
- 152 条固定 Ads 与 1,438 条 Pegasus 历史 IOC 固定 `REJECT`。
- Spotify、Google `gvt2`、OpenAI RUM 等九条功能护栏位于 Ads 前。

## DNS、UDP、APNs 与双栈

- AliDNS、DNSPod 双 DoH、证书校验和 `encrypted-dns-follow-outbound-mode=false` 保持不变。
- AliDNS 双 IPv4/双 IPv6 负责引导；`doh.pub` 动态解析，不冻结旧 IP。
- 16 条大陆应用 DNS 在端口拒绝前直连；13 条境外应用 DNS 在端口拒绝后代理。
- 公网 53、853、8853 在局域网例外之后拒绝。
- STUN 在公网 DNS 与业务规则前固定 `Proxy`。
- `GEOIP,CN,DIRECT,no-resolve` 不强制本地解析未知域名。
- `proxy-test-udp=apple.com@1.1.1.1` 保留，供具体真实策略的 UDP 测试使用。
- [Surge UDP 文档](https://manual.nssurge.com/policies/udp.html)明确要求 SOCKS5、Shadowsocks 等同时具备客户端 `udp-relay=true` 和服务端支持；HTTP/HTTPS、SSH、Trust Tunnel 本身不能转发 UDP。
- `include-all-networks=true`、`include-apns=true` 与 ApplePush 顺序不变，故 DNS、推送和哨兵没有被本次纠错改写。

## 网络诊断边界

主配置 `[Proxy]` 为空，真实节点只由 `NodePool.policy-path` 导入。Surge 全局网络诊断只寻找主配置代理实体，因此代理和 UDP 两行保持空白。DNS 与直连测试仍正常。

R13.11 禁止以下“修复”。

- 禁止重新加入 `Fail-Closed = reject` 让全局诊断固定超时。
- 禁止重新加入本机 SOCKS5 `Diagnostics` 让 TCP 假绿、UDP必败。
- 禁止把 UDP 不支持行为改为 DIRECT。
- 禁止声称空白诊断代表真实节点失效。

要获得全局诊断对真实节点的支持，只能把真实节点定义放进 `[Proxy]`，例如通过用户私有的配置分离/托管节点段。公开仓库不能保存订阅和令牌，因此不能在单一公开文件中安全地替用户完成这一步。

## 供应链与发布

| 资源 | 模式 | 控制 |
| --- | --- | --- |
| 29 份仓库规则 | 不可变 | 完整提交 SHA、活动条目、文件 SHA-256、CDN 在线比对 |
| `domestic.conf` | 动态 | 精确 URL、格式与规模检查、24 小时更新 |
| 18 份服务上游 | 维护输入 | 固定提交、Git Blob、上游/本地 SHA-256、显式增删边界 |
| Pegasus 上游 | 维护输入 | 固定 Amnesty 提交、Git Blob、上游/本地 SHA-256 |
| 发布目录 | 固定白名单 | UTF-8/LF、无 BOM/NUL、无符号链接、确定性 ZIP |

## 自动验证

- 30 个策略组、142 条活动规则、30 个运行资源与唯一 FINAL。
- 10 个带显式 `REJECT` 的 `url-test`，0 个 Smart，0 个静态代理。
- `Proxy → Auto` 默认、`NodePool → REJECT` 首项、五个地区过滤和四个服务地区边界。
- DNS、UDP `REJECT`、APNs、STUN、QUIC、双栈和 BiliBili 顺序。
- 29 个固定资源、1 个动态资源、29 个本地规则文件和零嵌入规则。
- 133 项故障注入，覆盖 General、空源失败关闭、Smart/Diagnostics 回归、DIRECT 泄漏、策略循环、DNS/规则顺序和供应链边界。
- 发布目录、ZIP 路径穿越、重复文件、符号链接、编码和清单校验。

## 剩余限制

静态配置不能证明私人订阅在线、节点标签真实、服务端支持 UDP、远端递归 DNS 不泄漏、运营商链路稳定，也看不到未随仓库提供的模块改写。`url-test` 选择最低测试延迟，不等同于对每个网站都有 Smart 的站点记忆；需要时可在 `NodePool` 固定表现更好的节点。

`include-all-networks=true` 的 AirDrop/Xcode 兼容性警告仍存在。若关闭它，可能改变 APNs 与全网络防旁路覆盖，因此 R13.11 不擅自修改。最终仍需在真实设备的 Wi-Fi 和蜂窝网络完成验收。
