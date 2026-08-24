# 更新日志

## 2026-08-25 R12.16 服务分流冲突修正

### 修正

- 将 Bilibili 国内版和国际版拆为两个规则文件，不新增策略组。国内 API、页面、图片和视频 CDN 进入 `DIRECT`，国际版进入现有 `Streaming`，并通过规则顺序优先接管 `apiintl.biliapi.net`。
- 从 `ProxyMedia.list` 删除 `apm-misaka.biliapi.net` 与 `cache.video.iqiyi.com`。前者回到 Bilibili 国内直连，后者回到爱奇艺国内直连，消除泛媒体表抢先匹配。
- 将 `PROTOCOL,STUN,Proxy` 移到 `GEOIP,CN,DIRECT` 前，避免国内 IP 的 STUN 被 GEOIP 提前直连。
- 将 29 个运行时规则地址从浮动的 `@main` 固定到发布标签 `r12.16-20260825`。安装工作流在提交通过后创建该标签，设备刷新规则时获得同一份发布内容。
- 将 `Game.list` 移到 OneDrive/Microsoft 之前，使 40 组 Xbox、Minecraft、Bethesda、Forza 等重叠条目真正进入 `Games`，而不是提前落入 `Microsoft`。
- 从 TikTok 删除会覆盖国内字节服务的 `snssdk.com`；从 Bahamut、Disney、HBO、Microsoft、Game 删除共享 CA、CDN、遥测和第三方 SaaS 后缀，减少无关流量被专用服务组截获。
- 将 HBO 默认策略从美国改为 `Proxy`，避免 HBO Asia、Now 等区域服务默认被强制送往美国。
- 删除 `Direct.list` 中 14 条 Google 直连例外，使 Google 更新、推送和基础服务统一进入 `Google` 策略组。
- 删除 Netflix 上游中的 1,119 条 IPv4/IPv6 宽泛云网段，改用经审核的 `IP-ASN,2906,no-resolve`，避免 AWS 共用地址误命中 Netflix。
- 扩展固定上游更新器，支持按服务禁用规则类型和加入审核后的本地规则；增加 Bilibili、Netflix 及共享域名排除的回退审计。
- 基线保持 31 个策略组，活动规则调整为 86 条，远程源调整为 29 个。审计扩展为 56 项故障注入和 17 项 ZIP 白名单回归。

### 保持不变

- `NodePool → Smart` 架构、Telegram 强制代理、`ApplePush = fallback, Proxy, DIRECT`、AliDNS 加密 DNS、CGNAT/局域网边界和失败关闭策略均未改变。

## 2026-08-24 R12.15 网络切换测速风暴修正

### 修正

- 将订阅导入从自动策略组中拆出，新增隐藏的被动 `NodePool = select`，它只负责按小时更新 `policy-path`，不承担路由和自动测速。
- 将 `AllServer` 从包含全订阅的 `fallback` 改为 `smart`，并通过 `include-other-group=NodePool` 复用节点，避免 Wi-Fi、蜂窝数据切换后立即对整份订阅进行集中 HEAD 探测。
- 将香港、台湾、日本、新加坡和美国五个地区组从 `url-test` 改为 `smart`，直接筛选 `NodePool`，不再通过 `AllServer` 级联触发重复评估。
- 在 `AllServer` 和五个地区组中显式保留 `Fail-Closed`。即使订阅为空、下载失败或地区筛选结果为空，也不会因 Smart 组的空组替代策略而静默转为 `DIRECT`。
- 保留 Telegram 强制代理、`ApplePush = fallback, Proxy, DIRECT`、AliDNS 加密 DNS、53/853/8853 端口控制、APNs 捕获、CGNAT 与局域网边界以及 85 条活动规则，不借测速修复改变流量归属。
- 将锁文件升级为 schema 8，记录 `NodePool → Smart` 策略架构；配置审计器扩展到 31 个策略组和 49 项故障注入测试。
- 同步更新 ZIP 白名单、R12.15 发布包名、GitHub Actions、迁移说明、贡献规范、发布清单、两份一致的 SHA-256 清单和完整 README。

### 原因

R12.14 的 `AllServer = fallback` 会在网络切换后丢弃旧测试结果，并在首次使用时对所有订阅节点重新测试。截图中的 310 个请求与约 155 个节点各产生两次探测高度吻合。单纯增加 `interval`、隐藏通知或放宽 `timeout` 都不能阻止网络切换后的结果失效，因此 R12.15 改为被动导入与 Smart 决策分层。

