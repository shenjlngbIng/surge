# Surge iOS Privacy + Push R12.16

这是一份面向 Surge iOS 的规则模式配置。它把订阅导入、自动选路、地区选择和服务分流分开处理，并保留明确的失败关闭边界。公开版本不包含节点、订阅令牌、证书或脚本。

R12.16 清理了专用服务与通用规则之间的冲突。Xbox、Minecraft、Bethesda 和 Forza 会先进入 `Games`，不会被 Microsoft 规则提前截获。Netflix 删除了宽泛云网段，改用 `IP-ASN,2906,no-resolve`。国内服务、共享 CDN、遥测域名和 Google 的旧直连例外也重新整理过。

公开主配置地址

https://raw.githubusercontent.com/shenjlngbIng/surge/main/Surge.conf

## 当前基线

| 项目 | 当前值 |
| --- | --- |
| 配置版本 | R12.16 |
| 推荐环境 | Surge iOS 5.14.6 或更高 |
| 运行模式 | Rule |
| 策略组 | 31 个 |
| 主配置活动规则 | 86 条 |
| 远程规则源 | 29 个 |
| 普通 RULE-SET | 27 个 |
| 精确 DOMAIN-SET | 2 个 |
| 中国域名 | 306 条 |
| 全球域名 | 116 条 |
| 精确域名交叉冲突 | 0 |
| 配置故障注入测试 | 56 项 |
| ZIP 路径回归测试 | 17 项 |

配置依赖 Smart 策略组。设备无法识别 `smart` 时，应更新 Surge 或恢复相应功能授权。不要把 Smart 组自行改回包含全部订阅节点的 `fallback` 或 `url-test`，这会重新带来网络切换后的集中探测。

## 与常见公开配置相比

公开配置各有侧重。这里对照 README 末尾列出的公开模板，重点观察订阅接入、自动选路、规则来源、失败处理和发布方式。差异用于说明本配置的取向，不作优劣排名。

| 对照维度 | 公开配置中的常见写法 | R12.16 的处理 | 使用上的区别 |
| --- | --- | --- | --- |
| 订阅接入 | 多个自动组或地区组分别填写 `policy-path` | 只有隐藏的 `NodePool` 持有订阅地址 | 订阅只下载和解析一次，来源关系更容易检查 |
| 自动选路 | 用 `url-test`、`fallback` 按固定间隔测试整组节点 | `AllServer` 与五个地区组使用 Smart，并从 `NodePool` 取节点 | 自动选择会参考真实连接质量和站点记录，减少多个组重复测试同一订阅 |
| 空订阅处理 | 自动组没有可用成员时可能被 Surge 临时替换为 DIRECT | 每个 Smart 组都显式保留 `Fail-Closed` 哨兵 | 订阅失效和地区零匹配会明确失败，避免无提示直连 |
| 服务策略 | 不少模板给流媒体、AI 或最终策略同时提供代理和 DIRECT | 代理服务组不提供 DIRECT，`Final` 只提供 `Proxy` 与 `REJECT` | 临时选错策略时也不容易越过代理边界 |
| 推送可达性 | Telegram 数据与 Apple 推送经常跟随同一个代理组 | Telegram 保持代理，APNs 单独进入 `ApplePush` | 代理故障时只有 APNs 可以按顺序回落直连，应用数据仍受原策略约束 |
| 规则来源 | 直接引用第三方仓库当前分支，内容会随上游更新 | 19 个服务源固定提交、Blob 和 SHA-256，运行地址再固定到发布标签 | 每次发布所用规则可以复查，异常变化不会直接进入设备 |
| 规则精度 | 完整接收上游共享 CDN、云平台、遥测和宽网段 | 按服务删除非唯一归属项，并维护精确的中国与全球域名表 | 降低共享基础设施把无关应用带进错误策略的概率 |
| 规则顺序 | 主要依靠维护者手工保持先后关系 | 关键先后关系写入审计器和故障注入测试 | 服务规则被大规则提前截获时，验证命令会直接失败 |
| 发布方式 | 以单个配置文件或规则目录为主要交付内容 | 配置、规则、锁文件、工具、清单、校验和与工作流一同发布 | 下载者可以核对文件完整性，维护者可以复现同一份 ZIP |

### 节点来源只有一个入口

