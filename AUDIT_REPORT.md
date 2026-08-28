# Surge R13.2 Enhanced 全量审计报告

审计日期：2026-08-28

## 结论

R13.2 通过配置结构、策略引用、循环依赖、规则顺序、原版保留性、本地规则库存、来源锁、动态源在线格式、故障注入、发布白名单、ZIP 路径安全、清单与双份 SHA-256 检查。

交付结论为“可以发布，仍需 Surge iOS 真机验收”。当前环境没有 Surge iOS 原生解析器、用户订阅节点、运营商路径和 iOS 后台状态，因此不能把静态检查包装成运行时证明。

## 审计范围

- `Surge.conf` 全部 5 个配置节。
- 34 个策略组、组成员、可见性、导入来源、正则和循环关系。
- 130 条活动规则及首条命中顺序。
- 30 个固定提交远程资源和 30 份本地规则快照。
- 3 个 SukkaW 动态运行资源。
- 4 个 JSON 锁、15 个维护与审计脚本、工作流和 13 个根目录文件。
- 66 文件严格发布清单、确定性 ZIP 和双份 SHA-256。
- 从 R13.1 到 R13.2 的功能保留与去向调整。

## R13.1 保留性

| 检查项 | R13.1 | R13.2 | 结果 |
| --- | ---: | ---: | --- |
| 原策略组名称 | 33 | 33 个仍存在 | 33/33 保留 |
| 原规则匹配条件 | 125 | 125 个仍存在 | 125/125 保留 |
| 原固定远程 URL | 30 | 30 个仍存在 | 30/30 保留 |
| 原本地 `.list` | 30 | 30 个字节未改 | 30/30 保留 |
| `Fail-Closed` | `127.0.0.1:1` | 相同 | 保留 |
| 订阅占位符 | 1 处 | 1 处 | 保留，未填私人 URL |
| APNs/AI/流媒体/游戏等分类 | 存在 | 存在 | 保留 |

配置差异中有 16 条原规则改变策略去向，但没有删除匹配对象或远程 URL：

- `WeChat.list`、`Direct.list`、`BiliBili.list` 和 `China.list` 从 `DIRECT` 改为 `Domestic`。
- 12 个国内共享云后缀从 `Proxy` 改为 `Domestic`。

`Domestic` 默认成员仍是 `DIRECT`，所以境内默认行为保持直连；区别是用户可以在境外或受限网络中整体切到 `Proxy`。

## 配置结构结果

| 检查项 | 结果 |
| --- | ---: |
| 配置节 | 5/5 |
| 策略组 | 34 |
| 活动规则 | 130 |
| 运行时远程资源 | 33 |
| 固定提交资源 | 30 |
| 动态资源 | 3 |
| 本地规则文件 | 30 |
| 未知策略引用 | 0 |
| 策略组循环 | 0 |
| 重复活动规则 | 0 |
| 地区正则编译 | 5/5 |
| `FINAL` | 1 条且位于末尾 |
| 订阅占位符 | 恰好 1 处 |
| 主配置内嵌规则快照 | 0 |

`Surge.conf` 为 UTF-8、LF、无 BOM、无 NUL，并以换行结束。未发现 `token=`、`password=`、Authorization、URL 用户名密码或带查询参数的私人订阅。

## 策略架构

### 订阅与失败关闭

`NodePool` 是唯一持有 `policy-path` 的组，保持可见 `select`。显式首成员是 `Fail-Closed`，随后才是远程订阅导入的实际代理。公开 URL 仍为：

```text
https://example.invalid/REPLACE_WITH_SUB_STORE_URL
```

订阅为空、地址未替换、格式不兼容或 Sub-Store 模块未接管时，连接失败而不是直连。

### Smart 默认

`Proxy` 的成员顺序为 `AllServer`、`NodePool` 和五个地区组。`AllServer` 与地区组使用 `smart`，显式保留 `Fail-Closed`、`evaluate-before-use=true` 和 `include-other-group=NodePool`。

Smart 只接受实际代理成员。`include-other-group=NodePool` 会展开 NodePool 的代理，地区正则只筛选导入成员，显式 `Fail-Closed` 不被筛掉。旧 `url-test` 的 `interval` 和 `tolerance` 已删除，因为 Surge 官方说明 `interval` 对 Smart 无效。

### 可见控制组

| 组 | 默认 | 可见 | 审计目的 |
| --- | --- | --- | --- |
| `AdBlock` | `REJECT` | 是 | 广告误报可快速切到 `DIRECT` 对比 |
| `Security` | `REJECT` | 是 | 钓鱼或历史 IOC 误报可快速隔离 |
| `UDP` | `Proxy` | 是 | STUN/UDP 可在 Proxy、NodePool、拒绝和直连间排查 |
| `Domestic` | `DIRECT` | 是 | 国内流量可整体切换到 Proxy |
| `ApplePush` | `Proxy` 后备 `DIRECT` | 否 | 保持低频自动后备，避免日常误触 |