## 2026-08-24 R12.14 稳定性与推送保全修正

### 修正

- 将运行仓库从通用仓库 `shenjlngbIng/-` 迁移到 Surge 专用仓库 `shenjlngbIng/surge`，同步更新主配置、28 个 jsDelivr 规则地址、审计器、测试、锁文件和文档链接。
- 将重复的 `dns.alidns.com` Host 项合并为单行多地址映射，避免首条匹配遮蔽后续 IPv4 和 IPv6 引导地址。
- 将 `AllServer` 的探测结果有效期从 60 秒调整为 600 秒，并把成员延迟阈值从无实际约束的 300 秒调整为 5 秒，降低全节点频繁探测带来的请求与内存压力。
- 为刻意失败的 `Fail-Closed` 哨兵加入 `no-error-alert=true`，保留失败关闭语义并停止无意义的 POSIX 61 弹窗。
- 在所有远程规则之前增加 `DOMAIN-SUFFIX,ls.apple.com,DIRECT`，避免 Apple 配置查询进入代理选择或失败回落环路。
- 将 `100.64.0.0/10` 同时加入 `skip-proxy` 与本地直连规则，补全运营商 CGNAT 边界。
- 关闭与普通蜂窝上网和 APNs 无关的 `include-cellular-services`，减少 IMS、VoLTE、Wi-Fi Calling、MMS 等运营商专用流量的兼容风险。
- 删除 iOS 不使用的 `read-etc-hosts`、未被引用的 `Domestic` 策略组，以及在 `encrypted-dns-follow-outbound-mode=false` 下不参与内部 DNS 链路的 `EncryptedDNS` 组和 DOH/DOH3/DOQ 规则。
- `ApplePush` 保持 `Proxy → DIRECT` 回落顺序，探测阈值改为 5 秒；Telegram 应用数据仍强制代理，APNs 后台通知链路保持可回落。
- 更新锁文件 schema 7、审计器、30 项故障注入测试、ZIP 白名单、工作流、迁移说明、发布清单和 SHA-256 校验。
- 将安装与持续审计合并为单一 install.yml，避免安装提交修改工作流文件而被 GitHub 权限拒绝；同步升级到 actions/checkout v7 和 actions/setup-python v6。

## 2026-08-09 R12.13 精确国内外域名集

### 修正

- 取消运行时上游 Direct、China、Global 及其巨型域名集合，避免宽泛直连、关键词和重复兜底继续影响结果。
- 将旧的 `ChinaDomain.list` 补充表替换为 `China.list` 与 `Global.list` 两个外置 DOMAIN-SET，文件名与其他规则集保持一致。
- 将广告补充规则简化为 `Ads.list`，保持 Rules 目录命名一致。
- 国内集仅保留 306 条明确归属的大陆服务域名，国外集仅保留 116 条明确归属的境外服务域名。
- 禁止公共后缀、域名关键词、共享云/CDN、重复后缀及国内外交叉冲突。
- 未收录流量继续由 `GEOIP,CN,DIRECT` 与 `FINAL,Proxy` 兜底，不以内嵌规则替代外部规则集。
- 新增精确域名集审计并接入 GitHub Actions、锁文件、发布清单和完整性校验。

## 2026-08-09 R12.12 国内外总分流修正

### 修正

- 将仓库维护规则从 GitHub Raw 切换到 jsDelivr，降低中国网络环境下规则集首次加载失败的概率。
- 按 blackmatrix7/ios_rule_script 固定提交 `ccc2d6b711007324bacb55cdfbbf7e36ad48145a` 增加 Direct、China、China_Domain、Global 和 Global_Domain 五个上游总规则。
- 将 WeChat、Direct、ChinaDomain 和 GEOIP,CN 的策略统一改为 `DIRECT`，避免国内流量因手动策略组选择被误送进代理。
- 从本地 ChinaDomain 补充表中移除与上游 Global 冲突的 Battle.net、Blizzard、Futu5 和 Futunn 条目，避免国内表提前截获国外流量。
- 保留 YouTube、Google、Microsoft 等专用规则在 China/Global 总规则之前，避免专用服务被国内总规则或国外兜底覆盖。
- 删除宽泛的 QUIC、UDP 规则，仅保留 STUN 代理分流，避免不支持 UDP 的节点直接阻断 YouTube 回落到 TCP。
- 移除香港、台湾、日本、新加坡和美国地区组对“专用/解锁”节点的误排除，保留地区关键词筛选。

## 2026-08-09 R12.11 参考来源集中说明

