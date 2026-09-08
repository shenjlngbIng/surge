# 升级到 R13.23

本版改善手选节点失效时的推送和规则下载路径。订阅仍只填“桔子”这一处，Sub-Store 模块保持原样。

## 操作步骤

1. 保留旧的可用配置、有效订阅地址和外部资源缓存。
2. 通过 [主配置链接](https://raw.githubusercontent.com/shenjlngbIng/surge/main/Surge.conf) 导入 R13.23。
3. 搜索 `桔子 =`，将 `policy-path=` 后的完整占位 URL 替换为自己的 Surge 格式订阅地址。
4. 确认 NodePool 有真实节点，Auto 至少有一个健康节点，并取消 Auto 的临时手动覆盖。启用新配置及规则模式，更新失败的外部资源，确认 APNs.list 在内的 29 份规则均已就绪。
5. 开关一次飞行模式，恢复网络并确认 Surge 已运行，再锁屏测试 Telegram 新消息。Wi-Fi 与蜂窝网络分别验证。

只更新外部资源不会修改旧主配置。顶部版本应为 R13.23；无需删除配置、重装软件、清空缓存或更改 Sub-Store 名称。

| 项目 | R13.22 | R13.23 |
| --- | --- | --- |
| 推送回退顺序 | Proxy、DIRECT | Proxy、Auto、DIRECT |
| GitHub raw 出口 | Proxy | Auto |
| 订阅入口 | 桔子，一处 | 不变 |
| 策略组和分流指令 | 40 组、142 条 | 不变 |
| 29 份外置列表及地址 | 固定提交 | 不变 |

“包含所有网络请求”警告会保留。Surge 的 APNs 接管需要同时开启 include-all-networks 和 include-apns，不能通过关掉前者来解决推送。[官方参数](https://manual.nssurge.com/profile/general.html)

如果仍有加载失败，查看外部资源页的最新状态，保留失败条目的详细错误及更新时刻。如果只有推送异常，查看 APNs 请求实际使用的节点或 DIRECT，再核对通知权限和专注模式。提供日志时隐藏私人订阅、节点地址和凭据。
