# Security Policy

R13.13 的公开配置不包含真实订阅、节点、令牌或私人日志。用户只在本机把 `NodePool.policy-path` 占位 URL 替换为自己的 Surge 格式订阅地址。

## 必须保持的边界

- `[Proxy]` 保持为空，不加入静态节点、本机回环或伪诊断代理。
- `NodePool` 是唯一包含 `policy-path` 的策略组，第一项为内建 `REJECT`，订阅更新间隔为 3,600 秒。
- `Auto`、五个地区组以及 ChatGPT、Claude、Gemini、TikTok 都使用带显式 `REJECT` 的 `url-test`，禁止加入 `DIRECT`。
- `Proxy` 默认选择 `Auto`，同时保留手动 `NodePool`、五个地区入口和 `REJECT`。
- `udp-policy-not-supported-behaviour=REJECT`，不允许用 `DIRECT` 掩盖节点不支持 UDP 的问题。
- 禁止恢复 `Diagnostics = socks5, 127.0.0.1,...`。本机回环不能证明真实节点 TCP 或 UDP 可用。
- 29 个仓库规则资源固定到完整提交 `2b8fa93901061cf0482b079203630bcd11bfe0b1`；唯一动态资源为审阅过的 `domestic.conf`。

## 私人数据

不要把以下内容提交到仓库、Issue、Release 或公开截图：

- 真实订阅 URL 与访问令牌；
- 节点服务器、端口、用户名、密码与证书；
- Sub-Store 私人下载标识；
- 设备日志、节点名称、个人域名和可识别网络信息。

凭据泄露后应立即在服务商或 Sub-Store 中撤销并重新生成。公开模板始终保留 `example.invalid` 占位地址。

## 能证明与不能证明的内容

仓库审计可以验证配置结构、规则顺序、固定资源、空源失败关闭、DNS/UDP 边界和发布包完整性。它不能证明私人节点在线、服务端支持 UDP、远端递归 DNS 不泄漏、运营商没有劫持或所有第三方服务永远稳定。

使用 `policy-path` 时，Surge iOS 的全局代理和 UDP 诊断可能无法枚举外置节点。该空白是诊断显示边界，不应被伪代理填充，也不代表真实节点一定失败。升级后应在 Wi-Fi 和蜂窝网络分别验证真实节点、ChatGPT、国内 BiliBili、Telegram、APNs、IPv4/IPv6 出口和 DNS。
