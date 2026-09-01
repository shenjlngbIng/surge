# Surge iOS Privacy + Push R13.12

R13.12 修复 R13.11 全局“测试代理策略”和“UDP 代理转发”空白的问题。根因不是 DNS，而是 `policy-path` 节点只属于外置策略组，不会成为主配置 `[Proxy]` 中的代理实体。R13.12 改用 Surge iOS 官方支持的配置分离方式，让私人托管配置 `Private-Proxies.conf` 的真实 `[Proxy]` 段进入主配置；全局网络诊断因此测试真实节点，不再空白，也不使用本机回环制造假绿。

R13.11 的失败关闭修复继续保留。日常自动入口、五个地区入口以及 ChatGPT、Claude、Gemini、TikTok 仍为含显式 `REJECT` 的 `url-test`，并启用 `evaluate-before-use=true`。没有真实节点或全部测试失败时请求明确失败，不会静默变成 `DIRECT/SUBSTITUTE`。

公开仓库不能附带私人订阅或节点凭据，所以只下载公开 `Surge.conf` 仍不能凭空获得代理。必须先在 Surge 中安装自己的托管节点配置，并把文件名保存为 `Private-Proxies.conf`。这是获得真实诊断与保护凭据二者同时成立的必要条件。

## 截图对应的修复

| 现象 | 根因 | R13.12 处理 |
| --- | --- | --- |
| “测试代理策略”空白 | `policy-path` 节点不在 `[Proxy]` | 关联私人托管配置的真实 `[Proxy]` 段 |
| “UDP 代理转发”空白 | 没有可供全局诊断选择的代理实体 | 对同一真实节点执行 UDP 探针 |
| R13.10 TCP 绿、UDP 报 SOCKS5 不支持 | 测试了 Surge 本机回环，不是真实节点 | 继续禁止回环 `Diagnostics` |
| Smart 空组变成 `DIRECT/SUBSTITUTE` | 自动组无可用真实成员 | 继续使用显式 `REJECT` 的 `url-test` |
| `include-all-networks` 警告 | 全网络接管可能影响 AirDrop、Xcode 或 USB Dashboard | 为 APNs 与防旁路继续保留 |

## 当前基线

| 项目 | 数量或状态 |
| --- | --- |
| 策略组 | 30 |
| 活动规则 | 142 |
| `[Proxy]` 公开嵌入代理 | 0；真实代理来自 `Private-Proxies.conf` |
| 自动组 | 10 个 `url-test`，全部含显式 `REJECT` |
| Smart 组 | 0 |
| 固定远程规则 | 29 |
| 动态远程规则 | 1 |
| 本地 `.list` 文件 | 29 |
| 固定 Ads | 152 条 |
| 固定 Pegasus | 1,438 条 |
| 国内 BiliBili | 16 个精确后缀 |
| 配置故障注入 | 133 项 |
| Sub-Store 转换器测试 | 7 项 |
| 固定快照提交 | `2b8fa93901061cf0482b079203630bcd11bfe0b1` |

主配置不嵌入节点或规则快照。29 份固定规则通过 jsDelivr 的完整提交 SHA 加载；唯一动态资源是 SukkaW 的 `domestic.conf`，每 24 小时更新。

## 快速使用

### 已有完整 Surge 托管配置

1. 在 Surge 中通过私人 URL 安装服务商提供的完整托管配置。
2. 把该配置文件保存或重命名为 `Private-Proxies.conf`。文件必须含真实 `[Proxy]` 段。
3. 再导入本仓库的 `Surge.conf`。其 `[Proxy]` 只包含 `#!include Private-Proxies.conf`，不会复制或公开凭据。
4. 打开 `NodePool`，确认第一项 `REJECT` 后面能看到真实节点；再把 `Proxy` 选择为第一项 `Auto`。

### 使用 Sub-Store 组合订阅

1. 在提供节点的 Sub-Store 组合订阅中，把 `Scripts/SubStore-Surge-Profile.js` 添加为最后一个 `Response Transformer`。发布标签对应的脚本地址为：

   ```text
   https://raw.githubusercontent.com/shenjlngbIng/surge/r13.12-20260901/Scripts/SubStore-Surge-Profile.js
   ```

2. 在原 Surge 输出链接末尾加入 `surge-profile=1`。例如组合名为 `Surge` 时：

   ```text
   http://sub.store/download/collection/Surge/Surge?surge-profile=1
   ```

3. 在 Safari 打开该链接并交给 Surge 安装，文件名必须设为 `Private-Proxies.conf`。转换器只在这个参数存在且目标为 Surge 时工作；正常订阅输出不受影响。
4. 打开 `Private-Proxies.conf`，确认首行是自更新的 `#!MANAGED-CONFIG`，并且 `[Proxy]` 下确有真实节点。随后导入本仓库的 `Surge.conf`。
5. `NodePool` 会通过 `include-all-proxies=true` 复用这些真实节点。`Auto` 首次使用前等待测试，之后在结果过期或网络变化时重新评估。

