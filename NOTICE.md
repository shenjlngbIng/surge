# 第三方来源与许可说明

本仓库发布 Surge iOS Privacy + Push R13.22 External Rules + Sentinel 配置、固定规则副本和维护工具。规则与第三方数据的权利归各自作者或项目所有。根目录 MIT License 只覆盖本仓库有权以该许可发布的代码和内容，不改变第三方材料原有的许可或权利状态。

## Blackmatrix7 规则来源

18 份服务规则以 `blackmatrix7/ios_rule_script` 的固定提交为维护输入。具体仓库、提交、文件路径、Git Blob、上游 SHA-256、本地增删边界和本地 SHA-256 记录在 `Rules/upstreams.lock.json`。

相关上游内容采用 GPL-2.0。完整许可副本见 `THIRD_PARTY_LICENSES/blackmatrix7-GPL-2.0.txt`。运行时不会直接访问 Blackmatrix7 地址，设备通过本仓库固定提交的 GitHub raw URL 读取审阅副本。

## SukkaW 来源

`Rules/Ads.list` 含有历史 SukkaW 来源和仓库维护内容。准确的历史输入提交尚未确认，因此 `Rules/maintained_sources.lock.json` 明确披露该限制，并禁止未经固定来源与差异审阅的自动刷新。R13.22 将该固定快照的 143 条活动规则作为外部 RULE-SET 引用，交由 AdBlock 策略控制。运行时不再直接引用 SukkaW 动态资源。SukkaW/Surge 采用 AGPL-3.0；许可副本见 `THIRD_PARTY_LICENSES/SukkaW-AGPL-3.0.txt`。

## Amnesty Tech Pegasus 数据

`Rules/Pegasus.list` 保存 Amnesty Tech 固定提交 `3d8f248a0d015f183724ae7d096a5c46a8bb5fc7` 中 `2021-07-18_nso/domains.txt` 的 1,438 个非空域名。上游 URL、Git Blob、上游 SHA-256、本地 SHA-256 和处理方式记录在 `Rules/resources.lock.json`。

固定提交根目录在复核时没有发现通用许可证文件。详情见 `THIRD_PARTY_LICENSES/AmnestyTech-NOTICE.txt`。本地副本保留纯域名，主配置以外部 `DOMAIN-SET` 引用，并交由默认 REJECT 的 Security 策略控制。

## 仓库维护规则

`APNs.list`、`Ads.list`、`AppleCN.list`、`BiliBili.list`、`China.list`、`Direct.list`、`Global.list`、`ProxyMedia.list`、`Telegram.list` 和 `WeChat.list` 的维护方式、来源说明、许可状态、活动条目数与 SHA-256 记录在 `Rules/maintained_sources.lock.json`。

来源不明的历史内容不会被猜测归属。后续修改需要保留差异记录，并按锁文件要求更新哈希。

## 运行时交付范围

R13.22 通过 GitHub raw URL 引用本仓库固定提交 `6e8e1bfbbdda66ee8ad0a5ad3979b6de8b5b7a51` 的 29 个规则快照，保留来源内容、顺序和匹配选项。Ads、Pegasus 和 China 分别连接到对应控制组，默认处理方式不变。主配置没有内嵌列表；完整维护包附原始来源文件与许可信息。

下面这些在线系统属于配置依赖或交付基础设施，不属于本地规则数据许可范围。

- GitHub 主配置与外部规则文件交付；jsDelivr 不再作为规则下载依赖。
- AliDNS 与 DNSPod 的 DNS、DoH 和引导地址。
- 华为与 Cloudflare 的连通性测试端点。
- Cloudflare `1.1.1.1` 的 UDP 连通性探针地址。
- Surge 内建数据库和客户端实现。
- 用户私下配置的订阅服务与 Sub-Store 部署。

使用者应自行确认其所在地区、分发方式和用途是否符合相关服务条款与法律要求。
