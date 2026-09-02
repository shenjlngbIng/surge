# R13.17 真机故障恢复审计报告

审计日期：2026-09-02

## 结论

R13.16 不能继续使用。真机截图同时出现 NodePool、Auto、地区组失败，以及所有 jsDelivr 资源超时。根因是不可达的 `Fail-Closed = http, 127.0.0.1, 1` 被放入 Smart，而加密 DNS 又依赖这个 Smart 组，形成启动死锁。

R13.17 删除回环假代理。Auto 只递归导入 NodePool 的真实代理；没有可用节点时没有 DIRECT 替代项，天然失败关闭。

## 当前结构

```ini
[Proxy]
# empty

[Proxy Group]
Proxy = select, Auto, NodePool, HongKong, TaiWan, Japan, Singapore, America, ...
NodePool = select, policy-path=<one Surge URL>, ...
Auto = smart, evaluate-before-use=true, include-other-group=NodePool, ...
```

- 39 个策略组，NodePool、Auto、五个地区入口和 20 个服务策略完整保留。
- 5 个严格地区源隐藏；对应可见地区组在无匹配节点时回退 Auto。
- `[Proxy]` 中没有回环代理、拒绝别名、静态节点或私人凭据。
- jsDelivr 更新流量在规则表前段明确进入 Proxy。

## DNS

- AliDNS DoH 与 DNSPod DoH，证书校验开启。
- Surge 自身加密 DNS 直连引导，避免 NodePool 尚未建立时循环依赖。
- 应用内 DoH/DoT、STUN、公开 DNS 端口的代理与拒绝边界保持。
- 53 端口继续由 `hijack-dns=*:53` 接管。

## 供应链

- 29 个运行资源全部固定到提交 `2b8fa93901061cf0482b079203630bcd11bfe0b1`。
- 删除动态 `ruleset.skk.moe` 国内补充，避免独立 HTTP 500/漂移路径。
- 私人 Sub-Store 地址仍只存在于用户本地 Ready 配置，不进入公开仓库。

全局代理/UDP 诊断是否枚举 `policy-path` 节点仍属于 Surge 的显示边界，不使用假代理伪造结果。
