# Surge iOS Privacy + Push R12.17

这是一份面向 Surge iOS 的规则模式配置。它把订阅导入、自动选路、地区选择和服务分流分开处理，并保留明确的失败关闭边界。公开版本不包含节点、订阅令牌、证书或脚本。

R12.17 在既有分流修正上完成运行资源自有化。Xbox、Minecraft、Bethesda 和 Forza 会先进入 `Games`，不会被 Microsoft 规则提前截获；Viu 也不会再被 HBO 的 `now.com` 父级后缀误分流。Netflix 删除了宽泛云网段，改用 `IP-ASN,2906,no-resolve`。Pegasus IOC 固定副本现已进入本仓库，Surge 运行时不再直接访问第三方规则仓库。

公开主配置地址

https://raw.githubusercontent.com/shenjlngbIng/surge/main/Surge.conf

## 当前基线

| 项目 | 当前值 |
| --- | --- |
| 配置版本 | R12.17 |
| 推荐环境 | Surge iOS 5.14.6 或更高 |
| 运行模式 | Rule |
| 策略组 | 33 个 |
| 主配置活动规则 | 98 条 |
| 仓库运行资源 | 30 个 |
| 普通 RULE-SET | 27 个 |
| DOMAIN-SET | 3 个，含 1 个安全 IOC 和 2 个精确域名集 |
| 中国域名 | 306 条 |
| 全球域名 | 116 条 |
| 精确域名交叉冲突 | 0 |
| Pegasus IOC | 1,438 条 |
| 第三方运行时 URL | 0 个 |
| 配置故障注入测试 | 78 项 |
| ZIP 路径回归测试 | 24 项 |
| 发布清单与升级清理测试 | 10 项 |

配置依赖 Smart 策略组。设备无法识别 `smart` 时，应更新 Surge 或恢复相应功能授权。不要把 Smart 组自行改回包含全部订阅节点的 `fallback` 或 `url-test`，这会重新带来网络切换后的集中探测。

## 与常见公开配置相比

公开配置各有侧重。这里对照 README 末尾列出的公开模板，重点观察订阅接入、自动选路、规则来源、失败处理和发布方式。差异用于说明本配置的取向，不作优劣排名。

| 对照维度 | 公开配置中的常见写法 | R12.17 的处理 | 使用上的区别 |
| --- | --- | --- | --- |
| 订阅接入 | 多个自动组或地区组分别填写 `policy-path` | 只有隐藏的 `NodePool` 持有订阅地址 | 订阅只下载和解析一次，来源关系更容易检查 |
| 自动选路 | 用 `url-test`、`fallback` 按固定间隔测试整组节点 | `AllServer` 与五个地区组使用 Smart，并从 `NodePool` 取节点 | 自动选择会参考真实连接质量和站点记录，减少多个组重复测试同一订阅 |
| 空订阅处理 | 自动组没有可用成员时可能被 Surge 临时替换为 DIRECT | 每个 Smart 组都显式保留 `Fail-Closed` 哨兵 | 订阅失效和地区零匹配会明确失败，避免无提示直连 |
| 服务策略 | 不少模板给流媒体、AI 或最终策略同时提供代理和 DIRECT | 代理服务组不提供 DIRECT，`Final` 只提供 `Proxy` 与 `REJECT` | 临时选错策略时也不容易越过代理边界 |
| 推送可达性 | Telegram 数据与 Apple 推送经常跟随同一个代理组 | Telegram 保持代理，APNs 单独进入 `ApplePush` | 代理故障时只有 APNs 可以按顺序回落直连，应用数据仍受原策略约束 |
| 规则来源 | 直接引用第三方仓库当前分支，内容会随上游更新 | 19 个服务源和 1 个安全资源固定提交、Blob 与 SHA-256；Surge 只加载本仓库发布标签 | 每次发布所用规则可以复查，第三方异常变化不会直接进入设备 |
| 规则精度 | 完整接收上游共享 CDN、云平台、遥测和宽网段 | 按服务删除非唯一归属项，并维护精确的中国与全球域名表 | 降低共享基础设施把无关应用带进错误策略的概率 |
| 规则顺序 | 主要依靠维护者手工保持先后关系 | 关键先后关系写入审计器和故障注入测试 | 服务规则被大规则提前截获时，验证命令会直接失败 |
| 发布方式 | 以单个配置文件或规则目录为主要交付内容 | 配置、规则、锁文件、工具、清单、校验和与工作流一同发布 | 下载者可以核对文件完整性，维护者可以复现同一份 ZIP |

