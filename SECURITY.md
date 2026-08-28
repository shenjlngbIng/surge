# 安全说明

## 报告问题

请不要在公开问题中粘贴真实订阅地址、访问令牌、设备标识、完整日志或包含私有信息的配置。报告配置漏洞时，先把敏感值换成无效占位符，并提供最小复现条件、受影响版本和预期行为。

如果问题会导致订阅泄露、规则绕过、意外直连、供应链内容替换、ZIP 路径逃逸或安装工作流执行未审阅内容，请按高优先级处理。在修复和发布前避免公开可直接利用的细节。

## 公开配置边界

R13.4 的 `NodePool.policy-path` 必须保持下面的无效地址。

```text
https://example.invalid/REPLACE_WITH_SUB_STORE_URL
```

真实地址只能保存在用户自己的设备上。配置用 `Fail-Closed` 防止订阅为空时静默直连。若使用 `sub.store` 合成地址，必须由对应 Surge 模块接管。未接管时 `[Host]` 会把该主机指向本机并主动失败。

## 规则供应链

原有 30 个运行资源只能来自本仓库完整提交 `d1d714d575d5494ef1a7613238f4f301e1b293df`。`main`、可移动标签或其他提交都属于拒绝条件。新增运行资源只允许以下三个经过审阅的精确动态 URL，不能替换为镜像、重定向地址或猜测路径。

- `https://ruleset.skk.moe/List/domainset/reject_phishing.conf`
- `https://ruleset.skk.moe/List/domainset/reject.conf`
- `https://ruleset.skk.moe/List/non_ip/domestic.conf`

Pegasus 的 1,438 个域名通过本仓库固定 `DOMAIN-SET` 加载，来源与本地哈希由 `Rules/resources.lock.json` 固定。152 条固定广告规则通过仓库 `RULE-SET` 加载。19 份服务规则由 `Rules/upstreams.lock.json` 管理，其余仓库维护列表由 `Rules/maintained_sources.lock.json` 披露。三份动态资源的发布观察值由 `Rules/r10.lock.json` 记录，但预期会变化，因此在线审计验证 HTTP、UTF-8、规则格式、重复行和大小边界，不把发布时 SHA-256 当作永久固定值。主配置不得保存这些资源的逐条内容。

发现下面任一情况时应停止发布。

- 30 个仓库 URL 没有固定到指定完整提交。
- 动态 URL、类型、策略、更新间隔或先后顺序偏离审阅清单。
- 锁文件中的 Git Blob、SHA-256、条目数或来源身份不一致。
- Pegasus、固定 Ads 或本地规则内容发生未记录变化。
- 动态源在线检查出现 HTTP、编码、格式、重复或大小异常。
- 发布目录包含白名单外文件、链接或特殊文件。

## 网络边界

Wi-Fi 访问、热点访问和 Web 控制面板默认关闭。局域网和 16 个经审阅的大陆应用 DNS 主机先处理，其余公网 DNS 端口 53、853 和 8853 随后拒绝。大陆主机进入隐藏的 `Domestic`，13 个境外 HTTPS DNS 主机进入 `Proxy`；Surge 自身 DoH 使用固定引导地址并保持证书校验。

当前两个加密 DNS 会并发查询，而且 `encrypted-dns-follow-outbound-mode=false` 使 Surge 自身 DoH 直连。这避免域名型代理节点形成启动解析环，但不是全局匿名 DNS 方案；明确的本地解析仍可能被 AliDNS 与 DNSPod 看到。不要把这一设计描述为零泄漏或单一信任方。

末端 `GEOIP,CN,Domestic,no-resolve` 不为尚未命中的域名触发本地解析；这些域名落入默认 `Final/Proxy`，由代理侧解析。其后的公网 IPv4 与 IPv6 字面量在 `FINAL` 前统一走 `Proxy`。`Proxy` 默认选择 `AllServer`，`AllServer` 和五个地区组使用 Surge Smart；`NodePool` 仍提供可见手动选择和 `Fail-Closed`。`UDP`、`Security`、`AdBlock` 与 `Domestic` 只在界面隐藏，定义、默认值和规则引用保留；需要人工切换时先在私人副本中临时改为 `hidden=0`。用户仍需在真机上检查节点的 UDP、APNs、DNS 和双栈能力。

Surge 可能在升级时按策略组名称保留旧选择。隐藏组之前应明确核对 `AdBlock=REJECT`、`Security=REJECT`、`UDP=Proxy` 与 `Domestic=DIRECT`，避免旧的 `DIRECT` 或调试选择在界面隐藏后继续生效。

历史 Pegasus IOC 和动态钓鱼列表不能替代 iOS 更新、Lockdown Mode、账户保护或专业取证。报告中不要把 IOC 命中直接当作感染结论。

## 发布安全

打包器使用 66 文件严格白名单，拒绝未知路径、符号链接、特殊文件、BOM、CRLF、NUL 和缺失结尾换行。候选 ZIP 导入器还会检查路径穿越、大小上限、加密条目、CRC、大小写碰撞和 Unicode 归一化碰撞。

GitHub Actions 手动安装要求包外取得的整包 SHA-256。工作流在复制文件前验证 ZIP、双份文件哈希、运行锁、来源锁、配置审计、规则审计、动态源在线格式和故障注入。快照标签还会解析到固定提交，避免标签被移动后继续安装。
