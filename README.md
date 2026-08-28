# Surge iOS Privacy + Push R13.2 Enhanced

这是一套面向 Surge iOS 的规则模式配置。它把私有订阅、Smart 自动节点、手动节点池、国内流量总开关、DNS 出口、UDP、APNs、广告与钓鱼防护、历史 Pegasus IOC、服务分流和发布校验放在同一套可复核结构中。公开版本不包含真实订阅、节点、令牌、证书、MITM、脚本或重写内容。

R13.2 是 R13.1 的保留式增强。原有 33 个策略组、125 个规则匹配条件和 30 个固定远程 URL 全部保留；新版本增加 `Domestic`、5 个主配置匹配项和 3 个经过审阅的动态补充源。16 个原规则只调整策略去向，匹配条件和原 URL 没有删除。

`Proxy` 默认使用 `AllServer` Smart 组，`NodePool` 仍是唯一订阅入口和手动节点池。`AllServer` 与五个地区组根据真实连接质量和测试结果自适应选择代理。`UDP` 默认跟随 `Proxy`。订阅为空、格式错误或地区无节点时，`Fail-Closed` 使连接明确失败，不会无提示直连。

主配置共有 34 个策略组、130 条活动规则和 33 个运行时远程资源，其中 30 个继续固定到原仓库完整提交，3 个 Sukka 补充源按 24 小时更新。发布包保存原来的 30 份本地规则快照；动态补充源只记录 URL、审计观察值和许可，不把 28 万余条内容复制进包内或主配置。

公开主配置地址

https://raw.githubusercontent.com/shenjlngbIng/surge/main/Surge.conf

## 当前基线

| 项目 | 当前值 |
| --- | --- |
| 配置版本 | R13.2 Enhanced |
| 更新日期 | 2026.08.28 |
| 推荐环境 | Surge iOS 5.14.6 及以上，建议 5.21.0 及以上 |
| 运行模式 | Rule |
| 策略组 | 34 个 |
| 主配置活动规则 | 130 条 |
| 运行时远程资源 | 33 个 |
| 固定提交资源 | 30 个，全部为 R13.1 原 URL |
| 动态补充资源 | 3 个，固定到审核过的域名与路径 |
| 普通 `RULE-SET` | 28 个 |
| `DOMAIN-SET` | 5 个 |
| 本地规则文件 | 30 个 |
| 中国精确域名 | 306 条 |
| 全球精确域名 | 116 条 |
| 精确域名交叉冲突 | 0 个 |
| Pegasus IOC | 1,438 个历史域名 |
| 固定 Ads | 152 条活动规则 |
| 动态广告与钓鱼 | 282,772 个发布时域名条目 |
| 动态国内补充 | 869 条发布时规则 |
| 第三方运行时规则 URL | 3 个，均为 `ruleset.skk.moe` 精确 URL |
| 主配置内嵌规则快照 | 0 条 |
| 配置故障注入测试 | 110 项 |
| ZIP 安全回归测试 | 26 项 |
| 发布清单回归测试 | 15 项 |
| 完整发布文件 | 66 个 |
| 固定规则快照 | `d1d714d575d5494ef1a7613238f4f301e1b293df` |
| 完整包名 | `Surge-R13.2-Complete-No-Embedded-20260828.zip` |

公开包中的 `NodePool.policy-path` 使用不可路由占位符。下载后必须在私人副本中替换，仓库版和公开压缩包应一直保留占位地址。

## R13.2 的主要取舍

| 关注点 | 常见写法 | R13.2 的处理 | 实际影响 |
| --- | --- | --- | --- |
| 订阅接入 | 多个自动组各自读取订阅 | 只有 `NodePool` 持有 `policy-path` | 订阅只维护一个入口，来源和故障更容易定位 |
| 日常节点 | 固定选择订阅中的一个节点 | `Proxy` 默认使用 `AllServer` Smart | 自动适应真实连接质量；仍可切到 `NodePool` 手选 |
| 自动选路 | 固定周期全量延迟测试 | `AllServer` 和地区组使用 Smart | 大订阅按需测试子集，并结合真实连接质量与失败重试 |
| 空订阅 | 空组可能失去代理成员 | 节点组显式保留 `Fail-Closed` | 订阅失效时连接失败，不会无提示直连 |
| UDP | 直接跟订阅首节点或直连 | 可见 `UDP` 默认使用 `Proxy` | STUN/UDP 跟随主代理，保留手选、拒绝和直连排错路径 |
| APNs | 全程代理或全程直连 | `ApplePush` 先用 `Proxy`，失败后回落 `DIRECT` | 推送保留第二条可用路径，普通国际服务仍受代理策略约束 |
| DNS | 系统 DNS、代理 DNS 和应用 DoH 混用 | 双明文 DNS、双 DoH、固定引导和应用 DoH 代理规则 | Surge 内部解析与应用自建解析的边界更清楚 |
| 国内流量 | 多条规则分别写死直连或代理 | 统一进入可见 `Domestic` | 默认直连，出境或受限网络可一键改为代理 |
| 规则来源 | 全部固定后逐渐陈旧，或全部浮动难以复核 | 原 30 份保持固定，3 份高价值补充源动态更新 | 稳定基线不丢失，同时补足时效；动态变化需持续监测 |
| 规则内容 | 把大量 IOC 或广告行写进主配置 | 所有规则保持外部引用 | 主配置没有逐条规则快照，完整包也不复制三份大型动态内容 |
| 最终流量 | `FINAL` 可直接选择 `DIRECT` | `Final` 只有 `Proxy` 与 `REJECT` | 未命中流量仍维持代理或拒绝边界 |
| 发布方式 | 只交付一个 `.conf` | 配置、规则、锁、工具、清单、哈希和工作流一起发布 | 下载者可以检查完整性，维护者可以复现同一份 ZIP |

这套配置更看重边界清楚和结果可复核。它不会承诺零探测、绝对无泄漏或自动选择永远优于手动节点。节点、运营商、iOS 后台状态和 Surge 版本仍会影响真机表现。

## 配置怎样工作

一次连接进入 Surge 后，会按主配置中的顺序处理。

1. Surge 接管符合配置范围的网络与 DNS 请求。
2. 局域网发现、多播地址、私网、CGNAT、回环和链路本地范围先处理。
3. Apple 公共 Wi-Fi 门户探测先直连，STUN 随后进入可见的 `UDP` 组。
4. 公网 53、853 和 8853 端口随后拒绝，局域网解析器不受这三条公网限制影响。
5. Apple 引导查询、出口检测站点和应用 DoH 域名按各自策略匹配。
6. 动态钓鱼域名与固定 Pegasus 历史 IOC 依次进入 `Security`。
7. APNs、Apple 国内服务、微信和固定直连集合继续处理。
8. 固定 Ads 与动态基础广告源依次进入 `AdBlock`，随后处理 AI、流媒体、国际服务和游戏。
9. 国内共享云后缀进入 `Domestic`，动态国内补充和固定 China 集合继续补齐国内边界。
10. Global 精确集合先走 `Proxy`，随后 `GEOIP,CN` 把中国 IP 字面量交给 `Domestic`。
11. 其余公网 IPv4 和 IPv6 字面量强制进入 `Proxy`。
12. 剩余连接落入 `FINAL,Final,dns-failed`。