`NodePool` 是隐藏的订阅容器。它使用 `select`，只负责读取 `policy-path`，不会承担业务流量，也不会主动测试整份订阅。`AllServer` 和五个地区组通过 `include-other-group=NodePool` 取得真实节点，服务组再选择这些稳定的上层策略。

这种分层把节点来源、自动选择和业务分流拆开了。订阅地址只出现一次，地区正则也只作用于同一个节点池。节点重复、策略组各自下载订阅、多个自动组同时测试等问题都更容易定位。

### Smart 承担日常自动选择

Smart 会结合真实连接的首包延迟、重传情况和站点使用记录评估节点。节点较多时，常规测试只覆盖一部分成员，手动测试才会检查全部成员。R12.16 因此没有给 `AllServer` 和地区组设置 `interval`、`timeout` 或 `evaluate-before-use`。

Smart 仍然会做定期和必要的连通性测试。这里减少的是多个 `url-test` 或 `fallback` 对同一订阅反复发起整组测试，后台请求不会被承诺降到零。

### 失败路径保持收紧

Surge 在策略组没有可用代理成员时可能临时使用 DIRECT。R12.16 给 `AllServer` 和五个地区组加入本机 `127.0.0.1:1` 哨兵，让组内始终存在一个代理类型成员。哨兵连接预期失败，失败结果不会变成直连。

`Final` 默认进入 `Proxy`，并提供 `REJECT` 作为更严格的手动选择。代理类服务组统一移除 DIRECT。唯一保留的可用性例外是 `ApplePush`，它先尝试 `Proxy`，五秒内不可用才回落 DIRECT。这条退路只服务 APNs，不会放宽 Telegram 应用数据或其他国际服务。

### 第三方规则先经过本地筛选

第三方列表在这里充当待审核输入，生成后的仓库快照才会交给 Surge。`Rules/upstreams.lock.json` 记录上游提交、文件路径、Git Blob、SHA-256、排除项和本地补充。更新工具下载内容后会校验这些记录，并过滤 iOS 不使用的进程规则和未经单独审核的新 ASN。

筛选会处理域名归属范围。共享遥测、公共云、通用 CDN 和跨服务后缀不会因为出现在某个上游列表中就自动进入对应策略。Netflix 使用官方网络 `AS2906`，Disney、HBO、Microsoft、Bahamut 和 Game 则删除了各自上游中的共享平台项。这样做会牺牲一点规则数量，换来更清楚的命中边界。

### 规则顺序也是受检内容

Surge 使用首条命中结果，两个正确的规则文件放错先后仍会产生错误分流。R12.16 明确检查 YouTube 位于 Google 前，Game 位于 OneDrive 和 Microsoft 前，专用流媒体位于通用媒体和中国域名兜底前。

`tools/audit_config.py` 会检查这些位置关系。56 项故障注入测试还会故意改坏策略类型、成员、规则顺序和失败边界，确认审计器能够拦住错误。配置维护因此不只依赖人工浏览几百行文本。

### DNS 和本地网络有明确边界

配置同时提供 AliDNS 的普通 DNS、DoH 和 DoT，并为加密 DNS 写入固定引导地址。`encrypted-dns-follow-outbound-mode=false` 用来避免内部解析跟随业务代理形成循环。传统 53 端口会被 Surge 接管，进入规则系统的 53、853 和 8853 外部连接受到单独控制。

局域网、CGNAT、回环和 IPv6 本地范围均有明确规则。Wi-Fi 代理入口、热点入口和 Web 控制面板默认关闭。节点不支持 UDP 时连接会拒绝，代理路径阻断 QUIC，STUN 明确进入 `Proxy`。这些选择共同限定了哪些流量可以离开代理路径。

### 保持纯分流配置

公开文件没有 MITM、脚本和重写段，也不携带证书。它只处理网络接管、策略选择、DNS、规则匹配和推送可达性。下载者无需安装 CA，维护者也不用同时审查脚本权限、解密范围和重写副作用。

### 发布包可以复现和验证

仓库把配置当作一套需要构建和验收的文件发布。两份锁文件记录配置不变量、规则数量、内容哈希与上游来源。发布前会执行配置审计、规则审计、精确域名交叉检查、56 项故障注入测试和 17 项 ZIP 路径测试。