## General、DNS 与网络边界

- `loglevel=notify`，提供日常诊断信息，不启用高开销 `verbose`。
- `include-all-networks=true`、`include-apns=true`、`icmp-forwarding=false` 保留。
- Wi-Fi 代理、热点代理和 Web 控制面板保持关闭。
- UDP 不支持时为 `REJECT`，QUIC 继续 `per-policy`。
- IPv6 保持开启，VIF 使用 `auto`，IPv4 与 IPv6 公网字面量都有代理兜底。
- `captive.apple.com` 精确直连，改善公共 Wi-Fi 登录；未加入宽泛 SYSTEM 直连集合。

DNS 仍使用 AliDNS 与 DNSPod 两个 DoH，并保持 `encrypted-dns-follow-outbound-mode=false` 和证书校验。Surge 会并发查询多个加密 DNS，因此两个服务都可能看到查询，且连接直连。本版按“不删除原功能”边界保留它们，没有把这描述为匿名 DNS，也没有通过增加第三个解析器假装提高隐私。

## 规则顺序

以下关键顺序由审计器直接约束：

1. 私网与本地主机在公网阻断前处理。
2. `captive.apple.com` 在 STUN 与公网 DNS 阻断前。
3. STUN 在 53、853、8853 端口规则前。
4. Apple 配置引导在出口检测和普通服务前。
5. 动态钓鱼在固定 Pegasus 前，Pegasus 在 APNs 前。
6. Apple 流媒体专用主机在 AppleCN 前。
7. 固定 Ads 在动态基础广告前，两者都在 AI 规则前。
8. BiliBili 国际版在国内版前。
9. Microsoft 专用覆盖与 Google Cloud 例外在 Game 前。
10. Game 在 OneDrive 和 Microsoft 前。
11. 12 个国内共享云后缀在动态国内补充和 China 前。
12. 动态国内补充在固定 China 前，China 在 Global 前。
13. Global 在 `GEOIP,CN,Domestic,no-resolve` 前。
14. CN GeoIP、IPv4 兜底、IPv6 兜底和唯一 `FINAL` 紧邻并保持顺序。

所有 CIDR 都通过地址族与语法检查，并带 `no-resolve`。`GEOIP,CN` 也带 `no-resolve`，不会为了尚未解析的域名主动触发本地 DNS。

## 固定规则库存

30 个固定 URL 全部指向：

```text
https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@d1d714d575d5494ef1a7613238f4f301e1b293df/Rules/
```

审计时 30/30 返回 HTTP 200，合计 5,542 条有效内容，格式与文件内重复检查通过。包内 30 份 `.list` 与 R13.1 完整包字节一致，Pegasus、服务规则和仓库维护规则的来源锁继续通过。

固定提交提高可复现性，但不会自动获得新规则。定期更新检查任务会比较仓库新提交，只报告变化，不自动修改配置。

## 动态运行资源

| 资源 | 类型 | 策略 | 发布时条目 | 字节 | 发布时 SHA-256 |
| --- | --- | --- | ---: | ---: | --- |
| `reject_phishing.conf` | DOMAIN-SET | Security | 147,468 | 3,146,611 | `c7dd0c7429e1f11168b1e1923a54defbca6403f13ba7e10246b3b87b5c367f4e` |
| `reject.conf` | DOMAIN-SET | AdBlock | 135,304 | 3,014,590 | `5ceb8c9903e4fc967722eab763a91e7d5ef91fcbe9bad71d1c378cf5ad800e4d` |
| `domestic.conf` | RULE-SET | Domestic | 869 | 22,632 | `56809cd8399666433acb1229c3a472667a32c86fc2a0b9861a5dca54020564aa` |

发布时三份资源均返回 HTTP 200，UTF-8 解码、类型格式、大小和文件内重复检查通过。三份动态资源合计 283,641 条，全部 33 个远程资源合计 289,183 条、6,337,816 字节。

动态内容不随 ZIP 分发。`Rules/r10.lock.json` 保存发布观察值，在线审计检查当前可用性与格式，不要求未来 SHA-256 固定。这样明确承认动态更新带来的供应链与误报风险。