Surge 采用首条命中。两个内容正确的规则文件只要位置颠倒，结果也会改变。R13.2 因此把重要先后关系同时写进配置审计和故障注入测试。

## 快速开始

### 准备完整目录

解压发布包后保留原目录结构。`Surge.conf` 会读取仓库中的固定远程规则，维护工具还依赖 `Rules`、锁文件和清单。只拿走主配置可以导入设备，但无法得到完整的来源记录、审计和可复现发布能力。

公开包共有 66 个文件。解压后不要把其他配置、日志、缓存、订阅备份或 ZIP 放进发布目录，再运行打包器时这些未知文件会被拒绝。

### 准备私人配置

公开 `Surge.conf` 中的订阅地址如下。

```ini
NodePool = select, Fail-Closed, policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL, update-interval=3600, no-alert=0, hidden=0, include-all-proxies=0
```

复制 `Surge.conf` 作为私人副本，只替换 `policy-path` 后面的 URL。订阅应输出 Surge 策略列表，或输出带有效 `[Proxy]` 内容的 Surge 配置。

```ini
NodePool = select, Fail-Closed, policy-path=https://你的私有地址, update-interval=3600, no-alert=0, hidden=0, include-all-proxies=0
```

保留 `Fail-Closed`、更新间隔、可见性和其余参数。整行换回旧版会丢失 R13.2 的失败关闭和手动节点入口。

真实订阅地址、Sub-Store 令牌和含节点信息的二维码只能留在私人设备或私人备份中。不要把填写后的配置提交到公开仓库，也不要把它放进需要公开分享的压缩包。

### 使用 Sub-Store 地址

配置包含下面这条 Host 映射。

```ini
sub.store = 127.0.0.1
```

它用于失败关闭。`policy-path` 若采用 `sub.store` 合成域名，需要安装并启用与你自己的 Sub-Store 部署相符的 Surge 模块，由模块接管该请求。模块未工作时，请求会到达本机无服务地址并失败，避免合成接口误发到公网。

使用普通 HTTPS 订阅地址时，这条映射不会影响该订阅。使用自定义 Sub-Store 域名时，应按自己的部署修改私人副本，公开版本继续保留当前安全占位。

### 导入和首次检查

1. 把私人配置导入 Surge iOS。
2. 重新载入配置并刷新外部资源。
3. 打开可见的 `NodePool`，确认订阅节点已经出现。
4. 确认 `Proxy` 选择 `AllServer`。从旧配置升级时，Surge 可能保留以前的手动选择，需要切换一次。
5. 如需固定节点，再进入 `NodePool` 选择一个确认支持目标服务、TCP 和所需 UDP 的稳定节点，并把 `Proxy` 切到 `NodePool`。
6. 检查香港、台湾、日本、新加坡和美国组能否按节点名称筛选。
7. 测试 Telegram 前台连接和锁屏后的 APNs 通知。
8. 分别在 Wi-Fi 和蜂窝网络下检查 DNS、IPv4、IPv6 与 UDP。

新导入的公开配置会让 `NodePool` 默认选中 `Fail-Closed`，但 `AllServer` 会展开 NodePool 的全部实际代理成员并自动选择。只有把 `Proxy` 手动切到 `NodePool` 时，才需要先在 NodePool 中选定真实节点。

## 订阅与节点选择

### NodePool 是唯一订阅入口

`NodePool` 使用 `select`，每 3,600 秒更新一次 `policy-path`。它负责读取订阅，并保留为手动稳定节点入口。服务规则不会直接选择订阅节点，它们先进入 `Proxy`、地区组或服务组，再由策略链确定出口。

`NodePool` 保持 `hidden=0`。`AdBlock`、`Security`、`UDP` 和新增的 `Domestic` 也保持可见，方便误报、UDP 和国内路由异常时直接排查。只有低频且带自动后备的 `ApplePush` 保持隐藏。

只有 `NodePool` 可以持有 `policy-path`。`AllServer` 和地区组通过 `include-other-group=NodePool` 读取节点。这样可以避免多个组分别下载同一份订阅，也能让审计器确认节点只来自一个容器。

### Smart 自动组承担默认出站

`Proxy` 的首个成员是 `AllServer`。填入有效订阅后，默认代理、出口检测站点以及多数服务会由 Smart 组根据真实连接质量选择节点。`NodePool` 仍排在第二位，用户随时可以改为手动固定节点。

```ini
Proxy = select, AllServer, NodePool, HongKong, TaiWan, Japan, Singapore, America, no-alert=0, hidden=0, include-all-proxies=0
```

需要手动固定节点时，把 `Proxy` 切到 `NodePool`。需要特定服务单独选区时，也可以只修改对应服务组，不必改变全局默认节点。

### AllServer 和地区组使用 Smart

`AllServer` 与五个地区组使用 `smart`，并在首次使用前完成评估。Smart 会结合真实连接首包时间、丢包和测试结果更新评分；连接失败或质量显著下降时，可以尝试其他候选节点。成员超过 12 个时，常规测试只覆盖高频与长时间未测的子集，手动全测才会检查全部成员。

```ini
AllServer = smart, Fail-Closed, evaluate-before-use=true, no-alert=0, hidden=0, include-all-proxies=0, include-other-group=NodePool
```

| 地区组 | 常见匹配内容 |
| --- | --- |
| `HongKong` | 香港、港区、HK、HKG、Hong Kong、Kowloon |
| `TaiWan` | 台湾、台北、高雄、TW、TPE、Taiwan、Taipei |
| `Japan` | 日本、东京、大阪、JP、NRT、HND、KIX、Japan |
| `Singapore` | 新加坡、狮城、SG、SIN、Singapore |
| `America` | 美国、美东、美西、US、USA 及常见美国城市和机场代码 |

节点供应商的命名差异很大。地区组只有 `Fail-Closed` 时，先检查节点名称。需要扩充正则时，在私人副本中修改对应组，并保留 `Fail-Closed`、`include-other-group=NodePool` 和 `include-all-proxies=0`。

Smart 仍会产生测试连接，但不会使用 R13.1 的 `interval=1800` 和 `tolerance=100`。Surge 官方说明 `interval` 对 Smart 无效，因此本版删除这些无效参数。大订阅仍建议在 Sub-Store 端先清理失效和重复节点。

## 策略组说明

### 核心策略组

| 策略组 | 类型 | 默认成员 | 可见性 | 用途 |
| --- | --- | --- | --- | --- |
| `Final` | `select` | `Proxy` | 可见 | 接收最终未匹配流量，可手动改为 `REJECT` |
| `Proxy` | `select` | `AllServer` | 可见 | 通用代理入口，可切到 NodePool 手选 |
| `NodePool` | `select` | `Fail-Closed`，导入后手动选节点 | 可见 | 唯一订阅容器和稳定节点入口 |
| `AllServer` | `smart` | `Fail-Closed` 后的自动节点 | 可见 | 全订阅质量自适应选择 |
| 五个地区组 | `smart` | `Fail-Closed` 后的地区节点 | 可见 | 按节点名称筛选并自适应选择 |
| `ApplePush` | `fallback` | `Proxy`，随后 `DIRECT` | 隐藏 | APNs 代理优先，失败后回落直连 |
| `AdBlock` | `select` | `REJECT` | 可见 | 固定与动态广告规则处置，可选 `REJECT-DROP` 或 `DIRECT` |
| `Security` | `select` | `REJECT` | 可见 | 动态钓鱼与历史 Pegasus IOC 处置 |
| `UDP` | `select` | `Proxy` | 可见 | STUN 与其他受策略控制的 UDP 出口 |
| `Domestic` | `select` | `DIRECT` | 可见 | 国内服务、国内补充、China 集合与 CN GeoIP 总开关 |