### 节点来源只有一个入口

`NodePool` 是隐藏的订阅容器。它使用 `select`，只负责读取 `policy-path`，不会承担业务流量，也不会主动测试整份订阅。`AllServer` 和五个地区组通过 `include-other-group=NodePool` 取得真实节点，服务组再选择这些稳定的上层策略。

这种分层把节点来源、自动选择和业务分流拆开了。订阅地址只出现一次，地区正则也只作用于同一个节点池。节点重复、策略组各自下载订阅、多个自动组同时测试等问题都更容易定位。

### Smart 承担日常自动选择

Smart 会结合真实连接的首包延迟、重传情况和站点使用记录评估节点。节点较多时，常规测试只覆盖一部分成员，手动测试才会检查全部成员。R12.17 因此没有给 `AllServer` 和地区组设置 `interval`、`timeout` 或 `evaluate-before-use`。

Smart 仍然会做定期和必要的连通性测试。这里减少的是多个 `url-test` 或 `fallback` 对同一订阅反复发起整组测试，后台请求不会被承诺降到零。

### 失败路径保持收紧

Surge 在策略组没有可用代理成员时可能临时使用 DIRECT。R12.17 给 `AllServer` 和五个地区组加入本机 `127.0.0.1:1` 哨兵，让组内始终存在一个代理类型成员。哨兵连接预期失败，失败结果不会变成直连。

`Final` 默认进入 `Proxy`，并提供 `REJECT` 作为更严格的手动选择。代理类服务组统一移除 DIRECT。唯一保留的可用性例外是 `ApplePush`，它先尝试 `Proxy`，五秒内不可用才回落 DIRECT。这条退路只服务 APNs，不会放宽 Telegram 应用数据或其他国际服务。

### 第三方规则先经过本地筛选

第三方列表在这里充当待审核输入，生成后的仓库快照才会交给 Surge。`Rules/upstreams.lock.json` 记录 19 个服务上游的提交、文件路径、Git Blob、SHA-256、排除项和显式本地补充；`Rules/resources.lock.json` 单独记录 Pegasus 的固定来源与本地副本；`Rules/maintained_sources.lock.json` 披露其余 10 个仓库维护列表的来源状态、哈希、条目数和许可边界。两个更新工具只在维护时访问第三方，设备运行时只访问 `shenjlngbIng/surge` 的固定发布标签。

终审曾发现 8 个服务文件中有 278 条历史本地行只存在于生成结果，没有写入锁。现在这些行已经全部进入对应服务的 `add` 数组。更新器只使用固定上游、类型过滤、排除项和显式 `add` 生成文件，不再读取旧输出作为输入；从空目录重建与当前 19 个服务快照逐字节一致。历史来源不明确的行不会伪造第三方归属，锁文件会保留“仓库既有审阅内容、历史许可仍需所有者复核”的披露。

筛选会处理域名归属范围。共享遥测、公共云、通用 CDN 和跨服务后缀不会因为出现在某个上游列表中就自动进入对应策略。Netflix 使用官方网络 `AS2906`，Disney、HBO、Microsoft、Bahamut 和 Game 则删除了各自上游中的共享平台项。这样做会牺牲一点规则数量，换来更清楚的命中边界。

### 规则顺序也是受检内容

Surge 使用首条命中结果，两个正确的规则文件放错先后仍会产生错误分流。R12.17 明确检查 YouTube 位于 Google 前，Game 位于 OneDrive 和 Microsoft 前，专用流媒体位于通用媒体和中国域名兜底前。