不能把 `Private-Proxies.conf`、私人下载 URL、令牌或节点日志提交到公开仓库。若只安装公开主配置而没有这个私人文件，Surge 应直接提示关联文件缺失，而不是以空节点或直连继续运行。

## 策略架构

| 策略 | 默认或成员 | 行为 |
| --- | --- | --- |
| `Final` | `Proxy`、`REJECT` | 未命中流量默认进入代理总入口 |
| `Proxy` | `Auto`、`NodePool`、五个地区组、`REJECT` | 默认自动选优，也可固定节点或手动拒绝 |
| `Auto` | 显式 `REJECT`＋`NodePool` 的真实节点 | `url-test` 自动选低延迟可用节点；空源明确失败 |
| `NodePool` | 显式 `REJECT`＋`[Proxy]` 的全部真实节点 | 手动节点池；不复制凭据，失效时不会替换成直连 |
| 五个地区组 | 显式 `REJECT`＋名称过滤后的节点 | 香港、台湾、日本、新加坡、美国独立自动选优 |
| `ChatGPT`、`Claude`、`Gemini`、`TikTok` | 显式 `REJECT`＋日本、新加坡、台湾、美国节点 | 在审阅地区内自动选优，排除香港 |
| `ApplePush` | `Proxy`，后备 `DIRECT` | 唯一有意保留的直连后备，用于 APNs 可达性 |
| `Bahamut` | 台湾、香港 | 保持服务地区边界 |
| `Apple` | `DIRECT` 首选 | 国内 Apple 服务保持低延迟，可手动改代理 |

`AdBlock`、`Security`、`UDP`、`Domestic`、`AllServer` 与旧 `Smart` 都不存在。Ads 与 Pegasus 固定 `REJECT`，STUN 固定 `Proxy`，已知国内流量固定 `DIRECT`。

## 自动选择为什么不用 Smart

Smart 会利用真实连接质量、重传、失败和站点历史，节点来源稳定时确实更聪明。但 Surge 官方同时规定，Smart 忽略内建策略和嵌套组；组里没有可用真实代理时会使用 `DIRECT/SUBSTITUTE`。私人托管配置首次安装失败、节点被删除或地区筛选为空时仍可能没有候选，真机已经复现过直连替代。

`url-test` 支持显式内建成员。R13.12 把 `REJECT` 保持为每个自动组的第一个成员，`policy-regex-filter` 只过滤导入成员，不会过滤显式 `REJECT`。`evaluate-before-use=true` 会在第一次请求前等待评估；评估失败时请求报错。因此它牺牲 Smart 的站点记忆，换取可验证的失败关闭和稳定的低延迟自动选择。

## 网络诊断与 UDP 的真实边界

R13.12 的 `[Proxy]` 关联 `Private-Proxies.conf` 中的真实代理。正确安装后，全局“测试代理策略”必须显示真实 HTTP 探针结果，“UDP 代理转发”也必须显示真实测试结果，而不能再整段空白。若两段仍为空，说明私人文件未关联、文件名不一致，或其中没有有效代理行。

不要用本机 SOCKS5 回环把结果强行变绿。它只能证明回环 TCP 可连，并不能证明真实节点或 UDP 可用。

正确测试方式如下。

1. 在 `Private-Proxies.conf` 和 `NodePool` 确认真实节点已经加载。
2. 运行全局网络诊断，代理策略行不应为空；TCP 延迟只证明被测节点的 TCP 路径。
3. UDP 行应返回成功或明确的不支持/失败结果，测试目标为 `apple.com@1.1.1.1`。
4. 若提示“不支持 UDP relay”，检查订阅输出是否为 Shadowsocks/SOCKS5 节点写入 `udp-relay=true`，并确认服务端真的开放 UDP。VMess、Trojan、TUIC、Hysteria 2、MASQUE、WireGuard 等仍取决于各自服务端能力。
5. 配置保持 `udp-policy-not-supported-behaviour=REJECT`。不能用 `DIRECT` 把失败改成绿色，否则 UDP 会绕过代理。

配置只能启用客户端支持，不能凭空给服务商节点增加服务器端 UDP 能力。若所有真实节点都不支持 UDP，唯一正确修复是更换支持 UDP 的订阅节点或让服务商开启它。

## 国内 BiliBili

国内版继续保持以下修复。

- `Rules/BiliBili.list` 固定 16 个审阅后缀并指向 `DIRECT`。
- `httpdns.bilivideo.com` 与 `line3-h5-mobile-api.biligame.com` 位于 Ads 前并固定直连。
- BiliBili 固定资源启用 `extended-matching`，可按 SNI/Host 参与匹配。
- 国内 API、页面、图片、视频 CDN 与动态国内补充不经过隐藏状态组。
- 国际版专用策略和文件继续删除；七条历史国际域名只进入通用 `Proxy`，防止被国内父后缀误覆盖。

## 软件分流总览

