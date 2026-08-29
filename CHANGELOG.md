# 更新日志

## 2026-08-29 R13.4 全量软件分流复核

- 移除 `BiliBiliIntl.list`、运行引用与来源锁条目；七个历史国际域名只以前置通用 `Proxy` 护栏避免误入国内父后缀或旧 `ProxyMedia` 快照，不再进入 `Streaming`。
- 将 `httpdns.bilivideo.com` 精确放到固定与动态广告规则之前，解决国内 BiliBili CDN 选择因广告表误杀而等待回退的问题；其他 BiliBili 遥测与广告重叠项仍拦截。
- `ChatGPT`、`Claude`、`Gemini` 与 `TikTok` 默认日本，新加坡、台湾、美国为受支持地区后备，香港不再作为候选；`Bahamut` 默认台湾、香港后备。
- 其余 18 份固定服务规则按现有过滤逻辑与 2026-08-28 上游最新提交复核，活动规则新增与删除均为 0。
- 当前基线为 34 个策略组、137 条活动规则、29 个固定资源、3 个动态资源和 29 份本地规则文件；故障注入扩展为 125 项。

## 2026-08-29 R13.4 BiliBili 国内版直连热修复

- 将固定 `BiliBili.list` 的策略从隐藏的 `Domestic` 改为内建 `DIRECT`，避免 Surge 按同名策略组沿用旧的 `Proxy` 选择后，把国内 API、图片和视频 CDN 送往海外节点。
- 保持 `BiliBiliIntl.list → Streaming` 位于国内规则之前；`apiintl.biliapi.net`、`bilibili.tv`、`biliintl.com` 和国际版 CDN 的分流不变，不会被国内直连覆盖。
- 没有增加宽泛 `DOMAIN-KEYWORD`、进程名或 User-Agent 规则，也没有改变 DNS、QUIC、节点、订阅、规则文件内容、远程 URL、策略组数量和活动规则数量。
- 运行锁新增“国内 BiliBili 绕过隐藏策略选择”不变量，配置故障注入增至 117 项；README、迁移说明、审计报告、清单和双份哈希同步更新。

## 2026-08-28 R13.4 Strict DNS 严格解析边界与界面精简

- 以 R13.3 为基线保留全部 34 个策略组、130 个规则匹配条件、33 个远程运行资源、30 份本地规则文件和唯一订阅入口，没有删除原功能。
- 将末端 `GEOIP,CN,Domestic` 恢复为 `GEOIP,CN,Domestic,no-resolve`。未命中域名不再为中国 GeoIP 判定强制调用本地 AliDNS/DNSPod DoH，而是落入默认 `Final/Proxy`，由代理侧解析；已解析的中国 IP 仍可进入 `Domestic`。
- 保留 R13.3 的 16 个大陆应用 DNS 主机优化，它们继续位于通用 53、853、8853 端口拒绝之前并进入 `Domestic`，避免已知国内 DoH/DoT 无条件绕海外节点。
- 将 `AdBlock`、`Security`、`UDP` 和 `Domestic` 改为 `hidden=1`。四个组的类型、成员、默认选择和全部规则引用保持不变，需要排错时可在私人副本中临时取消隐藏。
- 没有给检测网站增加新的特例，也没有把 `encrypted-dns-follow-outbound-mode` 改为 `true`；保留域名型代理节点启动时的解析防环边界。
- 明确记录取舍：未知且未被国内域名规则覆盖的中国服务可能改走代理；应根据最近请求补充经过审阅的精确域名，不应去掉全局 `no-resolve` 来换取宽泛直连。
- 运行锁升级为 schema 18，记录隐藏辅助组、严格 CN GeoIP、未命中域名 `Final/Proxy` 兜底和代理侧解析不变量。
- 配置故障注入增至 116 项，新增 `Domestic` 可见性退化检查；ZIP 安全回归增至 28 项，README、迁移、安全、贡献、审计、工作流、清单、双份哈希和确定性打包器同步更新。
- 完整包更新为 `Surge-R13.4-Complete-No-Embedded-20260828.zip`。