最终 ZIP 使用固定顺序、时间戳和权限，并附带文件清单与两份 SHA-256 清单。安装工作流还会限制文件数量、单文件大小、解压总量和路径类型，拒绝路径穿越与特殊设备条目。同一版本的维护、上传和复核都能落到具体文件与校验结果上。

## 这份配置怎样工作

一次连接进入 Surge 后，会依次经过下面几层。

1. Surge 接管符合条件的网络和 DNS 请求。
2. 本地网段、CGNAT、回环地址和必要的 Apple 系统查询先行直连。
3. APNs、广告、AI、流媒体和国际服务按专用规则匹配。
4. 中国与全球精确域名表负责补充常用服务边界。
5. STUN 明确进入代理。
6. 未命中的中国 IP 由 `GEOIP,CN,DIRECT` 处理。
7. 其余连接落入 `FINAL,Final,dns-failed`。

Surge 从上到下检查规则，首条命中决定策略。专用规则必须排在宽泛规则前面。YouTube 位于 Google 前，Game 位于 OneDrive 和 Microsoft 前，专用流媒体位于通用媒体与中国域名兜底前。顺序本身就是配置行为的一部分。

## 快速开始

### 准备私有配置

公开文件中的订阅地址是不可路由占位符。

~~~ini
NodePool = select, policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL, update-interval=3600, no-alert=0, hidden=1, include-all-proxies=0
~~~

复制 `Surge.conf` 作为私有文件，只替换 `policy-path` 后面的 URL。订阅应输出 Surge 策略列表，或带有有效 `[Proxy]` 段的完整 Surge 配置。

~~~ini
NodePool = select, policy-path=https://你的私有地址, update-interval=3600, no-alert=0, hidden=1, include-all-proxies=0
~~~

真实订阅地址不要提交到公开仓库。

### 导入和首次检查

1. 把私有配置导入 Surge iOS。
2. 重新载入配置并刷新外部资源。
3. 打开 `AllServer`，确认能看到订阅中的真实节点。
4. 检查香港、台湾、日本、新加坡和美国组是否能匹配相应节点。
5. 保持 `Proxy` 默认选择 `AllServer`，或按需要选择地区组。
6. 检查 Telegram 前台连接和锁屏后的 APNs 通知。

`NodePool` 设置了 `hidden=1`。它不会出现在普通策略选择页面，这是预期结果。

## 订阅与自动选路

### NodePool 只负责导入节点

`NodePool` 使用 `select`，每小时更新一次 `policy-path`。它不承担规则出站，也不主动遍历全部节点。

只有 `NodePool` 可以持有 `policy-path`。服务组、`Proxy` 和规则都不能直接选择它。这样的限制能防止多个策略组重复加载同一份订阅。

### AllServer 使用 Smart

~~~ini
AllServer = smart, Fail-Closed, no-alert=0, hidden=0, include-all-proxies=0, include-other-group=NodePool
~~~

`AllServer` 从 `NodePool` 读取节点，并根据真实连接表现选择策略。它是 `Proxy` 的默认成员。

Smart 仍会在首次使用、连接失败和恢复阶段做必要探测。配置避免的是网络接口切换后由全订阅 `fallback` 触发的集中测试，并不承诺完全没有探测请求。

### 五个地区组直接筛选 NodePool

| 地区组 | 常见匹配内容 |
| --- | --- |
| HongKong | 香港、港区、HK、Hong Kong 等名称 |
| TaiWan | 台湾、台北、TW、Taiwan 等名称 |
| Japan | 日本、东京、大阪、JP 等名称 |
| Singapore | 新加坡、狮城、SG 等名称 |
| America | 美国、美东、美西、US 及常见城市名称 |

每个地区组都使用 `smart, Fail-Closed`，并通过 `include-other-group=NodePool` 读取订阅。地区正则没有排除带有“专用”或“解锁”等字样的节点，避免误删流媒体线路。

节点供应商的命名差异很大。某个地区只有 `Fail-Closed` 时，应先检查节点名称，再在私有副本中补充该地区的正则。不要让地区组改读 `AllServer`，也不要开启 `include-all-proxies=true`。

## 策略组说明

### 核心策略组