`tools/audit_config.py` 会检查这些位置关系。78 项故障注入测试还会故意改坏策略类型、成员、可见性、资源归属、规则顺序和失败边界，确认审计器能够拦住错误。配置维护因此不只依赖人工浏览几百行文本。

### DNS 和本地网络有明确边界

配置同时提供 AliDNS 的普通 DNS、DoH 和 DoT，并为加密 DNS 写入固定引导地址。`encrypted-dns-follow-outbound-mode=false` 用来避免内部解析跟随业务代理形成循环。传统 53 端口会被 Surge 接管，进入规则系统的 53、853 和 8853 外部连接受到单独控制。

这个设置也意味着 Surge 自己的加密 DNS 连接固定使用 DIRECT，不会跟随 AI、流媒体或地区策略。DoH/DoT 会加密查询内容，但 AliDNS 仍是解析提供方；没有 MITM 时，端口规则也无法识别所有伪装为普通 HTTPS 的应用内置 DoH。因此这里的“DNS 防绕过”指常见端口和已知服务边界，不宣称绝对阻断任意应用自带解析器。

局域网、CGNAT、回环和 IPv6 本地范围均有明确规则。Wi-Fi 代理入口、热点入口和 Web 控制面板默认关闭。节点不支持 UDP 时连接会拒绝，QUIC 采用 `per-policy`，STUN 进入隐藏的 `UDP` 组且默认仍为 `Proxy`。这些选择共同限定了哪些流量可以离开代理路径。

### 保持纯分流配置

公开文件没有 MITM、脚本和重写段，也不携带证书。它只处理网络接管、策略选择、DNS、规则匹配和推送可达性。下载者无需安装 CA，维护者也不用同时审查脚本权限、解密范围和重写副作用。

### 发布包可以复现和验证

仓库把配置当作一套需要构建和验收的文件发布。四份锁文件分别记录运行配置不变量、服务规则上游、独立静态资源来源和仓库维护列表披露。发布前会执行配置审计、规则审计、精确域名交叉检查、固定来源校验、78 项故障注入、24 项 ZIP 路径测试和 10 项严格发布清单测试。

最终 ZIP 使用固定顺序、时间戳和权限，并附带文件清单与两份 SHA-256 清单。`tools/release_inventory.py` 是打包、发布清单和校验和共同使用的唯一允许清单；未知文件、`.env`、日志、符号链接和特殊文件会让构建失败。安装工作流还会先核对用户从包外取得的整包 SHA-256，再限制文件数量、单文件大小、解压总量和路径类型。升级时只清理旧发布清单中存在、但新清单已取消的受管理文件，不碰用户自有路径。

## 这份配置怎样工作

一次连接进入 Surge 后，会依次经过下面几层。

1. Surge 接管符合条件的网络和 DNS 请求。
2. 本地网段、CGNAT、回环地址和必要的 Apple 系统查询先行直连。
3. Pegasus IOC 先进入可关闭的 `Security` 阻断组。
4. APNs、广告、AI、流媒体和国际服务按专用规则匹配。
5. 中国与全球精确域名表负责补充常用服务边界。
6. STUN 进入 `UDP` 组，默认仍走代理。
7. 未命中的中国 IP 由 `GEOIP,CN,DIRECT,no-resolve` 处理。
8. 其余连接落入 `FINAL,Final,dns-failed`。

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
| ApplePush | fallback | Proxy | 隐藏；APNs 代理优先，失败后回落 DIRECT |
| AdBlock | select | REJECT | 隐藏；广告默认阻断，排错选项继续保留在配置中 |
| Security | select | REJECT | 隐藏；Pegasus IOC 默认阻断，排错选项继续保留在配置中 |
| UDP | select | Proxy | 隐藏；STUN/UDP 默认代理，DIRECT 与 REJECT 继续保留在配置中 |
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
ApplePush = fallback, Proxy, DIRECT, interval=60, evaluate-before-use=true, no-alert=0, hidden=1
~~~

