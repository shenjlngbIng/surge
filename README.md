# Surge iOS Privacy + Push R12.15

一份面向 Surge iOS 的规则模式配置，重点解决三件事：

- Wi-Fi、蜂窝数据和热点切换后，不再由全订阅 fallback/url-test 集中遍历所有节点。
- Telegram 应用流量始终走代理，同时保留 APNs 的独立通知容灾链路。
- DNS、最终策略和空订阅状态保持失败关闭，不用静默 DIRECT 掩盖故障。

R12.15 将订阅导入与自动选路彻底拆分。隐藏的 NodePool 只下载节点，AllServer 与五个地区组使用 Smart 决策。DNS、Telegram、APNs、85 条活动规则和既有局域网边界没有因为这次测速修复而改变。

> 公开版故意使用不可路由的订阅占位符。下载后必须在私有副本中填入自己的 Surge 格式订阅地址，否则代理连接按设计失败。

## 版本与前置条件

| 项目 | 要求 |
| --- | --- |
| 平台 | Surge iOS |
| 推荐版本 | 5.14.6 或更高 |
| Smart 最低版本 | Surge iOS 5.11.0 |
| Smart 授权 | Surge iOS 功能更新订阅功能 |
| 配置模式 | Rule |
| 订阅输出 | Surge 策略列表，或含 Proxy 段的完整 Surge 配置 |
| 私密材料 | 只能保存在私有副本 |

如果设备无法识别 Smart 策略组，应先升级 Surge 或恢复功能更新订阅。不要把 AllServer 改回包含整份订阅的 fallback，也不要把五个地区组改回 url-test，否则会恢复网络切换后的集中测速问题。

## 这次修正解决什么

截图中的提示是 Surge 在一秒内处理了 310 个请求，最高频目标显示为某个 Port Map 地址。仅凭截图不能断言每一条请求都来自测速，但这个数量与“约 155 个节点，每个节点产生两次连通性请求”高度吻合。

R12.14 的 AllServer 同时承担订阅导入与 fallback 检测。Surge 在网络接口切换后会清理旧自动测试结果，组再次被使用时会重测成员。单纯把 interval 从 60 秒改为 600 秒只能延长正常结果的有效期，不能阻止网络切换后结果失效。

下面几种做法都不是根治：

| 做法 | 为什么无效或有副作用 |
| --- | --- |
| 增大 interval | 网络切换仍可能使旧结果失效 |
| 增大 timeout | 只会让故障测试等待更久 |
| 设置 no-alert | 只隐藏部分策略变化提醒，不减少请求 |
| 保留 evaluate-before-use | 首次使用还会等待整组评估 |
| 删除 Fail-Closed | 可能把故障变成意外直连 |
| Final 改为 DIRECT | 隐藏节点或规则错误，破坏隐私边界 |

R12.15 的处理方式是改变职责结构，而不是调整一个测速数字。

## 快速开始

### 1. 获取公开配置

主配置地址：

https://raw.githubusercontent.com/shenjlngbIng/surge/main/Surge.conf

推荐同时获取完整仓库，因为主配置依赖 Rules、锁文件、审计工具、许可证和发布清单。只下载 Surge.conf 可以运行，但无法完成本仓库提供的完整性审计。

### 2. 创建私有副本

不要直接在公开分支中填真实订阅。复制 Surge.conf，在私有副本中找到：

~~~ini
NodePool = select, policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL, update-interval=3600, no-alert=0, hidden=1, include-all-proxies=0
~~~

只替换 policy-path 的 URL：

~~~ini
NodePool = select, policy-path=https://sub.store/download/你的完整输出地址?target=Surge, update-interval=3600, no-alert=0, hidden=1, include-all-proxies=0
~~~

不要修改后面的类型和安全参数，也不要把真实地址提交到 GitHub。

### 3. 导入并刷新