## 2026-08-28 R13.3 Domestic Performance 国内应用性能修正

- 以 R13.2 为基线保留全部 34 个策略组、130 个规则匹配条件、33 个远程运行资源、30 份本地规则文件和唯一订阅入口，没有删除原功能。
- 将 16 个已审阅的大陆应用 DNS 主机从 `Proxy` 调整为可见 `Domestic`，并整体移动到 53、853、8853 通用端口拒绝之前。国内应用自带的大陆 DoH/DoT 默认直连，受限网络仍可一键切到 `Proxy`。
- Google DNS、Cloudflare、Quad9、NextDNS、AdGuard 和 OpenDNS 等 13 个境外应用 DNS 主机继续进入 `Proxy`，且仍位于通用端口拒绝之后；未经审阅的公网 DoT 不会绕过 853 拒绝。
- 将末端 `GEOIP,CN,Domestic,no-resolve` 改为 `GEOIP,CN,Domestic`，让未被精确域名表收录的域名能够按解析后的中国 IP 进入 `Domestic`。非中国 IP 继续由 IPv4/IPv6 公网兜底送入 `Proxy`。
- 保留双 DoH、固定 Host 引导、证书校验、`encrypted-dns-follow-outbound-mode=false`、`hijack-dns=*:53`、Smart、UDP、APNs、动态规则和固定快照。
- 运行锁升级为 schema 17，记录大陆/境外应用 DNS 清单、策略和可解析 CN GeoIP 不变量。
- 配置审计新增大陆 DNS 完整性、连续顺序、策略回退、境外 DNS 顺序和 CN GeoIP 解析行为断言；故障注入增至 115 项，ZIP 安全回归增至 27 项。
- 完整包更新为 `Surge-R13.3-Complete-No-Embedded-20260828.zip`，README、迁移、安全、贡献、审计、工作流、清单、双份哈希和确定性打包器同步更新。

## 2026-08-28 R13.2 Enhanced 保留式增强与完整包同步

- 以 R13.1 为基线升级，原 33 个策略组、125 个规则匹配条件、30 个固定远程 URL 和 30 份本地规则快照全部保留，没有删除原服务分类。
- 新增可见的 `Domestic = select, DIRECT, Proxy`，把 WeChat、Direct、BiliBili、China 和 12 个国内共享云后缀统一交给一个可切换策略。16 条原规则只改变策略去向，匹配对象与原 URL 不变。
- `Proxy` 首选改为 `AllServer`。`AllServer` 与香港、台湾、日本、新加坡、美国五个地区组从 `url-test` 改为 `smart`，保留 `Fail-Closed`、`evaluate-before-use=true` 和 `include-other-group=NodePool`，删除对 Smart 无效的 `interval` 与 `tolerance`。
- `UDP` 改为可见并默认 `Proxy`，随后保留 `NodePool`、`REJECT` 与 `DIRECT`。`AdBlock` 和 `Security` 也改为可见，便于误报定位；`ApplePush` 继续隐藏。
- 新增 `DOMAIN,captive.apple.com,DIRECT`，改善酒店、机场、商场等公共 Wi-Fi 门户登录。
- 新增 SukkaW 动态钓鱼 DOMAIN-SET、基础广告 DOMAIN-SET 和国内 RULE-SET，全部使用 86,400 秒更新间隔。动态内容不写入 `Surge.conf`，也不复制进发布包。
- 保留固定 `Pegasus.list` 和 `Ads.list`，动态钓鱼位于 Pegasus 之前，动态基础广告位于固定 Ads 之后。
- 新增 `GEOIP,CN,Domestic,no-resolve`，放在 Global 后和公网 IP 兜底前，不为尚未解析的域名强制触发本地 DNS。
- `loglevel` 从 `warning` 调整为 `notify`，用于保留日常排障所需信息。
- 运行锁升级为 schema 16，分别记录 30 个不可变仓库资源、3 个动态运行资源、30 个本地规则文件、34 个策略组、130 条规则和零内嵌规则内容。
- 配置故障注入扩展为 110 项，ZIP 安全回归扩展为 26 项；完整发布目录继续保持 66 个文件。
- README 按完整手册规格更新，覆盖保留边界、订阅、Smart、Domestic、DNS 真实限制、UDP、APNs、动态供应链、规则顺序、维护命令、常见故障、真机验收与发布检查。
- 完整包更新为 `Surge-R13.2-Complete-No-Embedded-20260828.zip`，工作流、迁移、审计、清单、双份哈希和确定性打包器同步更新。