代理可用时，APNs 优先走代理。`evaluate-before-use=true` 会在首次选择前等待首轮评估，失败后再回落直连；单次探测上限由全局 `test-timeout=5` 控制。`include-all-networks=true` 和 `include-apns=true` 均已开启。`ApplePush` 与 `AdBlock`、`Security`、`UDP` 一起设置为 `hidden=1`，只精简策略选择页面，不改变规则调用和默认成员。

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
proxy-test-udp = apple.com@223.5.5.5
block-quic = per-policy
PROTOCOL,STUN,UDP
~~~

节点不支持 UDP 时，连接会明确失败，不会静默直连。Surge 会用国内可达的 DNS 目标检查节点 UDP 能力；QUIC 是否阻断由所选策略能力决定。STUN 默认进入 `UDP=Proxy`。需要兼容性排查时，应先在私有副本中把 `UDP` 临时改为 `hidden=0`，再选择 DIRECT 或 REJECT；其中 DIRECT 会暴露真实公网 IP。

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
5. 本仓库 Pegasus 安全域名表。
6. APNs。
7. Apple 国内服务、微信和明确直连项。
8. 广告规则。
9. ChatGPT、Claude 和 Gemini。
10. 专用流媒体规则，并用 `viu.now.com` 精确覆盖 HBO 的父级后缀。
11. Telegram、GitHub、X 和 Google。
12. Game、OneDrive 和 Microsoft，并提前处理共享登录域名和过宽云网段。
13. 中国与全球精确域名表。
14. STUN、中国 GEOIP 和 Final。

Game 排在 Microsoft 前。这样，两个规则集中重叠的 Xbox、Minecraft、Bethesda 和 Forza 域名会进入 `Games`。Google 的下载、更新和消息域名不再留在 `Direct.list`，现在统一进入 `Google`。

`cache.video.iqiyi.com` 已从通用媒体规则删除，会被 `China.list` 的爱奇艺后缀接住。TikTok 中宽泛的 `snssdk.com` 也已删除，国内字节服务会回到中国域名兜底。TikTok 自己使用的精确 CDN 主机仍保留在 TikTok 专用规则中。

## 远程规则库存

Surge.conf 通过 jsDelivr 加载仓库中的 30 个规则文件。运行地址统一固定到发布标签 `r12.17-20260825`。其中 19 份服务快照保留固定上游、提交、Blob、SHA-256 和本地处理说明；Pegasus 另有独立来源锁；其余 10 个文件由仓库直接维护，并在 `maintained_sources.lock.json` 中逐一披露。设备运行时没有第三方静态规则 URL。

这里的“运行资源自有化”专指 30 个外部 `RULE-SET`/`DOMAIN-SET` 的内容进入自己的仓库，不表示所有网络基础设施都由仓库托管。文件仍由 jsDelivr/GitHub 标签交付；`GEOIP,CN` 使用 Surge 默认 GeoIP Country 数据库，9 条 `IP-ASN` 使用应用内置 ASN 数据；AliDNS、Cloudflare、华为连通性测试和私有 `NodePool` 也是外部服务。GeoIP 会按 `disable-geoip-db-auto-update=false` 更新，ASN 数据随 Surge 应用更新。这些属于公开披露的系统依赖，不计入 30 个静态规则文件。

| 规则文件 | 策略 | 活动条目 |
| --- | --- | ---: |
| Pegasus.list | Security | 1,438 |
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

### Pegasus 固定副本

`Rules/Pegasus.list` 来自 Amnesty Tech 固定提交 `3d8f248a0d015f183724ae7d096a5c46a8bb5fc7` 的 `2021-07-18_nso/domains.txt`。本地文件保留 1,438 个非空域名，不扩大为后缀；上游 Git Blob、上游 SHA-256、本地 SHA-256、条目数量和处理方式都记录在 `Rules/resources.lock.json`。

普通设备只下载你仓库中的 `Pegasus.list`。`tools/update_external_resources.py` 才会在维护时访问固定的第三方提交，并且只有 Blob、SHA-256 和渲染结果同时符合锁文件时才接受内容。若要升级上游提交，需要先审阅域名差异，再同步修改资源锁，不能把 URL 改成 `main`。

## 服务规则的本地筛选

