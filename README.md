# Surge iOS Privacy + Push R13.9

这是面向 Surge iOS 的完整分流配置。R13.9 修复 R13.8 真机网络诊断会把 `[Proxy]` 中的 `Fail-Closed = reject` 当成真实代理测试、导致 TCP 与 UDP 固定超时的问题。Telegram、推送、哨兵、DNS、BiliBili、四个已删除的隐藏开关、规则内容和固定快照均不变。

日常流量默认进入可见的 `Smart`。它从只含真实订阅节点的 `NodePool` 递归导入代理，首次使用前评估，随后综合真实连接首包时间、TCP 重传、失败重试、测速结果和约一小时的站点记忆动态选路。香港、台湾、日本、新加坡、美国五个地区入口也使用 Smart，并保留原有精确名称过滤。ChatGPT、Claude、Gemini 与 TikTok 直接递归导入日本、新加坡、台湾、美国四个地区中的真实节点，在地区边界内跨区自动重试。Surge 对 Smart 使用固定五分钟测试调度，因此配置不写无效的 `interval` 或 `tolerance`。

配置没有恢复 `AdBlock`、`Security`、`UDP`、`Domestic` 四个隐藏开关。Surge 官方文档明确说明，Smart 只接受真实代理策略；任何自动组没有可用成员时都可能以 `DIRECT` 替代，并在日志中显示 `SUBSTITUTE`。R13.9 因此不声称全局严格失败关闭。需要严格手动边界时，直接把 `Proxy` 切到内建 `REJECT`；不再定义会污染网络诊断的自定义拒绝代理。

## 当前基线

| 项目 | 数量或状态 |
| --- | --- |
| 策略组 | 30 |
| 活动规则 | 142 |
| 固定远程规则 | 29 |
| 动态远程规则 | 1 |
| 本地 `.list` 文件 | 29 |
| 固定 Ads | 152 条 |
| 固定 Pegasus | 1,438 条 |
| 国内 BiliBili | 16 个精确后缀 |
| 配置故障注入 | 119 项 |
| 固定快照提交 | `2b8fa93901061cf0482b079203630bcd11bfe0b1` |

主配置不嵌入规则快照。29 份固定规则都通过 jsDelivr 的完整提交 SHA 加载；唯一动态资源是 `https://ruleset.skk.moe/List/non_ip/domestic.conf`，每 24 小时更新。

## 快速使用

1. 打开 `Surge.conf`，只替换 `NodePool` 的 `policy-path`。配置行如下。

   ```ini
   NodePool = select, policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL, ...
   ```

2. 私下填入你的 Surge 格式订阅或 Sub-Store 地址。不要把真实地址、令牌或节点信息提交到公开仓库。
3. 在 Surge 中重新下载配置，不要只刷新旧规则缓存。
4. 打开 `Proxy`，确认当前选择为 `Smart`。旧配置可能保留此前选择的 `Auto` 或 `NodePool`，升级后只需手动切换这一次。
5. `Smart` 首次使用会先评估节点，之后依据真实连接质量、失败记录和站点历史动态选路；界面显示的是近期最常用节点，不代表每条新连接都使用同一节点。
6. 地区组会在匹配节点中智能选择；AI/TikTok 会在四个允许地区的真实节点间独立 Smart 选优。需要临时指定节点时，可在 Surge iOS 的策略组界面长按对应 Smart 策略进行临时覆盖。
7. 需要严格手动控制时，把 `Proxy` 直接切到 `REJECT`；需要固定节点时再进入 `NodePool` 选择真实节点。
8. 清理旧版留下的规则缓存，重载配置后按本文末尾的真机清单验证。

## 策略架构

| 策略 | 默认或成员 | 说明 |
| --- | --- | --- |
| `Final` | `Proxy`、`REJECT` | 未命中流量默认代理 |
| `Proxy` | `Smart`、`NodePool`、五个地区组、`REJECT` | 默认智能选路，可固定真实节点或手动拒绝 |
| `Smart` | `NodePool` 中的真实订阅节点 | 综合真实连接质量、失败重试、测速与站点记忆动态选择 |
| `NodePool` | 仅私人订阅节点 | 手动稳定入口，不做全订阅测速 |
| 五个地区组 | 名称过滤后的订阅节点 | Smart 自动选优并可重试，可临时手动覆盖 |
| `ApplePush` | `Proxy`，后备 `DIRECT` | 唯一明确允许直连后备的可用性例外 |
| `ChatGPT`、`Claude`、`Gemini`、`TikTok` | 日本、新加坡、台湾、美国的真实节点 | Smart 跨允许地区自动选优并重试，排除香港 |
| `Bahamut` | 台湾、香港 | 与官方服务地区边界一致 |
| `Apple` | `DIRECT` 首选 | 国内 Apple 服务保持低延迟，可手动切代理 |
| 其他国际软件 | `Proxy`＋适用地区 | 默认继承当前稳定节点 |

旧版 `AdBlock`、`Security`、`UDP`、`Domestic` 隐藏选择组已经删除。Ads 与 Pegasus 固定 `REJECT`，STUN 固定 `Proxy`，已知国内流量固定 `DIRECT`。这能避免升级后继续继承隐藏组中的旧调试选择。