### 文档

- 将配置参考、Sub-Store 资料、实际规则上游和本仓库维护范围集中放到 README 文末。
- 补充 Sub-Store 项目、Surge 模块和输出服务的公开地址。

## 2026-08-09 R12.10 README 用词修正

### 文档

- 删除拟人化章节名，改为“关键取舍”和“具体做法”。
- 将流程章节改为连接处理流程，保留原有图示和导航。

## 2026-08-09 R12.9 README 结构与识别度调整

### 文档

- 增加配置副标题、阅读导航和四项设计取向说明。
- 增加配置处理流程图，说明 DNS 接管、规则分流、失败关闭和最终策略之间的关系。
- 保留部署、来源、审计和故障排查内容不变。

## 2026-08-09 R12.8 参考来源说明补充

### 文档

- README 增加 Rabbit-Spec、As-Lucky、Coldvvater 和 Thoseyearsbrian Aegis 的公开来源链接。
- 明确区分设计参考、运行时规则上游和本仓库自己的整合内容。
- NOTICE.md 同步补充参考项目、许可证边界和公开包不包含的私有材料。

## 2026-08-09 R12.7 README 操作说明补全

### 文档

- 明确公开主配置、私有 policy-path、Sub-Store Surge 输出地址和可选模块地址的区别。
- 补充仓库根目录上传、覆盖、保留、漏传文件和旧版遗留目录处理方法。
- 补充 404、500、请求超时、节点全红、DNS 诊断和旧 Core/Simple 外部资源排查。
- 补充 Wi-Fi、蜂窝数据、APNs、局域网和 allow-wifi-access 的实际区别。
- 补充发布清单、GitHub Actions 和 README 修改后的校验和更新要求。

## 2026-08-09 R12.6 DNS 参考配置融合

### 修正

- 参考 Aegis，将加密 DNS 调整为阿里 DNS 的 HTTPS 与 TLS 双通道，并增加 IPv4/IPv6 引导映射。
- 将 `dns-server` 引导地址改为国内可达的阿里 DNS 地址，避免 1.1.1.1/9.9.9.9 在移动网络诊断中超时。
- 开启 `include-cellular-services = true`，减少蜂窝服务流量绕过 Surge DNS 接管的可能性。

### 取舍

- 保留 `include-local-networks = false`，避免为了 DNS 接管破坏 AirDrop、Bonjour 和局域网设备发现。
- Rabbit-Developer、Rabbit-EN、Lucky 和 Coldvvater 配置中的明文 DNS、`system` DNS 或注释状态加密 DNS 未直接照搬；只吸收其中经验证的规则集和兼容性结构。

## 2026-08-09 R12.5 远程规则集版

### 修正

- 将 27 个已审计的 `Rules/*.list` 改为仓库自有 Raw URL 的运行时 `RULE-SET`，保留原有策略映射和 `ChinaDomain` 顺序。
- 将 APNs 规则改为远程 `RULE-SET`，保留 `ApplePush` 代理优先、直连回落设计。
- `Final` 策略组加入显式 `REJECT` 选择，远程规则集或节点异常时不静默直连。
- 将审计器、规则锁、回归测试、README、发布清单和 SHA-256 校验同步到 schema 5 的 `remote-ruleset` 模式。

### 边界

- 只吸收 Aegis 和主流配置的模块化远程规则、DNS 接管、UDP 失败关闭和显式拒绝思路。
- 不直接启用未经独立复核的 `Scam_Block`、`Quarantine_Block` 或其他外部威胁情报列表，避免高误报进入主规则链路。
- 不加入 `Sub-Store Core`、`Sub-Store Simple`、Vendor 文件、真实订阅、节点、Token、密码或证书私钥。

## 2026-08-09 R12.4 DNS 隐私边界修正

### 修正

- 撤回 `system, 223.5.5.5, 119.29.29.29`，避免把系统或运营商 DNS 纳入公开隐私配置。
- 普通 DNS 恢复为 `1.1.1.1, 9.9.9.9`，仅用于加密 DNS 主机的引导与连通性用途。
- 保留阿里 DNS 与 `doh.pub` 的 HTTPS 加密 DNS，以及两个 DoH 主机的固定映射。
- 同步审计器、锁文件、README、发布清单和 SHA-256 校验值。

### 边界

- 网络诊断中 1.1.1.1/9.9.9.9 超时不应通过加入 `system` 或运营商 DNS 来掩盖。
- 不写入真实订阅地址、节点、证书私钥或重复 Sub-Store 模块。