19 个第三方服务规则固定在 `blackmatrix7/ios_rule_script` 的提交 `c00517ce10760a93728b241923a451dfa617be80`。更新工具会核对 Git Blob 与 SHA-256，再合并本地规则。

合并过程会过滤 iOS 不使用的 `PROCESS-NAME`，并拒绝未经单独审核的新 `IP-ASN`。每个服务还可以在 `Rules/upstreams.lock.json` 中声明精确排除项、禁用的规则类型和经过审核的本地补充。

R12.17 保留并验证下面几类误分流处理。

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
| Surge.conf | R12.17 主配置 |
| Rules/*.list | 30 个仓库运行规则快照 |
| Rules/r10.lock.json | 配置哈希、规则库存和安全不变量 |
| Rules/upstreams.lock.json | 固定上游、排除项与本地补充 |
| Rules/resources.lock.json | Pegasus 固定来源、上游与本地哈希 |
| Rules/maintained_sources.lock.json | 10 个仓库维护列表的来源状态、哈希和许可披露 |
| tools/audit_config.py | 配置结构、策略组和规则顺序审计 |
| tools/audit_rules.py | 规则库存、哈希和语义边界审计 |
| tools/audit_precise_domains.py | 中国与全球精确域名审计 |
| tools/test_audit_config.py | 78 项配置故障注入测试 |
| tools/test_stage_surge_zip.py | ZIP 路径白名单回归测试 |
| tools/release_inventory.py | 打包、清单与校验和共用的严格发布允许清单 |
| tools/test_release_inventory.py | 未知文件、符号链接与升级清理回归测试 |
| tools/update_service_rules.py | 固定上游下载、合并与验证 |
| tools/update_external_resources.py | 验证或刷新固定的独立静态资源 |
| tools/embed_runtime_rules.py | 刷新锁文件元数据 |
| tools/convert_to_remote_rules.py | 校验远程规则引用库存 |
| tools/generate_release_manifest.py | 生成发布文件清单 |
| tools/generate_checksums.py | 生成两份 SHA-256 清单 |
| tools/package_release.py | 生成确定性完整 ZIP |
| tools/stage_surge_zip.py | 安全暂存候选 ZIP |
| AUDIT_REPORT.md | 全仓检查结果、修改前后利弊与发布条件 |
| RELEASE_MANIFEST.txt | 发布文件及内容摘要 |
| SHA256SUMS.txt | 发布文件 SHA-256 |
| SHA256SUMS_fixed.txt | 与主清单逐字节一致的冻结副本 |
| .github/workflows/install.yml | 安装与持续审计工作流 |
| THIRD_PARTY_LICENSES | 第三方许可证副本 |

当前发布布局包含 30 个规则文件和 15 个 Python 工具。完整文件数以 `RELEASE_MANIFEST.txt`、`SHA256SUMS.txt` 与打包命令的实际输出为准，三者必须互相一致，不在 README 中维护一组容易过期的硬编码总数。

## 上传与发布

### 已有仓库直接更新

解压完整发布包，把其中全部文件按原目录结构上传到仓库。`Rules`、`tools`、`.github` 和 `THIRD_PARTY_LICENSES` 都要保留。提交到 `main` 后，创建指向本次提交的标签 `r12.17-20260825`。标签创建完成并等待 jsDelivr 同步后，再在 Surge 中刷新外部资源。

只上传 `Surge.conf` 会让规则快照、服务筛选和锁文件缺失，完整审计也无法运行。

### 使用安装工作流

也可以把未解压的 `Surge-R12.17-self-maintained-20260825.zip` 放在仓库根目录，并保留 `.github/workflows/install.yml`。随后在 Actions 中手动运行 `Install and audit Surge R12.17`，并在必填的 `archive_sha256` 输入框填写包外公布的整包 SHA-256。

安装任务会在解压和执行 ZIP 内工具之前验证整包 SHA-256，再检查文件数量、单文件大小、解压总量和路径安全。它拒绝绝对路径、路径穿越、反斜杠、未知发布文件、大小写或 Unicode 碰撞和特殊设备条目。升级时只删除旧发布清单明确管理、但新版本已经取消的文件，用户自有文件不会因为发布同步而被清理。验证完成后任务才会提交，并创建固定的规则发布标签。

### 本地生成发布包

~~~bash
python3 tools/package_release.py --output ../Surge-R12.17-self-maintained-20260825.zip
~~~

ZIP 使用固定时间戳、固定顺序和统一权限。同一份内容可以生成一致的归档结构。Git 元数据、缓存、pyc 和已知的候选压缩包不会进入发布包；其他未知文件不会被静默忽略，而是直接阻止构建。整包 SHA-256 必须在 ZIP 之外发布，因为归档不能可靠地把自身哈希写入自身。

## 维护与审计

### 完整验证命令

~~~bash
python3 -m compileall -q tools
python3 tools/convert_to_remote_rules.py
python3 tools/update_external_resources.py --verify-lock
python3 tools/update_service_rules.py --verify-lock
python3 tools/embed_runtime_rules.py
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/audit_precise_domains.py
python3 tools/test_audit_config.py
python3 tools/test_release_inventory.py
python3 tools/test_stage_surge_zip.py
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
sha256sum -c SHA256SUMS.txt
cmp --silent SHA256SUMS.txt SHA256SUMS_fixed.txt
python3 tools/package_release.py --output ../Surge-R12.17-self-maintained-20260825.zip
~~~

正常基线会出现下面的关键结果。

~~~text
PASS: repository-only runtime resources=30 third_party_runtime_urls=0 embedded_rule_contents=0
PASS: verified pinned resources=1 entries=1438
PASS: verified upstream lock services=19
PASS R12.17 groups=33 rules=98 runtime_resources=30
PASS R12.17 runtime_sources=30 local_rule_files=30 rules=98 pegasus=1438
PASS precise domains DIRECT=306 Proxy=116 conflicts=0
PASS R12.17 mutations=78
PASS: strict release inventory regression cases=10
PASS: ZIP allowlist regression cases=24
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

上游提交升级需要单独审阅。更新者应核对许可证、文件路径、Blob、SHA-256、排除项和条目变化，再提交新的锁文件。服务文件只允许由固定上游和锁中的显式输入生成；不要通过手改输出再运行更新器来隐式保留规则。

### 更新固定 Pegasus 资源

离线核对仓库副本与来源锁：

~~~bash
python3 tools/update_external_resources.py --verify-lock
~~~

联网下载固定提交并确认生成结果仍与当前锁完全一致：

~~~bash
python3 tools/update_external_resources.py --download --check
~~~

升级到新的上游提交时，先比较全部新增、删除域名，再更新 `Rules/resources.lock.json` 中的提交、路径、Blob、上游 SHA-256 和本地 SHA-256。不得只替换下载地址，也不得让 `Surge.conf` 直接引用第三方 URL。

## 常见问题

### AllServer 只有 Fail-Closed

`NodePool` 没有返回可用节点。常见原因包括占位 URL 尚未替换、订阅过期、输出格式不兼容或节点语法无效。

先检查私有 `policy-path` 的状态和输出内容，再刷新外部资源。不要删除 `Fail-Closed`，也不要把 `Final` 改成 DIRECT。

### 地区组只有 Fail-Closed

订阅已有节点，但节点名称没有命中地区正则。在私有 Sub-Store 输出中补充明确的地区名称或旗帜，或者审慎扩展对应正则。

### Telegram 前台可用但锁屏没有通知

确认 `include-apns=true`，检查 `APNs.list` 是否加载成功，并查看请求是否进入隐藏的 `ApplePush`。首次使用会等待首轮评估，代理无法连接时再尝试 DIRECT；需要人工切换时，先在私有副本中临时设置 `hidden=0`。

### 网络切换后仍有大量请求

检查当前启用的配置是否为 R12.17。`NodePool` 应为隐藏的 `select`，`AllServer` 和五个地区组应为 `smart`。除 `ApplePush` 外，不应存在读取整份订阅的 `fallback`、`url-test` 或 `load-balance`。

手动点击测试全部策略本来就会产生集中请求。若没有手动测试，继续在 Surge 最近请求中查看发起进程、策略路径和目标地址。

### 规则文件出现 404

确认仓库已经创建标签 `r12.17-20260825`，文件大小写和目录结构必须与 `Surge.conf` 完全一致。新标签需要等待 jsDelivr 同步，随后再刷新外部资源。

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

仓库审计属于静态、来源和构建验证，不能替代 Surge iOS 真机上的订阅解析、节点连通、APNs、流媒体地区与 Wi-Fi/蜂窝切换测试。完整自动检查结论和仍需真机确认的项目见 [AUDIT_REPORT.md](./AUDIT_REPORT.md)。

发现敏感信息泄露时，应先撤销或轮换凭据，再清理 Git 历史。只删除最新文件无法移除已经公开的历史内容。

更多要求见 [SECURITY.md](./SECURITY.md) 和 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 发布前检查

- [ ] `Surge.conf` 仍使用 `example.invalid` 占位符
- [ ] `NodePool` 为 `select` 和 `hidden=1`
- [ ] `ApplePush`、`AdBlock`、`Security`、`UDP` 均为 `hidden=1`，默认成员顺序未改变
- [ ] 只有 `NodePool` 持有 `policy-path`
- [ ] `AllServer` 与五个地区组均为 `smart, Fail-Closed`
- [ ] Telegram 没有 DIRECT 路径
- [ ] ApplePush 顺序为 Proxy、DIRECT
- [ ] BiliBiliIntl 位于 BiliBili 国内规则前，策略分别为 Streaming 与 DIRECT
- [ ] `Pegasus.list` 从本仓库固定标签加载，`Security` 保留 DIRECT 排错开关
- [ ] STUN 位于 `GEOIP,CN,DIRECT,no-resolve` 前并进入 UDP 组
- [ ] `viu.now.com` 位于 HBO.list 前并进入 Streaming
- [ ] Google/YouTube 与 Microsoft/Game 的共享基础设施覆盖仍在专用规则前
- [ ] Game 位于 OneDrive 和 Microsoft 前
- [ ] Netflix 不含 IP-CIDR 与 IP-CIDR6
- [ ] AliDNS 的三个引导地址仍在同一 Host 行
- [ ] 53、853 和 8853 端口控制仍在
- [ ] 30 个运行时规则地址均属于本仓库并固定到 `r12.17-20260825`
- [ ] `Surge.conf` 中不存在第三方 RULE-SET 或 DOMAIN-SET URL
- [ ] 上传提交后已创建同名发布标签
- [ ] 30 个运行资源、33 个策略组与 98 条活动规则审计通过
- [ ] 78 项配置测试、24 项 ZIP 测试与 10 项发布清单测试通过
- [ ] 手动安装使用包外 SHA-256，旧受管理文件清理测试通过
- [ ] 发布清单与两份 SHA-256 清单已刷新
- [ ] 完整 ZIP 已重新生成并通过内容检查

## 资料与许可证

配置结构和策略组选型参考了 Surge 官方文档及多个公开配置。服务规则来源以 [Rules/upstreams.lock.json](./Rules/upstreams.lock.json) 为准，独立安全资源来源以 [Rules/resources.lock.json](./Rules/resources.lock.json) 为准，仓库维护列表的来源状态与许可披露以 [Rules/maintained_sources.lock.json](./Rules/maintained_sources.lock.json) 为准；这些维护地址都不会被 Surge 直接加载。

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

固定维护输入

- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) — 19 份服务规则的固定输入
- [AmnestyTech/investigations](https://github.com/AmnestyTech/investigations) — Pegasus IOC 的固定输入

仓库原创脚本、配置结构和文档使用根目录 [MIT License](./LICENSE)。第三方规则和数据继续遵循各自许可证，许可证副本位于 [THIRD_PARTY_LICENSES](./THIRD_PARTY_LICENSES)。来源与本地修改范围见 [NOTICE.md](./NOTICE.md)，版本迁移见 [MIGRATION.md](./MIGRATION.md)，更新记录见 [CHANGELOG.md](./CHANGELOG.md)。