## 国内 BiliBili 修复

旧配置有三类风险，任何一类都可能让国内版卡住。

- 国内 BiliBili 虽然指向 `DIRECT`，但固定列表缺少 `biligame.net`、`bilivideo.cn`、`bilicomic.com`、`bilivideo.net`。
- 动态广告大表会命中 `httpdns.bilivideo.com` 和 `line3-h5-mobile-api.biligame.com`，应用会等待 HTTPDNS/H5 请求超时后再回退。
- 规则匹配只依赖普通域名解析时，SNI/Host 路径可能漏过应直连的请求。

R13.9 保持以下处理不变。

1. `Rules/BiliBili.list` 补全为 16 个审阅后缀并固定 `DIRECT`。
2. `httpdns.bilivideo.com` 与 `line3-h5-mobile-api.biligame.com` 作为精确功能护栏放在 Ads 前。
3. BiliBili 固定规则启用 `extended-matching`，可按 SNI/Host 参与匹配。
4. 国内 API、页面、图片、视频 CDN 与动态国内补充均固定 `DIRECT`，不经过可继承状态的隐藏组。
5. 国际版专用文件和策略继续保持删除。`apiintl.biliapi.net`、`bilibili.tv`、`biliintl.com` 等七条历史域名仅走通用 `Proxy`，用于防止误入国内父后缀或旧媒体集合。

## 广告误杀与移动端性能

R13.9 仍不加载动态 `reject.conf` 和 `reject_phishing.conf`。这两份十万级列表在移动端会增加下载、解析和内存压力，而且实测与功能域名发生重叠。它们的维护项目也只建议在 Surge for Mac 使用大规模列表，并建议移动平台使用专门的内容拦截工具。

保留以下防护边界。

- 152 条固定、可审阅的 Ads 规则固定 `REJECT`。
- 1,438 个 Amnesty Tech 2021 Pegasus 历史 IOC 固定 `REJECT`。
- 九条 Ads 前置功能护栏保护 BiliBili、Spotify、Google 更新/CDN 与 OpenAI RUM。
- 动态国内表只用于 `DIRECT` 补充，不参与广告或安全拒绝。

Pegasus 历史列表不能替代 iOS 更新、Lockdown Mode 或当前威胁情报。

## 软件分流总览

| 类别 | 默认策略 | 备注 |
| --- | --- | --- |
| 微信、国内直连、China 精确域名、CN GeoIP | `DIRECT` | 不再经过 `Domestic` 状态组 |
| 国内 BiliBili | `DIRECT` | 16 后缀＋两条 Ads 前置功能护栏 |
| ChatGPT | `ChatGPT` Smart | 四个允许地区自动选优；补充 11 个 OpenAI 官方当前网络依赖 |
| Claude、Gemini | 同名 Smart | 日本、新加坡、台湾、美国之间自动选优 |
| TikTok | `TikTok` Smart | 同上，香港不进入候选池 |
| Bahamut | `Bahamut` | 台湾、香港 |
| YouTube、Netflix、Disney+、HBO、Prime Video | 同名策略组 | 默认 `Proxy`，可切地区 |
| Spotify | `Spotify` | 五条音视频、电视、Podcast 功能护栏 |
| Telegram、X、GitHub | 同名策略组 | 默认 `Proxy` |
| Google、Microsoft、OneDrive、Games | 同名策略组 | 保留共享云和登录端点前置护栏 |
| Apple 国内服务 | `Apple` | 默认 `DIRECT`；流媒体例外先进入 `Streaming` |
| STUN | `Proxy` | 防止 UDP 探测绕过代理 |
| 未匹配公网 IPv4/IPv6 | `Proxy` | 紧贴唯一 `FINAL` 之前 |

## 首条命中顺序

Surge 规则按首条命中执行。R13.9 维持以下关键顺序。

1. 局域网发现、多播拒绝和本地网段。
2. Apple Captive Portal 直连。
3. STUN 固定代理。
4. 16 条已审阅大陆应用 DNS 直连。
5. 公网 53、853、8853 拒绝。
6. 出口诊断和 13 条境外应用 DNS 代理。
7. 固定 Pegasus 拒绝。
8. APNs 与 Apple 流媒体前置例外。
9. WeChat、Direct 和九条 Ads 前置功能护栏。
10. 七条退役 BiliBili 国际版兼容护栏。
11. 固定 Ads 拒绝。
12. AI、流媒体、国际软件和国内 BiliBili 固定列表。
13. 共享国内云后缀、动态国内补充和固定 China 集合。
14. Global、`GEOIP,CN,DIRECT,no-resolve`、双栈公网代理兜底和唯一 `FINAL`。

## `extended-matching`

除 Ads 外，29 份固定资源中的其余 28 份均启用 `extended-matching`；动态国内补充也启用。Surge 可按 SNI/Host 处理域名类规则，降低 DNS 路径不同导致的漏分流。Ads 保持普通匹配，以控制 iOS 上的匹配成本并缩小拦截面。

