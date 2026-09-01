# R13.13 到 R13.14 回退修复说明

R13.14 撤回 R13.10 至 R13.13 的诊断和失败占位架构，恢复一条订阅地址直接进入主策略组的用法。

## 升级

1. 导入完整的 R13.14 `Surge.conf`。
2. 搜索 `REPLACE_WITH_SURGE_SUBSCRIPTION_URL`，替换为现有 Surge 格式订阅 URL。
3. 保存并重新加载配置。
4. 打开策略页，确认只显示主要入口 `Proxy`，并能看到真实节点名称和延迟。
5. 删除旧配置副本即可；不需要重建 Sub-Store 订阅，也不需要 `Private-Proxies.conf` 或转换脚本。

| 项目 | R13.13 | R13.14 |
|---|---|---|
| 节点来源 | `NodePool.policy-path` | `Proxy.policy-path` |
| 可见控制 | Proxy、Auto、NodePool、五地区 | 仅 Proxy |
| 空组 | 显式 REJECT，显示红色失败 | 删除 |
| 服务组 | 可见并递归地区组 | 隐藏并跟随 Proxy |
| DNS 出口 | 加密 DNS 默认直连 | 加密 DNS 与已知 DoH/DoT 跟随 Proxy |
| 安装文件 | 一个配置 | 一个配置 |

全局网络诊断不一定枚举 `policy-path` 外置节点。请以 `Proxy` 中真实节点延迟、实际网页和真实 UDP 流量验收；配置不会使用回环或假代理伪造结果。
