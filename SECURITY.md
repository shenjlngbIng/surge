# 安全策略与运行边界

R13.12 的目标是在 Surge iOS 上同时提供真实代理诊断、默认自动和空源失败关闭。私人托管配置把真实节点装入 `[Proxy]`；日常路径由带显式 `REJECT` 的 `url-test` 自动选优。关联文件缺失、地区无匹配节点或测试全部失败时，不允许以 `DIRECT/SUBSTITUTE` 替代。这个边界只覆盖仓库内可审计行为，无法证明私人节点、上游 DNS、操作系统或第三方规则绝对可信。

## 私密信息

公开主配置只允许引用固定本地文件名 `Private-Proxies.conf`，不得包含该文件、其托管 URL 或任何节点行。不要提交真实订阅、Sub-Store 地址、令牌、设备日志、节点名称或个人域名。私人文件应只保存在 Surge 的本地配置区；凭据泄露后应立即在服务端撤销和轮换。

## 自动、诊断与失败关闭边界

- 公开 `[Proxy]` 只允许 `#!include Private-Proxies.conf`。该私人托管配置必须含真实 `[Proxy]` 段；禁止本机 `Diagnostics` 回环、静态拒绝别名或公开真实节点。
- `NodePool` 保持手动 `select`，第一项为内建 `REJECT`，其余成员通过 `include-all-proxies=true` 来自关联的真实代理。
- 全局代理诊断必须显示真实 HTTP 探针结果；UDP 诊断必须显示真实成功或明确失败。两段空白表示关联文件没有生效，不能再视为正常。
- `Scripts/SubStore-Surge-Profile.js` 只有在明确传入 `surge-profile=1` 且目标为 Surge 时才包装输出。它拒绝空输出、仅 DIRECT/REJECT 的输出和额外 INI 段，防止生成假诊断或配置注入。
- `Auto`、五个地区组和四个受限服务组共十个 `url-test`，都显式列出 `REJECT`，并保持首次使用前评估、600 秒有效期和 100 ms 容差。
- 地区组只导入名称匹配的 `NodePool` 节点；ChatGPT、Claude、Gemini 与 TikTok 只递归导入日本、新加坡、台湾、美国。
- Smart 组完全禁止。真机已证明空 Smart 会被 Surge 改成 `DIRECT/SUBSTITUTE`，这与失败关闭目标冲突。
- `Proxy` 默认 `Auto`，第二项保留手动 `NodePool`，末项保留内建 `REJECT`。任何自动组都不得加入 `DIRECT`。
- `ApplePush` 是唯一明确的可用性例外，其后备顺序允许 `DIRECT`，用于保留 APNs 可达性。

需要固定真实节点时进入 `NodePool` 选择；需要立即阻断时把 `Proxy` 切到 `REJECT`。

## 规则供应链

- 29 份运行规则固定到完整提交 `2b8fa93901061cf0482b079203630bcd11bfe0b1`，由 jsDelivr 按不可变提交分发。
- 唯一动态资源是 SukkaW 的 `https://ruleset.skk.moe/List/non_ip/domestic.conf`，仅用于国内域名补充。
- 移动配置禁止加载 `reject.conf` 和 `reject_phishing.conf`。这些大表既不固定，也可能在 iOS 上带来内存、更新时间与误杀风险。
- 固定资源除 Ads 外启用 `extended-matching`，让域名规则能够按 SNI/Host 匹配，降低仅依赖本地 DNS 解析的遗漏；Ads 保持普通匹配以控制移动端成本。
- `Rules/r10.lock.json` 记录配置哈希、资源清单、活动条目和关键不变量。审计器会核对本地内容、固定提交 URL、在线固定副本与动态资源格式。

更新第三方规则前应固定来源提交、复核许可和差异，并同步更新对应锁文件。不要把分支名、标签或 `main` 用作运行时固定地址。

## 网络边界

- Surge 的远程访问保持关闭；本配置不开放控制端口。
- `allow-wifi-access=false`、`allow-hotspot-access=false` 和 `proxy-restricted-to-lan=true` 阻止把 Surge 本机代理服务暴露给其他设备或公网。
- AliDNS 与 DNSPod DoH 开启证书校验；`encrypted-dns-follow-outbound-mode=false` 用于避免域名型代理节点的启动解析环。
- AliDNS 使用官方双 IPv4/双 IPv6 静态引导；DNSPod `doh.pub` 通过 AliDNS 引导动态解析，不再冻结服务方已不建议公开使用的旧 IP。
- 局域网流量先行放行，随后拒绝未经审阅的公网 53、853 和 8853；已审阅的大陆应用 DNS 可直连，境外应用 DNS 进入代理。
- STUN 固定进入 `Proxy`，`udp-policy-not-supported-behaviour=REJECT`，避免不支持 UDP 的节点静默直连。
- IPv4、IPv6 公网字面量在末尾进入 `Proxy`，唯一 `FINAL` 仍指向 `Final`。
- Captive Portal 和 APNs 属于可用性例外，必须与一般业务代理规则分开评估。

## 已知限制与真机验证

静态审计不能证明订阅节点在线、节点没有 DNS 泄漏、服务端支持 UDP、运营商没有劫持，也看不到未随仓库提供的模块改写。`url-test` 的低延迟结果不保证每个站点体验都最佳。升级后至少在 Wi-Fi 和蜂窝各验证一次，检查国内 BiliBili、ChatGPT、APNs、IPv4/IPv6 出口、DNS 和具体真实节点的 UDP。全局代理/UDP 诊断若仍为空白，应先检查 `Private-Proxies.conf` 的文件名、内容和关联状态。

## 报告问题

公开报告应包含版本、最小复现步骤、命中规则、策略名和已脱敏日志。不要附带订阅 URL、认证头、设备标识或完整节点信息。疑似凭据泄露应先撤销凭据，再通过仓库维护者提供的私密渠道联系。
