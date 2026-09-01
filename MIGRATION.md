# R13.15 到 R13.16 哨兵恢复说明

R13.16 在 R13.15 完整策略结构上恢复旧版 `Fail-Closed` 哨兵。哨兵只进入 `Auto` 的 Smart 候选，不进入 NodePool、Proxy 或可见地区组，因此正常订阅不会重新出现成排红色失败卡片。

## 升级

1. 导入完整的 R13.16 `Surge.conf`。
2. 搜索 `REPLACE_WITH_SURGE_SUBSCRIPTION_URL`，替换为现有 Surge 格式订阅 URL。
3. 保存并重新加载配置。
4. 打开策略页，确认 `NodePool` 能看到真实节点，`Auto` 能自动选择，地区与服务策略均已恢复。
5. 删除旧配置副本即可；不需要重建 Sub-Store 订阅，也不需要 `Private-Proxies.conf` 或转换脚本。

| 项目 | R13.15 | R13.16 |
|---|---|---|
| 节点来源 | `NodePool.policy-path` | 保持不变 |
| 策略分组 | 完整 | 保持不变 |
| Fail-Closed | 缺失 | 恢复为唯一静态哨兵，仅供 Auto 失败兜底 |
| 地区空组 | 回退 Auto | 保持不变 |
| DNS 出口 | 加密 DNS 跟随 Proxy | 保持不变 |
| 安装文件 | 一个配置 | 一个配置 |

全局网络诊断不一定枚举 `policy-path` 外置节点。请以 `Proxy` 中真实节点延迟、实际网页和真实 UDP 流量验收；配置不会使用回环或假代理伪造结果。
