# Surge iOS Privacy + Push R13.5

这是面向 Surge iOS 的完整分流配置。R13.5 已对国内外软件、策略组、规则顺序、DNS、UDP、APNs、IPv4/IPv6 兜底和远程规则供应链做全盘复核，重点修复国内 BiliBili 长时间加载和旧版“失败关闭”并不成立的问题。

Surge 官方说明，自动策略组在没有可用成员时会使用 `DIRECT` 替代，日志显示为 `SUBSTITUTE`；Smart 还会忽略内建策略和嵌套组。因此本版删除 `AllServer` Smart，`NodePool` 与五个地区入口全部改为手动 `select`，首项是内建 `reject` 的别名 `Fail-Closed`。这意味着节点选择需要人工完成，但无可用节点时不会由自动组静默直连。

## 当前基线

| 项目 | 数量或状态 |
| --- | ---: |
| 策略组 | 29 |
| 活动规则 | 142 |
| 固定远程规则 | 29 |
| 动态远程规则 | 1 |
| 本地 `.list` 文件 | 29 |
| 固定 Ads | 152 条 |
| 固定 Pegasus | 1,438 条 |
| 国内 BiliBili | 16 个精确后缀 |
| 配置故障注入 | 82 项 |
| 固定快照提交 | `2b8fa93901061cf0482b079203630bcd11bfe0b1` |

主配置不嵌入规则快照。29 份固定规则都通过 jsDelivr 的完整提交 SHA 加载；唯一动态资源是 `https://ruleset.skk.moe/List/non_ip/domestic.conf`，每 24 小时更新。

## 快速使用

1. 打开 `Surge.conf`，只替换 `NodePool` 的 `policy-path`：

   ```ini
   NodePool = select, Fail-Closed, policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL, ...
   ```

2. 私下填入你的 Surge 格式订阅或 Sub-Store 地址。不要把真实地址、令牌或节点信息提交到公开仓库。
3. 在 Surge 中重新下载配置，不要只刷新旧规则缓存。
4. 打开 `NodePool`，选择一个真实可用节点。默认 `Fail-Closed` 会主动拒绝连接，这是安全哨兵，不是故障节点。
5. 如果使用地区组，再分别为日本、新加坡、台湾、美国、香港选择匹配节点。
6. 清理旧版留下的策略选择和规则缓存，重载配置后按本文末尾的真机清单验证。

## 策略架构

| 策略 | 默认或成员 | 说明 |
| --- | --- | --- |
| `Final` | `Proxy`、`REJECT` | 未命中流量默认代理 |
| `Proxy` | `NodePool`、五个地区组 | 默认进入手动节点池 |
| `NodePool` | `Fail-Closed`＋私人订阅节点 | 手动稳定入口，不做全订阅测速 |
| 五个地区组 | `Fail-Closed`＋名称过滤后的节点 | 手动选择，不使用 Smart/url-test |
| `ApplePush` | `Proxy`，后备 `DIRECT` | 唯一明确允许直连后备的可用性例外 |
| `ChatGPT`、`Claude`、`Gemini`、`TikTok` | 日本、新加坡、台湾、美国 | 排除不适合的香港默认出口 |
| `Bahamut` | 台湾、香港 | 与官方服务地区边界一致 |
| `Apple` | `DIRECT` 首选 | 国内 Apple 服务保持低延迟，可手动切代理 |
| 其他国际软件 | `Proxy`＋适用地区 | 默认继承当前稳定节点 |

旧版 `AdBlock`、`Security`、`UDP`、`Domestic` 隐藏选择组已经删除。Ads 与 Pegasus 固定 `REJECT`，STUN 固定 `Proxy`，已知国内流量固定 `DIRECT`。这能避免升级后继续继承隐藏组中的旧调试选择。

## 国内 BiliBili 修复

国内版卡住并不只是“有没有直连规则”的问题。旧配置同时存在三类风险：

- 国内 BiliBili 虽然指向 `DIRECT`，但固定列表缺少 `biligame.net`、`bilivideo.cn`、`bilicomic.com`、`bilivideo.net`。
- 动态广告大表会命中 `httpdns.bilivideo.com` 和 `line3-h5-mobile-api.biligame.com`，应用会等待 HTTPDNS/H5 请求超时后再回退。
- 规则匹配只依赖普通域名解析时，SNI/Host 路径可能漏过应直连的请求。

R13.5 的处理如下：