| 策略组 | 类型 | 默认成员 | 用途 |
| --- | --- | --- | --- |
| Final | select | Proxy | 接收最终未匹配流量，可手动改为 REJECT |
| Proxy | select | AllServer | 通用代理入口 |
| ApplePush | fallback | Proxy | APNs 代理优先，失败后回落 DIRECT |
| AdBlock | select | REJECT | 广告阻断，可切换 REJECT-DROP |
| NodePool | select | 订阅输出 | 隐藏的节点导入容器 |
| AllServer | smart | Fail-Closed | 全部节点的 Smart 选择 |

### 服务策略组

| 策略组 | 默认选择 | 对应规则 |
| --- | --- | --- |
| ChatGPT | America | ChatGPT.list |
| Claude | America | Claude.list |
| Gemini | America | Gemini.list |
| GitHub | Proxy | Github.list |
| YouTube | Proxy | YouTube.list |
| NETFLIX | Proxy | Netflix.list |
| Disney+ | Proxy | Disney.list |
| HBO | Proxy | HBO.list |
| PrimeVideo | America | PrimeVideo.list |
| Emby | Proxy | Emby.list |
| TikTok | Proxy | TikTok.list |
| Bahamut | TaiWan | Bahamut.list |
| Spotify | Proxy | Spotify.list |
| Streaming | Proxy | BiliBiliIntl.list 与 ProxyMedia.list |
| Telegram | Proxy | Telegram.list |
| X | Proxy | Twitter.list |
| Apple | DIRECT | AppleCN.list |
| Google | Proxy | Google.list |
| Microsoft | Proxy | OneDrive.list 与 Microsoft.list |
| Games | Proxy | Game.list |

服务组不会直接读取 `NodePool`。它们只选择 `Proxy`、地区 Smart 组或 `AllServer`。Apple 额外提供 `DIRECT`，默认也保持直连。

## Telegram 与 Apple Push

Telegram 应用数据和 Apple 的通知唤醒连接属于两条链路。

`Telegram.list` 中的域名与 IP 始终进入 `Telegram`，该策略组不提供 `DIRECT`。Telegram 核心地址还加入 `always-raw-tcp-hosts`，减少协议识别带来的兼容问题。

APNs 由 `APNs.list` 进入 `ApplePush`。

~~~ini
ApplePush = fallback, Proxy, DIRECT, interval=60, timeout=5, no-alert=0, hidden=0
~~~

代理可用时，APNs 优先走代理。代理在五秒内不可用时，ApplePush 可以回落直连，保留后台通知可达性。`include-all-networks=true` 和 `include-apns=true` 均已开启。

`include-cellular-services=false` 只退出运营商专用链路的接管。普通蜂窝数据和 APNs 仍在配置范围内。

## DNS 与网络边界

### Surge 内部解析

配置使用 AliDNS 的 IPv4、DoH 和 DoT。

~~~ini
dns-server = 223.5.5.5, 223.6.6.6
encrypted-dns-server = https://dns.alidns.com/dns-query, tls://dns.alidns.com
encrypted-dns-follow-outbound-mode = false
hijack-dns = *:53
~~~

`dns.alidns.com` 的两个 IPv4 和一个 IPv6 引导地址写在同一条 Host 映射中。Host 匹配有顺序，拆成重复键会让后面的地址失去作用。

`encrypted-dns-follow-outbound-mode=false` 让 Surge 的内部加密解析不跟随普通代理规则，降低代理服务器域名解析形成循环的风险。

### 应用自带 DNS

配置接管发往 53 端口的传统 DNS，并对目的端口 53、853 和 8853 设置 `REJECT`。已知公共 DNS 域名按直连或代理边界处理。

这些规则控制进入 Surge 的应用连接。它们不会替代 `encrypted-dns-server` 指定的内部解析链。

### 本地网络

下列范围保留在 `skip-proxy` 和本地规则中。

- RFC 1918 私网
- `100.64.0.0/10` 运营商 CGNAT
- IPv4 与 IPv6 回环地址
- 链路本地和 IPv6 ULA
- `.local` 与 `localhost`

`include-local-networks=false`、`allow-wifi-access=false` 和 `allow-hotspot-access=false` 共同限制局域网接管与代理入口。公开配置不把 iPhone 暴露为局域网代理或网关。

`DOMAIN-SUFFIX,ls.apple.com,DIRECT` 位于所有远程规则之前，避免 Apple 配置查询进入代理选择或失败回落环路。