## 2026-08-27 R13.1 稳定节点与远程规则修正

- 按完整使用手册重写 README，补齐订阅与 Sub-Store 接入、节点选择、策略组、DNS、UDP、APNs、规则顺序、30 份规则库存、来源维护、上传发布、故障排查、真机验收和发布前检查，并逐项改写为 R13.1 当前行为。
- 把 `NodePool` 设为可见的手动稳定节点入口，并加入 `Fail-Closed`。`Proxy` 与 `UDP` 都默认使用 `NodePool`，订阅为空时不会静默直连。
- 保持 `ApplePush`、`AdBlock`、`Security` 和 `UDP` 隐藏，减少日常误触，同时保留各组的排错与紧急关闭成员。
- 用显式 `url-test` 替换 Smart 地区组与隐藏 `PrivacyAuto`。`AllServer` 和五个地区组只导入 `NodePool`，间隔 1,800 秒、容差 100 毫秒，并在首次使用前评估。
- 加密 DNS 改为 AliDNS DoH 与 DNSPod DoH，新增 `doh.pub` 引导地址，继续开启证书校验并保持 `encrypted-dns-follow-outbound-mode=false`。
- UDP 探针改为 `apple.com@9.9.9.9`。STUN 提前到公网 DNS 端口、公共域名和公网 IP 规则之前。
- 在局域网规则后拦截公网 53、853 和 8853 端口。应用常见 DoH 域名继续走 `Proxy`。
- 把宽泛 `DOMAIN-SUFFIX,ls.apple.com,DIRECT` 收紧为 `DOMAIN,configuration.ls.apple.com,DIRECT`，让其余 Apple 国内服务继续受 Apple 策略控制。
- 出口检测域名统一跟随 `Proxy`，使检测结果对应当前默认节点。
- 保留 `Rules/Pegasus.list` 的固定远程 `DOMAIN-SET`，1,438 个域名不写入主配置。
- 保留 `Rules/Ads.list` 的固定远程 `RULE-SET`，152 条活动规则不写入主配置。
- 将 12 个共享云和用户托管后缀在 China 集合前明确交给 `Proxy`，降低宽泛直连带来的租户内容旁路。
- 继续用 `0.0.0.0/0` 与 `::/0` 代理公网 IP 字面量，并让两条规则紧贴唯一的末尾 `FINAL`。
- 运行锁升级为 schema 15，记录 30 个固定远程资源、30 个本地规则文件、零内嵌规则内容、DNS、UDP、节点架构与双栈兜底。
- 配置审计更新为 33 个策略组和 125 条活动规则，故障注入保持 99 项。ZIP 导入安全回归扩展为 25 项。
- 完整发布包更新为 `Surge-R13.1-Complete-No-Embedded-20260827.zip`。打包器、安装工作流、候选 ZIP 路径、清单、双份哈希和全部说明文档同步更新。

## 2026-08-26 R12.17 DNS 与出口完整性补丁

