# R12.17 迁移说明

R12.17 把配置需要的最后一份第三方运行时静态资源收进自有仓库，并同步当前已经审阅的配置、锁文件、工具、工作流和文档。R12.16 的 Bilibili、Game/Microsoft、Netflix 和共享域名修正全部保留。

`NodePool → Smart` 架构、Telegram、APNs、DNS 与失败关闭设计保持不变。公开配置中的订阅地址仍是不可路由占位符，真实订阅和凭据只能放在私有副本中。

## R12.17 资源迁移

下面第一张表对比的是本次检查过程中产生的 `R12.16 Reviewed v3` 审阅稿。该审阅稿已经启用 Security、UDP、Pegasus 与 98 条规则，但 Pegasus 仍由设备直接读取第三方固定提交；R12.17 将它改为仓库本地副本。

| 项目 | R12.16 Reviewed v3 | R12.17 |
| --- | --- | --- |
| Pegasus IOC | 设备直接读取 Amnesty Tech 固定提交 | 设备读取本仓库 `Rules/Pegasus.list` |
| 第三方运行时静态 URL | 1 个 | 0 个 |
| 仓库运行资源 | 29 个 | 30 个 |
| 策略组 | 33 个 | 33 个 |
| 活动规则 | 98 条 | 98 条 |
| 资源来源锁 | 服务上游锁 | 服务上游锁、`resources.lock.json` 与 `maintained_sources.lock.json` |

Pegasus 本地副本保留原固定源的 1,438 个域名，不扩大为后缀。设备只访问 `shenjlngbIng/surge@r12.17-20260825`，维护工具才会访问锁定的第三方提交。

如果从仓库当前公开的 R12.16 发布版直接升级，还会同时得到审阅稿中已经完成的配置修正：策略组从 31 个增至 33 个，活动规则从 86 条增至 98 条，新增 Security 与 UDP 开关、Pegasus IOC、UDP 探测、Viu/HBO 覆盖、Google/YouTube 与 Game/Microsoft 共享基础设施覆盖，并把 `GEOIP,CN,DIRECT` 收紧为 `GEOIP,CN,DIRECT,no-resolve`。完整利弊见 `AUDIT_REPORT.md`。

## 最短升级步骤

1. 备份当前可用的私有 `Surge.conf`。
2. 用 R12.17 完整仓库文件替换公开基线，不要只替换主配置；使用安装工作流时填写包外公布的 `archive_sha256`。
3. 从旧私有配置中只复制 `NodePool.policy-path` 的 URL。
4. 不要复制旧版 `[Rule]`、服务策略组或规则文件，以免带回已修复的顺序和域名冲突。
5. 提交后创建固定标签 `r12.17-20260825`，等待 jsDelivr 同步。
6. 在 Surge 中重新载入配置并刷新全部外部资源。

不要只上传 `Pegasus.list` 或只替换 `Surge.conf`。两者必须和 `Rules/r10.lock.json`、`Rules/resources.lock.json`、`Rules/maintained_sources.lock.json`、审计工具、清单及校验和保持同一版本。安装工作流只删除旧发布清单明确管理、而新版本已取消的文件，不会把用户自有文件当作发布残留清理。

## Bilibili 国内版与国际版分流

新版使用两个规则文件，共用现有策略，不增加 Bilibili 策略组。

~~~ini
RULE-SET,https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@r12.17-20260825/Rules/BiliBiliIntl.list,Streaming
RULE-SET,https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@r12.17-20260825/Rules/BiliBili.list,DIRECT
~~~

国际版规则排在国内版之前，先接住 `apiintl.biliapi.net`、`bilibili.tv`、`biliintl.com` 和国际版专用 CDN。国内版随后接管 `bilibili.com`、`biliapi.com`、`biliapi.net`、图片域名和视频 CDN。

评论请求常用的 `api.bilibili.com` 会命中国内版 DIRECT。`bilivideo.com`、`hdslb.com` 和 `biliimg.com` 也保持直连。国际版仍可在 `Streaming` 中选择 `Proxy` 或地区节点。

