# R13.4 到 R13.5 Strict Fail-Closed 迁移说明

R13.5 是行为边界升级。不要只替换单个 BiliBili 文件或沿用旧策略选择；应整体导入新配置、规则锁和审计工具。

## 关键差异

| 项目 | R13.4 | R13.5 |
| --- | --- | --- |
| 默认代理 | `AllServer` Smart | 手动 `NodePool` |
| 地区入口 | Smart | 手动 `select`，首项 `Fail-Closed` |
| 失败关闭 | Smart 内含伪失败节点，仍可能 `DIRECT/SUBSTITUTE` | 内建 `reject` 别名＋无自动组 |
| 隐藏状态组 | AdBlock、Security、UDP、Domestic | 删除，规则固定策略 |
| 动态运行资源 | 钓鱼、广告、国内，共 3 份 | 仅动态国内 1 份 |
| BiliBili 国内集合 | 12 后缀 | 16 后缀＋两条前置功能护栏 |
| 固定资源匹配 | 普通匹配 | 除 Ads 外启用 `extended-matching` |
| 运行资源 | 29 固定＋3 动态 | 29 固定＋1 动态 |
| 策略组/规则 | 34 / 137 | 29 / 142 |
| 完整包 | `Surge-R13.4-Complete-No-Embedded-20260828.zip` | `Surge-R13.5-Complete-No-Embedded-20260829.zip` |

## 为什么删除 Smart

Surge 官方说明，自动组没有可用成员时会使用 `DIRECT`，日志显示 `SUBSTITUTE`。Smart 还会忽略内建策略和嵌套组。R13.4 把 `Fail-Closed` 写进 Smart 并不能证明无直连回退。

R13.5 将 `Fail-Closed` 定义为内建 `reject` 的别名，所有节点和地区入口使用手动 `select`。代价是不能无人值守自动择优；收益是无节点时的静态行为可证明。

## 升级步骤

1. 备份私人订阅地址和你当前选择的节点名称，不要把备份提交到仓库。
2. 完整导入 R13.5，而不是把新规则复制到旧 R13.4 配置。
3. 只替换 `NodePool.policy-path` 的占位 URL。
4. 在 Surge 中重新下载并加载配置，清理旧规则缓存。
5. 打开 `NodePool`，选择真实节点。若仍选择 `Fail-Closed`，代理请求被拒绝是预期结果。
6. 为需要的地区组选择节点，尤其是 ChatGPT/Claude/Gemini/TikTok 使用的日本、新加坡、台湾、美国。
7. 按 README 的 Wi-Fi 与蜂窝真机清单验收。

## 旧策略状态

R13.5 删除 `AllServer`、`AdBlock`、`Security`、`UDP` 和 `Domestic`。Surge 即使保留旧组名选择，也找不到这些组，因此不会继续沿用旧的隐藏 `DIRECT`、`Proxy` 或广告调试状态。

不要自行恢复同名组。需要排错时查看最近请求中的首条命中和最终策略，修正规则或节点，不要通过可持久化的隐藏开关绕开边界。

## BiliBili

国内版现在固定包含：

- 原 12 个 API、页面、图片和视频后缀；
- 新增 `biligame.net`、`bilivideo.cn`、`bilicomic.com`、`bilivideo.net`；
- Ads 前置 `httpdns.bilivideo.com`；
- Ads 前置 `line3-h5-mobile-api.biligame.com`。

国际版专用规则继续保持删除。七条历史域名只走通用 `Proxy` 兼容护栏。不要恢复 `BiliBiliIntl.list` 或把这些域名并入国内 `DIRECT`。

## 广告与安全

R13.5 不再加载 `reject.conf` 和 `reject_phishing.conf`。这是移动端性能与误杀边界调整，不代表关闭所有防护：

- 152 条固定审阅 Ads 继续 `REJECT`；
- 1,438 条固定 Pegasus 历史 IOC 继续 `REJECT`；
- 九条确认重叠的功能依赖在 Ads 前进入正确策略；
- iOS 自身更新、Lockdown Mode 和专门内容拦截工具仍应按需要使用。

## 节点与服务地区

- ChatGPT、Claude、Gemini、TikTok 不再提供通用 Proxy 或香港作为组内候选。
- Bahamut 只提供台湾、香港。
- 其他国际服务默认 `Proxy`，仍可手动切换地区。
- 地区组不会自动选择最快节点。节点不可用时应手动更换，不要改回 Smart 以换取表面可用性。

## 回退

确需回退时，恢复完整 R13.4 包和当时的私人订阅地址。不要混用 R13.5 的 `Surge.conf`、`Rules/r10.lock.json`、清单、哈希或审计脚本。R13.4 的自动组直连替代、隐藏组持久状态和动态大表风险会同时恢复。