`Final` 不提供 `DIRECT`。代理规则缺失、域名未收录或 DNS 失败时，默认结果仍是 `Proxy`，用户也可以手动收紧到 `REJECT`。

`UDP` 保留 `DIRECT` 只用于临时兼容性排查。选择它会暴露真实公网地址，排查完成后应恢复 `Proxy` 或已验证的 `NodePool` 节点。

### 服务策略组

| 策略组 | 默认选择 | 对应远程规则 |
| --- | --- | --- |
| `ChatGPT` | `Proxy` | `ChatGPT.list` |
| `Claude` | `Proxy` | `Claude.list` |
| `Gemini` | `Proxy` | `Gemini.list` |
| `GitHub` | `Proxy` | `Github.list` |
| `YouTube` | `Proxy` | `YouTube.list` |
| `NETFLIX` | `Proxy` | `Netflix.list` |
| `Disney+` | `Proxy` | `Disney.list` |
| `HBO` | `Proxy` | `HBO.list` |
| `PrimeVideo` | `Proxy` | `PrimeVideo.list` |
| `Emby` | `Proxy` | `Emby.list` |
| `TikTok` | `Proxy` | `TikTok.list` |
| `Bahamut` | `Proxy` | `Bahamut.list` |
| `Spotify` | `Proxy` | `Spotify.list` |
| `Streaming` | `Proxy` | `BiliBiliIntl.list` 与 `ProxyMedia.list` |
| `Telegram` | `Proxy` | `Telegram.list` |
| `X` | `Proxy` | `Twitter.list` |
| `Apple` | `DIRECT` | `AppleCN.list` |
| `Google` | `Proxy` | `Google.list` |
| `Microsoft` | `Proxy` | `OneDrive.list` 与 `Microsoft.list` |
| `Games` | `Proxy` | `Game.list` |

代理类服务组没有 `DIRECT`。`Apple` 以国内服务兼容为目标，默认保留 `DIRECT`，同时允许手动改用代理或地区组。

## 失败关闭设计

### Fail-Closed 哨兵

```ini
Fail-Closed = http, 127.0.0.1, 1, no-error-alert=true
```

本机 `127.0.0.1:1` 预期没有 HTTP 代理服务。订阅为空、订阅下载失败或地区正则没有匹配时，节点组仍保留一个代理类型成员，连接会明确失败。

`no-error-alert=true` 只隐藏这个预期哨兵造成的错误提醒，不会把失败转换为直连。删除哨兵会改变空组行为，也会让当前审计失败。

### 最终策略

```ini
Final = select, Proxy, REJECT, no-alert=0, hidden=0, include-all-proxies=0
FINAL,Final,dns-failed
```

未匹配连接默认进入 `Proxy`。用户可以把 `Final` 改为 `REJECT`，配置没有最终直连选择。某个远程规则暂时加载失败时，后面的精确域名、公网 IP 代理兜底和 `Final` 仍会继续工作。

## Telegram 与 Apple Push

Telegram 应用数据和 Apple 推送唤醒属于两条独立链路。

`Telegram.list` 中的域名和 IP 进入 `Telegram`。该组不提供 `DIRECT`。Telegram 核心地址还加入 `always-raw-tcp-hosts`，用于减少协议识别造成的兼容问题。

APNs 由 `APNs.list` 进入隐藏的 `ApplePush`。

```ini
ApplePush = fallback, Proxy, DIRECT, interval=60, evaluate-before-use=true, no-alert=0, hidden=1
```

代理可用时，APNs 优先使用 `Proxy`。首轮评估会在第一次选择前完成，代理失败后再尝试 `DIRECT`。全局 `test-timeout=5` 控制测试等待上限。

这条直连后备只服务 APNs。Telegram、AI、流媒体和最终流量不会跟着获得直连退路。真机仍要在锁屏状态、Wi-Fi 和蜂窝切换后各收一次推送，静态配置无法证明运营商和 iOS 后台一定及时交付。

## DNS 与网络边界

### Surge 内部解析

配置使用两个 AliDNS 明文地址和两个 DoH 端点。

```ini
dns-server = 223.5.5.5, 223.6.6.6
encrypted-dns-server = https://dns.alidns.com/dns-query, https://doh.pub/dns-query
encrypted-dns-follow-outbound-mode = false
encrypted-dns-skip-cert-verification = false
hijack-dns = *:53
```

`dns.alidns.com` 的两个 IPv4 和一个 IPv6 引导地址写在同一条 Host 映射中。`doh.pub` 使用两个 IPv4 引导地址。Host 匹配具有顺序，重复键可能让后续映射失去作用。

`encrypted-dns-follow-outbound-mode=false` 让 Surge 自身的加密 DNS 不跟随普通代理规则，降低域名型代理节点在启动阶段形成解析依赖环的风险。证书校验保持开启。

这不是匿名 DNS 设计。Surge 会并发查询配置中的多个加密 DNS，AliDNS 和 DNSPod 都可能看到查询，且当前选项使这些连接直连。本版按“基于 R13.1 增强、不删除原功能”的边界保留两个端点，没有通过再加第三个服务假装提高隐私。若要改变信任对象，应另行选择单一可信解析器并做可用性测试。

### 应用自带 DNS

配置接管发往 53 端口的传统 DNS，并在局域网规则之后拒绝公网目的端口 53、853 和 8853。局域网内的明确私有地址已经提前直连，因此本地路由器或内网解析器仍可以按现有网络工作。

常见公共 DoH 和 DoT 域名明确进入 `Proxy`，包括 AliDNS、DNSPod、Google DNS、Cloudflare、Quad9、NextDNS、AdGuard、OpenDNS 与若干公共服务。Surge 自身的加密 DNS 由内部解析链处理，应用自己发起的 HTTPS DNS 请求则继续受规则系统约束。

这组规则覆盖常见入口，无法穷举新的加密解析协议、未知域名和硬编码地址。应用更新后出现新端点时，需要结合最近请求记录继续审阅。

### 出口与 DNS 检测

Net.Coffee、IPPure、BrowserLeaks、Surfshark DNS、Fastly resolver、icanhazip、ipinfo、ipapi 和 IPIP 相关端点统一进入 `Proxy`。Net.Coffee 使用的 `1.1.1.1/32` 出口探针也进入 `Proxy`。

检测结果对应当前 `Proxy` 选择。`Proxy` 选中 `NodePool` 时，它应反映手动节点。`Proxy` 选中 `AllServer` 或地区组时，它应反映该自动组当前选出的节点。

网页出口在境外而解析器仍显示中国移动、阿里或其他国内服务时，先看最近请求的策略路径。检测端点全部走代理后，剩余差异通常来自节点服务端 DNS。客户端配置无法替远端节点重写其解析器，只能更换节点或由提供方调整。

