# R13.12 到 R13.13 单订阅迁移说明

R13.13 撤回 R13.12 的双配置安装流程。升级后不再需要 `Private-Proxies.conf`、Sub-Store `Response Transformer` 或 `surge-profile=1` 参数。

## 迁移步骤

1. 导入完整的 R13.13 `Surge.conf`。
2. 进入文本模式，搜索 `REPLACE_WITH_SURGE_SUBSCRIPTION_URL`。
3. 将完整占位 URL 替换为自己的 Surge 格式订阅地址。Sub-Store 地址建议附加 `?target=Surge`；若原地址已有查询参数则附加 `&target=Surge`。
4. 保存并重新加载配置。
5. 打开 `NodePool`，确认第一项是 `REJECT`，后面能看到真实节点；`Proxy` 选择 `Auto`。
6. 确认 R13.13 正常工作后，可以从 Surge 配置列表删除旧的 `Private-Proxies.conf`。删除旧文件不会影响 R13.13。

## 行为变化

| 项目 | R13.12 | R13.13 |
| --- | --- | --- |
| 用户操作 | 先装私人配置，再装主配置 | 只改一个订阅 URL |
| 节点来源 | `[Proxy]` 关联文件 | `NodePool.policy-path` |
| Sub-Store 自定义脚本 | 必需 | 不需要 |
| 导入顺序 | 严格要求 | 无额外顺序 |
| 全局代理/UDP 诊断 | 可枚举 `[Proxy]` 节点 | 外置节点可能不显示 |
| 日常代理、分流和自动测速 | 支持 | 支持 |
| 空源失败关闭 | `REJECT` | `REJECT` |

全局诊断空白不作为真实节点 UDP 成功或失败的结论。请在 `NodePool` 中测试具体节点，或使用真实 UDP 流量验收。不要恢复 R13.10 的本机 SOCKS5 回环诊断桥。