## UDP、QUIC 与 STUN

~~~ini
udp-policy-not-supported-behaviour = REJECT
block-quic = all-proxy
PROTOCOL,STUN,Proxy
~~~

节点不支持 UDP 时，连接会明确失败，不会静默直连。代理路径会阻断 QUIC，多数应用随后回落到 TCP 或 HTTP/2。STUN 明确进入代理，避免其绕过当前出站选择。

某个应用无法正确回落时，应检查该应用和节点协议。全局开放 UDP 直连会改变整个配置的隐私边界。

## 失败关闭设计

### Fail-Closed 哨兵

~~~ini
Fail-Closed = http, 127.0.0.1, 1, no-error-alert=true
~~~

本机端口 `127.0.0.1:1` 预期没有代理服务。订阅为空、下载失败或地区正则没有匹配时，Smart 组仍至少保留这个成员，连接会明确失败。

`no-error-alert=true` 只隐藏哨兵产生的预期错误提醒，不会把失败改成直连。

### 最终策略

~~~ini
Final = select, Proxy, REJECT, no-alert=0, hidden=0, include-all-proxies=0
FINAL,Final,dns-failed
~~~

未匹配流量默认进入 `Proxy`。用户可以手动把 `Final` 改为 `REJECT`，配置不提供最终直连选项。规则集加载失败时，剩余流量仍会继续走后面的精确域名、GEOIP 和 Final，不会自动放行到 DIRECT。

## 规则顺序

主配置中的活动规则按下面的顺序排列。

1. 局域网发现与组播地址。
2. 私网、CGNAT、回环地址和本地主机。
3. Apple 系统配置查询。
4. DNS 域名与端口控制。
5. APNs。
6. Apple 国内服务、微信和明确直连项。
7. 广告规则。
8. ChatGPT、Claude 和 Gemini。
9. 专用流媒体规则。
10. Telegram、GitHub、X 和 Google。
11. Game、OneDrive 和 Microsoft。
12. 中国与全球精确域名表。
13. STUN、中国 GEOIP 和 Final。

Game 排在 Microsoft 前。这样，两个规则集中重叠的 Xbox、Minecraft、Bethesda 和 Forza 域名会进入 `Games`。Google 的下载、更新和消息域名不再留在 `Direct.list`，现在统一进入 `Google`。

`cache.video.iqiyi.com` 已从通用媒体规则删除，会被 `China.list` 的爱奇艺后缀接住。TikTok 中宽泛的 `snssdk.com` 也已删除，国内字节服务会回到中国域名兜底。TikTok 自己使用的精确 CDN 主机仍保留在 TikTok 专用规则中。

## 远程规则库存

Surge.conf 通过 jsDelivr 加载仓库中的 29 个规则文件。运行地址统一固定到发布标签 `r12.16-20260825`。其中 19 份服务快照保留固定上游、提交、Blob、SHA-256 和本地处理说明，其余文件由仓库直接维护并写入配置锁。

| 规则文件 | 策略 | 活动条目 |
| --- | --- | ---: |
| APNs.list | ApplePush | 12 |
| AppleCN.list | Apple | 166 |
| WeChat.list | DIRECT | 33 |
| Direct.list | DIRECT | 9 |
| Ads.list | AdBlock | 152 |
| ChatGPT.list | ChatGPT | 52 |
| Claude.list | Claude | 6 |
| Gemini.list | Gemini | 21 |
| YouTube.list | YouTube | 192 |
| Netflix.list | NETFLIX | 36 |
| Disney.list | Disney+ | 165 |
| HBO.list | HBO | 45 |
| PrimeVideo.list | PrimeVideo | 18 |
| Emby.list | Emby | 218 |
| TikTok.list | TikTok | 86 |
| Bahamut.list | Bahamut | 7 |
| BiliBiliIntl.list | Streaming | 7 |
| BiliBili.list | DIRECT | 12 |
| Spotify.list | Spotify | 30 |
| ProxyMedia.list | Streaming | 319 |
| Telegram.list | Telegram | 51 |
| Github.list | GitHub | 31 |
| Twitter.list | X | 33 |
| Google.list | Google | 705 |
| Game.list | Games | 596 |
| OneDrive.list | Microsoft | 16 |
| Microsoft.list | Microsoft | 664 |
| China.list | DIRECT | 306 |
| Global.list | Proxy | 116 |

