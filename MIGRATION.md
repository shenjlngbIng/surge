# 升级到 R13.19

1. 导入新的 Surge.conf。
2. 沿用当前已经正常工作的订阅地址，替换唯一的完整占位 URL。地址在隐藏的 Subscription 组中；NodePool 仍是可见的手动节点池。
3. 保存、启用新配置。Proxy 默认 Auto，NodePool 默认 Auto。

不需要新增分离文件、脚本或 Sub-Store 模块。旧私人副本可能保存旧地址，不应覆盖刚修好的订阅。

主配置外部资源恢复为 29 份规则和 1 个订阅；规则 URL 应以 raw.githubusercontent.com 开头并含固定提交 SHA。仅更新旧配置的“外部资源”不会把旧主配置升级为本版。

AdBlock、Security、Domestic 和 UDP 现在连接到对应规则，若设备保留过旧开关选择，应按当前需要查看这些选择。Fail-Closed 的单项失败属于空池保护的预期表现。
