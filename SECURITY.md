# 安全策略与运行边界

R13.6 的目标是在 Surge iOS 上提供可审计的混合自动分流。日常路径使用 `url-test` 自动选优，手动 `NodePool` 保留 `Fail-Closed` 安全入口。这个边界只覆盖仓库内可审计行为，无法证明私人节点、上游 DNS、操作系统或第三方规则绝对可信。

## 私密信息

公开配置只允许保留下面的无效占位地址。

```text
https://example.invalid/REPLACE_WITH_SUB_STORE_URL
```

不要提交真实订阅、Sub-Store 地址、令牌、设备日志、节点名称或个人域名。私人副本应放在仓库之外；凭据泄露后应立即在服务端撤销和轮换。

## 混合自动与失败关闭边界

- `[Proxy]` 中的 `Fail-Closed = reject` 是 Surge 内建 `REJECT` 的别名。
- `NodePool` 保持手动 `select`，首项是 `Fail-Closed`，其他成员来自私人 `policy-path`。
- `Auto` 使用 `url-test`，从 `NodePool` 导入真实节点，并排除 `Fail-Closed`。
- 香港、台湾、日本、新加坡、美国五个地区入口使用 `url-test`，只导入名称匹配的 `NodePool` 节点。
- 六个自动组统一锁定 600 秒结果有效期、100 毫秒切换容差和首次使用前评估。
- `Proxy` 默认进入 `Auto`，第二项保留 `NodePool`。AI、TikTok 和流媒体策略继续引用经过地区限制复核的组。
- 配置不使用 Smart。Smart 会忽略嵌套组，无法按当前方式复用 `NodePool`。
- Surge 官方说明，自动组没有可用成员时可能以 `DIRECT` 替代，并显示 `SUBSTITUTE`。R13.6 对此不作严格失败关闭承诺。
- `ApplePush` 是明确的可用性例外，其后备顺序允许 `DIRECT`，用于保留 APNs 可达性。

需要严格手动边界时，把 `Proxy` 切到 `NodePool`，再选择已知可用节点或 `Fail-Closed`。`NodePool` 不会自动寻找最快节点，选中 `Fail-Closed` 后，相关连接会被主动拒绝。

## 规则供应链

- 29 份运行规则固定到完整提交 `2b8fa93901061cf0482b079203630bcd11bfe0b1`，由 jsDelivr 按不可变提交分发。
- 唯一动态资源是 SukkaW 的 `https://ruleset.skk.moe/List/non_ip/domestic.conf`，仅用于国内域名补充。
- 移动配置禁止加载 `reject.conf` 和 `reject_phishing.conf`。这些大表既不固定，也可能在 iOS 上带来内存、更新时间与误杀风险。
- 固定资源除 Ads 外启用 `extended-matching`，让域名规则能够按 SNI/Host 匹配，降低仅依赖本地 DNS 解析的遗漏；Ads 保持普通匹配以控制移动端成本。
- `Rules/r10.lock.json` 记录配置哈希、资源清单、活动条目和关键不变量。审计器会核对本地内容、固定提交 URL、在线固定副本与动态资源格式。

更新第三方规则前应固定来源提交、复核许可和差异，并同步更新对应锁文件。不要把分支名、标签或 `main` 用作运行时固定地址。

## 网络边界

- Surge 的远程访问保持关闭；本配置不开放控制端口。
- AliDNS 与 DNSPod DoH 使用固定引导地址并开启证书校验；`encrypted-dns-follow-outbound-mode=false` 用于避免域名型代理节点的启动解析环。
- 局域网流量先行放行，随后拒绝未经审阅的公网 53、853 和 8853；已审阅的大陆应用 DNS 可直连，境外应用 DNS 进入代理。
- STUN 固定进入 `Proxy`，`udp-policy-not-supported-behaviour=REJECT`，避免不支持 UDP 的节点静默直连。
- IPv4、IPv6 公网字面量在末尾进入 `Proxy`，唯一 `FINAL` 仍指向 `Final`。
- Captive Portal 和 APNs 属于可用性例外，必须与一般业务代理规则分开评估。

## 已知限制与真机验证

静态审计不能证明订阅节点在线、节点没有 DNS 泄漏、运营商没有劫持，也看不到未随仓库提供的模块改写。自动组为空时的 `DIRECT/SUBSTITUTE` 属于 Surge 已知行为。升级后至少在 Wi-Fi 和蜂窝各验证一次，检查国内 BiliBili 首页、搜索、视频与弹幕，ChatGPT 登录和对话，APNs 推送，IPv4/IPv6 出口、DNS 检测和 UDP 应用。出现异常时先停用外部模块，再查看 Surge 最近请求中的首条命中规则和最终策略。

## 报告问题

公开报告应包含版本、最小复现步骤、命中规则、策略名和已脱敏日志。不要附带订阅 URL、认证头、设备标识或完整节点信息。疑似凭据泄露应先撤销凭据，再通过仓库维护者提供的私密渠道联系。
