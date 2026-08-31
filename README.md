# Surge iOS Privacy + Push R13.11

R13.11 是一次安全纠错版。真机日志已经证明 R13.10 的本机 `Diagnostics` SOCKS5 桥只能完成 TCP，不能完成 SOCKS5 UDP relay；同时 `Smart` 在订阅未加载、资源更新失败或地区筛选为空时会被 Surge 替换成 `DIRECT`，事件中显示为 `SUBSTITUTE`。这意味着旧版 TCP 诊断的绿色结果也可能来自直连，不能继续当作真实代理证据。

R13.11 删除错误诊断桥和全部 Smart 组。日常自动入口、五个地区入口以及 ChatGPT、Claude、Gemini、TikTok 改为 `url-test`，每组都显式放入内建 `REJECT`，并启用 `evaluate-before-use=true`。有真实节点时自动选择通过测试且延迟较低的节点；没有节点或全部测试失败时请求明确失败，不再静默直连。

DNS、Telegram、ApplePush、哨兵、国内 BiliBili、Ads/Pegasus、STUN、QUIC、IPv4/IPv6 兜底、四个已删除的隐藏开关和固定规则快照均保持原边界。

## 截图中的三条事件

| 事件 | 含义 | R13.11 处理 |
| --- | --- | --- |
| `Smart组中没有可用的子策略，改用 SUBSTITUTE（DIRECT 的别名）` | Smart 没有读到真实节点，Surge 自动直连 | 删除全部 Smart；自动组以显式 `REJECT` 兜底 |
| `SOCKS proxy server doesn't support UDP relay` | R13.10 测试的是 Surge 自己的本机 SOCKS5 服务，该服务没有提供诊断所需的 UDP ASSOCIATE | 删除 `Diagnostics` 回环桥，不再制造必败 UDP 测试 |
| `include-all-networks` 警告 | 全网络接管可能影响 AirDrop、Xcode 调试或 USB Dashboard | 为 APNs 与防旁路继续保留；这是已知兼容性取舍，不是 DNS 或节点故障 |

事件中的 `SOCKS5 proxy listen on 127.0.0.1:6153` 和 `HTTP proxy listen on 127.0.0.1:6152` 是 Surge 本机监听信息，不代表服务暴露到局域网。配置仍保持 `allow-wifi-access=false`、`allow-hotspot-access=false` 和 `proxy-restricted-to-lan=true`。

## 当前基线

| 项目 | 数量或状态 |
| --- | --- |
| 策略组 | 30 |
| 活动规则 | 142 |
| `[Proxy]` 静态代理 | 0 |
| 自动组 | 10 个 `url-test`，全部含显式 `REJECT` |
| Smart 组 | 0 |
| 固定远程规则 | 29 |
| 动态远程规则 | 1 |
| 本地 `.list` 文件 | 29 |
| 固定 Ads | 152 条 |
| 固定 Pegasus | 1,438 条 |
| 国内 BiliBili | 16 个精确后缀 |
| 配置故障注入 | 133 项 |
| 固定快照提交 | `2b8fa93901061cf0482b079203630bcd11bfe0b1` |

主配置不嵌入节点或规则快照。29 份固定规则通过 jsDelivr 的完整提交 SHA 加载；唯一动态资源是 SukkaW 的 `domestic.conf`，每 24 小时更新。

## 快速使用

1. 先保存你自己的 Surge 格式订阅或 Sub-Store 输出地址。
2. 打开 `Surge.conf`，只把下面一行中的占位 URL 换成私人地址，不能把真实令牌提交到公开仓库。

   ```ini
   NodePool = select, REJECT, policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL, ...
   ```

3. 完整导入 R13.11。只导入公开原始链接而不替换占位 URL 时，`NodePool` 不会有节点；R13.11 会安全拒绝流量，而不是偷偷直连。
4. 打开 `NodePool`，确认能看到真实节点。第一项固定为 `REJECT`，这是订阅失效时的安全成员。
5. 打开 `Proxy`，选择第一项 `Auto`。升级后旧的 `Smart` 选择已不存在，通常会自动回到第一项；仍建议人工确认一次。
6. `Auto` 首次使用前会等待测试完成，之后每 600 秒或网络变化后重新评估；只有比当前节点快 100 ms 以上才切换，减少来回抖动。
7. 需要固定节点时，在 `NodePool` 选择具体真实节点；需要立即断网时，在 `Proxy` 选择 `REJECT`。

## 策略架构