页面直接显示本机公网 IPv4 或 IPv6 时，应检查私有模块、`include-all-networks`、`ipv6-vif`、`UDP` 选择和最近请求路径。不要通过关闭 IPv6 掩盖尚未定位的路由问题。

### 模块优先级

Surge 模块可以覆盖 General 项，并把 Rule、Host、Script 和 Rewrite 内容插入主配置之前。一个缺少 `no-resolve` 的模块规则集、提前直连的检测域名或改写 DNS 的模块，都可能在 R13.2 规则生效前改变结果。

排查 DNS 或出口异常时，先在无额外模块的基线下测试。最近请求若出现规则评估要求本地 DNS，检查对应模块中的 `RULE-SET` 是否缺少 `no-resolve`。关闭模块、重新载入配置并清理检测网站数据后再测，才能判断问题来自主配置还是补丁。

### 本地网络

下列范围同时出现在本地规则或 `skip-proxy` 中。

- RFC 1918 私网
- `100.64.0.0/10` 运营商 CGNAT
- IPv4 与 IPv6 回环地址
- IPv4 与 IPv6 链路本地地址
- IPv6 ULA
- `.local` 与 `localhost`

`include-local-networks=false`、`allow-wifi-access=false` 和 `allow-hotspot-access=false` 共同限制局域网接管与代理入口。Web 控制面板保持关闭，代理与网关限制在本机局域网边界内。

`captive.apple.com` 与 `configuration.ls.apple.com` 两个精确域名位于远程规则之前并直连，分别用于公共 Wi-Fi 门户和 Apple 配置引导。宽泛 `ls.apple.com` 后缀没有放行，其他 Apple 服务仍由 `AppleCN.list` 和 `Apple` 策略决定。

## UDP、QUIC 与 STUN

```ini
udp-policy-not-supported-behaviour = REJECT
proxy-test-udp = apple.com@9.9.9.9
block-quic = per-policy
PROTOCOL,STUN,UDP
```

节点不支持 UDP 时，连接会拒绝，不会静默直连。Surge 使用 `apple.com@9.9.9.9` 检查基础 UDP 能力。这个探针通过只能说明测试链路可达，无法保证游戏、语音、QUIC 或特定 STUN 服务都能工作。

STUN 在公网 DNS 端口、公共域名和公网 IP 规则之前进入 `UDP`。该组默认选择 `Proxy`，让 STUN 跟随当前主代理。`UDP` 已保持可见，可直接在 `Proxy`、`NodePool`、`REJECT` 和 `DIRECT` 之间排查。`DIRECT` 会暴露真实公网地址，只适合短时确认兼容性。

`block-quic=per-policy` 让 QUIC 行为跟随当前策略能力。某个应用无法回落到 TCP 时，应查看应用协议和节点支持情况。全局放开 UDP 直连会改变整套配置的隐私边界。

## 规则顺序

主配置的 130 条活动规则按下面的结构排列。

1. 局域网发现与允许的多播地址。
2. 无效地址和其余多播范围拒绝。
3. 私网、CGNAT、回环、链路本地和本地主机直连，Apple Wi-Fi 门户探测精确直连。
4. STUN 进入 `UDP`。
5. 公网 DNS 与 DoT 端口控制。
6. Apple 配置引导查询。
7. 出口检测端点和应用 DoH 域名。
8. 动态钓鱼域名与 Pegasus 历史 IOC。
9. APNs、Apple 国内服务、微信和固定直连集合。
10. 固定 Ads 与动态基础广告域名。
11. ChatGPT、Claude 和 Gemini。
12. YouTube、Netflix、Disney+、HBO、PrimeVideo、Emby、TikTok、Bahamut、Bilibili、Spotify 和通用媒体。
13. Telegram、GitHub、X 和 Google。
14. Microsoft 专用覆盖、Game、OneDrive 和 Microsoft。
15. 国内共享云、动态国内补充、China 与 Global 精确域名集合。
16. `GEOIP,CN`、公网 IPv4/IPv6 字面量兜底和 `Final`。

几个容易冲突的位置由审计器直接约束。

- STUN 必须位于公网 DNS 端口和所有公网域名、IP 规则之前。
- 动态钓鱼必须位于 Pegasus，Pegasus 必须位于 APNs 和普通服务规则之前。
- Apple 流媒体专用主机必须位于 `AppleCN.list` 之前。
- `yt3.ggpht.com` 必须先于 Google 通用规则进入 `YouTube`。
- `viu.now.com` 必须先于 HBO 的 `now.com` 父级规则进入 `Streaming`。
- `BiliBiliIntl.list` 必须位于国内 `BiliBili.list` 之前。
- Microsoft 登录与商店覆盖必须位于 `Game.list` 之前。
- `Game.list` 必须位于 `OneDrive.list` 和 `Microsoft.list` 之前。
- `35.192.0.0/12` 必须先进入 `Proxy`，避免宽泛 Google Cloud 网段全部进入 `Games`。
- 共享云和用户托管后缀必须进入 `Domestic`，并位于动态国内补充和 China 集合之前。
- Global 必须位于 `GEOIP,CN,Domestic,no-resolve` 之前。
- CN GeoIP、公网 IPv4 和 IPv6 兜底必须紧贴唯一的末尾 `FINAL`。

## 远程规则库存

`Surge.conf` 继续通过 jsDelivr 加载仓库中的 30 份规则文件。运行地址全部固定到完整 Git 提交 `d1d714d575d5494ef1a7613238f4f301e1b293df`。便于识别的标签 `r12.17-20260825` 已核实指向同一提交，运行时不依赖标签。

19 份服务规则保存固定上游提交、Git Blob、SHA-256、排除项和显式本地补充。Pegasus 使用独立来源锁。其余 10 份仓库维护列表通过 `maintained_sources.lock.json` 披露来源状态、哈希、条目数与许可边界。

| 规则文件 | 策略 | 活动条目 |
| --- | --- | --- |
| `Pegasus.list` | `Security` | 1,438 |
| `APNs.list` | `ApplePush` | 12 |
| `AppleCN.list` | `Apple` | 166 |
| `WeChat.list` | `Domestic` | 33 |
| `Direct.list` | `Domestic` | 9 |
| `Ads.list` | `AdBlock` | 152 |
| `ChatGPT.list` | `ChatGPT` | 52 |
| `Claude.list` | `Claude` | 6 |
| `Gemini.list` | `Gemini` | 21 |
| `YouTube.list` | `YouTube` | 192 |
| `Netflix.list` | `NETFLIX` | 36 |
| `Disney.list` | `Disney+` | 165 |
| `HBO.list` | `HBO` | 45 |
| `PrimeVideo.list` | `PrimeVideo` | 18 |
| `Emby.list` | `Emby` | 218 |
| `TikTok.list` | `TikTok` | 86 |
| `Bahamut.list` | `Bahamut` | 7 |
| `BiliBiliIntl.list` | `Streaming` | 7 |
| `BiliBili.list` | `Domestic` | 12 |
| `Spotify.list` | `Spotify` | 30 |
| `ProxyMedia.list` | `Streaming` | 319 |
| `Telegram.list` | `Telegram` | 51 |
| `Github.list` | `GitHub` | 31 |
| `Twitter.list` | `X` | 33 |
| `Google.list` | `Google` | 705 |
| `Game.list` | `Games` | 596 |
| `OneDrive.list` | `Microsoft` | 16 |
| `Microsoft.list` | `Microsoft` | 664 |
| `China.list` | `Domestic` | 306 |
| `Global.list` | `Proxy` | 116 |