1. 在 Surge iOS 中导入私有副本。
2. 重新载入配置或刷新外部资源。
3. 确认 AllServer 能解析到真实节点。
4. 确认香港、台湾、日本、新加坡和美国组能匹配相应节点。
5. 将 Proxy 保持为 AllServer，或按需求选择地区 Smart 组。
6. 完成 Wi-Fi → 蜂窝数据 → Wi-Fi 切换测试。

NodePool 设置了 hidden=1，因此它不出现在普通策略选择页面。它是内部节点仓库，不是给规则直接使用的策略。

## 策略架构

~~~mermaid
flowchart TD
    A["私有 Surge 订阅"] --> B["NodePool<br/>select · hidden"]
    B --> C["AllServer<br/>smart + Fail-Closed"]
    B --> D["五个地区组<br/>smart + Fail-Closed"]
    C --> E["Proxy 与服务策略组"]
    D --> E
    E --> F["规则匹配后的真实出站"]
~~~

### NodePool：只导入，不测速，不路由

~~~ini
NodePool = select, policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL, update-interval=3600, no-alert=0, hidden=1, include-all-proxies=0
~~~

各字段含义：

| 字段 | 作用 |
| --- | --- |
| select | 被动保存成员，不执行自动组的整组测速 |
| policy-path | 唯一的私有订阅入口 |
| update-interval=3600 | 每小时检查远程订阅更新 |
| hidden=1 | 不在普通策略选择界面暴露基础设施组 |
| include-all-proxies=0 | 不把 Fail-Closed 或其他本地策略重复导入 |

NodePool 不被任何规则、服务组或 Proxy 直接列为可选成员。它只通过 include-other-group 被六个 Smart 组读取。

### AllServer：总节点 Smart 决策

~~~ini
AllServer = smart, Fail-Closed, no-alert=0, hidden=0, include-all-proxies=0, include-other-group=NodePool
~~~

AllServer 是 Proxy 的默认成员。Smart 会利用实际连接表现、失败惩罚和必要的恢复探测选择策略，不再依赖固定周期对整份订阅做 fallback 遍历。

这不等于“永远零测速”。首次使用、节点异常、手动测试和恢复验证仍可能产生少量探测。R12.15 要消除的是网络切换后由配置结构触发的全订阅集中请求。

Smart 官方也不建议塞入大量几乎不会使用的低质量线路。若订阅有上百个节点，私有侧还应做一次质量整理：

- 在 Sub-Store 中删除“剩余流量、到期时间、官网”等非节点条目。
- 移除长期失效、协议不兼容和质量明显低于主力线路的节点。
- 保留质量接近的主力节点，再加入少量次级容灾节点。
- 地区限制服务继续使用对应地区 Smart 组，不让 Smart 猜测内容解锁地区。
- 没有明确需求时不要配置夸张的 policy-priority 权重。

仓库不写死节点数量或通用排除正则，因为不同供应商的命名差异很大。节点清洗应在私有 Sub-Store 输出阶段完成，公开配置只负责安全地消费结果。

### 地区组：直接筛选 NodePool

香港、台湾、日本、新加坡和美国组全部使用同一结构：

~~~ini
HongKong = smart, Fail-Closed, policy-regex-filter=地区正则, no-alert=0, hidden=0, include-all-proxies=0, include-other-group=NodePool
~~~

地区组不再把 AllServer 当作节点源。这样可以避免“总组自动测试一次，地区组再评估一次”的级联结构，同时保留地区名称筛选和 Smart 自学习。

地区正则同时覆盖中文、繁体字、旗帜、英文城市和常见缩写。配置没有排除“专用”“解锁”等节点名称，以免误删流媒体优化节点。

### 服务策略组

ChatGPT、Claude、Gemini、GitHub、YouTube、Netflix、Disney+、HBO、PrimeVideo、Emby、TikTok、Bahamut、Spotify、Telegram、Apple、Google、Microsoft、Games 等服务组仍为手动 select。

服务组只选择 Proxy、地区 Smart 组或 AllServer，不直接读取 NodePool。这样既能为单个服务固定地区，也不会重复创建订阅加载器。

## 失败关闭模型

### Fail-Closed 哨兵

