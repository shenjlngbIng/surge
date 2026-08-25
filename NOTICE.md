# 来源与本地修改

更新日期：2026-08-25

本仓库发布 Surge iOS Privacy + Push R12.17 配置及维护工具。规则与第三方数据版权归各自作者或项目所有，相关许可证和来源说明位于 `THIRD_PARTY_LICENSES/`。

本配置的设计过程参考了以下公开项目。

- [Rabbit-Spec Surge Developer](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-Developer.conf)
- [Rabbit-Spec Surge EN](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-EN.conf)
- [As-Lucky Lucky](https://raw.githubusercontent.com/As-Lucky/Lucky/main/Lucky-Surge.conf)
- [Coldvvater Surge 配置](https://gist.githubusercontent.com/Coldvvater/8093bc6be4340b5324b4a343493becfe/raw/Surge,conf)
- [Thoseyearsbrian Aegis](https://github.com/Thoseyearsbrian/Aegis) 及其 [Aegis_TC.conf](https://raw.githubusercontent.com/Thoseyearsbrian/Aegis/main/config/Aegis_TC.conf)
- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)
- [AmnestyTech/investigations](https://github.com/AmnestyTech/investigations)

上述项目用于比较 Surge 章节组织、DNS 处理、规则集引用、策略组设计和安全边界。当前仓库重新维护自己的配置、策略组、规则顺序、审计工具和发布流程，公开包不包含这些项目的节点、订阅、Token、脚本或证书材料。19 个服务规则的维护来源以 `Rules/upstreams.lock.json` 为准，独立 Pegasus 资源的维护来源以 `Rules/resources.lock.json` 为准，其余 10 个仓库维护列表的来源状态、哈希和许可说明以 `Rules/maintained_sources.lock.json` 为准。

R12.17 的设备运行时只加载 `shenjlngbIng/surge` 固定发布标签中的 30 个本地规则快照，不直接访问上述第三方规则仓库。第三方 URL 只用于维护时下载固定提交，并接受完整提交、Git Blob 和 SHA-256 校验。该范围不包含 jsDelivr/GitHub 交付、Surge 内建 GeoIP/ASN 数据、AliDNS、连通性测试端点和私有订阅地址；这些系统或在线依赖在 README 中单独披露。

R12.15 的被动 `NodePool` 与 Smart 决策分层是本仓库针对网络切换集中测速问题做出的组合设计。参考配置只用于验证 Surge 支持的策略组组织方式，没有复制其中的订阅、节点或私有资源。

R12.16 对固定上游快照执行本地、可复现的语义筛选。Bilibili 国内版与国际版使用两个规则文件和现有策略，国内版直连，国际版进入 `Streaming`。共享云、遥测和国内服务误代理项已经删除，Netflix 的宽泛云网段改为官方 Open Connect ASN。终审已把 278 条历史本地行全部显式写入 `Rules/upstreams.lock.json`；更新器只从固定上游和锁输入生成，不再用旧输出隐式续存规则。历史来源不明确的行保留未决许可披露，不将其错误归属于第三方项目。

R12.17 将 Amnesty Tech 固定提交 `3d8f248a0d015f183724ae7d096a5c46a8bb5fc7` 的 `2021-07-18_nso/domains.txt` 保存为 `Rules/Pegasus.list`。本地副本保留 1,438 个非空域名，不扩大为后缀。固定提交根目录在复核时未发现通用许可证文件，详情见 `THIRD_PARTY_LICENSES/AmnestyTech-NOTICE.txt`；本仓库根目录 MIT License 不覆盖该数据。

本仓库的原创维护内容包括：

- Surge 配置结构与策略组设计
- 失败关闭策略和规则顺序
- DNS 防绕过规则
- 仓库自有远程 `RULE-SET`/`DOMAIN-SET` 引用与规则集审计锁
- 第三方维护输入与设备运行时本仓库副本的隔离
- 国内外精确域名集的筛选、零冲突边界与维护工具
- Telegram 与 APNs 路由方案
- 配置和规则审计脚本
- ZIP 安全暂存工具
- GitHub Actions 工作流
- 使用、安全和贡献文档

原创脚本、配置结构与文档采用仓库根目录 `LICENSE` 中的 MIT License。第三方规则、数据和材料继续遵循各自许可证；MIT License 不替代或覆盖第三方许可证。

公开仓库不得包含真实订阅地址、代理节点、Token、密码、Cookie、私钥或证书。`Rules/*.list`、四份锁文件、`THIRD_PARTY_LICENSES/` 和维护工具属于审计链路，不应删除。