30 个文件都放在发布包里，便于审阅、来源复核和仓库上传。设备运行时仍从固定 CDN URL 加载它们，主配置不复制逐条内容。

### 三个动态补充源

R13.2 额外引用三份 SukkaW 维护资源。它们固定到精确域名与路径，不使用仓库 `main` 拼接地址，但内容会按上游发布变化。

| 运行 URL | 类型 | 策略 | 更新间隔 | 发布时活动条目 |
| --- | --- | --- | --- | ---: |
| `https://ruleset.skk.moe/List/domainset/reject_phishing.conf` | `DOMAIN-SET` | `Security` | 86,400 秒 | 147,468 |
| `https://ruleset.skk.moe/List/domainset/reject.conf` | `DOMAIN-SET` | `AdBlock` | 86,400 秒 | 135,304 |
| `https://ruleset.skk.moe/List/non_ip/domestic.conf` | `RULE-SET` | `Domestic` | 86,400 秒 | 869 |

发布包不保存这三份动态文件的内容，只在 `Rules/r10.lock.json` 记录发布时的 URL、条目数、字节数、上游时间、内容哈希和 SHA-256。`python3 tools/audit_rules.py --check-dynamic` 会下载当前版本并检查 HTTP、UTF-8、类型格式、重复行和大小上限，但不会要求动态内容永远保持发布时哈希。

动态源提高广告、钓鱼和国内规则的时效，也引入上游变化风险。`AdBlock`、`Security` 和 `Domestic` 因此保持可见，发生误报时可以先切换策略确认，再查看最近请求和上游变化。定期检查任务只报告变化，不会自动改写配置或订阅。

### Pegasus 固定副本

`Rules/Pegasus.list` 来自 Amnesty Tech 固定提交 `3d8f248a0d015f183724ae7d096a5c46a8bb5fc7` 中的 `2021-07-18_nso/domains.txt`。本地文件保留 1,438 个非空纯域名，不扩大为后缀。

`Rules/resources.lock.json` 记录上游仓库、提交、文件路径、Git Blob、上游 SHA-256、本地 SHA-256、条目数和处理方法。普通设备只读取本仓库固定提交中的 `Pegasus.list`。维护工具访问固定第三方来源时，Blob、哈希和渲染结果必须同时符合锁文件。

这是一份 2021 年历史 IOC。它能提供有限的纵深防护，无法识别新的攻击基础设施，也不能替代 iOS 更新、Lockdown Mode、账户保护和专业取证。IOC 命中只能说明访问目标与历史列表重合，不能单独证明设备已经感染。

### Ads 固定副本

`Rules/Ads.list` 有 152 条活动规则，其中 138 条为 `DOMAIN-KEYWORD`，14 条为 `DOMAIN-WILDCARD`。主配置通过固定 `RULE-SET` 把完整列表交给 `AdBlock`，不保存规则明细。

这份列表包含历史 SukkaW 来源和仓库维护内容。准确的历史输入提交仍未确认，`Rules/maintained_sources.lock.json` 已披露这一限制，并禁止没有固定来源和人工差异审阅的自动刷新。

关键词、通配符和大型动态域名集都可能产生误拦截。遇到网页或应用异常时，可以直接把可见的 `AdBlock` 切到 `DIRECT` 复测。确认命中项以后再调整列表，不要长期关闭所有广告处置来掩盖单条误判。

## 服务规则的本地筛选

19 份第三方服务规则固定在 `blackmatrix7/ios_rule_script` 的提交 `c00517ce10760a93728b241923a451dfa617be80`。更新工具会核对 Git Blob 和 SHA-256，再按锁文件应用类型过滤、精确排除与显式补充。

R13.2 延续下面这些边界。

- Netflix 删除上游中的宽泛 `IP-CIDR` 和 `IP-CIDR6`，保留官方网络 `IP-ASN,2906,no-resolve`。
- Disney 删除 Adobe、Braze、Conviva、New Relic 和 Optimizely 等共享遥测域名。
- HBO 删除共享 Brightcove、BoltDNS 和 AWS API 后缀。
- Microsoft 删除共享 Azure CDN、托管平台、HelpShift 和 Optimizely 后缀。
- Bahamut 删除 DigiCert、GVT1 和整个 Hinet 后缀，保留明确的动画 CDN 主机。
- Game 删除共享 `helpshift.com`，Xbox、Minecraft、Bethesda 和 Forza 继续进入 `Games`。
- TikTok 删除宽泛 `snssdk.com`，明确的 TikTok 海外主机和网络继续进入 `TikTok`。
- Google 删除共享 `appspot.com`，减少用户托管内容被统一归入 Google 服务策略的范围。

历史终审发现过 278 条只存在于本地生成结果、没有写进锁文件的旧行。这些内容已经进入对应服务的显式 `add` 数组。现在从空目录按固定上游和锁文件重建，结果会与当前 19 份服务快照逐字节一致。

不要直接手改生成后的服务文件来绕过来源锁。需要增加或删除规则时，先修改 `Rules/upstreams.lock.json` 的输入边界，再运行更新工具和全部审计。

## 精确国内外域名集合

`China.list` 保存 306 个明确归属的国内域名，`Global.list` 保存 116 个明确归属的境外域名。两个文件只接受纯域名形式，审计器会拒绝关键词、通配符、公共后缀、内部冗余和跨策略冲突。

下面 12 个共享云或用户托管后缀在动态国内补充与 China 集合之前明确进入 `Domestic`。

```text
alibabausercontent.com
aliyuncs.com
bcebos.com
coding.net
gitee.io
jdcloud.com
myqcloud.com
qcloudimg.com
qiniu.com
tencentcs.com
volccdn.com
volcengine.com
```

这些平台可以托管不同租户的内容。R13.2 不再把它们永久写死为 `Proxy` 或 `DIRECT`，而是统一交给可见的 `Domestic`。该组默认直连；在境外、校园网或受限网络中可以整体改为 `Proxy`。专用服务规则仍在它们之前完成匹配。

## 文件说明

