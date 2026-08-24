# R12.14 迁移说明

R12.14 是一次稳定性与推送保全修正。升级不会写入或替换个人订阅，公开包中的 `policy-path` 仍是不可路由占位地址。

## 升级方式

1. 备份当前私有 `Surge.conf`。
2. 使用 R12.14 的完整文件替换公开仓库内容。
3. 复制新版 `Surge.conf` 为私有副本。
4. 只把旧私有副本中 `AllServer` 的完整 `policy-path` 移入新副本，不复制旧的策略组和网络选项。
5. 导入新副本，先更新 `AllServer`，确认真实节点出现。
6. 检查 `ApplePush` 的当前选择与 Telegram、APNs 规则集更新状态。

不要把真实订阅 URL、Token、节点密码或证书提交到公开仓库。

## 行为变化

| 项目 | R12.13 | R12.14 |
| --- | --- | --- |
| AliDNS 引导 | 同一主机写三行 | 合并为一行三地址，避免首条匹配遮蔽 |
| AllServer 探测 | `interval=60, timeout=300` | `interval=600, timeout=5` |
| Fail-Closed | 每次探测可能产生错误提醒 | 保持失败关闭并抑制刻意连接失败提醒 |
| ApplePush 探测 | `timeout=300` | `timeout=5`，仍为 `Proxy, DIRECT` |
| Apple 系统配置查询 | 可能进入后续代理规则 | `ls.apple.com` 在远程规则前直连 |
| CGNAT | 未显式列入本地边界 | `100.64.0.0/10` 加入跳过代理和直连规则 |
| 蜂窝系统服务 | 额外接管 | 不接管 IMS、VoLTE、MMS 等专用流量 |
| 加密 DNS 协议组 | 存在不参与内部 DNS 链路的旧规则 | 删除失效策略组和 DOH/DOH3/DOQ 规则 |
| macOS hosts 选项 | 出现在 iOS 配置 | 删除 |

## Telegram 与推送

升级不会把 Telegram 改为直连。

- Telegram 消息、媒体和前台连接仍由 `Rules/Telegram.list` 进入 `Telegram` 代理策略组。
- iOS 后台通知仍由 `Rules/APNs.list` 进入 `ApplePush`。
- `ApplePush` 仍按 `Proxy`、`DIRECT` 的顺序回落。代理可用时优先代理，代理失败时 APNs 可直连保留通知能力。
- `include-all-networks=true` 和 `include-apns=true` 均保留。
- `include-cellular-services=false` 仅退出 IMS、VoLTE、Wi-Fi Calling、MMS、可视语音邮件等运营商专用流量，不影响普通 4G/5G 数据或 APNs。

## 升级后检查

- Surge 不再反复弹出 Fail-Closed POSIX 61 错误。
- `AllServer` 中存在真实节点，而不只有 Fail-Closed。
- Telegram 前台消息和媒体正常。
- 锁屏后等待数分钟，Telegram 通知仍能唤醒设备。
- 在 Surge 最近请求中，`configuration.ls.apple.com` 命中 DIRECT。
- 电话、短信、VoLTE、Wi-Fi Calling、MMS 和可视语音邮件保持正常。

若通知仍延迟，先确认 iOS 通知权限、低电量模式、Telegram 后台设置和 Apple APNs 网络可达性，再检查代理节点。不要通过把全部 Apple 流量强制代理来掩盖节点故障。
