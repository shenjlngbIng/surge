# Surge iOS Privacy + Push R13.13

R13.13 恢复正常的单订阅使用方式。用户只需要在 `Surge.conf` 中替换一次 `NodePool.policy-path` 的订阅地址，不需要创建 `Private-Proxies.conf`，不需要安装 Sub-Store 转换脚本，也不需要按特定顺序导入两个配置。

日常自动入口、五个地区入口、ChatGPT、Claude、Gemini 与 TikTok 继续使用带显式 `REJECT` 的 `url-test`。订阅为空、更新失败、地区无匹配节点或测速全部失败时，请求明确失败，不会静默替换为 `DIRECT/SUBSTITUTE`。

## 三步使用

1. 下载或导入根目录的 `Surge.conf`。
2. 在 Surge 的文本模式中搜索 `REPLACE_WITH_SURGE_SUBSCRIPTION_URL`，把完整占位地址替换为自己的 Surge 格式订阅地址。
3. 保存并重新加载配置，打开 `NodePool`，确认 `REJECT` 后面已经出现真实节点；`Proxy` 保持选择 `Auto`。

只需要改这一行：

```ini
NodePool = select, REJECT, policy-path=https://example.invalid/REPLACE_WITH_SURGE_SUBSCRIPTION_URL, update-interval=3600, no-alert=0, hidden=0, include-all-proxies=0
```

使用 Sub-Store 时，直接粘贴复制出来的下载地址。为避免输出格式依赖 User-Agent，建议明确指定 Surge：

```text
https://sub.store/download/你的订阅名称?target=Surge
```

若原地址已经带有 `?`，使用 `&target=Surge`。不要把私人订阅地址、令牌、节点名称或节点日志提交到公开仓库。

## 为什么不再要求分离配置

R13.12 为了让 Surge iOS 的全局网络诊断枚举真实节点，要求先安装含 `[Proxy]` 的 `Private-Proxies.conf`，再加载主配置。这个方案能改善全局诊断显示，但安装成本过高，也容易因为文件名或导入顺序产生“加载分离配置段失败”。

R13.13 采用 Surge 官方及常见公开配置使用的 `policy-path` 单订阅方式。它能正常加载节点、分流和自动测速，但外置节点不会成为主配置 `[Proxy]` 中的静态代理，因此全局“测试代理策略”和“UDP 代理转发”可能保持空白。这是诊断枚举边界，不代表节点 TCP 或 UDP 一定不可用。

不要加入本机 SOCKS5 回环来强行填绿。R13.10 已证明这种做法只能测试本机回环 TCP，并可能固定得到“不支持 UDP relay”的错误，不能证明真实节点可用。

## 当前基线

| 项目 | 数量或状态 |
| --- | --- |
| 用户需修改 | 1 个 `policy-path` URL |
| 额外私人配置 | 0 |
| Sub-Store 自定义脚本 | 0 |
| 策略组 | 30 |
| 活动规则 | 142 |
| 自动组 | 10 个带显式 `REJECT` 的 `url-test` |
| Smart 组 | 0 |
| 固定远程规则 | 29 |
| 动态远程规则 | 1 |
| 固定 Ads | 152 条 |
| 固定 Pegasus | 1,438 条 |
| 国内 BiliBili | 16 个精确后缀 |
| 固定快照提交 | `2b8fa93901061cf0482b079203630bcd11bfe0b1` |

主配置不嵌入节点或规则快照。29 份固定规则通过 jsDelivr 的完整提交 SHA 加载；唯一动态资源是 SukkaW 的 `domestic.conf`，每 24 小时更新。

## 策略架构

| 策略 | 默认或成员 | 行为 |
| --- | --- | --- |
| `Final` | `Proxy`、`REJECT` | 未匹配流量默认进入代理总入口 |
| `Proxy` | `Auto`、`NodePool`、五个地区组、`REJECT` | 默认自动选优，也可固定真实节点 |
| `Auto` | 显式 `REJECT`＋`NodePool` | 自动选择低延迟可用节点；空源明确失败 |
| `NodePool` | 显式 `REJECT`＋单个 `policy-path` | 每小时更新订阅，提供手动节点选择 |
| 五个地区组 | 显式 `REJECT`＋名称过滤后的节点 | 香港、台湾、日本、新加坡、美国独立自动选优 |
| AI 与 TikTok | 显式 `REJECT`＋日、新、台、美节点 | 排除香港，地区为空时拒绝 |
| `ApplePush` | `Proxy`，后备 `DIRECT` | 唯一保留的直连后备，用于 APNs 可达性 |

`AdBlock`、`Security`、`UDP`、`Domestic`、`AllServer` 与旧 `Smart` 均不存在。Ads 与 Pegasus 固定 `REJECT`，STUN 固定 `Proxy`，已知国内流量固定 `DIRECT`。

## DNS、UDP 与隐私边界

- Surge 自身使用 AliDNS 与 DNSPod DoH，证书校验开启。
- `encrypted-dns-follow-outbound-mode=false` 避免域名型节点的启动解析环。
- 已审阅的大陆应用 DNS 固定 `DIRECT`；境外应用 DNS 固定 `Proxy`。
- 公网 53、853、8853 端口在应用层规则中拒绝；系统 DNS 由 `hijack-dns=*:53` 接管。
- `udp-policy-not-supported-behaviour=REJECT`，不支持 UDP 的节点不会偷偷直连。
- `block-quic=per-policy`，具体 QUIC/UDP 能力仍取决于节点协议和服务器端配置。

配置无法凭空让服务商节点获得 UDP 能力，也无法证明远端递归 DNS、运营商网络或第三方节点绝对没有泄漏。最终需在真实设备的 Wi-Fi 和蜂窝网络分别验证。

## 国内 BiliBili

- `Rules/BiliBili.list` 固定 16 个审阅后缀并指向 `DIRECT`。
- `httpdns.bilivideo.com` 与 `line3-h5-mobile-api.biligame.com` 位于 Ads 前并固定直连。
- 国内 API、页面、图片、视频 CDN、起播、拖动、弹幕和评论不经过隐藏状态组。
- 国际版专用策略已删除，历史国际域名进入通用 `Proxy`，避免被国内父后缀误覆盖。

## 验收

1. `NodePool` 中 `REJECT` 后面能看到真实节点。
2. `Proxy` 当前选择为 `Auto`，日常访问不会出现 `DIRECT/SUBSTITUTE` 替代事件。
3. ChatGPT、Claude、Gemini、TikTok、Bahamut 和主要流媒体命中对应策略。
4. 国内 BiliBili 首页、搜索、账号、封面、起播、拖动、弹幕和评论命中 `DIRECT`。
5. Telegram、微信和 APNs 在 Wi-Fi/蜂窝切换后可用。
6. 在 `NodePool` 内对真实节点执行 TCP 测试；UDP 使用真实 UDP 流量或节点能力测试，不以全局诊断空白作为成功或失败结论。

## 本地审计与打包

```bash
python3 tools/convert_to_remote_rules.py
python3 tools/generate_runtime_lock.py
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/audit_precise_domains.py
python3 tools/test_audit_config.py
python3 tools/test_release_inventory.py
python3 tools/test_stage_surge_zip.py
python3 tools/package_release.py --output ../Surge-R13.13-Complete-No-Embedded-20260901.zip
```

在线动态资源检查需要网络：

```bash
python3 tools/audit_rules.py --check-dynamic
python3 tools/audit_rules.py --check-runtime-remote
python3 tools/update_external_resources.py --verify-lock
python3 tools/update_service_rules.py --verify-lock
```