## 2026-08-09 R12.3 国内 DNS 可达性修正

### 修正

- 将普通 DNS 恢复为 `system, 223.5.5.5, 119.29.29.29`。
- 将加密 DNS 恢复为阿里 DNS 与 `doh.pub`，并保留 `encrypted-dns-follow-outbound-mode = false`。
- 增加两个加密 DNS 主机的固定引导映射，并将对应主机规则设为 `DIRECT`。
- 同步审计器、锁文件、README、发布清单和 SHA-256 校验值。

### 边界

- 不修改或写入真实 Sub-Store 订阅地址；公开配置仍使用占位符。
- 不加入 `Sub-Store Core`、`Sub-Store Simple`、Vendor 文件、节点或证书私钥。

## 2026-08-09 R12.2 加密 DNS 循环修正

### 修正

- 将 `encrypted-dns-follow-outbound-mode` 从 `true` 改为 `false`。
- 加密 DNS 固定直连并绕过代理规则，避免节点服务器域名被同一代理策略再次解析而形成循环。
- 保留 HTTPS 加密 DNS、有效协议规则快照、节点失败关闭和其他分流逻辑不变。

### 边界

- 不在公开配置中写入节点 IP、真实订阅链接或其他私有信息。
- 不通过 `DOMAIN,gd.bjnet2.com,DIRECT` 等规则掩盖代理服务器自身的 DNS 引导问题。

## 2026-08-09 R12.1 代理回落修正版

### 修正

- `AllServer` 恢复为 `fallback`，增加 60 秒检测、300 秒节点超时和启动前评估。
- 默认 `Proxy` 优先使用 `AllServer`，避免首次载入时直接落到空的地区组。
- 代理健康检测超时恢复为 8 秒，降低移动网络下的误判。
- 移除主配置中的 `sub.store` 本地地址映射，由独立 Sub-Store 模块处理订阅转换。
- 保留现有 ChinaDomain 顺序、规则快照、APNs、加密 DNS 和失败关闭设计。

### 边界

- 不加入 `Sub-Store Core` 或 `Sub-Store Simple` 内嵌脚本。
- 不写入真实订阅链接、节点、密码、Token 或 MITM 证书。
- 不增加运行时远程 `RULE-SET`，不增加 P2P 端口直连。

## 2026-08-08 R12

### 修正

- APNs 改为独立 `ApplePush` Fallback，代理优先、直连故障回落。
- 启用 `include-all-networks` 与 `include-apns`，覆盖移动数据下的系统推送。
- 早期版本曾将 APNs 快照嵌入 `Surge.conf`；当前远程规则模式已移除这种做法，APNs 通过独立规则文件引用。
- 加密 DNS 改用 Cloudflare 与 Quad9 IP 端点，按 `EncryptedDNS` 代理优先、加密直连回落。
- 保持 Telegram 强制代理及既有国内外分流，不引入全量 Apple 代理规则。

### 校验

- 审计器、锁文件、回归测试和工作流统一升级为 R12。
- 增加发布文件清单，发布包按清单核对文件数量与 SHA-256。

## 2026-08-01 R11 LTS

### 新增

- 新增仓库级 `LICENSE`。
- 新增 `tools/generate_checksums.py`，统一生成发布文件校验和。
- GitHub Actions 增加 Python 3.12 与 3.13 双版本审计。
- README 增加完整目录、工具、工作流、FAQ 和故障排查说明。

### 优化

- 配置注释统一为简短文字标题，不使用装饰性横线。
- 统一审计脚本、锁文件、文档和工作流的 R11 LTS 版本标识。
- `audit_rules.py` 支持验证仓库规则目录和 ZIP 暂存规则目录。
- 完善 `.gitignore`，排除缓存、临时文件、压缩包和本地敏感配置。
- 工作流增加并发控制、超时限制、编译检查和 SHA-256 校验。

### 保持

- Telegram 强制代理。
- 系统 APNs 不由 Surge VIF 接管。
- APNs 精确直连兜底。
- `FINAL,Final,dns-failed` 失败关闭。
- 5546 条有效规则及既有规则顺序。

## 2026-08-01 R10.6

- 修复 Telegram 后台通知与 APNs 路由冲突。
- 补充 Telegram 核心网段。
- 清理旧校验和记录。

## 2026-07-31 R10.5

- 启用 AliDNS 与 DNSPod DoH。
- 增加 DNS 引导映射和防绕过规则。
- 同步配置审计、规则锁和回归测试。