| 路径 | 用途 |
| --- | --- |
| `Surge.conf` | R13.2 主配置 |
| `Rules/*.list` | 30 份固定运行规则快照 |
| `Rules/r10.lock.json` | 配置哈希、运行资源、节点架构与安全不变量 |
| `Rules/upstreams.lock.json` | 19 份服务规则的固定上游、排除项和本地补充 |
| `Rules/resources.lock.json` | Pegasus 固定来源、上游哈希和本地哈希 |
| `Rules/maintained_sources.lock.json` | 10 份仓库维护规则的来源状态与许可披露 |
| `tools/convert_to_remote_rules.py` | 检查 30 个固定与 3 个动态远程引用、选项和零内嵌内容 |
| `tools/generate_runtime_lock.py` | 按当前配置生成运行锁元数据 |
| `tools/audit_config.py` | 检查配置结构、策略组、规则顺序和失败边界 |
| `tools/audit_rules.py` | 检查规则库存、哈希、语义边界和可选动态源在线格式 |
| `tools/audit_precise_domains.py` | 检查 China 与 Global 精确域名集合 |
| `tools/test_audit_config.py` | 110 项配置故障注入测试 |
| `tools/test_stage_surge_zip.py` | 26 项候选 ZIP 和路径安全回归测试 |
| `tools/release_inventory.py` | 打包、清单和校验和共用的发布白名单 |
| `tools/test_release_inventory.py` | 15 项目录、文本和升级清理回归测试 |
| `tools/update_service_rules.py` | 固定上游下载、合并与验证 |
| `tools/update_external_resources.py` | Pegasus 固定来源验证和维护 |
| `tools/generate_release_manifest.py` | 生成发布文件清单 |
| `tools/generate_checksums.py` | 生成两份 SHA-256 文件清单 |
| `tools/package_release.py` | 生成确定性完整 ZIP |
| `tools/stage_surge_zip.py` | 安全暂存候选 ZIP |
| `AUDIT_REPORT.md` | 全仓审计结果、修正内容和剩余真机项目 |
| `MIGRATION.md` | R13.1 到 R13.2 的迁移说明 |
| `CHANGELOG.md` | 版本变化记录 |
| `RELEASE_MANIFEST.txt` | 发布文件路径、用途和内容摘要 |
| `SHA256SUMS.txt` | 发布文件 SHA-256 |
| `SHA256SUMS_fixed.txt` | 与主清单逐字节一致的冻结副本 |
| `.github/workflows/install.yml` | 安装与持续审计工作流 |
| `THIRD_PARTY_LICENSES` | 第三方许可证和来源说明副本 |

发布目录固定为 66 个文件，其中包含 30 份 `.list`、4 份 JSON 锁、15 个 Python 工具、3 份第三方许可文本、1 份工作流和 13 个根目录文件。唯一允许清单由 `tools/release_inventory.py` 维护，文档、打包器和工作流共用同一来源。

## 上传与发布

### 已有仓库直接更新

解压完整包，把全部文件按原目录结构上传到仓库。`Rules`、`tools`、`.github` 和 `THIRD_PARTY_LICENSES` 都要保留。提交到 `main` 后，公开主配置地址会继续指向根目录 `Surge.conf`。

当前 30 个仓库运行 URL 固定到旧规则快照提交 `d1d714d575d5494ef1a7613238f4f301e1b293df`。更新 README、审计器或 R13.2 主配置不会自动改变这些 URL。只有规则文件经过重新审阅、产生新的固定提交后，才应同步升级运行地址和所有锁。三份 Sukka 补充源按日更新，不能被描述为固定快照。

只上传 `Surge.conf` 会缺少规则快照、来源记录、维护工具、工作流和完整性清单。只上传 ZIP 也不会让 GitHub Raw 主配置地址自动可用，仓库仍需保留解压后的文件结构。

### 使用安装工作流

可以把未解压的 `Surge-R13.2-Complete-No-Embedded-20260828.zip` 放在仓库根目录，并保留 `.github/workflows/install.yml`。随后在 Actions 中手动运行 `Install and audit Surge R13.2`，在必填的 `archive_sha256` 输入框填写包外公布的整包 SHA-256。

工作流会先核对整包哈希，再检查路径、文件数量、单文件大小、解压总量、双份文件哈希、运行锁、来源锁、配置审计、规则审计和故障注入。全部通过后才会提交文件。

升级清理只处理旧发布清单中存在、而新清单已经取消的受管理文件。用户自己的仓库文件不会因为名称相似而被清理。候选包包含未知发布文件、路径穿越、反斜杠、大小写碰撞、Unicode 归一化碰撞、链接或特殊文件时，安装会停止。

### 本地生成发布包

```bash
python3 tools/package_release.py --output ../Surge-R13.2-Complete-No-Embedded-20260828.zip
```

ZIP 使用固定顺序、固定时间戳和统一权限。相同输入会生成相同字节。整包 SHA-256 应在 ZIP 外单独发布，归档无法可靠地把自身哈希写进自身内容。

## 维护与审计

### 完整验证命令

```bash
export PYTHONDONTWRITEBYTECODE=1
python3 -m compileall -q tools
python3 tools/convert_to_remote_rules.py
python3 tools/generate_runtime_lock.py
python3 tools/update_external_resources.py --verify-lock
python3 tools/update_service_rules.py --verify-lock
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/audit_rules.py --check-dynamic
python3 tools/audit_precise_domains.py
python3 tools/test_audit_config.py
python3 tools/test_release_inventory.py
python3 tools/test_stage_surge_zip.py
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
sha256sum -c SHA256SUMS.txt
cmp --silent SHA256SUMS.txt SHA256SUMS_fixed.txt
python3 tools/package_release.py --output ../Surge-R13.2-Complete-No-Embedded-20260828.zip
```

当前基线的关键结果如下。

```text
PASS: immutable_runtime_resources=30 dynamic_runtime_resources=3 embedded_rule_contents=0 reviewed_third_party_runtime_urls=3
PASS: verified pinned resources=1 entries=1438
PASS: verified upstream lock services=19
PASS R13.2 groups=34 rules=130 runtime_resources=33 immutable_resources=30 dynamic_resources=3 embedded_rule_contents=0
PASS R13.2 runtime_sources=33 immutable_sources=30 dynamic_sources=3 local_rule_files=30 rules=130 embedded_rule_contents=0
PASS precise domains Domestic=306 Proxy=116 conflicts=0
PASS R13.2 mutations=110
PASS: strict release inventory regression cases=15
PASS: ZIP allowlist regression cases=26
```

`audit_rules.py --check-dynamic` 需要联网，输出还会包含三行当前动态源的条目数、字节数和 SHA-256。动态内容发生正常更新时，当前哈希可以与发布观察值不同；HTTP、格式、重复行或大小边界异常才会失败。

`generate_runtime_lock.py` 会重写 `Rules/r10.lock.json`。配置和规则没有变化时，运行前后应无差异。主配置、规则内容、README 或其他发布文件发生变化后，发布清单和双份 SHA-256 都要重新生成。

### 更新固定服务规则

普通离线验证使用下面的命令。

```bash
python3 tools/update_service_rules.py --verify-lock
```

按照当前锁下载并检查固定上游使用下面的命令。

```bash
python3 tools/update_service_rules.py --download --check
```

升级上游提交需要逐份复核许可证、路径、Git Blob、SHA-256、排除项、显式补充和条目变化。确认结果后再按维护工具支持的写入方式更新。不要把来源改成 `main`，也不要通过手改输出偷偷保留锁外规则。

### 更新 Pegasus 固定资源

离线核对本地副本与来源锁使用下面的命令。

```bash
python3 tools/update_external_resources.py --verify-lock
```

下载固定提交并只比较结果使用下面的命令。

```bash
python3 tools/update_external_resources.py --download --check
```

升级到新的上游提交时，应先审阅全部新增和删除域名，再更新 `Rules/resources.lock.json` 中的提交、路径、Git Blob、上游 SHA-256、本地 SHA-256 与条目数。`Surge.conf` 仍然只能引用本仓库的新固定提交。

