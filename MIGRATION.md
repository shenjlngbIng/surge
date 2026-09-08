# 升级到 R13.20

本版精简注释、默认参数和两条重复 DNS 规则，保留原有 40 个策略组、29 份外置规则、单订阅入口、节点池和哨兵。辅助组继续隐藏，地区与服务组保持可见。

## 操作步骤

1. 备份正在使用的配置，记下当前有效的订阅地址、模块和手动选择的策略。
2. 通过 [主配置链接](https://raw.githubusercontent.com/shenjlngbIng/surge/main/Surge.conf) 导入新配置。
3. 搜索 `REPLACE_WITH_SURGE_SUBSCRIPTION_URL`，将完整占位 URL 替换为当前有效的 Surge 格式订阅地址。
4. 保留现有可用的 Sub-Store 模块，加载 Subscription 与 29 份规则，检查 NodePool 中的真实节点。
5. 启用新配置和规则模式，检查 Proxy、NodePool 以及各服务组的当前选择。

普通用户只需 Surge.conf，不需要导入维护 ZIP、关联分离文件或新增脚本。只点击“外部资源更新”不会升级旧主配置。主配置中的版本标记应为 R13.20。

## 与 R13.19 的区别

| 项目 | R13.19 辅助组隐藏版 | R13.20 |
| --- | --- | --- |
| 配置行数 | 387 | 311 |
| 主分流指令 | 144 | 142 |
| 外部规则文件 | 29 | 29 |
| 策略组 | 40 | 40 |
| 可见与隐藏组 | 29 / 11 | 29 / 11 |
| 订阅入口 | Subscription | Subscription |

移除 `dns.alidns.com` 和 `dns.nextdns.io` 的精确规则后，相应后缀仍转到 Proxy。省略的参数采用官方默认值，不改变已核对的组成员、初始选择或出站逻辑。完整删改清单见 [README.md](README.md)。

配置保留原有独立直连 DoH 和 UDP 参数。本次精简不代表真实节点的 UDP、解锁或 DNS 检测已经通过实机验证。