1. `Rules/BiliBili.list` 补全为 16 个审阅后缀并固定 `DIRECT`。
2. `httpdns.bilivideo.com` 与 `line3-h5-mobile-api.biligame.com` 作为精确功能护栏放在 Ads 前。
3. BiliBili 固定规则启用 `extended-matching`，可按 SNI/Host 参与匹配。
4. 国内 API、页面、图片、视频 CDN 与动态国内补充均固定 `DIRECT`，不经过可继承状态的隐藏组。
5. 国际版专用文件和策略继续保持删除。`apiintl.biliapi.net`、`bilibili.tv`、`biliintl.com` 等七条历史域名仅走通用 `Proxy`，用于防止误入国内父后缀或旧媒体集合。

## 广告误杀与移动端性能

R13.5 不再加载动态 `reject.conf` 和 `reject_phishing.conf`。这两份十万级列表在移动端会增加下载、解析和内存压力，而且实测与功能域名发生重叠。它们的维护项目也只建议在 Surge for Mac 使用大规模列表，并建议移动平台使用专门的内容拦截工具。

保留的防护边界：

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
| ChatGPT | `ChatGPT` | 补充 11 个 OpenAI 官方当前网络依赖 |
| Claude、Gemini | 同名地区限制组 | 日本、新加坡、台湾、美国 |
| TikTok | `TikTok` | 同上，不默认香港 |
| Bahamut | `Bahamut` | 台湾、香港 |
| YouTube、Netflix、Disney+、HBO、Prime Video | 同名策略组 | 默认 `Proxy`，可切地区 |
| Spotify | `Spotify` | 五条音视频、电视、Podcast 功能护栏 |
| Telegram、X、GitHub | 同名策略组 | 默认 `Proxy` |
| Google、Microsoft、OneDrive、Games | 同名策略组 | 保留共享云和登录端点前置护栏 |
| Apple 国内服务 | `Apple` | 默认 `DIRECT`；流媒体例外先进入 `Streaming` |
| STUN | `Proxy` | 防止 UDP 探测绕过代理 |
| 未匹配公网 IPv4/IPv6 | `Proxy` | 紧贴唯一 `FINAL` 之前 |

## 首条命中顺序

Surge 规则按首条命中执行。R13.5 维持以下关键顺序：

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

- Surge 自身使用 AliDNS 与 DNSPod 双 DoH，固定引导地址，证书校验开启。
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

上游只读比对：

```bash
python3 tools/update_external_resources.py --download --check
python3 tools/update_service_rules.py --download --check
```

生成发布文件：

```bash
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
sha256sum -c SHA256SUMS.txt
cmp --silent SHA256SUMS.txt SHA256SUMS_fixed.txt
python3 tools/package_release.py --output ../Surge-R13.5-Complete-No-Embedded-20260829.zip
```

## 真机验收

在 Wi-Fi 和蜂窝网络各做一次：

- BiliBili 首页、搜索、账号、封面、视频起播、拖动、弹幕和评论；最近请求应显示国内域名走 `DIRECT`。
- ChatGPT 登录、历史记录、对话流式输出、附件与语音入口；策略应为 `ChatGPT` 支持地区节点。
- Claude、Gemini、TikTok、Bahamut 和主要流媒体分别启动一次，确认没有落入错误地区。
- 微信消息、图片、小程序和国内常用软件保持直连。
- APNs 在锁屏、Wi-Fi/蜂窝切换后仍能收到通知。
- 检查 IPv4、IPv6 与 DNS 出口是否符合所选节点；注意远端代理使用的递归 DNS 由节点提供方决定。
- 测试一个 UDP 应用；节点不支持 UDP 时应失败，而不是直连。

如果 BiliBili 仍卡顿，先停用所有外部模块，清空规则缓存并重新下载配置，然后在最近请求中检查 `httpdns.bilivideo.com`、`line3-h5-mobile-api.biligame.com` 和实际视频 CDN 的首条命中。若命中正确但仍慢，应换一个稳定的直连网络/DNS 环境或检查运营商链路；配置不能修复服务端、运营商或节点本身故障。

## 主要依据

- [Surge 策略组与无可用成员替代行为](https://manual.nssurge.com/policy-groups/overview.html)
- [Surge Smart 策略组限制](https://manual.nssurge.com/policy-groups/smart.html)
- [Surge Select 策略组](https://manual.nssurge.com/policy-groups/select.html)
- [Surge 内建策略别名](https://manual.nssurge.com/policies/built-in.html)
- [Surge 域名规则与 extended matching](https://manual.nssurge.com/rules/domain.html)
- [OpenAI ChatGPT 网络建议](https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps)
- [SukkaW/Surge 移动端建议](https://github.com/SukkaW/Surge)
