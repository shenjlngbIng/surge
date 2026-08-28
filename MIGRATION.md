# R13.1 到 R13.2 Enhanced 迁移说明

R13.2 是 R13.1 的保留式增强，不是推倒重写。原有 33 个策略组名称、125 个规则匹配条件、30 个固定远程 URL、30 份本地规则快照、订阅占位符和 `Fail-Closed` 全部保留。

主配置、运行锁、审计器、故障注入、README、工作流、清单和哈希必须一起更新。只替换 `Surge.conf` 会留下 R13.1 的数量、策略架构和供应链断言，后续审计会得到错误结果。

## 主要变化

| 项目 | R13.1 | R13.2 Enhanced |
| --- | --- | --- |
| 策略组 | 33 | 34 |
| 活动规则 | 125 | 130 |
| 固定提交远程资源 | 30 | 30，原 URL 全部保留 |
| 动态远程资源 | 0 | 3 |
| 本地规则文件 | 30 | 30 |
| `Proxy` 默认 | `NodePool` | `AllServer` |
| 自动选择 | 6 个 `url-test` | 6 个 `smart` |
| `AdBlock` | 隐藏 | 可见 |
| `Security` | 隐藏 | 可见 |
| `UDP` | 隐藏，默认 `NodePool` | 可见，默认 `Proxy` |
| 国内总开关 | 无 | `Domestic = DIRECT, Proxy` |
| 国内固定规则 | 多处硬编码 `DIRECT` 或 `Proxy` | 统一进入 `Domestic` |
| Wi-Fi 门户 | 无精确补充 | `captive.apple.com` 直连 |
| 广告防护 | 固定 `Ads.list` | 固定 Ads 加动态基础 DOMAIN-SET |
| 安全防护 | 固定 Pegasus 历史 IOC | 动态钓鱼 DOMAIN-SET 加固定 Pegasus |
| 国内补充 | 固定 China 精确集合 | 动态国内 RULE-SET 加固定 China 与 CN GeoIP |
| 日志级别 | `warning` | `notify` |
| 配置故障注入 | 99 项 | 110 项 |
| ZIP 安全回归 | 25 项 | 26 项 |
| 完整包 | `Surge-R13.1-Complete-No-Embedded-20260827.zip` | `Surge-R13.2-Complete-No-Embedded-20260828.zip` |

## 没有删除的内容

- APNs、Apple、广告、安全、AI、流媒体、Telegram、X、Google、Microsoft、游戏和 STUN/UDP 分类仍在。
- 五个地区组、`AllServer`、`NodePool`、`Proxy`、`Final` 和 `Fail-Closed` 名称仍在。
- 原 30 个远程 URL 仍固定到提交 `d1d714d575d5494ef1a7613238f4f301e1b293df`。
- 原 125 个规则的“类型 + 匹配对象”全部仍存在。
- DNS、IPv6、全网络接管、ICMP 防泄漏、局域网访问限制和 APNs 接管参数仍在。
- 公开订阅仍是 `https://example.invalid/REPLACE_WITH_SUB_STORE_URL`，没有写入私人链接。

16 个原规则只改变策略去向：`WeChat.list`、`Direct.list`、`BiliBili.list`、`China.list` 和 12 个国内共享云后缀统一进入 `Domestic`。默认行为仍是直连，但用户可在受限网络中一键改为代理。

## 推荐迁移步骤

1. 备份 R13.1 私人副本中的真实 `policy-path` 和你手动选择的策略。不要把含令牌的备份放进公开目录。
2. 解压 R13.2 完整包，用全部 66 个文件替换旧发布文件，保留目录层级。
3. 在新的 `Surge.conf` 中只替换 `NodePool.policy-path`。不要整行覆盖，否则会丢失 `Fail-Closed` 和更新参数。
4. 导入配置并刷新外部资源，确认 30 个固定资源与 3 个动态资源都能加载。
5. 确认 `NodePool` 已出现订阅节点。若使用 Sub-Store 合成域名，同时确认对应模块已启用。
6. 检查 `Proxy` 当前选择。Surge 可能保留 R13.1 的 `NodePool` 选择；要使用新默认自动策略，请手动切到 `AllServer` 一次。
7. 测试 `Domestic=DIRECT`。在境外、校园网或受限网络中如国内服务异常，再切到 `Domestic=Proxy` 对比。
8. 完成 Wi-Fi、蜂窝、APNs、DNS、IPv4、IPv6、UDP、AI、流媒体、广告误报和钓鱼误报测试。

## Smart 迁移注意

`AllServer` 与五个地区组保留原名称，因此自定义服务组的引用不需要改名。它们从 `url-test` 变为 `smart`，继续通过 `include-other-group=NodePool` 读取实际代理，并显式保留 `Fail-Closed`。

Smart 根据真实连接质量、丢包和测试结果选择候选，并在连接失败时尝试其他代理。`interval` 对 Smart 无效，因此 R13.2 删除了旧的 1,800 秒间隔与 100 毫秒容差。若你需要永久固定节点，把 `Proxy` 切到 `NodePool` 并手动选择即可。

## 动态规则迁移注意

新增三份运行时 URL：

```text
https://ruleset.skk.moe/List/domainset/reject_phishing.conf
https://ruleset.skk.moe/List/domainset/reject.conf
https://ruleset.skk.moe/List/non_ip/domestic.conf
```

它们使用 86,400 秒更新间隔，内容不放进完整包。动态列表可能随上游变化并产生误报，所以 `Security`、`AdBlock` 和 `Domestic` 保持可见。遇到异常时先切换对应策略确认，不要删除原固定资源或改成未经审阅的镜像。

## 本地校验

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
python3 tools/audit_precise_domains.py
python3 tools/test_audit_config.py
python3 tools/test_release_inventory.py
python3 tools/test_stage_surge_zip.py
sha256sum -c SHA256SUMS.txt
cmp --silent SHA256SUMS.txt SHA256SUMS_fixed.txt
```

离线审计应报告 34 个策略组、130 条规则、33 个运行时资源、30 个本地规则文件和零条内嵌规则内容。动态在线检查应分别报告三份资源当前的条目数、字节数和 SHA-256。

## 回退

需要回退时，重新使用完整的 R13.1 发布包并恢复当时的私人订阅地址。不要把 R13.2 的 `Rules/r10.lock.json`、README、清单或审计工具留在 R13.1 目录中。

回退会同时失去 Smart 默认选择、可见的安全/广告/UDP 开关、`Domestic`、公共 Wi-Fi 门户补充、三份动态源和 CN GeoIP 路由。回退后要重新检查 APNs、DNS、双栈、UDP、国内服务与常用网站。