~~~ini
[Proxy]
Fail-Closed = http, 127.0.0.1, 1, no-error-alert=true
~~~

127.0.0.1:1 预期没有代理服务，因此选中后连接立即失败。no-error-alert 只抑制这个刻意失败产生的错误提醒，不会把失败改成 DIRECT。

### 为什么每个 Smart 组都显式包含哨兵

Surge iOS 5.11.3 起，完全没有子策略的 Smart 组可以使用替代策略。为防止空订阅或空地区筛选触发意外直连，本配置不依赖空组默认行为：

- AllServer 的第一个显式成员是 Fail-Closed。
- 五个地区组的第一个显式成员也是 Fail-Closed。
- NodePool 下载失败时，Smart 组仍不是空组。
- 地区正则零匹配时，地区组仍不是空组。

真实节点可用后，Smart 会根据成功连接表现选择真实节点；真实节点全部不可用时，失败会保持可见。

### 最终规则

~~~ini
Final = select, Proxy, REJECT, no-alert=0, hidden=0, include-all-proxies=0
FINAL,Final,dns-failed
~~~

未匹配流量默认继续进入 Proxy。用户可显式把 Final 改为 REJECT 做更严格的阻断，但配置不提供默认 DIRECT 兜底。

唯一有意保留的直连容灾是 ApplePush 中的 APNs 回落，原因见下一节。

## Telegram 与 APNs 为什么分开

Telegram 应用数据和 Apple Push Notification service 是两条不同链路。

| 流量 | 规则入口 | 策略 | 失败行为 |
| --- | --- | --- | --- |
| Telegram 消息、媒体、前台连接 | Rules/Telegram.list | Telegram → Proxy/地区组 | 不允许 DIRECT |
| iOS 后台通知唤醒 | Rules/APNs.list | ApplePush | Proxy 失败后允许 DIRECT |
| Apple 配置查询 | ls.apple.com 本地规则 | DIRECT | 避免进入代理回落环 |

ApplePush 保持：

~~~ini
ApplePush = fallback, Proxy, DIRECT, interval=60, timeout=5, no-alert=0, hidden=0
~~~

这是仓库唯一允许的 fallback 自动组。它只有两个成员，不会遍历整份订阅；Proxy 不可用时，APNs 仍可通过 DIRECT 维持锁屏通知。

Telegram 则没有任何 DIRECT 路径。审计器会拒绝把 Telegram 规则改为 DIRECT，也会拒绝让 APNs 规则绕过 ApplePush。

## 网络捕获边界

核心设置：

~~~ini
include-all-networks = true
include-local-networks = false
include-apns = true
include-cellular-services = false
~~~

| 设置 | 实际含义 |
| --- | --- |
| include-all-networks=true | 在 Wi-Fi、蜂窝数据等网络接口上继续接管普通流量 |
| include-local-networks=false | 不接管局域网设备间流量，降低 AirDrop、Bonjour 和设备发现兼容风险 |
| include-apns=true | 把 APNs 纳入 Surge 规则处理 |
| include-cellular-services=false | 不接管 IMS、VoLTE、Wi-Fi Calling、MMS 等运营商专用链路 |

include-cellular-services=false 不会关闭普通 4G/5G 数据，也不会取消 include-apns。

本地边界同时保留：

- RFC1918 私网：10/8、172.16/12、192.168/16。
- CGNAT：100.64/10。
- Loopback、链路本地地址和 IPv6 ULA。
- localhost、local 和局域网发现所需的 mDNS/SSDP 地址。

## DNS 设计

### 配置

~~~ini
dns-server = 223.5.5.5, 223.6.6.6
encrypted-dns-server = https://dns.alidns.com/dns-query, tls://dns.alidns.com
encrypted-dns-follow-outbound-mode = false
hijack-dns = *:53
allow-dns-svcb = false
use-local-host-item-for-proxy = false
~~~

Host 引导只有一条：

~~~ini
dns.alidns.com = 223.5.5.5, 223.6.6.6, 2400:3200::1
~~~

