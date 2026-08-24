# 来源与本地修改

更新日期：2026-08-24

本仓库发布 Surge iOS Privacy + Push R12.15 配置及维护工具。`Surge.conf` 中的第三方规则版权归各自作者或项目所有，相关许可证副本位于 `THIRD_PARTY_LICENSES/`。

本配置的设计过程参考了以下公开项目。

- [Rabbit-Spec Surge Developer](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-Developer.conf)
- [Rabbit-Spec Surge EN](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-EN.conf)
- [As-Lucky Lucky](https://raw.githubusercontent.com/As-Lucky/Lucky/main/Lucky-Surge.conf)
- [Coldvvater Surge 配置](https://gist.githubusercontent.com/Coldvvater/8093bc6be4340b5324b4a343493becfe/raw/Surge,conf)
- [Thoseyearsbrian Aegis](https://github.com/Thoseyearsbrian/Aegis) 及其 [Aegis_TC.conf](https://raw.githubusercontent.com/Thoseyearsbrian/Aegis/main/config/Aegis_TC.conf)

上述项目用于比较 Surge 章节组织、DNS 处理、规则集引用、策略组设计和安全边界。当前仓库重新维护自己的配置、策略组、规则顺序、审计工具和发布流程，公开包不包含这些项目的节点、订阅、Token、脚本或证书材料。运行时规则的实际上游以 `Rules/upstreams.lock.json` 为准。

R12.15 的被动 `NodePool` 与 Smart 决策分层是本仓库针对网络切换集中测速问题做出的组合设计。参考配置只用于验证 Surge 支持的策略组组织方式，没有复制其中的订阅、节点或私有资源。

本仓库的原创维护内容包括：

- Surge 配置结构与策略组设计
- 失败关闭策略和规则顺序
- DNS 防绕过规则
- 仓库自有远程 `RULE-SET`/`DOMAIN-SET` 引用与规则集审计锁
- 国内外精确域名集的筛选、零冲突边界与维护工具
- Telegram 与 APNs 路由方案
- 配置和规则审计脚本
- ZIP 安全暂存工具
- GitHub Actions 工作流
- 使用、安全和贡献文档

原创脚本、配置结构与文档采用仓库根目录 `LICENSE` 中的 MIT License。第三方规则、数据和材料继续遵循各自许可证；MIT License 不替代或覆盖第三方许可证。

公开仓库不得包含真实订阅地址、代理节点、Token、密码、Cookie、私钥或证书。`Rules/*.list`、`THIRD_PARTY_LICENSES/` 和维护工具属于审计链路，不应删除。