`China.list` 与 `Global.list` 只接受能够明确归属的域名后缀。公共后缀、关键词、共享云和跨策略重叠会被审计器拒绝。

## 服务规则的本地筛选

19 个第三方服务规则固定在 `blackmatrix7/ios_rule_script` 的提交 `c00517ce10760a93728b241923a451dfa617be80`。更新工具会核对 Git Blob 与 SHA-256，再合并本地规则。

合并过程会过滤 iOS 不使用的 `PROCESS-NAME`，并拒绝未经单独审核的新 `IP-ASN`。每个服务还可以在 `Rules/upstreams.lock.json` 中声明精确排除项、禁用的规则类型和经过审核的本地补充。

R12.16 已处理下面几类误分流。

- Netflix 删除上游中的宽泛 `IP-CIDR` 与 `IP-CIDR6`，保留官方网络 `IP-ASN,2906,no-resolve`。
- Disney 删除 Adobe、Braze、Conviva、New Relic 和 Optimizely 等共享遥测域名。
- HBO 删除共享 Brightcove、BoltDNS 和 AWS API 后缀，默认策略改为 `Proxy`。
- Microsoft 删除共享 Azure CDN、托管平台、HelpShift 和 Optimizely 后缀。
- Bahamut 删除 DigiCert、GVT1 和整个 Hinet 后缀，保留明确的动画 CDN 主机。
- Game 删除共享 `helpshift.com`，专属游戏域名继续进入 `Games`。

不要直接修改生成后的服务文件来绕过锁。需要增加或删除规则时，应先改 `Rules/upstreams.lock.json`，随后重新运行更新与审计命令。

## 文件说明