| 类别 | 默认策略 | 备注 |
| --- | --- | --- |
| 微信、China 精确域名、CN GeoIP | `DIRECT` | 国内流量不经过状态组 |
| 国内 BiliBili | `DIRECT` | 16 后缀＋两条功能护栏 |
| ChatGPT、Claude、Gemini | 同名 `url-test` | 四个允许地区自动选优，空源拒绝 |
| TikTok | `TikTok` | 四个允许地区，排除香港 |
| Bahamut | `Bahamut` | 台湾、香港 |
| YouTube、Netflix、Disney+、HBO、Prime Video | 同名选择组 | 默认继承 `Proxy`，可切地区 |
| Spotify | `Spotify` | 保留音视频、电视与 Podcast 功能护栏 |
| Telegram、X、GitHub | 同名选择组 | 默认继承 `Proxy` |
| Google、Microsoft、OneDrive、Games | 同名选择组 | 保留共享云与登录端点护栏 |
| Apple 国内服务 | `Apple` | 默认直连；流媒体例外先进入 `Streaming` |
| STUN | `Proxy` | 防止 UDP 探测绕过代理 |
| 未匹配公网 IPv4/IPv6 | `Proxy` | 位于唯一 `FINAL` 之前 |

## DNS、APNs 与全网络接管

- Surge 自身使用 AliDNS 与 DNSPod 双 DoH，证书校验开启。
- AliDNS 两条 IPv4 和两条官方 IPv6 地址负责引导；`doh.pub` 动态解析，不冻结旧 IP。
- `encrypted-dns-follow-outbound-mode=false` 避免域名型节点启动解析环。
- 已审阅大陆应用 DNS 位于公网端口拒绝前并固定 `DIRECT`；境外应用 DNS 位于其后并固定 `Proxy`。
- `GEOIP,CN,DIRECT,no-resolve` 不会为了 GeoIP 判断强制本地解析未知域名。
- `include-all-networks=true` 与 `include-apns=true` 保留全网络与推送接管。Surge 对 AirDrop、Xcode 和 USB Dashboard 的警告属于官方已知兼容性提示。
- `ApplePush = fallback, Proxy, DIRECT` 是通知可用性的唯一直连后备。若要求 APNs 也绝不直连，需要自行删除 `DIRECT`，代价是代理故障时可能收不到推送。

## 广告、安全与供应链

移动端不加载动态 `reject.conf` 和 `reject_phishing.conf`。保留 152 条固定 Ads 和 1,438 个历史 Pegasus IOC，二者固定 `REJECT`。九条 Ads 前置功能护栏保护 BiliBili、Spotify、Google 更新/CDN 与 OpenAI RUM。

运行配置含 29 个不可变仓库规则资源和 1 个动态国内补充。固定资源使用完整提交 SHA、条目数和 SHA-256 锁定；动态国内资源只用于 `DIRECT` 补充，不参与广告或安全拒绝。

## 验证与发布

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
python3 tools/test_substore_surge_profile.py
python3 tools/test_release_inventory.py
python3 tools/test_stage_surge_zip.py
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
sha256sum -c SHA256SUMS.txt
cmp --silent SHA256SUMS.txt SHA256SUMS_fixed.txt
python3 tools/package_release.py --output ../Surge-R13.12-Complete-No-Embedded-20260901.zip
```

## 真机验收

- `NodePool` 能看到真实节点，`Proxy` 当前选择 `Auto`，事件里不再出现 Smart `SUBSTITUTE`。
- 删除或改名 `Private-Proxies.conf` 后，主配置应明确报告关联文件问题，不能以空节点或直连继续运行。
- 国内 BiliBili 首页、搜索、账号、封面、起播、拖动、弹幕和评论命中 `DIRECT`。
- ChatGPT、Claude、Gemini、TikTok、Bahamut 和主要流媒体命中各自允许地区。
- Telegram、微信、APNs 在 Wi-Fi/蜂窝切换后可用。
- IPv4、IPv6 与 DNS 出口符合当前真实节点；远端递归 DNS 仍由节点提供方决定。
- 全局网络诊断的代理行显示真实延迟；UDP 行显示真实成功或明确失败，二者不能再整段空白。
- 对一个具体真实节点复测 UDP。不支持时应明确失败，不能直连。

## 主要依据

- [Surge 策略组与空组替代行为](https://manual.nssurge.com/policy-groups/overview.html)
- [Surge URL Test 自动组](https://manual.nssurge.com/policy-groups/url-test.html)
- [Surge 策略导入、过滤与成员顺序](https://manual.nssurge.com/policy-groups/policy-including.html)
- [Surge Smart 策略组](https://manual.nssurge.com/policy-groups/smart.html)
- [Surge UDP 协议支持与测试](https://manual.nssurge.com/policies/udp.html)
- [Surge General 与 include-all-networks](https://manual.nssurge.com/profile/general.html)
- [Surge 配置分离](https://manual.nssurge.com/profile/format.html)
- [Surge 托管配置](https://manual.nssurge.com/profile/managed-profile.html)
- [Telegram 官方 CIDR](https://core.telegram.org/resources/cidr.txt)
- [Apple APNs 官方端口与网段](https://support.apple.com/en-us/102266)
- [OpenAI ChatGPT 网络建议](https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps)
- [SukkaW/Surge](https://github.com/SukkaW/Surge)