`apm-misaka.biliapi.net` 已从泛媒体规则移除并由国内版直连规则接管。`cache.video.iqiyi.com` 也已移除并回到国内直连。

## R12.16 继承的其他变化

| 项目 | R12.15 | R12.16 |
| --- | --- | --- |
| Bilibili | 仅国际版专用规则 | 国内版 DIRECT，国际版 Streaming |
| 策略组 | 31 | 31，不新增 Bilibili 组 |
| 活动规则 | 85 | 86 |
| 远程源 | 28 | 29 |
| STUN | 位于中国 GEOIP 后 | 位于中国 GEOIP 前并强制进入 Proxy |
| 规则地址 | 跟随 `@main` | 固定到 `r12.17-20260825` |
| Xbox/Minecraft 等 | 先被 Microsoft 命中 | 先命中 Games |
| HBO 默认 | America | Proxy |
| Google 直连例外 | 14 条 | 删除，统一进入 Google |
| Netflix IP | 大量 AWS/云 CIDR | `IP-ASN,2906,no-resolve` |
| TikTok | 含共享 `snssdk.com` | 删除，国内字节域名回到国内兜底 |

Bahamut、Disney、HBO、Microsoft 和 Game 中的共享 CA、CDN、遥测与第三方 SaaS 后缀也已剔除，服务自己的专属域名仍保留。

## 升级后验证

### 运行资源

1. 确认 `Surge.conf` 中 30 个 `RULE-SET`/`DOMAIN-SET` 全部包含 `shenjlngbIng/surge@r12.17-20260825/Rules/`。
2. 确认不存在 `raw.githubusercontent.com`、Blackmatrix7 或 Amnesty Tech 的第三方运行时规则 URL。
3. 确认 `Rules/Pegasus.list` 有 1,438 个活动域名，并通过 `python3 tools/update_external_resources.py --verify-lock`。
4. 确认 `viu.now.com` 命中 `Streaming`，不会被 HBO 的 `now.com` 父级后缀抢先接管。

### Bilibili

1. 打开国内版客户端，播放视频并立即展开评论。
2. 确认 `api.bilibili.com`、`*.biliapi.com` 或 `*.biliapi.net` 命中 `DIRECT`。
3. 确认 `*.bilibili.tv` 也命中 `Streaming`。
4. 确认实际视频 CDN，如 `*.bilivideo.com`、`*.hdslb.com`，命中 `DIRECT`。

国内版评论仍慢时，应检查请求是否错误命中 `Streaming`，并确认设备加载的是当前发布标签。国际版异常时再检查已有 `Streaming` 的节点选择。

### 其他服务

- `cache.video.iqiyi.com` 应命中 `DIRECT`。
- `api.snssdk.com` 等国内字节域名应由国内规则直连。
- `xbox.com`、`minecraft.net`、Bethesda/Forza 域名应命中 `Games`。
- Google 更新、推送及下载域名应命中 `Google`，不再被 `Direct.list` 提前直连。
- Netflix 规则中应有 `IP-ASN,2906,no-resolve`，且不应出现 `IP-CIDR` 或 `IP-CIDR6`。
- HBO Asia/Now 默认跟随 `Proxy`；如需美国区 Max，再在 HBO 组手动选美国。

### 原有安全边界

- `NodePool` 仍为隐藏的 `select` 订阅容器，只有它持有 `policy-path`。
- `AllServer` 与五个地区组仍为 `smart, Fail-Closed`。
- Telegram 仍强制代理。
- `ApplePush` 仍为 `Proxy → DIRECT` 回落。
- `Security` 默认 REJECT，并保留 DIRECT 排错开关。
- STUN 位于中国 GEOIP 前并进入 `UDP`，该组默认选择 `Proxy`。
- AliDNS DoH/DoT、53/853/8853 控制、CGNAT 与 `ls.apple.com` 直连均保持不变。

## 回滚

如新版在你的网络中出现问题，重新导入升级前备份即可。不要把 `Final` 改为 `DIRECT` 掩盖规则或节点故障。
