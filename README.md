# Surge iOS Privacy + Push

适用于 Surge iOS 规则模式的个人配置模板。使用单一订阅入口、固定版本外部规则和分层策略组，为日常代理、地区受限服务、国内直连及系统推送提供明确的出站路径。

**当前版本：R13.25 · 更新日期：2026-09-09。** 公共模板不包含可用节点，只需在“桔子”组填入自己的 Surge 格式订阅地址。

[导入主配置](https://raw.githubusercontent.com/shenjlngbIng/surge/main/Surge.conf) · [升级说明](MIGRATION.md) · [检查报告](AUDIT_REPORT.md) · [更新日志](CHANGELOG.md) · [维护说明](CONTRIBUTING.md)

## 1. 配置概览

| 项目 | 当前实现 |
| --- | --- |
| 使用环境 | Surge iOS 5.14.6+，建议 5.21.0+；采用规则模式 |
| 策略组 | 41 个，30 个可见、11 个隐藏 |
| 服务选点 | 19 个服务组采用自动测速，其中 10 个限制地区候选；Apple 保留默认直连 |
| 自动策略 | Fast 按测试延迟选点；Auto 保留 Smart；两者均有 Fail-Closed |
| 主规则 | 157 条，其中 29 条引用外部规则 |
| 外部规则 | 26 份 RULE-SET、3 份 DOMAIN-SET，共 5,537 条有效内容；不内嵌列表 |
| 节点来源 | “桔子”组中的唯一 `policy-path`，刷新间隔设置为 3,600 秒 |
| DNS | AliDNS 与 DNSPod 独立直连 DoH，保留证书校验与必要引导 |
| 系统推送 | APNs 独立使用 ApplePush，保留代理备用与直连回退 |
| UDP/QUIC | 导入节点启用 UDP 中继；不支持 UDP 时拒绝；QUIC 按节点设置处理 |
| 解密与脚本 | 主配置不配置 MITM、重写或脚本；不安装 Sub-Store 模块 |

配置面向 iOS，未声明所有客户端版本均通过真机认证。建议使用 5.21.0+，是因为该版本起 Smart 纳入 UDP 响应等评价信息。[Surge Smart 文档](https://manual.nssurge.com/policy-groups/smart.html)

## 2. 安装与升级

1. 保留手机上仍可使用的配置、私人订阅地址及外部资源缓存。
2. 在 Surge 中通过 [主配置 URL](https://raw.githubusercontent.com/shenjlngbIng/surge/main/Surge.conf) 导入模板，确认顶部版本为 R13.25。
3. 搜索 `桔子 =`，将 `policy-path=` 后的完整占位地址替换成自己的 Surge 格式订阅地址，其余参数保留。
4. 更新订阅，确认 NodePool 能列出真实节点，Auto/Fast 有可用节点；随后确认 29 份外部规则均已加载。
5. 启用规则模式，选择 `Final → Proxy`、`Proxy → Fast`。设备可能保留以前的手动选择，不能仅凭文件中的排列顺序判断当前选项。
6. 取消自动组遗留的临时手动覆盖，完成一轮测速，再通过新的服务请求核对实际出口。

唯一订阅入口如下：

```ini
桔子 = select, REJECT, policy-path=https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL, update-interval=3600, external-policy-modifier="udp-relay=true,test-url=http://cp.cloudflare.com/generate_204,test-timeout=5", hidden=1
```

订阅须返回 Surge 代理定义，或包含有效 `[Proxy]` 段的完整 Surge 配置。其他客户端格式、网页和错误响应不能直接作为节点来源。导入参数统一覆盖节点的测试地址、测试超时和 UDP 中继开关，避免每个节点采用不同测试条件。[策略导入格式及参数](https://manual.nssurge.com/policy-groups/policy-including.html)

使用 Sub-Store 时继续使用已经可用的模块及导出 URL。`sub.store = 127.0.0.1` 只是本机入口映射；本配置不会启动后端、修复订阅服务的 HTTP 500，或把其他格式自动转换成 Surge。

公共主配置更新后，私人订阅地址可能需要重新填回。只更新“外部资源”不会升级主配置；不要用清空缓存代替检查订阅和下载路径。更详细的版本差异见 [MIGRATION.md](MIGRATION.md)。

## 3. 策略结构

### 3.1 总出口与节点来源

| 策略组 | 类型 | 成员及用途 |
| --- | --- | --- |
| Final | select | 末尾 FINAL 的出口，默认 Proxy，可选 DIRECT |
| Proxy | select | 默认 Fast；可选 Auto、NodePool 和五个通用地区入口 |
| Fast | url-test | 在全订阅节点中选择最近一轮测试的最低有效延迟 |
| Auto | smart | 根据连接表现和历史信息智能选点，保留原设计 |
| NodePool | select | 完整手动节点池，默认 Auto，可固定真实节点 |
| 桔子 | select，隐藏 | 唯一订阅来源；显式保留 REJECT，不作为业务出口 |
| HongKong-Nodes、TaiWan-Nodes、Japan-Nodes、Singapore-Nodes、America-Nodes | url-test，隐藏 | 严格地区节点源；只接受匹配名称的节点，空池保留 REJECT |
| HongKong、TaiWan、Japan、Singapore、America | fallback | 通用地区入口；依次尝试相应地区源、Auto，允许跨区回退 |

服务组直接复制严格地区源中的节点，在合并后的候选集合中测速。它们不继承外层地区入口的 Auto 回退，因此“通用地区优先”和“服务地区限制”是两种不同用途。

修改 Proxy 不会覆盖独立服务组的选点。Final 也只影响到达末尾 FINAL 的请求，不能把已经命中服务、国内或 UDP 规则的流量重新路由。需要固定某项服务时，应在该服务组内临时选择合格节点，使用后取消覆盖恢复自动模式。

### 3.2 服务与地区候选

下表中的地区仅指本配置已有的香港、台湾、日本、新加坡、美国五类节点。它是与官方服务范围相交后的配置范围，不代表服务商完整的世界地区清单。英国、德国等未建立分类的节点仍可进入全订阅组，不会自动进入地区受限服务。

| 服务组 | 主要规则 | 自动候选范围与依据 |
| --- | --- | --- |
| ChatGPT | ChatGPT.list | 美国、日本、新加坡、台湾；四地均在[官方支持名单](https://help.openai.com/en/articles/7947663-chatgpt-supported-countries)内，香港不在 |
| Claude | Claude.list | 美国、日本、新加坡、台湾；按 [Claude 官方地区](https://support.claude.com/en/articles/8461763-where-can-i-access-claude)筛选 |
| Gemini | Gemini.list | 美国、日本、新加坡、台湾；规则同时覆盖网页与 AI Studio/API，采用 [API 地区范围](https://ai.google.dev/gemini-api/docs/available-regions) |
| GitHub | Github.list | 全订阅节点 |
| YouTube | YouTube.list | 全订阅节点；付费套餐及特定内容的地区要求另行判断 |
| NETFLIX | Netflix.list | 香港、台湾、日本、新加坡、美国；[服务覆盖](https://help.netflix.com/en/node/14164)不代表片库一致 |
| Disney+ | Disney.list | 香港、台湾、日本、新加坡、美国；相关亚洲市场见[官方公告](https://press.disneyplus.com/news/espn-on-disneyplus-global) |
| HBO | HBO.list | 美国、新加坡、香港、台湾；按 [HBO Max 独立服务范围](https://help.hbomax.com/us-en/Answer/Detail/000002518)处理，不纳入日本 |
| PrimeVideo | PrimeVideo.list | 香港、台湾、日本、新加坡、美国；账号、订阅及[旅行片库](https://www.primevideo.com/help?nodeId=GJ2P83PMNC54XKV9)可能另有限制 |
| Emby | Emby.list | 全订阅节点；实际要求由所用服务器决定 |
| TikTok | TikTok.list | 美国、日本、新加坡、台湾；属于配置采用的保守候选，未取得完整官方出口地区表，不声明为完整官方白名单 |
| Bahamut | Bahamut.list | 仅台湾，延续原来的台湾片库取向；[官方授权页](https://ani.gamer.com.tw/seasonal.php?c=2026_S1)也有港澳内容，并非全站仅支持台湾 |
| Spotify | Spotify.list | 香港、台湾、日本、新加坡、美国；按 [Spotify 可用地区](https://support.spotify.com/us/article/where-spotify-is-available/)处理 |
| Streaming | ProxyMedia.list 及部分独立规则 | 全订阅节点；已核实的地区例外见下一节 |
| Telegram | Telegram.list | 全订阅节点；系统推送由 ApplePush 另行处理 |
| X | Twitter.list | 全订阅节点 |
| Apple | AppleCN.list | 保留 select，默认 DIRECT；可手动调整 |
| Google | Google.list 及共享资源例外 | 全订阅节点；已识别的 Gemini 请求优先进入 Gemini |
| Microsoft | Microsoft.list、OneDrive.list 及登录例外 | 全订阅节点 |
| Games | Game.list | 全订阅节点；不同游戏、账号区服和服务器没有统一地区范围 |

受限服务在候选为空或全部测试失败时连接失败，不把其他地区或 DIRECT 加入备用。例如香港 99 ms、新加坡 122 ms、日本 189 ms 时，ChatGPT 先排除香港，再比较其余合格节点。

地区分类依据节点名称中的地区、城市、旗帜和缩写。本版排除同时匹配多个现有地区标签，或包含中转、转发、箭头标记的名称。合法中转节点也可能被暂时排除；确认实际出口后，应在订阅生成端采用明确的出口地区名称。不能用修改名称代替实际出口验证。

节点名称与 204 测试均不能证明真实出口 IP、服务账号可用性、代理 IP 接受情况或影片授权。TikTok 还可能受账号、SIM 和设备状态影响；HBO GO、HBO Max 与第三方渠道的产品要求也可能不同。地区依据核对于 2026-09-08—09，官方范围变化后需维护配置，Surge 不会自动理解官网并更新名单。

### 3.3 混合流媒体的地区例外

部分平台共处于 ProxyMedia 或 HBO 列表中，不能只给整个列表选择一个国家。本版在远程列表之前加入明确的地区规则：

| 目标范围 | 使用的严格节点源 | 依据 |
| --- | --- | --- |
| hulu.com、hulu.tv、hulu.us、huluim.com、hulustream.com | America-Nodes | [Hulu 美国站国际访问说明](https://help.hulu.com/article/hulu-cant-use-internationally)；不包含 Hulu 日本站 |
| tver.jp、TVer-Release 用户代理匹配 | Japan-Nodes | [TVer 海外访问说明](https://help.tver.jp/hc/ja/articles/5106803908633) |
| now-ashare.com、now-tv.com、now.com、now.com.hk、nowe.com、nowe.hk | HongKong-Nodes | 从 HBO 混合列表分离香港平台；[Now E 官方应用说明](https://play.google.com/store/apps/details?hl=en&id=com.pccw.nowemobile)限定香港 |
| mytvsuper.com、viu.tv、viu.now.com | HongKong-Nodes | 香港服务取向；myTV SUPER 部分计划也覆盖澳门，当前没有澳门地区池。[开发者说明](https://play.google.com/store/apps/details?hl=zh_TW&id=com.tvb.mytvsuper.atv) |

这些例外不允许跨区回退，也不将整个公共 CDN 后缀归入某个国家。用户代理匹配仅在 Surge 能取得相关请求字段时适用。

其他混合平台尚未全部拆分。例如 BBC iPlayer 需要英国地区，而当前没有英国节点池；不同 DAZN 版本、私有 Emby、具体游戏也需要进一步确认产品与服务器要求。未拆分的流媒体仍由 Streaming 自动测速，不标为已完成解锁分类。[BBC 官方说明](https://player.bbc.com/en/help-and-support)

### 3.4 隐藏控制与推送组

| 分组 | 作用 | 默认或回退顺序 |
| --- | --- | --- |
| AdBlock | Ads.list 广告拦截 | REJECT；可选 REJECT-DROP、DIRECT |
| Security | Pegasus.list 历史风险域名 | REJECT；可选 REJECT-DROP、DIRECT |
| Domestic | China.list 与 CN GeoIP 兜底 | DIRECT；可选 Proxy |
| UDP | STUN 与尾部未匹配 UDP | Proxy；可选 NodePool、REJECT、DIRECT |
| ApplePush | APNs 系统推送 | Proxy → Auto → DIRECT；60 秒测试有效期 |

`hidden=1` 只隐藏策略卡片，分流仍然有效。需要显示时修改对应 hidden 参数即可。[策略组通用参数](https://manual.nssurge.com/policy-groups/parameters.html)

## 4. 测速与切换机制

Fast、19 个自动服务组和五个严格地区源均使用以下参数：

| 参数 | 值 | 含义 |
| --- | --- | --- |
| interval | 300 | 结果有效期为 300 秒，过期再次使用或网络变化时触发重测 |
| tolerance | 0 | 按本轮有效成绩选择最低值，取消原 100 ms 的切换门槛 |
| evaluate-before-use | true | 首次使用等待评估，避免直接尝试第一项哨兵 |
| no-alert | true | 不反复通知优选节点变更 |
| 节点 test-url | Cloudflare HTTP 204 | 统一测试目标 |
| 节点 test-timeout | 5 秒 | 单次测试的连接等待上限；不同于组级 timeout 分数过滤 |

url-test 使用指定 URL 的 HTTP 请求衡量延迟。重测不是固定后台定时任务；未完成新一轮评估时仍可能看到旧结果。临时手动覆盖也会改变自动行为。当前版本的旧组参数 `url=` 不生效，不应把填写服务首页当成解锁检测。[Surge 自动测试组](https://manual.nssurge.com/policy-groups/url-test.html)

Auto 保留 Smart，评价依据包含真实连接质量与历史表现，界面上的“经常使用”“偶尔使用”不代表所有请求固定经过同一节点。Smart 也不负责识别服务地区锁。[Smart 使用说明](https://kb.nssurge.com/surge-knowledge-base/zh/guidelines/smart-group)

因此，“有更低延迟但未切换”应分别检查组类型、是否完成同一轮测试、容差和临时覆盖。原 211 ms 与 189 ms 仅差 22 ms，原 100 ms 容差足以使其不切换；本版 url-test 已改为 0。最低测试延迟不代表最大带宽、最佳 UDP 或账号可用性，频繁跨节点切换还可能改变出口 IP。需要稳定会话时，可临时固定服务组内的合格节点。

参考过 [Rabbit](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-EN.conf)、[Coldvvater](https://gist.githubusercontent.com/Coldvvater/8093bc6be4340b5324b4a343493becfe/raw/Surge,conf)、[Lucky](https://raw.githubusercontent.com/As-Lucky/Lucky/main/Lucky-Surge.conf) 和 [Aegis](https://raw.githubusercontent.com/Thoseyearsbrian/Aegis/main/config/Aegis_CN.conf)。前两者及 Aegis 使用地区 Smart；Lucky 提供 url-test，但未显式指定容差。本配置保留 Smart，并为此次最低延迟偏好显式配置零容差；宽泛单字正则和未经核实的服务地区选项没有直接照搬。

## 5. Fail-Closed 保护

```ini
Fail-Closed = http, 127.0.0.1, 1, no-error-alert=true
```

这是有意设置、预期不可连接的本机 HTTP 代理哨兵。测速显示失败符合设计，`no-error-alert=true` 只抑制该代理的错误提醒。

| 位置 | 空池保护 |
| --- | --- |
| 桔子 | 显式 REJECT，使空订阅源仍有成员 |
| Auto | 代理类型的 Fail-Closed；Smart 会忽略内置拒绝策略，不能直接用 REJECT 替代 |
| Fast 与 19 个服务自动组 | 显式 Fail-Closed，首次使用前评估；导入过滤不删除这个显式成员 |
| 五个严格地区源 | 显式 REJECT，不把空池变成直连 |
| NodePool | 默认 Auto，过滤复制过来的 REJECT 占位 |

保护的目标是避免应代理的自动组依赖空组替代行为。[Smart 成员限制](https://manual.nssurge.com/policy-groups/smart.html)、[空组行为](https://manual.nssurge.com/policy-groups/overview.html)

国内、局域网、Apple 默认直连、ApplePush 的直连备用和手动选择 DIRECT 仍存在；VPN 关闭、配置加载失败等也不属于这些组的保护范围。因此本配置不是系统级全局断网开关。

## 6. 分流顺序

Surge 按首次匹配确定策略。当前有效规则分为以下阶段：

| 顺序 | 处理内容 |
| --- | --- |
| 1 | 本地发现、组播/广播、局域网、门户检测 |
| 2 | STUN、GitHub raw 与 jsDelivr 下载路径 |
| 3 | 国内应用 DNS 例外、53 拒绝、境外加密 DNS 例外、853/8853 拒绝 |
| 4 | Apple 定位引导、出口检测、Pegasus、APNs |
| 5 | Apple 流媒体例外、AppleCN、WeChat、Direct |
| 6 | 功能域名与 BiliBili 国际站例外，随后广告规则 |
| 7 | AI、Google 共享资源、流媒体地区例外、影音服务 |
| 8 | 社交、开发、Google、微软公共登录、游戏、OneDrive 与 Microsoft |
| 9 | 国内云服务、China、Global、CN GeoIP |
| 10 | 剩余 UDP、双栈公共 IP、FINAL |

少量前置域名用于解决实际重叠：APNs 先于 AppleCN，Spotify 等功能端点先于广告，香港 Now 先于 HBO，微软公共登录先于游戏。国内 BiliBili、WeChat、Direct 固定直连，BiliBili 国际站兼容域名归 Proxy。

共享 Cloudflare 验证、Stripe、WorkOS 等部分依赖仍按现有 ChatGPT 规则处理，未将整个共享平台随意拆散。新增例外应验证父域名、共享 CDN 及规则先后关系，避免整站放行或归区。

## 7. DNS、IPv6 与接管范围

Surge 自身使用 AliDNS/DNSPod 独立直连 DoH，`encrypted-dns-follow-outbound-mode=false` 解除节点解析对代理的反向依赖。传统 DNS 仍用于加密 DNS 域名引导等用途；保留证书校验。应用自己的 DNS 流量与 Surge 自身解析不是同一路径。[加密 DNS](https://manual.nssurge.com/dns/encrypted-dns.html)

| 设置 | 本配置的含义 |
| --- | --- |
| `hijack-dns = *:53` | 接管经过 Surge 的普通 DNS 查询 |
| allow-dns-svcb=false | 保持虚拟 IP 所需的解析行为 |
| use-local-host-item-for-proxy=false | 代理目标不因本地 Host 映射而统一改成 IP 连接 |
| no-resolve | IP 类规则不为了匹配而额外解析域名 |
| ipv6=true、ipv6-vif=auto | 保留双栈与 VIF 的自动处理 |
| include-all-networks=true、include-apns=true | 保留 APNs 所需接管组合 |
| include-local-networks=false、include-cellular-services=false | 关闭这两类扩展接管 |
| icmp-forwarding=false | 不直接转发 ICMP；ping 失败不能单独判定代理失败 |
| allow-wifi-access=false、allow-hotspot-access=false | 关闭局域网和热点代理共享 |

端口规则保留前置例外：国内已知应用 DNS 先处理，剩余 53 拒绝；境外已知加密 DNS 再处理，剩余 853/8853 拒绝。域名无法识别的公共 IP 请求不会自动获得对应域名例外；规则允许某端口也不代表该运营商实际提供该协议。

有限域名表无法识别所有应用内 HTTPS DNS。DNS 检测显示的运营商也不必与代理出口相同，本方案优先保证解析与代理启动，不作“零泄漏”承诺。完整网络接管可能影响 AirDrop、Xcode 和 USB 控制台，不能为消除提示而随意关闭 APNs 依赖项。[Surge 全局参数](https://manual.nssurge.com/profile/general.html)

## 8. Telegram 与系统推送

Telegram 应用数据由 Telegram 组处理，iOS 系统推送连接由 ApplePush 处理。ApplePush 的顺序为 `Proxy → Auto → DIRECT`：手选代理失败时先尝试其他代理，全部不可用时保留直连。此处是明确的可用性例外，不会改变 ChatGPT 等服务的地区边界。

APNs.list 位于 AppleCN 前，覆盖推送域名及已核对的 5 个 IPv4、4 个 IPv6 网段。`include-apns` 依赖 `include-all-networks`；隐藏 ApplePush 不影响规则工作。APNs 是系统共享连接，无法只按 Telegram 应用区分系统通知。[Apple 推送网络要求](https://support.apple.com/en-us/102266)

升级后如需验收推送，应先确认节点、APNs.list 和通知权限有效，再重建系统推送连接，分别在 Wi-Fi、蜂窝网络下锁屏接收新消息。检查请求中的 ApplePush 命中、实际出口和通知送达；普通 URL 测试只说明通用连通性，不能证明通知已经恢复。[Fallback 行为](https://manual.nssurge.com/policy-groups/fallback.html)

## 9. UDP 与 QUIC

订阅导入时启用 `udp-relay=true`，但转发能力仍由节点协议、服务端与链路共同决定。不支持 UDP 的所选策略按 `REJECT` 处理，不自动直连。QUIC 采用 `per-policy`；已有节点参数决定其放行方式。

`proxy-test-udp=apple.com@1.1.1.1` 用于节点 UDP 测试。TCP 延迟正常、Fail-Closed 报错或 UDP 栏目空白，都不能替代真实节点 UDP 验证。普通 HTTP/HTTPS 代理与支持 UDP 的协议能力不同，服务商提供的独立 UDP 端口也不应凭空猜测。[Surge UDP 说明](https://manual.nssurge.com/policies/udp.html)

## 10. 外部资源与版本管理

运行时资源包括 29 份固定规则及 1 个私人订阅。全部规则继续引用提交 [`6e8e1bf`](https://github.com/shenjlngbIng/surge/tree/6e8e1bfbbdda66ee8ad0a5ad3979b6de8b5b7a51/Rules)，规则快照日期为 2026-09-08；此次没有更换规则文件或固定地址。

| 资源层次 | 更新方式 |
| --- | --- |
| 主配置 Surge.conf | 通过 main 分支 URL 获得当前发布版；需核对顶部版本和私人订阅 |
| 桔子 节点订阅 | 设置 3,600 秒刷新间隔，实际调度由客户端决定 |
| 29 份外部规则 | `update-interval=-1`，固定提交；手动更新同一地址仍是同一快照 |
| 规则维护来源 | 通过来源锁、哈希与许可记录审核，再发布新的固定提交 |

GitHub raw 请求在活动规则模式下独立使用 Auto，避免总出口手选坏节点阻断规则下载。首次导入或尚无健康节点时，这条规则不能凭空建立下载通道；先保留旧配置及缓存，再检查 Auto、取消临时覆盖并更新失败资源。[外部规则参数](https://manual.nssurge.com/rules/ruleset.html)

Pegasus 是历史 IOC，Ads 是固定快照，不代替持续维护的安全产品。项目许可、第三方来源和归档限制见 [LICENSE](LICENSE)、[NOTICE.md](NOTICE.md)、[THIRD_PARTY_LICENSES](THIRD_PARTY_LICENSES)。

## 11. 故障排查

| 现象 | 检查顺序 |
| --- | --- |
| Fail-Closed、REJECT 显示失败 | 保护项预期失败；检查真实节点是否导入和通过测试 |
| 桔子 返回 HTTP 500 | 检查订阅/Sub-Store 服务响应、输出格式和实际 URL |
| 规则加载失败 | 查看资源页当前 HTTP/DNS/TLS/超时错误；检查 Auto 及网络，不以旧事件代替最新结果 |
| 有更低延迟但未选中 | 检查组类型、地区资格、临时覆盖、测试轮次和重测是否结束 |
| ChatGPT 只有哨兵 | 检查是否有美、日、新、台节点，以及名称是否因歧义或中转标签被排除 |
| 地区不对 | 区分外层 fallback 与严格地区源；以服务请求详情为准 |
| 出口检测与服务不同 | net.coffee 等检测跟随 Proxy，独立服务组可能另选节点 |
| 测速正常但无法登录/播放 | 验证实际 IP、账号地区、代理限制、产品版本和具体内容授权 |
| 前台 Telegram 正常、锁屏无通知 | 检查 ApplePush/APNs 命中、系统连接、通知权限与专注模式 |
| “包含所有网络请求”提示 | 保留 APNs 依赖组合，按兼容性需求判断，不直接关闭接管 |
| TCP 正常但 UDP 无结果 | 单独验证真实节点的 UDP 能力与日志 |
| 升级后没有变化 | 确认活动主配置为 R13.25；更新外部资源不会替换主配置 |
| 服务频繁切换 IP | 零容差优先最低测试值；需要会话稳定时在该服务组临时固定合格节点 |

## 12. 验证与维护

维护工具检查配置结构、规则来源、地区候选、故障恢复、发布库存及校验和。用户日常导入配置不需要安装 Python；以下命令供仓库维护与 CI 使用。

```bash
python3 tools/convert_to_remote_rules.py
python3 tools/generate_runtime_lock.py
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/audit_rules.py --check-runtime-remote
python3 tools/audit_precise_domains.py
python3 tools/test_runtime_rules.py
python3 tools/test_policy_failover.py
python3 tools/test_audit_config.py
python3 tools/update_external_resources.py --verify-lock
python3 tools/update_service_rules.py --verify-lock
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
```

具体执行结果见 [AUDIT_REPORT.md](AUDIT_REPORT.md)。检查为离线模型及维护环境中的资源核验，不等于已运行 iOS Surge 内核、测试私人订阅、验证 UDP 或完成登录/播放及锁屏通知验收。维护和反馈时不得提交私人订阅、节点密码或未经脱敏的日志。
