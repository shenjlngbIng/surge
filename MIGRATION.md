# R13.14 到 R13.15 完整策略恢复说明

R13.15 修正 R13.14 过度简化：恢复 NodePool、Auto、五个地区组和服务策略，同时保留一条 Sub-Store 订阅地址的安装方式。

## 升级

1. 导入完整的 R13.15 `Surge.conf`。
2. 搜索 `REPLACE_WITH_SURGE_SUBSCRIPTION_URL`，替换为现有 Surge 格式订阅 URL。
3. 保存并重新加载配置。
4. 打开策略页，确认 `NodePool` 能看到真实节点，`Auto` 能自动选择，地区与服务策略均已恢复。
5. 删除旧配置副本即可；不需要重建 Sub-Store 订阅，也不需要 `Private-Proxies.conf` 或转换脚本。

| 项目 | R13.14 | R13.15 |
|---|---|---|
| 节点来源 | `Proxy.policy-path` | `NodePool.policy-path` |
| 可见控制 | 仅 Proxy | Proxy、NodePool、Auto、五地区与服务组 |
| 空组 | 直接删除 | 隐藏严格筛选源，地区组空时回退 Auto |
| 服务组 | 隐藏并跟随 Proxy | 可见并可选择 Proxy/地区/Auto |
| DNS 出口 | 加密 DNS 跟随 Proxy | 保持不变 |
| 安装文件 | 一个配置 | 一个配置 |

全局网络诊断不一定枚举 `policy-path` 外置节点。请以 `Proxy` 中真实节点延迟、实际网页和真实 UDP 流量验收；配置不会使用回环或假代理伪造结果。