- 新增隐藏的 `PrivacyAuto` 自动单节点组，通过 `url-test` 从唯一的 `NodePool` 选择一个统一代理。它使用 `interval=600`、`tolerance=100`、`evaluate-before-use=true` 和 `no-alert=1`，首次请求先完成评估，后台更新且不在策略页显示；显式 `Fail-Closed` 保证无可用节点时不会回落直连。
- PrivacyAuto 不使用 Smart，避免其逐站点记忆给不同 DNS/IP 探测端点分配不同节点。新名称同时清除旧 Privacy 组可能遗留的临时手动覆盖。Net.Coffee、IPPure、BrowserLeaks、Surfshark DNS、Fastly resolver、icanhazip、ipinfo、ipapi 与 IPIP 相关域名，以及 Net.Coffee 的 `1.1.1.1/32` 出口探针，在所有业务/国内规则前固定进入该组。
- 27 个运行时 `RULE-SET` 统一加入 `no-resolve`，阻止尚未解析的代理域名因为规则集内的 IP 子规则触发本地 AliDNS 查询。
- 将应用生成的 `dns.alidns.com` 与 `doh.pub` 连接从 DIRECT 改为 Proxy；Surge 自己的 AliDNS DoH/DoT 仍以 `encrypted-dns-follow-outbound-mode=false` 在规则外直连，避免域名型节点形成解析循环。
- 显式固定 `encrypted-dns-skip-cert-verification=false`，并把证书校验加入配置审计与运行锁。
- 删除公网 IP 字面量的 `GEOIP,CN,DIRECT,no-resolve` 兜底，改为 `0.0.0.0/0` 与 `::/0` 在本地/服务规则之后统一进入 Proxy。IPv6 保持 `ipv6-vif=auto`，不会用禁用 VIF 的方式制造原始 IPv6 绕过。
- 30 个运行规则 URL 从便于人工识别的标签改为完整提交 `d1d714d575d5494ef1a7613238f4f301e1b293df`；安装工作流不再尝试把既有 `r12.17-20260825` 标签移动到配置补丁提交，只核对标签仍指向原快照。
- 运行配置锁升级为 schema 13，加入 PrivacyAuto 隐藏自动单节点、加密 DNS 证书校验、提交 SHA 规则快照、检测域名、运行规则无本地解析及 IPv4/IPv6 字面量失败关闭不变量。
- 配置基线保持 34 个策略组和 109 条活动规则；故障注入由 78 项扩展到 97 项，并同步审计器、迁移、README、报告、清单和校验和。
- 严格发布清单新增无 BOM UTF-8、LF、无 NUL 与末尾换行校验，回归测试从 10 项扩展到 15 项。
- 完整包更新为 `Surge-R12.17-Privacy-Auto-20260826.zip`，安装工作流、确定性打包器和临时归档白名单同步更新。
- 明确节点侧边界：PrivacyAuto 自动选中的具体节点仍出现与出口不一致的中国移动/阿里解析器，属于远端节点 DNS，只能停用该节点或由提供方修复，客户端配置不能替远端代理决定递归解析器。
- 记录真机根因：未审阅模块可覆盖 General 并把规则插在主配置顶部；本次 `dandanvip.sgmodule` 的 RULE-SET 曾在 PrivacyAuto 前触发 DNS lookup，卸载模块后 Net.Coffee 与 IPPure 均只显示所选日本节点的 Cloudflare 解析器。

## 2026-08-25 R12.17 运行资源自有化与全仓审计同步

### 策略界面精简补丁

- 核对并保留 `ApplePush=Proxy`、`AdBlock=REJECT`、`Security=REJECT`、`UDP=Proxy` 的既有最优默认路径，不改变成员顺序、规则归属或失败回落。
- 将 `ApplePush`、`AdBlock`、`Security`、`UDP` 改为 `hidden=1`，只从 Surge iOS 策略选择页面隐藏功能型卡片；规则仍正常引用这些组。
- 四组的 DIRECT、REJECT-DROP 与 REJECT 排错成员继续保留。需要临时切换时，先在私有副本中把对应组改为 `hidden=0`。
- 运行配置锁升级为 schema 10，新增隐藏功能组不变量；配置故障注入测试由 74 项增加到 78 项，并同步 README、迁移、贡献、审计、清单和校验和。

### 发布终审修复