Surge 的 Host 映射按顺序匹配，同一主机的多个地址必须放在一行，避免前一条遮蔽后续 IPv4 或 IPv6 地址。

### 处理原则

- Surge 内部加密 DNS 固定使用 AliDNS HTTPS 与 TLS。
- encrypted-dns-follow-outbound-mode=false 让这条内部解析链不跟随普通代理规则，避免代理服务器域名解析形成循环。
- hijack-dns 接管应用发往 53 端口的传统 DNS。
- 规则显式阻断目的端口 53、853 和 8853，限制应用自带的传统 DNS/DoT 绕过。
- 对已知其他公共 DNS 域名按 DIRECT、Proxy 或 REJECT 边界处理。
- 不使用 system DNS 作为公开隐私配置的上游。

在 encrypted-dns-follow-outbound-mode=false 时，普通规则中的 DOH、DOH3、DOQ 协议组不会控制 Surge 内部加密 DNS，因此配置没有保留这些无效旧规则。

## UDP、QUIC 与原始 TCP

- udp-policy-not-supported-behaviour=REJECT：节点不支持 UDP 时明确失败，不偷偷直连。
- block-quic=all-proxy：代理路径阻断 QUIC，促使多数应用回退到 TCP/HTTP2。
- PROTOCOL,STUN,Proxy：STUN 明确进入代理。
- Telegram 核心地址与 Apple Push 主机加入 always-raw-tcp-hosts，减少协议识别兼容问题。

若某个应用不能正确从 QUIC 回退，应该针对该应用和节点协议排查，不应全局恢复 UDP 静默直连。

## 规则结构

当前主配置有 85 条活动规则，引用 28 个仓库托管的远程源：

- 26 个 RULE-SET。
- 2 个精确 DOMAIN-SET。
- China.list 有 306 个明确国内后缀。
- Global.list 有 116 个明确境外后缀。
- 两个精确域名集交叉冲突为 0。

匹配顺序从上到下：

1. 局域网发现与组播边界。
2. 私网、CGNAT、Loopback 与本地主机直连。
3. ls.apple.com 系统配置查询直连。
4. DNS 域名与端口控制。
5. APNs。
6. Apple 国内服务、微信和明确国内直连。
7. 广告、AI、流媒体与国际服务专用规则。
8. Telegram、GitHub、X、Google、Microsoft 与游戏。
9. 精确 China/Global 域名兜底。
10. GEOIP,CN,DIRECT。
11. STUN 代理。
12. FINAL,Final,dns-failed。

专用服务规则必须位于精确域名和 GEOIP 兜底之前。例如 YouTube 必须先于 Google，避免更宽的规则抢先匹配。

### 为什么规则文件保留在仓库

Surge.conf 只引用 jsDelivr 上的仓库文件，不把数万条快照嵌入主配置。Rules 目录仍完整提交，原因是：

- 可审阅每次上游变化。
- 可固定上游提交和文件哈希。
- 可验证许可证与来源。
- 可防止运行时上游静默变化。
- 可在发布包中完成离线完整性校验。

运行时地址统一使用：

~~~text
https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@main/Rules/文件名
~~~

## 仓库文件说明