| 路径 | 用途 |
| --- | --- |
| Surge.conf | R12.16 主配置 |
| Rules/*.list | 29 个远程规则快照 |
| Rules/r10.lock.json | 配置哈希、规则库存和安全不变量 |
| Rules/upstreams.lock.json | 固定上游、排除项与本地补充 |
| tools/audit_config.py | 配置结构、策略组和规则顺序审计 |
| tools/audit_rules.py | 规则库存、哈希和语义边界审计 |
| tools/audit_precise_domains.py | 中国与全球精确域名审计 |
| tools/test_audit_config.py | 56 项配置故障注入测试 |
| tools/test_stage_surge_zip.py | ZIP 路径白名单回归测试 |
| tools/update_service_rules.py | 固定上游下载、合并与验证 |
| tools/embed_runtime_rules.py | 刷新锁文件元数据 |
| tools/convert_to_remote_rules.py | 校验远程规则引用库存 |
| tools/generate_release_manifest.py | 生成发布文件清单 |
| tools/generate_checksums.py | 生成两份 SHA-256 清单 |
| tools/package_release.py | 生成确定性完整 ZIP |
| tools/stage_surge_zip.py | 安全暂存候选 ZIP |
| RELEASE_MANIFEST.txt | 发布文件及内容摘要 |
| SHA256SUMS.txt | 发布文件 SHA-256 |
| SHA256SUMS_fixed.txt | 与主清单逐字节一致的冻结副本 |
| .github/workflows/install.yml | 安装与持续审计工作流 |
| THIRD_PARTY_LICENSES | 第三方许可证副本 |

当前发布布局包含 29 个规则文件、12 个 Python 工具和 58 个 ZIP 普通文件。`RELEASE_MANIFEST.txt` 记录 55 个文件，两份 SHA-256 清单各记录 56 个文件。

## 上传与发布

### 已有仓库直接更新

解压完整发布包，把其中全部文件按原目录结构上传到仓库。`Rules`、`tools`、`.github` 和 `THIRD_PARTY_LICENSES` 都要保留。提交到 `main` 后，创建指向本次提交的标签 `r12.16-20260825`。标签创建完成并等待 jsDelivr 同步后，再在 Surge 中刷新外部资源。

只上传 `Surge.conf` 会让规则快照、服务筛选和锁文件缺失，完整审计也无法运行。

### 使用安装工作流

也可以把未解压的 `Surge-R12.16-corrected-20260825.zip` 放在仓库根目录，并保留 `.github/workflows/install.yml`。随后在 Actions 中手动运行 `Install and audit Surge R12.16`。

安装任务会检查文件数量、单文件大小、解压总量和路径安全。它拒绝绝对路径、路径穿越、反斜杠和特殊设备条目。SHA-256 验证通过后，任务才会展开完整文件并提交，随后创建固定的规则发布标签。

### 本地生成发布包

~~~bash
python3 tools/package_release.py --output ../Surge-R12.16-corrected-20260825.zip
~~~

ZIP 使用固定时间戳、固定顺序和统一权限。同一份内容可以生成一致的归档结构。Git 元数据、缓存、pyc 和其他压缩包不会进入发布包。

## 维护与审计

### 完整验证命令

~~~bash
python3 -m compileall -q tools
python3 tools/convert_to_remote_rules.py
python3 tools/update_service_rules.py --verify-lock
python3 tools/embed_runtime_rules.py
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/audit_precise_domains.py
python3 tools/test_audit_config.py
python3 tools/test_stage_surge_zip.py
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
sha256sum -c SHA256SUMS.txt
cmp --silent SHA256SUMS.txt SHA256SUMS_fixed.txt
python3 tools/package_release.py --output ../Surge-R12.16-corrected-20260825.zip
~~~

正常基线会出现下面的关键结果。

~~~text
PASS: remote-only profile; external_rules=29 embedded_rule_contents=0
PASS: verified upstream lock services=19
PASS R12.16 rules=86
PASS R12.16 remote_sources=29 rules=86
PASS precise domains DIRECT=306 Proxy=116 conflicts=0
PASS R12.16 mutations=56
PASS: ZIP allowlist regression cases=17
updated release manifest: files=55
updated checksums: files=56
PACKAGED: files=58
~~~

配置内容变化后，SHA-256 会随之变化。规则数、远程源数量或策略组数量发生变化时，应在更新日志中解释，并同步修改审计器和故障注入测试。

### 更新固定服务规则

普通验证使用下面的命令。

~~~bash
python3 tools/update_service_rules.py --verify-lock
~~~

需要按照当前锁重新生成服务快照时使用下面的命令。

~~~bash
python3 tools/update_service_rules.py --download
~~~

上游提交升级需要单独审阅。更新者应核对许可证、文件路径、Blob、SHA-256、排除项和条目变化，再提交新的锁文件。

## 常见问题

### AllServer 只有 Fail-Closed

`NodePool` 没有返回可用节点。常见原因包括占位 URL 尚未替换、订阅过期、输出格式不兼容或节点语法无效。

先检查私有 `policy-path` 的状态和输出内容，再刷新外部资源。不要删除 `Fail-Closed`，也不要把 `Final` 改成 DIRECT。

### 地区组只有 Fail-Closed

订阅已有节点，但节点名称没有命中地区正则。在私有 Sub-Store 输出中补充明确的地区名称或旗帜，或者审慎扩展对应正则。

### Telegram 前台可用但锁屏没有通知

确认 `include-apns=true`，检查 `APNs.list` 是否加载成功，并查看请求是否进入 `ApplePush`。代理无法连接时，ApplePush 应在五秒后尝试 DIRECT。

### 网络切换后仍有大量请求

检查当前启用的配置是否为 R12.16。`NodePool` 应为隐藏的 `select`，`AllServer` 和五个地区组应为 `smart`。除 `ApplePush` 外，不应存在读取整份订阅的 `fallback`、`url-test` 或 `load-balance`。

手动点击测试全部策略本来就会产生集中请求。若没有手动测试，继续在 Surge 最近请求中查看发起进程、策略路径和目标地址。

### 规则文件出现 404

确认仓库已经创建标签 `r12.16-20260825`，文件大小写和目录结构必须与 `Surge.conf` 完全一致。新标签需要等待 jsDelivr 同步，随后再刷新外部资源。

### DNS 解析异常

确认 `dns.alidns.com` 的 Host 映射仍在，并且三个引导地址位于同一行。检查 AliDNS 的 HTTPS 与 TLS 端点是否可达，也要确认私有模块没有覆盖 `encrypted-dns-server`。

恢复 `system` DNS 可能暂时掩盖问题，也会改变公开配置的解析边界。先定位订阅服务器、代理节点域名或网络本身的解析故障。

### 局域网设备无法访问代理

公开配置关闭了 Wi-Fi 和热点代理入口。需要把 iPhone 用作局域网代理或网关时，应在私有副本中单独评估访问控制和同网段风险。

## 安全与隐私

公开仓库不得包含下面这些内容。

- 真实订阅地址和 Sub-Store 私有接口
- 节点地址、端口、用户名和密码
- Token、Cookie、会话和设备标识
- MITM CA、私钥和证书密码
- 私有脚本、重写和未审计模块

本配置没有 MITM、脚本或重写段。用户自行加入的节点、模块、MITM 和脚本不在仓库审计范围内。

发现敏感信息泄露时，应先撤销或轮换凭据，再清理 Git 历史。只删除最新文件无法移除已经公开的历史内容。

更多要求见 [SECURITY.md](./SECURITY.md) 和 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 发布前检查

- [ ] `Surge.conf` 仍使用 `example.invalid` 占位符
- [ ] `NodePool` 为 `select` 和 `hidden=1`
- [ ] 只有 `NodePool` 持有 `policy-path`
- [ ] `AllServer` 与五个地区组均为 `smart, Fail-Closed`
- [ ] Telegram 没有 DIRECT 路径
- [ ] ApplePush 顺序为 Proxy、DIRECT
- [ ] BiliBiliIntl 位于 BiliBili 国内规则前，策略分别为 Streaming 与 DIRECT
- [ ] STUN 位于 `GEOIP,CN,DIRECT` 前并进入 Proxy
- [ ] Game 位于 OneDrive 和 Microsoft 前
- [ ] Netflix 不含 IP-CIDR 与 IP-CIDR6
- [ ] AliDNS 的三个引导地址仍在同一 Host 行
- [ ] 53、853 和 8853 端口控制仍在
- [ ] 29 个运行时规则地址均固定到 `r12.16-20260825`
- [ ] 上传提交后已创建同名发布标签
- [ ] 29 个远程源与 86 条活动规则审计通过
- [ ] 56 项配置测试与 17 项 ZIP 测试通过
- [ ] 发布清单与两份 SHA-256 清单已刷新
- [ ] 完整 ZIP 已重新生成并通过内容检查

## 资料与许可证

配置结构和策略组选型参考了 Surge 官方文档及多个公开配置。实际运行的第三方规则来源、固定提交和 SHA-256 以 [Rules/upstreams.lock.json](./Rules/upstreams.lock.json) 为准。

Surge 官方资料

- [Surge 规则系统](https://manual.nssurge.com/rules/overview.html)
- [Rule Set](https://manual.nssurge.com/rules/ruleset.html)
- [Smart Group](https://kb.nssurge.com/surge-knowledge-base/guidelines/smart-group)
- [Policy Including](https://manual.nssurge.com/policy-groups/policy-including.html)
- [策略组通用参数](https://manual.nssurge.com/policy-groups/parameters.html)
- [自动策略组测试](https://kb.nssurge.com/surge-knowledge-base/technotes/testing-group)

参考配置

- [Rabbit-Spec Surge Developer](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-Developer.conf)
- [Rabbit-Spec Surge EN](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-EN.conf)
- [As-Lucky Lucky](https://raw.githubusercontent.com/As-Lucky/Lucky/main/Lucky-Surge.conf)
- [Coldvvater Surge 配置](https://gist.githubusercontent.com/Coldvvater/8093bc6be4340b5324b4a343493becfe/raw/Surge,conf)
- [TutuBetterRules Surge](https://github.com/bunizao/TutuBetterRules/blob/tutu/Surge/Surge.conf)
- [Aioneas Surge](https://github.com/Aioneas/Surge)
- [Thoseyearsbrian Aegis](https://github.com/Thoseyearsbrian/Aegis)

仓库原创脚本、配置结构和文档使用根目录 [MIT License](./LICENSE)。第三方规则和数据继续遵循各自许可证，许可证副本位于 [THIRD_PARTY_LICENSES](./THIRD_PARTY_LICENSES)。来源与本地修改范围见 [NOTICE.md](./NOTICE.md)，版本迁移见 [MIGRATION.md](./MIGRATION.md)，更新记录见 [CHANGELOG.md](./CHANGELOG.md)。