## 常见问题

### 订阅地址怎么不见了

公开包从一开始就使用下面的占位地址。

```text
https://example.invalid/REPLACE_WITH_SUB_STORE_URL
```

它故意不可用，用于防止真实订阅和令牌进入公开仓库。原始上传配置里也没有可恢复的真实地址。请在私人副本中填入自己的 URL，公开副本、GitHub 仓库和分享包继续保留占位符。

### NodePool 只有 Fail-Closed

`NodePool` 没有获得可用订阅节点。常见原因包括占位 URL 没替换、订阅过期、输出格式不兼容、Sub-Store 模块没有接管、TLS 或 DNS 失败以及节点语法无效。

先检查私人 `policy-path` 的返回状态和内容，再刷新配置。不要删除 `Fail-Closed`，也不要把 `Proxy` 或 `Final` 临时改成 `DIRECT` 来掩盖订阅故障。

### 导入后仍停在旧的手动节点

R13.2 把 `Proxy` 的第一项改为 `AllServer`，但 Surge 可能按策略组名称保留旧版本的已选成员。升级覆盖配置后若 `Proxy` 仍显示 `NodePool`，手动切到 `AllServer` 一次即可。

`NodePool` 自身仍可能保持在 `Fail-Closed`，这不影响 `AllServer` 展开订阅中的实际代理。只有把 `Proxy` 改回 NodePool 手选模式时，才必须先选定一个真实节点。

### 地区组只有 Fail-Closed

订阅可能已经有节点，但名称没有命中地区正则。先看节点名是否包含中文地区、英文地区、旗帜、机场代码或常见缩写。可以在私人 Sub-Store 输出中规范命名，也可以审慎扩展对应组的 `policy-regex-filter`。

地区组应继续读取 `NodePool`。不要开启 `include-all-proxies=true`，否则其他本地代理或策略成员可能混入地区测试。

### Smart 组产生很多请求

`AllServer` 和五个地区组会结合真实连接质量与固定 5 分钟复测工作。成员超过 12 个时常规轮次只测子集，手动点击全部测试仍会产生集中连接。配置中的 `interval` 不会改变 Smart 的这项机制，因此 R13.2 没有继续保留旧的 1,800 秒参数。

需要完全固定出口时，让 `Proxy` 选择 `NodePool` 并在其中选定节点。大订阅可以在 Sub-Store 端先精简节点，再交给 Surge。

### Telegram 可用但锁屏没有通知

确认 `include-apns=true`，检查 `APNs.list` 是否加载成功，并在最近请求中查看 APNs 是否进入隐藏的 `ApplePush`。代理不可用时，该组才会尝试 `DIRECT`。

需要人工查看时，在私人副本中把 `ApplePush` 临时设为 `hidden=0`。完成锁屏、Wi-Fi 和蜂窝测试后再恢复隐藏。

### DNS 检测显示国内解析器

先确认检测站点走 `Proxy`，并查看它最终选择的节点。网页出口在境外、解析器在国内时，节点服务端 DNS 是首要检查对象。切换另一个已知节点后再测，可以快速区分客户端规则与节点问题。

最近请求出现模块 `RULE-SET` 触发本地 DNS 时，关闭对应模块并重新载入。模块规则位于主配置之前，主配置无法在后面撤销已经发生的解析。

### 检测页面显示真实 IPv4 或 IPv6

确认 `Proxy` 没有选到错误路径，`UDP` 没有停在 `DIRECT`，并检查私有模块是否覆盖 `include-all-networks`、`ipv6-vif`、检测域名或公网 IP 兜底。清理检测网站数据或使用新的无痕标签页后再测。

公网字面量规则已经覆盖 `0.0.0.0/0` 与 `::/0`。真实地址仍出现时，需要从最近请求判断流量有没有进入 Surge。直接关闭 IPv6 会掩盖原因。

### 规则文件出现 404

先区分资源类型。30 个仓库 URL 应使用完整提交 `d1d714d575d5494ef1a7613238f4f301e1b293df`；另外 3 个动态 URL 应精确位于 `ruleset.skk.moe/List/...` 的已审阅路径。不要把其中任何一个改成猜测的镜像或浮动 GitHub 分支。

本地包里的 30 份规则文件用于审阅和仓库发布，不等于设备会自动读取本地目录。CDN 或 Sukka 服务暂时不可达时，现有缓存可能继续工作，新设备或清缓存后的设备则可能加载失败。使用 `python3 tools/audit_rules.py --check-dynamic` 可以单独检查三个动态端点。

### DNS 解析异常

确认 `[Host]` 中 `dns.alidns.com` 和 `doh.pub` 的引导映射仍在，且 AliDNS 的三个地址位于同一行。检查两个 DoH 端点是否可达，也要确认私人模块没有覆盖 `encrypted-dns-server`、`hijack-dns`、IPv6 VIF 或规则顺序。

恢复 `system` DNS 可能暂时改变症状，也会改变当前解析边界。先定位订阅服务器、代理节点域名、DoH 端点或本地网络中的实际故障。

### 某个应用的语音或游戏失败

先确认当前 Smart 或手动节点支持 UDP，再查看 STUN 是否进入可见的 `UDP`。在 `Proxy`、`NodePool`、`REJECT` 和 `DIRECT` 之间逐项复测。

`DIRECT` 通过只说明应用需要或偏好直连 UDP，也意味着真实公网地址会暴露。更合适的长期处理通常是换用支持目标协议的代理节点，或对确有必要的应用单独制定经过审阅的规则。

### 局域网设备无法访问 iPhone 代理

公开配置关闭 Wi-Fi 和热点代理入口，也关闭 Web 控制面板。需要把 iPhone 作为局域网代理或网关时，应在私人副本中单独配置访问控制，并评估同网段设备能够接触到的接口。

## 安全与隐私

公开仓库不得包含下面这些内容。

- 真实订阅地址和 Sub-Store 私有接口
- 节点地址、端口、用户名和密码
- Token、Cookie、会话与设备标识
- MITM CA、私钥和证书密码
- 私有脚本、重写、模块和完整设备日志

本配置没有 MITM、脚本或重写段。用户自行加入的节点、模块、证书、脚本和自定义规则不在仓库审计范围内。

发现凭据泄露时，先撤销或轮换订阅和令牌，再清理 Git 历史。只删除最新提交中的一行，无法移除已经公开的旧版本。

发布工具会拒绝 `.env`、未知文件、符号链接、特殊文件、BOM、CRLF、NUL 和缺少结尾换行的文本。双份 SHA-256 用于检查包内每个受管理文件，整包 SHA-256 必须通过压缩包以外的渠道提供。

更多要求见 [SECURITY.md](./SECURITY.md) 和 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 真机验收

静态审计能够证明文件之间一致，并能捕获已经建模的配置退化。下面这些项目仍需在真实设备完成。

