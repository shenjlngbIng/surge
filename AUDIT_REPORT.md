# R13.9 全盘分流与网络诊断审计报告

审计日期为 2026-08-30。

审计对象包括 `Surge.conf`、29 份本地规则、四份锁文件、维护脚本、发布清单、ZIP 与 GitHub Actions。

## 结论

本次覆盖完整配置。国内外软件策略、首条命中、策略组失效行为、DNS、UDP、APNs、双栈兜底、固定和动态资源、发布链均已逐项复核。

静态目标基线为 30 个策略组、142 条活动规则、29 个不可变运行资源、1 个动态国内资源和 29 个本地 `.list` 文件。主配置没有嵌入规则快照，也不含公开订阅凭据。

## 发现与处理

| 严重度 | 发现 | 修复 |
| --- | --- | --- |
| 高 | `[Proxy] Fail-Closed = reject` 会被网络诊断当成真实代理，TCP/UDP 测试固定超时 | 删除自定义拒绝代理；`NodePool` 只保留真实节点，手动失败关闭改为 `Proxy → REJECT` |
| 高 | 自动组无可用成员时可能 `DIRECT/SUBSTITUTE` | 明示风险，保留手动 `Proxy → REJECT` 入口，不再声称全局严格失败关闭 |
| 中 | `url-test` 只反映固定测速地址，可能出现测速快但真实访问质量差 | 总入口和五个地区组升级为 Smart，综合真实首包、重传、失败重试、测速与站点记忆 |
| 高 | `AdBlock`、`Security`、`UDP`、`Domestic` 会继承旧选择，实际行为可能偏离文档默认 | 删除四个状态组，规则固定为 `REJECT`、`Proxy` 或 `DIRECT` |
| 高 | 十万级动态广告/钓鱼表不适合 iOS，并已误杀功能域名 | 删除两份移动端动态表，保留 152 条固定 Ads 与固定 Pegasus |
| 高 | 国内 BiliBili 固定集合缺四个后缀，HTTPDNS/H5 与广告表重叠 | 补为 16 后缀，增加两条 Ads 前置直连护栏并启用扩展匹配 |
| 中 | Spotify 音视频/电视/Podcast、Google `gvt2`、OpenAI RUM 与广告表重叠 | 增加七条对应策略护栏，与 BiliBili 合计九条 |
| 中 | ChatGPT 规则未覆盖当前官方网络建议中的部分依赖 | 增加 11 条官方依赖，本地活动规则 52 增至 63 |
| 中 | 固定资源只按普通 DNS 路径匹配，SNI/Host 可能漏分流 | 除 Ads 外的固定资源及动态国内补充启用 `extended-matching` |
| 中 | AI/TikTok/Bahamut 可通过通用 Proxy 或不合适地区绕过限制 | AI/TikTok 仅四个支持地区；Bahamut 仅台湾、香港 |
| 中 | AI/TikTok 原先是手动 `select`，默认只进入日本 Smart，无法在其他允许地区自动容错 | 四组改为 Smart，递归汇总四个允许地区的真实节点；不新增隐藏组 |
| 中 | 固定规则使用旧快照提交且远程内容未逐文件在线核验 | 快照钉住 `2b8fa939…`，增加 29 文件 CDN 哈希校验 |
| 中 | `doh.pub` 虽使用主机名，仍被 `[Host]` 冻结到 DNSPod 已不建议公开使用的旧 IP | 删除 DNSPod 静态映射，改由双栈 AliDNS 引导动态解析；AliDNS 补齐第二条官方 IPv6 |
| 低 | Pegasus 文件头仍声明旧 `Security` 策略 | 文件头、资源锁和运行规则统一为 `REJECT` |

## 策略组审计

Surge 官方文档说明，Smart 会根据真实连接质量、测试结果和站点历史动态选路，并在连接失败时按评分重试其他代理。Smart 只接受真实代理策略，会忽略显式内建策略和直接嵌套组；`include-other-group` 则会递归展开其他组的已解析成员。自动组没有可用策略时仍会替代为 `DIRECT`，日志显示为 `SUBSTITUTE`。R13.9 因此只让 Smart 导入 `NodePool` 中的真实代理，并把手动拒绝放在 `Proxy` 的内建策略中。

