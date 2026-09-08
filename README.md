# Surge iOS Privacy + Push R13.23

面向 Surge iOS 的规则模式配置，采用单订阅入口、外部规则快照和分层策略组。日常使用只需填写一处 Surge 格式订阅地址，随后通过策略组选择出口。本文依据当前 [Surge.conf](Surge.conf) 编写，参数含义对照 Surge 官方手册。

| 项目 | 当前配置 |
| --- | --- |
| 客户端 | Surge iOS 5.14.6 及以上，建议 5.21.0 及以上 |
| 出站模式 | 规则模式 |
| 主配置 | 142 条分流指令，其中 29 条引用外部规则 |
| 外部规则 | 26 份 RULE-SET、3 份 DOMAIN-SET，无内嵌规则列表 |
| 策略组 | 共 40 个，29 个可见、11 个隐藏 |
| 节点来源 | 隐藏的 桔子 组，唯一 `policy-path` |
| 自动选点 | Smart、五个地区测速源和地区回退 |
| 配置内代理 | 仅有本机 Fail-Closed 哨兵，不含私人节点 |
| HTTPS 解密 | 主配置未配置 MITM、重写或脚本 |

建议使用 5.21.0 及以上版本，是因为这一版本起 Smart 会将 UDP 响应和静默转发失败纳入节点评价。配置检查不等同于全部客户端版本的实机认证。[Smart 官方说明](https://manual.nssurge.com/policy-groups/smart.html)

## 安装与升级

1. 先备份手机上正在使用的配置，保存当前有效的订阅地址和自行安装的模块。
2. 在 Surge 中通过 URL 导入 [Surge.conf](https://raw.githubusercontent.com/shenjlngbIng/surge/main/Surge.conf)。该链接是公共模板，不含可用节点凭据。
3. 在文本配置中搜索 `桔子 =`，仅将这一行的完整占位 URL 替换为自己的 Surge 格式订阅地址。
4. 保存后加载订阅与外部规则，确认 桔子 已获得节点，NodePool 能列出真实节点。
5. 启用规则模式。首次使用时，Proxy 默认选择 Auto；需要固定节点时，在 NodePool 中选择真实节点，再将 Proxy 切换到 NodePool。

唯一订阅入口如下，保留其余参数即可。

```ini
桔子 = select, REJECT, policy-path=https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL, update-interval=3600, external-policy-modifier="udp-relay=true", hidden=1
```

订阅应返回 Surge 代理定义，或包含有效 `[Proxy]` 段的完整 Surge 配置。网页、错误提示和其他客户端格式均不能直接作为这里的节点来源。订阅刷新间隔设置为 3600 秒，实际下载还受客户端调度和缓存影响。[策略导入说明](https://manual.nssurge.com/policy-groups/policy-including.html)

使用本机 Sub-Store 时，继续保留已经可用的模块和导出地址。`[Host]` 中的 `sub.store = 127.0.0.1` 是本机入口映射，本文件不会安装或启动 Sub-Store，也不提供后端。自建后端使用自己的实际域名时，不受这条映射影响。

升级主配置后仍需填回私人订阅，不能用公开模板覆盖后直接获得节点。只更新“外部资源”也不会升级主配置。设备可能保留以前的策略选择，应检查 Proxy、NodePool 及曾经手动修改的选项。[升级说明](MIGRATION.md)

## 策略组与选择方法

### 总出口和节点来源

| 策略组 | 类型 | 用途 |
| --- | --- | --- |
| Final | select | 末尾 FINAL 规则的出口，默认 Proxy，可手动选 DIRECT |
| Proxy | select | 主要代理出口，默认 Auto，可选节点池或五个地区 |
| NodePool | select | 列出订阅节点供手动选择，默认 Auto |
| Auto | smart | 根据连接表现选择代理，保留 Fail-Closed 哨兵 |
| HongKong、TaiWan、Japan、Singapore、America | fallback | 优先相应地区的测速组，失效后回退 Auto |
| 桔子 | select，隐藏 | 唯一订阅源，仅向其他组提供成员 |
| 五个 `地区-Nodes` 组 | url-test，隐藏 | 按节点名称筛选地区，设置 600 秒间隔和 100 ms 切换容差 |
| ApplePush | fallback，隐藏 | 依次尝试 Proxy、Auto、DIRECT，间隔设置为 60 秒 |

地区筛选依赖节点名称中的中文、英文、旗帜或地区缩写。名称识别无法核实服务器真实地理位置。地区组允许回退 Auto，因此不能保证账号或流媒体请求始终从指定地区出站。需要固定出口时，选择明确的真实节点，并检查该服务组的当前选项。

Smart 的展示节点用于反映近期使用情况，不保证所有连接都使用同一节点。地区测速组的间隔参数也不代表后台持续每隔 600 秒发起测试，测试触发受使用、网络变化及客户端行为影响。[Smart](https://manual.nssurge.com/policy-groups/smart.html)、[自动测速组](https://manual.nssurge.com/policy-groups/url-test.html)

Final 只处理到达末尾的请求。已命中服务规则、UDP 规则或公共 IP 规则的请求不会再进入 Final。将 Final 改为 DIRECT 不会把整份配置切成全局直连。

### 服务分组

以下为新配置的初始选择。手动选项和设备保存的状态可能覆盖初始选择。

| 策略组 | 主要外部规则 | 初始选择 |
| --- | --- | --- |
| ChatGPT | ChatGPT.list | Proxy |
| Claude | Claude.list | Proxy |
| Gemini | Gemini.list | Proxy |
| GitHub | Github.list | Proxy |
| YouTube | YouTube.list | Proxy |
| NETFLIX | Netflix.list | Proxy |
| Disney+ | Disney.list | Proxy |
| HBO | HBO.list | Proxy |
| PrimeVideo | PrimeVideo.list | Proxy |
| Emby | Emby.list | Proxy |
| TikTok | TikTok.list | Proxy |
| Bahamut | Bahamut.list | TaiWan |
| Spotify | Spotify.list | Proxy |
| Streaming | ProxyMedia.list 及前置流媒体例外 | Proxy |
| Telegram | Telegram.list | Proxy |
| X | Twitter.list | Proxy |
| Apple | AppleCN.list | DIRECT |
| Google | Google.list 及共享资源例外 | Proxy |
| Microsoft | Microsoft.list、OneDrive.list 及公共登录例外 | Proxy |
| Games | Game.list | Proxy |

国内 BiliBili、WeChat 和 Direct 规则固定为 DIRECT，没有额外创建控制组。BiliBili 国际站的兼容域名在前面单独转到 Proxy。服务组选择节点只决定出口，不能保证服务解锁、账号地区或订阅权益。

### 隐藏辅助组

| 策略组 | 控制范围 | 初始选择 |
| --- | --- | --- |
| AdBlock | Ads.list 匹配的广告请求 | REJECT |
| Security | Pegasus.list 历史风险域名 | REJECT |
| Domestic | China.list 与 CN GeoIP 兜底 | DIRECT |
| UDP | STUN 与未命中前置规则的其他 UDP | Proxy |

四个组通过 `hidden=1` 隐藏，分流和选项仍有效。需要显示时，可删除对应组的 `hidden=1` 或改为 `hidden=0`。REJECT 与 REJECT-DROP 的用途是拒绝连接，测速显示失败属于正常表现。[策略组参数](https://manual.nssurge.com/policy-groups/parameters.html)

## 哨兵保护及其边界

`Fail-Closed` 是指向 `127.0.0.1:1` 的本机 HTTP 代理项，预期不可连接。`no-error-alert=true` 仅抑制该项的错误提醒，不会让它变成可用代理，也不会隐藏所有诊断结果。

当前保护关系如下。

| 位置 | 保护方式 |
| --- | --- |
| 桔子 | 显式保留 REJECT，空订阅时仍有成员 |
| Auto | 保留代理类型的 Fail-Closed，防止空 Smart 被替换为 DIRECT |
| NodePool | 默认 Auto，过滤从订阅源导入的 REJECT 占位 |
| 地区测速源 | 显式保留 REJECT，外层地区组可回退 Auto |

Smart 会忽略内置策略和嵌套组，因而不能仅靠向 Smart 填入 REJECT 代替这个代理类型哨兵。订阅成员通过 `include-other-group` 导入，保留原有真实节点。[Smart](https://manual.nssurge.com/policy-groups/smart.html)、[组成员导入](https://manual.nssurge.com/policy-groups/policy-including.html)

这些设置保护应走代理的流量。国内与局域网直连、Apple 默认直连、APNs 的 DIRECT 回退，以及用户手动选择的 DIRECT 仍然存在。配置未实现系统级全局断网开关，配置加载失败、VPN 被关闭或设备系统异常也不属于离线模型的保证范围。

## 分流顺序与保留的例外

规则按从上到下首次匹配生效，调整顺序可能改变出口。当前主配置按以下顺序组织。

| 顺序 | 处理内容 |
| --- | --- |
| 1 | 本地发现放行，其他组播与广播拒绝，局域网和门户检测直连 |
| 2 | STUN 进入 UDP 组，GitHub raw 使用 Auto，jsDelivr 使用 Proxy |
| 3 | 国内 DNS 例外、53 端口拒绝、境外加密 DNS 例外、853/8853 拒绝，随后处理定位引导与出口检测 |
| 4 | Pegasus、APNs、Apple 流媒体例外、AppleCN、WeChat、Direct |
| 5 | 功能域名及 BiliBili 国际站例外优先，随后匹配广告规则 |
| 6 | AI、共享 Google 资源、视频与音频服务 |
| 7 | 社交、开发、Google、Microsoft 公共端点、游戏、OneDrive 和 Microsoft |
| 8 | 国内云服务固定直连，China 和 Global 域名兜底 |
| 9 | CN GeoIP、剩余 UDP、双栈公共 IP、FINAL 依次兜底 |

主配置中的少量独立指令用于前置处理、冲突例外和最终兜底。29 份规则列表仍从外部加载，未复制到主配置中。

以下几类看似重复的内容有不同用途，因此继续保留。

| 内容 | 保留原因 |
| --- | --- |
| BiliBili 国际站域名 | 避免被国内 biliapi.net 后缀或旧流媒体规则接管 |
| Apple 流媒体、Viu 例外 | 避免被 AppleCN 和 HBO 中的宽泛父域名提前匹配 |
| Spotify、BiliBili、Google 和 ChatGPT 功能域名 | 在广告规则前保留已核对的功能请求 |
| Microsoft 登录与商店端点 | 避免公共服务被游戏规则归入 Games |
| `skip-proxy` 与局域网 DIRECT 规则 | 分别影响系统代理接管和最终出站策略，不能互相替代 |
| STUN 与尾部 UDP 规则 | 前者优先处理 STUN，后者保留业务和国内规则的优先级 |

## DNS、接管范围与隐私

Surge 自身使用 AliDNS 和 DNSPod 的独立直连 DoH，保留证书校验。`encrypted-dns-follow-outbound-mode=false` 避免节点域名解析反过来依赖代理。传统 DNS 主要承担加密 DNS 域名引导和连通性检测，不能因此宣称所有 DNS 数据包都经过加密。[加密 DNS](https://manual.nssurge.com/dns/encrypted-dns.html)

| 设置 | 当前作用 |
| --- | --- |
| `hijack-dns = *:53` | 接管经过 Surge 的普通 DNS 查询 |
| `allow-dns-svcb = false` | 保持虚拟 IP 所需的解析行为 |
| `use-local-host-item-for-proxy = false` | 代理请求不因本地 Host 映射而统一改成 IP 连接 |
| 已列出的国内应用 DNS 域名 | 保留前置 Proxy 例外 |
| 已列出的境外应用 DNS 域名 | 443、853、8853 端口使用 Proxy，53 端口仍拒绝 |
| 53、853、8853 端口规则 | 拒绝到达这些规则的剩余流量，保留前置例外 |
| `no-resolve` | IP 类规则不为匹配而额外触发本地解析 |

这些规则处理 Surge 能识别目标域名的应用请求。境外端点例外位于 53 端口拒绝之后、853/8853 拒绝之前，避免加密 DNS 被端口规则提前拦截，同时保留原有明文 DNS 限制。应用直接访问公共 IP 且无法识别域名时，不会自动获得域名例外。规则放行也不代表每家服务商都提供全部端口。[规则顺序](https://manual.nssurge.com/rules/overview.html)、[Google DoT](https://developers.google.com/speed/public-dns/docs/dns-over-tls)

应用自行访问的未知 HTTPS DNS 端点无法仅靠有限域名列表全部识别。检测网站显示的 DNS 运营商也不保证与代理出口一致。当前方案优先保证独立解析和代理启动，不承诺“零 DNS 泄漏”或检测页面全绿。

`include-all-networks=true` 与 `include-apns=true` 保留较广的接管范围；局域网和蜂窝服务扩展接管仍关闭。这可能影响 AirDrop、Xcode 或 USB 控制台。`icmp-forwarding=false` 禁止直接转发 ICMP，因而 ping 失败不能单独证明代理不可用。[全局参数](https://manual.nssurge.com/profile/general.html)

## Telegram 后台推送

Telegram 应用数据由 Telegram 组处理，iOS 的系统推送连接由 ApplePush 组处理。两条路径都需要检查。ApplePush 隐藏只影响卡片显示，APNs 外部规则仍先于 AppleCN 生效。

本版 ApplePush 按 `Proxy → Auto → DIRECT` 选择出口。手动选中的 Proxy 节点被判定不可用时，先通过 Auto 尝试其他节点；代理全部不可用时保留直连，以兼顾其他应用通知。fallback 依据通用连通性测试选择出口，测试成功不能证明 APNs 或 Telegram 通知一定送达；直连回退也可能无法恢复海外应用推送。[Fallback](https://manual.nssurge.com/policy-groups/fallback.html)

`include-apns=true` 必须配合 `include-all-networks=true`。事件中的“包含所有网络请求已开启”是兼容性警告，关闭该项会同时影响 APNs 接管。两项继续保留，也不关闭警告日志。[接管参数](https://manual.nssurge.com/profile/general.html)

APNs.list 覆盖 Apple 公布的 5 个 IPv4、4 个 IPv6 网段以及推送域名。未把整个 Apple、akadns.net 或 Apple 的共享 CDN 归入推送组。参考方案里的 identity.apple.com 是证书申请门户，缺少证据时不将其当作普通通知连接的必需修正。[Apple 推送网络范围](https://support.apple.com/en-us/102266)、[Apple 企业网络服务](https://support.apple.com/en-us/101555)

升级后先确认真实节点可用、APNs.list 已加载，再开关一次飞行模式并恢复 Surge，促使系统推送长连接重新建立。保持 Telegram 通知权限开启、关闭会静音通知的专注模式，分别在 Wi-Fi 和蜂窝网络下锁屏，让另一账号发送新消息。旧连接不会仅因下载了新配置就必然迁移。[APNs 长连接说明](https://support.apple.com/en-us/102266)

验收时查看请求中的 ApplePush 命中及实际出口，并确认 Telegram 通知到达。APNs 是系统共享连接，本配置不能仅代理 Telegram 的系统通知。不要把普通节点测速或一条警告消失当作推送验收结果。

## UDP 与 QUIC

| 设置 | 含义 |
| --- | --- |
| `external-policy-modifier="udp-relay=true"` | 在导入订阅时启用需要该开关的协议的 UDP 转发 |
| `udp-policy-not-supported-behaviour=REJECT` | 所选策略不支持 UDP 时拒绝，不自动改成直连 |
| `block-quic=per-policy` | QUIC 是否放行由节点自身设置决定 |
| `proxy-test-udp=apple.com@1.1.1.1` | 通过节点向指定 DNS 服务器查询，用于 UDP 测试 |

UDP 仍依赖节点协议、服务端能力和链路状态。Shadowsocks 与 SOCKS5 需要客户端开关及服务端支持；普通 HTTP/HTTPS 代理不支持 UDP。订阅声明单独 UDP 端口时应保留服务商给出的值，本配置不猜测端口。[UDP 转发](https://manual.nssurge.com/policies/udp.html)

普通延迟测试只验证 TCP 路径。诊断页若只有 Fail-Closed 报错、UDP 区域为空，就没有给出真实订阅节点的 UDP 结果。定位故障需要真实节点的 UDP 测试或连接日志；不能用哨兵报错、普通测速或空白栏目替代。

## 外部资源与更新

运行时共有 29 份规则和 1 个 桔子 订阅资源。规则使用本仓库 [固定提交](https://github.com/shenjlngbIng/surge/tree/6e8e1bfbbdda66ee8ad0a5ad3979b6de8b5b7a51/Rules) 的 GitHub raw URL，快照日期为 2026-09-08。R13.23 沿用 R13.21 的全部规则文件与固定地址。没有使用 jsDelivr 下载规则；配置中的 jsDelivr 域名规则仅保留普通访问分流。

GitHub raw 的前置规则改用现有 Auto，避免 Proxy 手选坏节点时一起阻断规则下载，不增加新的策略组或下载脚本。该规则只对经过当前配置规则系统的请求生效，首次导入、Surge 未开启或全局直连模式不受它保证。Auto 若被临时手动固定到坏节点，也需先取消覆盖。[Smart 与临时覆盖](https://manual.nssurge.com/policy-groups/smart.html)

首次导入仍需要一条可工作的下载路径。保留旧的可用配置和已缓存资源，先加载订阅并确认 Auto 有健康节点，再启用新配置、更新失败的规则。不要清空缓存或反复重装。当前事件里出现过“加载失败”时，应以外部资源页的现状、重新更新后的时间和详细错误判断；历史事件不会因后来下载成功而自动变成成功记录。

规则的 `update-interval=-1` 禁止定期刷新，客户端会缓存已下载资源。手动更新同一固定 URL 仍得到同一份快照。上游变化需要维护者复核并发布新快照，再升级主配置才能采用。[外部规则参数](https://manual.nssurge.com/rules/ruleset.html)

Pegasus 是历史 IOC，Ads 是固定广告规则快照，两者均不能替代持续更新的安全产品，也无法保证拦截同域广告或所有恶意请求。来源、许可证及历史输入限制见 [NOTICE.md](NOTICE.md)。

## 常见问题

| 现象 | 如何判断与处理 |
| --- | --- |
| 桔子 返回 HTTP 500 | 检查 Sub-Store 或订阅服务的响应；修改分流注释无法修复服务端错误 |
| 规则资源加载失败或超时 | 确认规则模式及 Auto 有健康节点、无临时手动覆盖；再更新失败资源。仍失败时检查资源页的具体 HTTP、DNS、TLS 或超时信息 |
| Telegram 前台正常、锁屏无推送 | 确认 APNs.list 已加载，检查 ApplePush 实际出口，重建系统推送连接并发送新消息验证 |
| 包含所有网络请求警告 | APNs 接管依赖此项；保留警告和开关，了解 AirDrop/Xcode 兼容性代价 |
| 某个地区没有节点 | 检查订阅节点名称是否匹配地区；地区组可能回退 Auto |
| Fail-Closed 或 REJECT 显示失败 | 属于保护项的预期结果，继续检查真实节点 |
| 真实节点测速全部失败 | 检查订阅更新、节点连接错误和测试地址，不以规则数目判断可用性 |
| TCP 有延迟，UDP 无结果 | 分别验证真实节点的 UDP 服务及转发日志 |
| 服务切换地区后仍不符合预期 | 检查该服务组、地区回退、节点实际出口，以及账号和服务限制 |
| 辅助组看不到 | 四个控制组已隐藏，可在文本中调整对应 hidden 参数 |
| 升级后没有生效 | 确认启用的是新主配置；外部资源更新不替换旧主配置 |
| 国内流量仍直连 | 属于国内、局域网和明确直连例外的设计行为 |

## R13.23 推送与规则下载恢复

- ApplePush 在 Proxy 和 DIRECT 之间增加 Auto，手选节点失效时先尝试其他代理。
- GitHub raw 改用 Auto，规则下载不再跟随 Proxy 的手动节点选择。
- 补充 APNs 域名、IP 边界、Telegram、下载分流和失效恢复测试。29 份外置列表及地址不变，仍保留 40 个组和 142 条分流指令。

### 沿用 R13.22 的订阅源简称

订阅源从 `Subscription` 改为 `桔子`，节点池、Auto 和五个地区源的 7 处引用已同步修改。仅缩短名称，订阅地址、更新间隔、节点筛选、隐藏设置及分流行为不变。

### 沿用 R13.21 的修正

- 从 Ads 删除 8 条会匹配正常业务网站的关键词，来源标记改为注释。活动条目从 152 降为 143，保留细分广告和跟踪匹配，不新增整站放行规则。
- 将境外 DNS 域名例外移到 853/8853 拒绝之前，保留 53 端口限制。主配置仍为 142 条指令，不添加复杂逻辑规则。
- 新增正常网站、广告和 DNS 端口正反例，并验证恢复旧规则时测试能够报错。

地区组仍允许回退 Auto，服务组的默认出口保持不变。共享的 Cloudflare 验证、Stripe 和 WorkOS 域名仍归入 ChatGPT；手动拆分服务出口时，应同时确认这些共享依赖的出口。此次不更改区域策略或删除登录依赖。

### 沿用 R13.20 的精简

| 删除内容 | 数量 | 行为依据 |
| --- | --- | --- |
| `no-alert=0` | 40 处 | 默认 false；select 和 smart 不发送该类切换通知 |
| `hidden=0` | 29 处 | 默认可见，保留需要隐藏的 11 处 hidden=1 |
| `include-all-proxies=0` | 34 处 | 默认不导入全部本地代理，原有成员和订阅引用不变 |
| 默认全局设置 | 8 项 | 采用官方默认值，列表见下文 |
| DNS 精确域名规则 | 2 条 | 由同出口后缀规则完整覆盖 |

省略的全局设置为 `auto-suspend=true`、`wifi-assist=false`、`all-hybrid=false`、`show-error-page-for-reject=false`、`disable-geoip-db-auto-update=false`、`http-api-web-dashboard=false`、`proxy-restricted-to-lan=true` 和 `gateway-restricted-to-lan=true`。其中 auto-suspend 表示发现 Surge Mac 网关接管时自动暂停；代理与网关的局域网限制仍采用默认开启状态。[全局默认值](https://manual.nssurge.com/profile/general.html)

删去的 `dns.alidns.com` 与 `dns.nextdns.io` 精确规则分别由 `alidns.com` 和 `nextdns.io` 的 DOMAIN-SUFFIX 规则覆盖，两者继续使用 Proxy。保留完整节点池、40 个策略组、29 份外部规则、UDP 参数和哨兵。完整变更见 [CHANGELOG.md](CHANGELOG.md)。

## 验证与维护

本版检查涵盖 107 项配置故障注入、原有广告及 DNS 测试，以及新增的 27 个推送和下载域名案例、79 个 IP/端口案例、6 个推送 SNI 案例、11 项交付路径检查和 7 个退化案例。地区筛选、空订阅、全部失效和手动选择模型继续保留。执行结果与验证边界见 [AUDIT_REPORT.md](AUDIT_REPORT.md)。

```bash
python3 tools/convert_to_remote_rules.py
python3 tools/audit_config.py
python3 tools/audit_rules.py --check-runtime-remote
python3 tools/audit_precise_domains.py
python3 tools/test_runtime_rules.py
python3 tools/test_policy_failover.py
python3 tools/test_audit_config.py
```

运行环境没有 iOS Surge 内核，也未连接私人代理。上述结果不证明设备上的 UDP 转发、流媒体解锁或 DNS 检测一定成功。公开仓库不得存放私人订阅、节点密码或未经脱敏的日志。