## DNS、UDP 与 APNs

- Surge 自身使用 AliDNS 与 DNSPod 双 DoH，证书校验开启。
- 传统引导 DNS 同时配置 AliDNS 两条 IPv4 和两条官方 IPv6 地址；这些服务器只负责连通性测试和解析 DoH 主机名。
- `dns.alidns.com` 保留四地址静态引导；`doh.pub` 不再钉住 DNSPod 已不建议公开使用的旧 IP，而是通过上述引导 DNS 动态解析，允许服务方调整后端。
- `encrypted-dns-follow-outbound-mode=false` 避免域名型代理节点启动时形成解析环。
- 已审阅大陆应用 DNS 位于端口拒绝前并固定 `DIRECT`；境外应用 DNS 位于端口拒绝后并固定 `Proxy`。
- `GEOIP,CN` 保留 `no-resolve`，未知域名不会为了 GeoIP 判断强制走本地 DNS。
- `udp-policy-not-supported-behaviour=REJECT`，不支持 UDP 的节点不会静默直连。
- `block-quic=per-policy` 保留按策略控制；STUN 明确代理。
- APNs 由隐藏 `ApplePush` fallback 管理，先代理、失败后可直连。这是通知可用性的有意例外。

## 验证与维护

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
python3 tools/audit_rules.py --check-runtime-remote
python3 tools/audit_precise_domains.py
python3 tools/test_audit_config.py
python3 tools/test_release_inventory.py
python3 tools/test_stage_surge_zip.py
```

上游只读比对

```bash
python3 tools/update_external_resources.py --download --check
python3 tools/update_service_rules.py --download --check
```

生成发布文件

```bash
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
sha256sum -c SHA256SUMS.txt
cmp --silent SHA256SUMS.txt SHA256SUMS_fixed.txt
python3 tools/package_release.py --output ../Surge-R13.9-Complete-No-Embedded-20260830.zip
```

## 真机验收

在 Wi-Fi 和蜂窝网络各完成一遍以下检查。

- BiliBili 首页、搜索、账号、封面、视频起播、拖动、弹幕和评论；最近请求应显示国内域名走 `DIRECT`。
- ChatGPT 登录、历史记录、对话流式输出、附件与语音入口；策略应为 `ChatGPT` 支持地区节点。
- Claude、Gemini、TikTok、Bahamut 和主要流媒体分别启动一次，确认没有落入错误地区。
- 微信消息、图片、小程序和国内常用软件保持直连。
- APNs 在锁屏、Wi-Fi/蜂窝切换后仍能收到通知。
- 检查 IPv4、IPv6 与 DNS 出口是否符合所选节点；注意远端代理使用的递归 DNS 由节点提供方决定。
- 测试一个 UDP 应用；节点不支持 UDP 时应失败，而不是直连。
- 如果 AirDrop、Xcode 调试或 USB Dashboard 异常，先临时关闭 `include-all-networks` 验证；这是 Surge 官方披露的全网络接管兼容性取舍。

如果 BiliBili 仍卡顿，先停用所有外部模块，清空规则缓存并重新下载配置，然后在最近请求中检查 `httpdns.bilivideo.com`、`line3-h5-mobile-api.biligame.com` 和实际视频 CDN 的首条命中。若命中正确但仍慢，应换一个稳定的直连网络/DNS 环境或检查运营商链路；配置不能修复服务端、运营商或节点本身故障。

## 主要依据

- [Surge 策略组与无可用成员替代行为](https://manual.nssurge.com/policy-groups/overview.html)
- [Surge Smart 策略组](https://manual.nssurge.com/policy-groups/smart.html)
- [Surge 策略成员导入与过滤](https://manual.nssurge.com/policy-groups/policy-including.html)
- [Surge 自动组临时覆盖](https://manual.nssurge.com/policy-groups/parameters.html)
- [Surge Select 策略组](https://manual.nssurge.com/policy-groups/select.html)
- [Surge 内建策略别名](https://manual.nssurge.com/policies/built-in.html)
- [Surge 域名规则与 extended matching](https://manual.nssurge.com/rules/domain.html)
- [Surge 加密 DNS 与主机名引导](https://manual.nssurge.com/dns/encrypted-dns.html)
- [Surge DNS 服务器与 IPv6 语法](https://manual.nssurge.com/dns/dns-server.html)
- [DNSPod 免费 DoH/DoT 域名接入公告](https://docs.dnspod.cn/notices/mian-fei-ban-dot-dohbu-zai-gong-kai-ipjie-ru-de-gong-gao/)
- [AliDNS 官方双 IPv4 与双 IPv6 地址](https://help.aliyun.com/en/dns/httpdns-ios14-native-encryption-dns-scheme)
- [Telegram 官方 CIDR 列表](https://core.telegram.org/resources/cidr.txt)
- [Apple APNs 官方端口与网段](https://support.apple.com/en-us/102266)
- [OpenAI ChatGPT 网络建议](https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps)
- [SukkaW/Surge 移动端建议](https://github.com/SukkaW/Surge)