| 路径 | 用途 |
| --- | --- |
| Surge.conf | R12.15 主配置 |
| Rules/*.list | 28 个提交并审计的远程规则源 |
| Rules/r10.lock.json | schema 8 配置、规则哈希和安全不变量 |
| Rules/upstreams.lock.json | 固定的第三方上游提交、Blob 与 SHA-256 |
| tools/audit_config.py | 配置结构和安全边界审计 |
| tools/audit_rules.py | 规则库存、锁文件和快照审计 |
| tools/audit_precise_domains.py | 国内外精确域名零冲突审计 |
| tools/test_audit_config.py | 49 项故障注入测试 |
| tools/test_stage_surge_zip.py | ZIP 路径白名单回归测试 |
| tools/update_service_rules.py | 固定上游规则合并与验证 |
| tools/embed_runtime_rules.py | 刷新锁文件元数据，不嵌入规则 |
| tools/package_release.py | 生成确定性完整发布 ZIP |
| RELEASE_MANIFEST.txt | 发布文件及内容摘要 |
| SHA256SUMS.txt | 发布文件 SHA-256 |
| SHA256SUMS_fixed.txt | 与主清单逐字节一致的冻结镜像 |
| .github/workflows/install.yml | 安装与持续审计工作流 |
| THIRD_PARTY_LICENSES | 第三方规则许可证副本 |

当前发布布局：

| 项目 | 数量 |
| --- | ---: |
| 规则文件 | 28 |
| Python 工具 | 12 |
| 清单记录文件 | 54 |
| SHA-256 记录文件 | 55 |
| ZIP 内普通文件 | 57 |

## 安装和发布

### 已有仓库直接更新

如果仓库已经包含完整文件，正常提交后 GitHub Actions 会在 Python 3.12 和 3.13 上执行全部审计。无需把发布 ZIP 永久提交到已安装仓库。

### 用工作流安装完整包

1. 在本地生成 Surge-R12.15-release.zip。
2. 把 .github/workflows/install.yml 放到目标仓库的相同路径。
3. 把未解压的 Surge-R12.15-release.zip 上传到仓库根目录。
4. 在 Actions 中手动运行 Install and audit Surge R12.15。

workflow_dispatch 安装任务会：

- 限制 ZIP 最多 128 个普通文件。
- 限制单个文件不超过 8 MiB。
- 限制解压总量不超过 32 MiB。
- 拒绝绝对路径、路径穿越、反斜杠和特殊设备条目。
- 检查必需文件。
- 在暂存目录验证 SHA-256。
- 展开完整仓库、删除 ZIP 并提交。

普通 push 和 pull_request 不执行安装，只做只读审计。

### 本地生成发布包

~~~bash
python3 tools/package_release.py --output ../Surge-R12.15-release.zip
~~~

ZIP 使用固定时间戳、固定文件顺序和统一权限，便于重复生成与比较。ZIP、pyc、Git 元数据和缓存不会进入发布包。

## 从 R12.14 升级

最重要的变化只有一个：真实 policy-path 从旧 AllServer 移到新 NodePool。

不要复制旧策略组整行。正确做法：

1. 备份旧私有配置。
2. 以新版 Surge.conf 为基线。
3. 从旧 AllServer 中取出私有 URL。
4. 填入新 NodePool.policy-path。
5. 重新载入并刷新外部资源。
6. 验证 Wi-Fi、蜂窝数据、Telegram 与锁屏通知。

完整步骤和回滚方法见 [MIGRATION.md](./MIGRATION.md)。

## 维护者工作流

### 固定上游验证

~~~bash
python3 tools/update_service_rules.py --verify-lock
~~~

该命令下载 Rules/upstreams.lock.json 中固定提交的 19 个服务规则，验证 SHA-256 与 Git Blob，再确认合并结果与仓库快照一致。它不会自动追踪上游最新分支。

若确实要更新上游，必须单独审阅来源、许可证、排除项、规则变化和锁文件，不能在普通配置修复中顺手漂移第三方数据。

### 刷新元数据与发布清单

按顺序执行：

~~~bash
python3 tools/convert_to_remote_rules.py
python3 tools/embed_runtime_rules.py
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
~~~

先刷新 r10.lock.json，再生成发布清单，最后生成两份 SHA-256 文件。顺序错误会让后一步记录前一步的旧哈希。

### 全量验证

~~~bash
python3 -m compileall -q tools
python3 tools/convert_to_remote_rules.py
python3 tools/update_service_rules.py --verify-lock
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/audit_precise_domains.py
python3 tools/test_audit_config.py
python3 tools/test_stage_surge_zip.py
python3 tools/generate_release_manifest.py
git diff --exit-code -- RELEASE_MANIFEST.txt
sha256sum -c SHA256SUMS.txt
cmp --silent SHA256SUMS.txt SHA256SUMS_fixed.txt
python3 tools/package_release.py --output ../Surge-R12.15-release.zip
~~~

R12.15 正常基线应包含：

~~~text
PASS: remote-only profile; external_rules=28 embedded_rule_contents=0
PASS: verified pinned upstream services=19
PASS R12.15 rules=85
PASS R12.15 remote_sources=28 rules=85
PASS precise domains DIRECT=306 Proxy=116 conflicts=0
PASS R12.15 mutations=49
PASS: ZIP allowlist regression cases=15
updated release manifest: files=54
updated checksums: files=55
PACKAGED: files=57
~~~

哈希值本身每次内容变更都会变化，数量和安全不变量不应无说明地变化。

## 审计器保护的关键不变量

配置审计器和故障注入测试会拒绝以下变化：

- NodePool 不是 select、不是 hidden 或开始自动测速。
- NodePool 被规则或可见策略直接选择。
- 私有订阅 URL 被提交到公开配置。
- AllServer 不是 Smart、缺少 Fail-Closed 或不从 NodePool 取成员。
- 地区组恢复 url-test、缺少正则、缺少 Fail-Closed 或级联读取 AllServer。
- 除 ApplePush 外出现 fallback、url-test 或 load-balance。
- Telegram 出现 DIRECT。
- APNs 绕过 ApplePush。
- ApplePush 的 Proxy、DIRECT 顺序改变。
- Final 变成 DIRECT。
- DNS 恢复 system、加密端点变化或 Host 引导拆成重复键。
- include-all-networks、include-apns、CGNAT 或 ls.apple.com 边界丢失。
- 规则源、顺序、哈希、条目数或许可证链路不一致。
- ZIP 接受路径穿越或仓库范围外文件。

test_audit_config.py 不是只跑一次正常配置。它会逐项破坏 49 个安全条件，并确认审计器能把每个错误拦住。

## 故障排查

### 配置提示不支持 Smart

表现：

- 导入时报 unknown group type。
- AllServer 或地区组无法创建。

处理：

1. 确认 Surge iOS 至少为 5.11.0。
2. 确认 Smart 功能已通过功能更新订阅解锁。
3. 推荐升级到 5.14.6 或更高。
4. 不要用旧版 fallback 语法临时覆盖公开配置。

### AllServer 只有 Fail-Closed

这说明 NodePool 没有返回可用策略，常见原因：

- policy-path 仍是 example.invalid 占位符。
- Sub-Store 输出地址 404、500 或超时。
- 输出内容不是 Surge 策略列表，也没有有效 Proxy 段。
- 私有 URL 的 Token 过期或参数被截断。
- 订阅节点语法无效，被 Surge 跳过。

先在可信环境检查私有 URL 的 HTTP 状态和输出格式，再重新载入外部资源。不要删除 Fail-Closed，也不要把 Final 改为 DIRECT。

### 地区组只有 Fail-Closed

AllServer 有节点而单个地区组为空，通常是节点名称没有匹配正则。

可选处理：

- 在 Sub-Store 中给节点加入明确地区名称或旗帜。
- 在私有副本中审慎扩展对应 policy-regex-filter。
- 确认没有把地区缩写写成正则无法识别的形式。

不要让地区组从 AllServer 级联读取，也不要把 include-all-proxies 改成 true。

### 网络切换后仍有大量请求

依次检查：

1. 确认当前实际启用的是 R12.15 私有副本，而不是旧 R12.14。
2. 搜索活动配置，AllServer 和五个地区组都应为 smart。
3. 只有 ApplePush 可以是 fallback，不应存在全订阅 url-test/load-balance。
4. NodePool 应为 select、hidden=1，并且只有它持有 policy-path。
5. 确认没有手动点击“测试全部策略”；手动全测本来就会产生大量请求。
6. 在 Surge 最近请求中查看发起进程、策略路径、目标和备注。
7. 若最高频目标是代理节点地址或测试 URL，继续检查是否有其他配置、脚本或自动组在测速。
8. 若最高频目标是应用业务域名，可能是应用自身重试环，应按进程排查。

Smart 仍会在必要时做初始或恢复探测，所以“有少量测试”不等于修正失败。判断标准是是否还会在每次网络切换时集中遍历整份订阅。

### 节点全部显示失败

- 检查订阅是否过期、节点服务器是否可达。
- 检查节点协议是否被当前 Surge 版本支持。
- 检查代理服务器域名能否通过引导 DNS 解析。
- 检查测试 URL 是否被节点或运营商阻断。
- 检查节点是否只支持 TCP，而应用强依赖 UDP。
- 检查同一出口 IP 是否被目标服务限制。

不要通过恢复 system DNS、允许 UDP 静默直连或把 Final 改为 DIRECT 来隐藏节点故障。

### Telegram 前台可用但锁屏通知延迟

1. 确认 Rules/APNs.list 更新成功。
2. 确认 include-apns=true。
3. 确认 ApplePush 顺序仍是 Proxy、DIRECT。
4. 检查 iOS 通知权限、低电量模式和 Telegram 后台设置。
5. 检查 APNs 网络可达性。
6. 不要把全部 Apple 流量强制代理。

### Telegram 持续 Updating

先切换 Telegram 服务组到另一个稳定且出口用户较少的节点。Telegram 服务端可能限制共享出口 IP 上的客户端数量，这类问题未必是配置或 TCP 转发错误。

Telegram 仍不应改为 DIRECT。

### ls.apple.com 请求循环

确认下面规则位于所有远程规则之前：

~~~ini
DOMAIN-SUFFIX,ls.apple.com,DIRECT
~~~

如果它已经命中 DIRECT 但请求仍持续，查看发起的系统进程和响应状态；配置可以修正错误路由，不能修复 Apple 服务或应用自身的重试逻辑。

### DNS 超时或解析失败

- 确认 dns.alidns.com 的三个引导地址仍在同一 Host 行。
- 确认 encrypted-dns-server 没有被模块覆盖。
- 确认 encrypted-dns-follow-outbound-mode=false。
- 确认没有加入 system DNS。
- 确认网络能访问 AliDNS 的 HTTPS 或 TLS 端点。
- 订阅服务器域名解析失败时，先修复私有订阅服务，不要放开所有 DNS 绕过。

### 局域网设备无法访问

include-local-networks=false 是有意边界。Surge 本身不会接管局域网间流量，同时 skip-proxy 和本地规则保留常用私网。

若你要把 iPhone 当作局域网代理或网关，需要单独评估 allow-wifi-access、访问控制和同网段安全。本公开配置默认：

~~~ini
allow-wifi-access = false
allow-hotspot-access = false
proxy-restricted-to-lan = true
gateway-restricted-to-lan = true
~~~

不要为了单个设备发现问题全局开启局域网代理入口。

### jsDelivr 规则暂时 404

- 确认仓库分支为 main。
- 确认 Rules 文件名大小写完全一致。
- 确认文件已经推送到 GitHub。
- 等待 CDN 同步后再刷新。
- 使用审计器确认 28 个 URL 与仓库库存一致。

主配置不会在远程规则失败时自动切换成 DIRECT；未命中流量最终进入 Final。

## 安全与隐私边界

公开仓库不包含：

- 真实订阅或 Sub-Store 私有接口。
- 节点地址、端口、用户名和密码。
- Token、Cookie、会话、设备标识。
- MITM CA、私钥或证书密码。
- Sub-Store Core/Simple 内嵌脚本。
- 未经独立审计的威胁情报模块。

公开配置也没有 MITM、脚本或重写段。用户自行添加的节点、模块、MITM、脚本和重写规则不在仓库审计范围内。

发现敏感信息泄露时，应先撤销或轮换凭据，再清理 Git 历史；仅删除最新一版文件不足以消除历史泄露。

更多要求见 [SECURITY.md](./SECURITY.md) 和 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 设计参考

本配置比较过以下公开配置的章节组织、订阅容器、Smart 地区组、DNS 和规则处理方式：

- [Rabbit-Spec Surge Developer](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-Developer.conf)
- [Rabbit-Spec Surge EN](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-EN.conf)
- [As-Lucky Lucky](https://raw.githubusercontent.com/As-Lucky/Lucky/main/Lucky-Surge.conf)
- [Coldvvater Surge 配置](https://gist.githubusercontent.com/Coldvvater/8093bc6be4340b5324b4a343493becfe/raw/Surge,conf)
- [Thoseyearsbrian Aegis](https://github.com/Thoseyearsbrian/Aegis)

这些来源不是可以整份混合粘贴的“最优配置”。R12.15 吸收的是被动订阅容器与 Smart 决策分层思路，同时保留本仓库自己的失败关闭、Telegram/APNs、DNS、精确域名集和审计链路。

Surge 官方资料：

- [Smart Group](https://kb.nssurge.com/surge-knowledge-base/guidelines/smart-group)
- [Policy Including](https://manual.nssurge.com/policy-groups/policy-including.html)
- [Common Group Parameters](https://manual.nssurge.com/policy-groups/parameters.html)
- [Requirement Expressions](https://manual.nssurge.com/profile/requirement.html)
- [Surge iOS Release Notes](https://kb.nssurge.com/surge-knowledge-base/release-notes/surge-ios)
- [Automatic Policy Group Testing](https://kb.nssurge.com/surge-knowledge-base/technotes/testing-group)

规则上游以 [Rules/upstreams.lock.json](./Rules/upstreams.lock.json) 固定的仓库、提交、Blob 和 SHA-256 为准。第三方许可证见 [THIRD_PARTY_LICENSES](./THIRD_PARTY_LICENSES)，来源边界见 [NOTICE.md](./NOTICE.md)。

## 设计取舍

R12.15 选择的是“自动体验、网络切换成本和失败关闭”之间的平衡：

- 完全被动 select 最省测试，但需要用户手动选节点。
- 全订阅 url-test/fallback 自动化简单，但网络切换时可能集中重测。
- 被动 NodePool 加 Smart 保留自动选择，同时避免订阅容器本身成为全量测速器。
- 显式 Fail-Closed 防止 Smart 空组替代策略造成静默直连。
- ApplePush 单独保留两成员 fallback，以通知可达性换取受控的 DIRECT 容灾。

这不是所有设备、所有运营商和所有节点供应商都无需调整的万能配置，但它是本仓库安全目标下的推荐基线。任何私有调整都应先说明要解决的具体问题，再验证没有恢复请求风暴或绕过失败关闭。

## 发布前检查表

- [ ] 公开 Surge.conf 仍使用 example.invalid 占位符。
- [ ] NodePool 为 select、hidden=1，且是唯一 policy-path 持有者。
- [ ] AllServer 和五个地区组均为 smart, Fail-Closed。
- [ ] 除 ApplePush 外没有 fallback、url-test 或 load-balance。
- [ ] Telegram 无 DIRECT 路径。
- [ ] ApplePush 顺序为 Proxy、DIRECT。
- [ ] AliDNS 引导地址在同一 Host 行。
- [ ] 53、853、8853 端口控制仍在。
- [ ] include-all-networks 与 include-apns 仍为 true。
- [ ] include-cellular-services 仍为 false。
- [ ] CGNAT 与 ls.apple.com 本地规则仍在远程规则之前。
- [ ] 28 个远程规则源、85 条活动规则和两个精确域名集审计通过。
- [ ] 49 项配置故障注入和 15 项 ZIP 回归通过。
- [ ] RELEASE_MANIFEST 与两份 SHA-256 清单已重新生成。
- [ ] Wi-Fi → 蜂窝数据 → Wi-Fi 不再触发全订阅集中测速。
- [ ] Telegram 前台连接与锁屏 APNs 通知均已验证。

## 许可证

本仓库原创脚本、配置结构和文档使用根目录 [MIT License](./LICENSE)。第三方规则和数据继续遵循各自许可证，MIT License 不替代或覆盖第三方条款。