- 新增共享的严格发布清单 `tools/release_inventory.py` 和 10 项回归测试。打包、发布清单与校验和不再递归接受任意文件；未知文件、`.env`、日志、符号链接、特殊文件和符号链接输出会直接失败。
- 将 8 个服务文件中的 278 条历史本地规则全部显式写入 `Rules/upstreams.lock.json`，并把锁升级为 schema 2。更新器改为仅从固定上游、过滤、排除与 `add` 输入生成，19 份快照从零重建 changed=0；所有下载和渲染完成后才替换输出。
- 新增 `Rules/maintained_sources.lock.json`，逐一记录 10 个仓库维护列表的条目数、哈希、来源状态、许可边界和维护限制，不为历史来源不明的内容伪造第三方归属。
- 安装工作流新增必填 `archive_sha256`，在解压和执行 ZIP 内工具前验证整包外部哈希。升级只清理旧发布清单明确管理、但新清单已取消的文件。
- ZIP 暂存器增加大小写与 Unicode 归一化碰撞检测，改为临时目录完整写入后原子替换；CRC 或写入失败不留下半成品。ZIP 回归由 19 项增至 24 项。
- README 在原内容上补充 jsDelivr/GitHub、Surge GeoIP/ASN、AliDNS/测试端点、加密 DNS 直连与应用内 DoH 的边界，不把“30 个静态规则自有化”扩大为整套网络基础设施自托管。

### 运行资源

- 将主配置唯一剩余的第三方运行时静态资源 Amnesty Tech Pegasus 域名表复制为 `Rules/Pegasus.list`，保留固定提交 `3d8f248a0d015f183724ae7d096a5c46a8bb5fc7` 的 1,438 个域名。
- 新增 `Rules/resources.lock.json`，记录源仓库、完整提交、文件路径、Git Blob、上游 SHA-256、本地 SHA-256、条目数量和本地处理方式。
- 新增 `tools/update_external_resources.py`，支持离线验证本地副本，以及联网下载固定提交后执行 Blob、上游哈希和渲染哈希三重核对。
- `Surge.conf` 的 30 个 `RULE-SET`/`DOMAIN-SET` 现全部指向 `shenjlngbIng/surge@d1d714d575d5494ef1a7613238f4f301e1b293df`；第三方 URL 只存在于维护锁，不再由设备运行时加载。
- 增加 `THIRD_PARTY_LICENSES/AmnestyTech-NOTICE.txt`，保留来源信息并明确固定提交根目录未发现通用许可证文件，避免用本仓库 MIT License 覆盖第三方数据。

### 配置与分流

- 保留问题一的 `NodePool` 占位地址及 `Fail-Closed` 哨兵，不改变公开模板的失败关闭设计。
- 延续已审阅的 `test-timeout=5`、UDP 探测、`block-quic=per-policy`、`ApplePush evaluate-before-use`、`Security`、`UDP`、广告 DIRECT 排错开关和 `GEOIP,CN,DIRECT,no-resolve`。
- 在 HBO 规则前加入 `DOMAIN-SUFFIX,viu.now.com,Streaming`，避免 HBO 上游的 `now.com` 父级后缀在两个策略组选择不同地区时把 Viu 错分到 HBO。
- 保留 YouTube/Google、Game/Microsoft 和 `35.192.0.0/12` 的显式共享基础设施覆盖，使专用服务与通用平台边界可复核。
- 策略组基线为 33 个，主配置活动规则为 98 条，仓库运行资源为 30 个。

### 仓库、文档与验证

- 将运行配置锁升级为 schema 10，补充隐藏功能组、Security、UDP/QUIC、Viu/HBO、共享基础设施和仓库唯一运行源不变量。
- 重写配置与规则审计器，使其与当前配置一致，并检查全部策略引用、CIDR、运行源归属、固定更新间隔、文件数量、条目数量和内容哈希。
- 配置故障注入测试扩展为 78 项，ZIP 路径回归最终扩展为 24 项。
- 在现有 README 基础上补充资源自有化、Pegasus 维护、完整验证、文件说明、发布步骤和发布前清单；同步更新迁移、贡献、安全、来源、工作流、清单和校验和。
- 发布包改为 `Surge-R12.17-self-maintained-20260825.zip`，仍保持确定性文件顺序、时间戳和权限。

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
- 不通过 `DOMAIN,proxy-bootstrap.example.invalid,DIRECT` 等规则掩盖代理服务器自身的 DNS 引导问题。

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
