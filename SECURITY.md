# 安全边界

R13.15 的公开配置不包含真实订阅、节点、令牌或私人日志。用户只在本机把 `NodePool.policy-path` 的占位 URL 替换为自己的 Surge 格式 Sub-Store 订阅地址。

## 节点与策略

- `Proxy` 是唯一可见策略组，也是唯一含 `policy-path` 的组。
- 不允许在公开 `[Proxy]` 中嵌入节点、凭据、本机回环诊断代理或自定义拒绝代理。
- 不允许恢复 `NodePool`、`Auto`、地区空组或显式 `REJECT` 占位。
- 服务组隐藏并只跟随 `Proxy`；Apple 保留历史 `DIRECT` 默认。
- UDP 不支持时使用 `REJECT`，不得回退 `DIRECT` 伪造可用。

## DNS

- Cloudflare 与 Quad9 DoH 开启证书校验并跟随规则和出口模式。
- Surge 自身的加密 DNS 协议及已知应用内 DoH/DoT 域名固定进入 `Proxy`。
- 53 端口 DNS 被接管，53、853、8853 未审阅出口被拒绝。
- Cloudflare 与 Quad9 的固定引导地址来自各自官方文档。

## 供应链

29 个仓库规则资源固定到完整提交 `2b8fa93901061cf0482b079203630bcd11bfe0b1`。唯一动态资源是经过审阅的国内补充表。移动端不加载大型动态广告或钓鱼拒绝表。

安全问题请提交不含订阅 URL、令牌、节点凭据和私人日志的最小复现。