| 策略 | 默认或成员 | 行为 |
| --- | --- | --- |
| `Final` | `Proxy`、`REJECT` | 未命中流量默认进入代理总入口 |
| `Proxy` | `Auto`、`NodePool`、五个地区组、`REJECT` | 默认自动选优，也可固定节点或手动拒绝 |
| `Auto` | 显式 `REJECT`＋`NodePool` 的真实节点 | `url-test` 自动选低延迟可用节点；空源明确失败 |
| `NodePool` | 显式 `REJECT`＋私人 `policy-path` | 手动节点池；资源失效时不会替换成直连 |
| 五个地区组 | 显式 `REJECT`＋名称过滤后的节点 | 香港、台湾、日本、新加坡、美国独立自动选优 |
| `ChatGPT`、`Claude`、`Gemini`、`TikTok` | 显式 `REJECT`＋日本、新加坡、台湾、美国节点 | 在审阅地区内自动选优，排除香港 |
| `ApplePush` | `Proxy`，后备 `DIRECT` | 唯一有意保留的直连后备，用于 APNs 可达性 |
| `Bahamut` | 台湾、香港 | 保持服务地区边界 |
| `Apple` | `DIRECT` 首选 | 国内 Apple 服务保持低延迟，可手动改代理 |

`AdBlock`、`Security`、`UDP`、`Domestic`、`AllServer` 与旧 `Smart` 都不存在。Ads 与 Pegasus 固定 `REJECT`，STUN 固定 `Proxy`，已知国内流量固定 `DIRECT`。

## 自动选择为什么不用 Smart

Smart 会利用真实连接质量、重传、失败和站点历史，节点来源稳定时确实更聪明。但 Surge 官方同时规定，Smart 忽略内建策略和嵌套组；组里没有可用真实代理时会使用 `DIRECT/SUBSTITUTE`。本配置的节点来自私人 `policy-path`，在首次导入、资源刷新、Sub-Store 暂停或地区筛选为空时可能短暂为空，真机已经复现了直连替代。

`url-test` 支持显式内建成员。R13.11 把 `REJECT` 写成每个自动组的第一个成员，`policy-regex-filter` 只过滤导入成员，不会过滤显式 `REJECT`。`evaluate-before-use=true` 会在第一次请求前等待评估；评估失败时请求报错。因此它牺牲 Smart 的站点记忆，换取可验证的失败关闭和稳定的低延迟自动选择。

## 网络诊断与 UDP 的真实边界

R13.11 的 `[Proxy]` 有意保持为空。`policy-path` 导入的节点只属于 `NodePool`，不会变成主配置 `[Proxy]` 的静态代理，所以 Surge 全局“网络诊断”中的“测试代理策略”和“UDP 代理转发”两行会保持空白。这是诚实结果，不是漏配。

不要再用本机 SOCKS5 回环把两行强行显示出来。它只能证明回环 TCP 可连，并不能证明真实节点或 UDP 可用。

正确测试方式如下。

1. 在 `NodePool` 确认当前资源已经加载真实节点。
2. 对一个具体真实节点执行策略测试；TCP 延迟只能证明该节点的 TCP 路径。
3. 在节点详情或 UDP 测试入口对这个具体节点测试 `apple.com@1.1.1.1`。
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
python3 tools/test_release_inventory.py
python3 tools/test_stage_surge_zip.py
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
sha256sum -c SHA256SUMS.txt
cmp --silent SHA256SUMS.txt SHA256SUMS_fixed.txt
python3 tools/package_release.py --output ../Surge-R13.11-Complete-No-Embedded-20260831.zip
```

## 真机验收

- `NodePool` 能看到真实节点，`Proxy` 当前选择 `Auto`，事件里不再出现 Smart `SUBSTITUTE`。
- 断开或填错私人 `policy-path` 后，流量应报错或显示 `REJECT`，不能直连成功。
- 国内 BiliBili 首页、搜索、账号、封面、起播、拖动、弹幕和评论命中 `DIRECT`。
- ChatGPT、Claude、Gemini、TikTok、Bahamut 和主要流媒体命中各自允许地区。
- Telegram、微信、APNs 在 Wi-Fi/蜂窝切换后可用。
- IPv4、IPv6 与 DNS 出口符合当前真实节点；远端递归 DNS 仍由节点提供方决定。
- 对一个具体真实节点测试 UDP。不支持时应明确失败，不能直连。
- 全局网络诊断的代理与 UDP 行保持空白；不要把空白当作节点失败，也不要恢复本机假桥。

## 主要依据

- [Surge 策略组与空组替代行为](https://manual.nssurge.com/policy-groups/overview.html)
- [Surge URL Test 自动组](https://manual.nssurge.com/policy-groups/url-test.html)
- [Surge 策略导入、过滤与成员顺序](https://manual.nssurge.com/policy-groups/policy-including.html)
- [Surge Smart 策略组](https://manual.nssurge.com/policy-groups/smart.html)
- [Surge UDP 协议支持与测试](https://manual.nssurge.com/policies/udp.html)
- [Surge General 与 include-all-networks](https://manual.nssurge.com/profile/general.html)
- [Surge 配置分离](https://manual.nssurge.com/profile/format.html)
- [Telegram 官方 CIDR](https://core.telegram.org/resources/cidr.txt)
- [Apple APNs 官方端口与网段](https://support.apple.com/en-us/102266)
- [OpenAI ChatGPT 网络建议](https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps)
- [SukkaW/Surge](https://github.com/SukkaW/Surge)