- 在 Wi-Fi 和蜂窝网络间切换，确认 Surge 持续接管且没有异常直连。
- 在锁屏状态接收 APNs 推送，确认代理失败时后备路径可用。
- 用两个不同检测站点检查当前 `Proxy` 的网页出口和 DNS 解析器。
- 分别测试公网 IPv4 与 IPv6 字面量，确认请求进入 `Proxy`。
- 进行语音、游戏或 STUN 测试，确认当前节点支持所需 UDP。
- 分别选择 `NodePool` 与 `AllServer`，确认手动固定和 Smart 自适应都符合预期。
- 在境内和受限网络分别测试 `Domestic=DIRECT` 与 `Domestic=Proxy`。
- 临时切换 `AdBlock` 和 `Security` 的处置策略，确认紧急关闭路径有效。
- 检查目标流媒体和 AI 服务的地区可用性，确认服务组选择符合节点地区。

测试完成后，确认 `Proxy`、`UDP`、`Domestic` 与服务组仍使用预期路径。如果选择手动模式，再把 `NodePool` 保持在已验证节点。

## 已知限制

- Surge 版本、iOS 网络栈、节点协议和运营商路径可能带来设备差异。
- Smart 会利用真实连接和测试数据，但不保证每个网站都选中同一节点，也不保证自动结果永远优于手动选择。
- APNs 后备提供第二条路径，无法保证每个网络都能及时推送。
- DNS 规则覆盖常见绕行方式，无法穷举所有加密解析协议和硬编码地址。
- 历史 Pegasus IOC 会过时，固定 Ads 与动态广告/钓鱼列表都可能误判或漏判。
- 三份动态规则会在发布后变化；完整包只能证明发布时观察值和当前格式，不能逐条人工保证未来内容。
- 固定提交可以锁定内容，无法保证 jsDelivr、GitHub 或用户网络永远可达。
- 公开包故意不含可用订阅，导入后必须私下完成 `NodePool` 设置。
- 静态审计无法替代节点服务端 DNS、UDP、IPv6、流媒体地区和 iOS 后台行为测试。

## 发布前检查

- [ ] `Surge.conf` 仍使用 `example.invalid` 订阅占位符
- [ ] 真实订阅、节点和令牌没有进入公开目录
- [ ] `NodePool` 仍为可见 `select`，首个成员为 `Fail-Closed`
- [ ] 只有 `NodePool` 持有 `policy-path`
- [ ] `Proxy` 与可见 `UDP` 仍默认使用 `AllServer`/`Proxy` 主链路
- [ ] `AllServer` 与五个地区组仍为 `smart`，没有无效 `interval` 或 `tolerance`
- [ ] `ApplePush` 仍隐藏，`AdBlock`、`Security`、`UDP` 和 `Domestic` 仍可见
- [ ] `Domestic` 成员顺序仍为 `DIRECT`、`Proxy`
- [ ] `ApplePush` 成员顺序仍为 `Proxy`、`DIRECT`
- [ ] Telegram 和 `Final` 没有 `DIRECT` 成员
- [ ] `wifi-assist=false`，本机 Wi-Fi、热点和 Web 入口仍关闭
- [ ] 双明文 DNS、双 DoH、两个 Host 引导和证书校验保持正确
- [ ] STUN 位于公网 DNS 端口与公网规则之前
- [ ] 公网 53、853 和 8853 端口在局域网规则之后拒绝
- [ ] `captive.apple.com` 与 `configuration.ls.apple.com` 精确直连，宽泛后缀没有恢复
- [ ] Pegasus 与 Ads 都从本仓库固定提交加载
- [ ] 主配置没有 Pegasus 域名、Ads 明细或其他内嵌规则快照
- [ ] 原 30 个运行 URL 全部保留并固定到 `d1d714d575d5494ef1a7613238f4f301e1b293df`
- [ ] 3 个动态运行 URL 与更新间隔精确匹配审阅清单
- [ ] 28 个 `RULE-SET` 全部带 `no-resolve`
- [ ] Bilibili 国际版、Viu、YouTube、Microsoft 和 Game 的专用顺序保持正确
- [ ] 12 个共享云后缀位于动态国内补充和 China 之前并进入 `Domestic`
- [ ] Global、CN GeoIP、公网 IPv4/IPv6 与唯一 `FINAL` 顺序正确
- [ ] 33 个远程资源、30 个本地规则文件、34 个策略组和 130 条规则通过审计
- [ ] 110 项配置测试、26 项 ZIP 测试和 15 项发布清单测试通过
- [ ] `RELEASE_MANIFEST.txt` 与两份 SHA-256 清单已经刷新
- [ ] 完整 ZIP 已重新生成两次并确认字节一致
- [ ] 整包 SHA-256 已在 ZIP 外记录

## 资料与许可证

配置结构和策略组选型参考 Surge 官方资料与多个公开配置。服务规则的固定输入以 [Rules/upstreams.lock.json](./Rules/upstreams.lock.json) 为准，Pegasus 来源以 [Rules/resources.lock.json](./Rules/resources.lock.json) 为准，其余仓库维护列表的来源状态与许可披露以 [Rules/maintained_sources.lock.json](./Rules/maintained_sources.lock.json) 为准。设备不会直接访问固定维护输入地址，但会访问明确列出的三个 Sukka 动态运行 URL。

Surge 官方资料

- [Surge 规则系统](https://manual.nssurge.com/rules/overview.html)
- [Rule Set](https://manual.nssurge.com/rules/ruleset.html)
- [策略组引用](https://manual.nssurge.com/policy-groups/policy-including.html)
- [Smart Group](https://manual.nssurge.com/policy-groups/smart.html)
- [策略组通用参数](https://manual.nssurge.com/policy-groups/parameters.html)
- [自动策略组测试](https://kb.nssurge.com/surge-knowledge-base/technotes/testing-group)
- [Module 优先级与插入规则](https://manual.nssurge.com/profile/module.html)

参考配置

- [Rabbit-Spec Surge Developer](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-Developer.conf)
- [Rabbit-Spec Surge EN](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-EN.conf)
- [As-Lucky Lucky](https://raw.githubusercontent.com/As-Lucky/Lucky/main/Lucky-Surge.conf)
- [Coldvvater Surge 配置](https://gist.githubusercontent.com/Coldvvater/8093bc6be4340b5324b4a343493becfe/raw/Surge,conf)
- [TutuBetterRules Surge](https://github.com/bunizao/TutuBetterRules/blob/tutu/Surge/Surge.conf)
- [Aioneas Surge](https://github.com/Aioneas/Surge)
- [Thoseyearsbrian Aegis](https://github.com/Thoseyearsbrian/Aegis)

固定维护输入

- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)，19 份服务规则的固定输入
- [AmnestyTech/investigations](https://github.com/AmnestyTech/investigations)，Pegasus 历史 IOC 的固定输入
- [SukkaW/Surge](https://github.com/SukkaW/Surge)，三份动态补充源及 AGPL-3.0 许可

仓库原创脚本、配置结构和文档使用根目录 [MIT License](./LICENSE)。第三方规则和数据继续遵循各自许可，许可副本位于 [THIRD_PARTY_LICENSES](./THIRD_PARTY_LICENSES)。来源与本地修改范围见 [NOTICE.md](./NOTICE.md)，版本迁移见 [MIGRATION.md](./MIGRATION.md)，完整审计见 [AUDIT_REPORT.md](./AUDIT_REPORT.md)，更新记录见 [CHANGELOG.md](./CHANGELOG.md)。