来源为 [SukkaW/Surge](https://github.com/SukkaW/Surge) 和 [ruleset.skk.moe](https://ruleset.skk.moe/)，上游标注 AGPL-3.0。许可副本已存在于 `THIRD_PARTY_LICENSES/SukkaW-AGPL-3.0.txt`。

## 自动化测试

| 测试 | 结果 |
| --- | ---: |
| 配置故障注入 | 110/110 被拒绝 |
| ZIP 安全回归 | 26/26 通过 |
| 发布清单回归 | 15/15 通过 |
| Python 编译 | 15/15 工具通过 |
| 运行锁再生成 | 与受审配置一致 |
| Pegasus 固定来源锁 | 通过 |
| 19 份服务规则来源锁 | 通过 |
| China/Global 精确集合 | Domestic 306、Proxy 116、交叉冲突 0 |
| 严格发布目录 | 66/66 文件 |
| 双份 SHA-256 | 一致并全部校验通过 |
| 确定性打包 | 相同输入两次 ZIP 字节一致 |

故障注入覆盖版本头、日志、接管、DNS、Host 引导、Fail-Closed、策略默认、可见性、Smart 参数、订阅泄露、动态与固定 URL、Security/AdBlock 内嵌、规则策略、CIDR、关键先后、CN GeoIP、公共兜底和 `FINAL`。

## No-Embedded 的准确含义

- `Surge.conf` 不包含 Pegasus 域名、广告域名、钓鱼域名或其他远程规则逐条内容。
- 完整包保留原 30 份固定 `.list`，用于审阅、仓库上传和来源复核；设备运行时仍读取固定 CDN URL。
- 三份大型动态规则不复制进包，只保留运行 URL 与审计元数据。
- 订阅节点、令牌、证书、MITM、脚本和重写均不在公开包内。

## README 与完整包一致性

README 已按完整使用手册规格更新，覆盖订阅与 Sub-Store、Smart、手动节点、Domestic、策略组、DNS 真实限制、UDP、APNs、规则顺序、33 个运行资源、动态风险、维护命令、上传工作流、故障排查、真机验收和发布前检查。

文档中的版本、日期、数量、包名、策略默认、可见性、命令和测试输出均由当前文件复核。R13.1 的手动默认、隐藏 UDP 和 `url-test` 行为没有被错误沿用为 R13.2 当前行为。

## 剩余风险

| 风险 | 实际影响 | 当前处理 |
| --- | --- | --- |
| 无 Surge iOS 原生解析器 | 私有语义差异只能在应用中发现 | 要求导入后执行配置检查与真机验收 |
| 动态列表变化 | 可能产生误报、撤回或上游故障 | 精确 URL、可见策略、在线格式检查和定期监控 |
| 双 DoH 并发直连 | 两个提供方都可能看到查询 | 明确披露，未擅自删除或替换原 DNS |
| 大型 DOMAIN-SET | 首次下载和索引较慢 | 不内嵌、24 小时更新、由 Surge 缓存与索引 |
| 固定 30 份规则陈旧 | 稳定但不会自动获得新提交 | 保持可复现并由定期任务检查更新 |
| GeoIP 误分类 | 少数 IP 可能走错 Domestic | Domestic 可一键切换到 Proxy |
| Smart 结果非固定 | 不同站点可能选择不同节点 | 可随时把 Proxy 切到 NodePool 手动固定 |
| APNs 后备 | 无法保证所有运营商及时推送 | 必须做锁屏、Wi-Fi、蜂窝切换测试 |

## 真机验收清单

- Surge 导入时没有未知参数、格式错误或资源类型警告。
- NodePool 能载入实际代理，订阅令牌没有出现在公开文件或日志截图中。
- AllServer 能选中真实节点；空订阅时只剩 Fail-Closed 并明确失败。
- 五个地区组能按实际节点命名筛选。
- `Domestic=DIRECT` 和 `Domestic=Proxy` 分别按网络环境工作。
- 常用网站在 AdBlock 与 Security 开启时没有明显误报。
- APNs 在锁屏、Wi-Fi 和蜂窝切换后正常。
- STUN/语音/游戏命中 UDP，节点支持所需 UDP Relay。
- 公共 Wi-Fi 门户能弹出并完成登录。
- IPv4 与 IPv6 出口符合预期，没有意外直连。
- AI、流媒体、Telegram、Google、Microsoft 和游戏命中预期服务组。
- Surge 日志没有持续的规则下载、DNS 循环或代理循环错误。

## 参考依据

- [Surge Smart Group](https://manual.nssurge.com/policy-groups/smart.html)
- [Surge Policy Including](https://manual.nssurge.com/policy-groups/policy-including.html)
- [Surge Rule System Overview](https://manual.nssurge.com/rules/overview.html)
- [Surge Rule Sets](https://manual.nssurge.com/rules/ruleset.html)
- [Surge Encrypted DNS](https://manual.nssurge.com/dns/encrypted-dns.html)
- [Sukka Ruleset Server](https://ruleset.skk.moe/)