R13.9 采用以下边界。

- 主配置不定义 `[Proxy]` 静态代理，网络诊断不会再误测一个故意拒绝流量的别名。
- `NodePool` 是手动 `select`，成员只由私人 `policy-path` 提供。
- `Smart` 只递归导入 `NodePool` 的真实订阅代理。
- 香港、台湾、日本、新加坡、美国均为 Smart，只导入名称匹配的 `NodePool` 节点。
- 总入口、五个地区组和四个受限服务组共十个 Smart，统一锁定 `evaluate-before-use=true` 和可见状态；不写对 Smart 无效的 `interval` 或 `tolerance`。Surge 自身按固定五分钟周期安排测试。
- ChatGPT、Claude、Gemini 与 TikTok 通过带引号的 `include-other-group` 递归汇总日本、新加坡、台湾、美国的真实代理，跨允许地区自动选优，不把香港或通用 Proxy 放入候选池。
- `Proxy` 首项为 `Smart`，第二项保留手动 `NodePool`，之后是五个地区入口，末项为手动 `REJECT`。
- `ApplePush` 保留 `Proxy → DIRECT` fallback，这是通知可达性的明确例外。
- 配置没有 `url-test` 或 load-balance 节点组，没有策略引用循环、未知成员或 Smart 中的显式内建成员。
- `Smart` 或地区组为空时仍可能发生 `DIRECT/SUBSTITUTE`。需要严格失败关闭时，用户应直接选择 `Proxy → REJECT`；需要固定节点时选择 `NodePool` 中的真实节点。

## 软件与地区审计

| 软件/类别 | 审计结果 |
| --- | --- |
| ChatGPT、Claude、Gemini | 仅日本、新加坡、台湾、美国；Smart 跨允许地区自动选优，不允许通用 Proxy 绕过边界 |
| TikTok | 同上 |
| Bahamut | 仅台湾、香港 |
| GitHub | Proxy、香港、日本、新加坡、美国 |
| YouTube、Netflix、Disney+、Emby、Spotify、Streaming、Telegram、X、Google、Microsoft、Games | 默认 Proxy，五个地区自动选优并支持临时手动覆盖 |
| HBO、Prime Video | 默认 Proxy，并保留各自更适合的地区排序 |
| Apple | DIRECT 首选；流媒体域名在 AppleCN 前进入 Streaming |
| 微信、Direct、China、CN GeoIP、国内 DNS、共享国内云 | 固定 DIRECT |
| 国内 BiliBili | 固定 DIRECT，16 后缀与两条前置功能护栏 |
| BiliBili 国际版 | 专用文件/策略保持删除，七条历史域名只走通用 Proxy |

18 份固定服务规则重新用锁定上游与本地过滤/增补边界生成比较，除 ChatGPT 明确新增的 11 条官方依赖外，现有服务快照无非预期增删。

## BiliBili 根因

旧版已把固定 BiliBili 列表指向 `DIRECT`，但仍可能长时间等待。审计确认了下面四项原因。

1. 固定列表不含 `biligame.net`、`bilivideo.cn`、`bilicomic.com`、`bilivideo.net`。
2. 动态广告表命中 `httpdns.bilivideo.com` 和 `line3-h5-mobile-api.biligame.com`。
3. 固定 BiliBili 规则位于广告边界之后，重叠功能域名会先被拒绝。
4. 普通规则匹配未覆盖所有 SNI/Host 路径。

处理后，两个确认重叠的功能主机位于 Ads 前，16 后缀集合与动态国内补充均固定直连；BiliBili 固定资源启用 `extended-matching`。国际兼容护栏仍在国内父后缀前，因此 `apiintl.biliapi.net` 不会被 `biliapi.net` 直连覆盖。

## 广告与安全边界

动态 `reject.conf` 与 `reject_phishing.conf` 已从运行配置删除。审计时确认其中至少存在以下功能重叠。

- `httpdns.bilivideo.com`
- `line3-h5-mobile-api.biligame.com`
- `audio-ak.cdn.spotify.com`
- `video-ak.cdn.spotify.com`
- `audio-ak-spotify-com.akamaized.net`
- `pod.spoti.fi`
- `tv-static.scdn.co`
- `gvt2.com`
- `rum.browser-intake-datadoghq.com`

当前只保留固定 Ads 与固定 Pegasus。固定列表可通过提交 SHA、锁文件、活动条目数与 SHA-256 复核；误报时必须走审阅差异，不允许临时切换隐藏 `DIRECT` 组。

## DNS、UDP、APNs 与双栈

- 传统引导 DNS 使用 AliDNS 双 IPv4＋双 IPv6；两个 DoH 和证书校验被审计锁定。
- `dns.alidns.com` 保留官方四地址静态引导；`doh.pub` 由引导 DNS 动态解析，不再冻结 DNSPod 旧 IP。
- 16 条大陆应用 DNS 在端口拒绝前固定直连；13 条境外应用 DNS 在端口拒绝后固定代理。
- 公网 53、853、8853 在局域网例外之后拒绝。
- STUN 在公网 DNS 与普通业务规则之前固定代理。
- `GEOIP,CN,DIRECT,no-resolve` 不为未知域名强制本地解析。
- IPv4 `0.0.0.0/0` 与 IPv6 `::/0` 紧贴唯一 FINAL 之前固定代理。
- 不支持 UDP 的节点行为为 `REJECT`；QUIC 保持按策略处理。
- APNs 继续先代理后直连，避免严格代理边界造成通知不可达。

## 供应链与发布

| 资源 | 模式 | 控制 |
| --- | --- | --- |
| 29 份仓库规则 | 不可变 | 完整提交 SHA、活动条目、文件 SHA-256、CDN 在线比对 |
| `domestic.conf` | 动态 | 精确 URL、格式/规模在线检查、24 小时更新 |
| 18 份服务上游 | 维护输入 | 固定提交、Git Blob、上游/本地 SHA-256、显式增删边界 |
| Pegasus 上游 | 维护输入 | 固定 Amnesty 提交、Git Blob、上游/本地 SHA-256 |
| 发布目录 | 固定白名单 | 65 文件 ZIP、UTF-8/LF/无 BOM/NUL/符号链接检查 |

运行配置不直接访问 Blackmatrix7 或 Amnesty 上游；设备读取仓库固定副本。动态国内表是唯一会在发布后改变内容的运行资源。

## 自动验证

自动验证覆盖以下内容。

- 配置结构、30 个策略组与 142 条规则；
- 30 个运行资源的类型、策略、顺序、更新间隔和扩展匹配；
- 16 个 BiliBili 精确后缀、国际版退役与前置功能护栏；
- 18 份服务来源锁、Pegasus 锁和维护来源锁；
- DNS、UDP、APNs、双栈和唯一 FINAL；
- 119 项故障注入，覆盖全部 36 项 `[General]` 设置、Smart 递归导入语法、静态拒绝代理回归和 `Proxy → REJECT` 边界；
- 发布目录与 ZIP 导入安全回归；
- 动态国内在线格式检查、固定上游零差异检查；
- 快照推送后的 29 份 jsDelivr 文件逐一哈希检查。
- Telegram 官方 14 个 CIDR 与 Apple 官方 5 个 IPv4、4 个 IPv6 APNs 网段逐项在线复核。

## 剩余风险

静态配置无法证明私人节点在线、地区标签真实、节点 DNS 无泄漏、运营商链路正常，也无法检查未随仓库提供的 Surge 模块。自动组没有可用成员时存在官方 `DIRECT/SUBSTITUTE` 风险，这项行为无法由配置覆盖。`include-all-networks=true` 还可能影响 AirDrop、Xcode 调试或 USB Dashboard，这是全网络接管的兼容性取舍。最终必须在真实设备的 Wi-Fi 和蜂窝网络完成验收。命中规则与策略正确但速度仍差时，应检查服务端、运营商、DNS 或节点质量，不能继续用更宽泛规则掩盖链路问题。
