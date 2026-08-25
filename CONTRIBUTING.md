# 贡献指南

## 基本要求

- 不提交真实订阅、节点、Token、密码或证书。
- 不引入未经固定版本或本仓库审计的远程脚本、`RULE-SET` 或 `DOMAIN-SET`。
- 运行时规则地址必须固定到当前发布标签 `r12.17-20260825`，不得恢复为 `@main`。
- `Surge.conf` 中的全部静态运行资源必须来自本仓库固定标签；第三方 URL 只能作为维护输入写入锁文件。
- Pegasus 必须由 `Rules/Pegasus.list` 提供，并同时通过 `Rules/resources.lock.json` 的提交、Blob、上游哈希、本地哈希和条目数量校验。
- 不为 Telegram 增加 `DIRECT` 路径。
- 不把全部 Apple 流量改为代理；APNs 只进入 `ApplePush` Fallback。
- 保留 `include-all-networks=true`、`include-apns=true` 和 `ApplePush = fallback, Proxy, DIRECT, interval=60, evaluate-before-use=true`。
- `NodePool` 必须保持隐藏的 `select` 订阅容器，只允许它持有 `policy-path`，不能由规则或可见策略组直接选择。
- `AllServer` 和五个地区组必须保持 `smart, Fail-Closed`，且只能通过 `include-other-group=NodePool` 读取订阅节点。
- 除 `ApplePush` 外，不增加 `url-test`、`fallback` 或 `load-balance` 自动组，避免网络切换恢复全订阅集中测速。
- 不删除 Smart 组中的显式 `Fail-Closed`。Smart 空组可能使用替代策略，显式哨兵是公开配置不静默直连的必要边界。
- 不重新启用 `include-cellular-services`，除非同时给出运营商兼容性验证与回滚方案。
- DNS 必须保持加密出站，禁止恢复 `system` 上游或明文直连绕过。
- `encrypted-dns-follow-outbound-mode=false` 时，不增加不会参与内部解析链的 DOH、DOH3、DOQ 规则组。
- `dns.alidns.com` 的 IPv4 与 IPv6 引导地址必须保留在同一个 Host 映射中。
- 保留 `ls.apple.com` 和 `100.64.0.0/10` 的本地直连边界。
- 不把 `Final` 改为默认直连。
- 不删除规则快照、许可证或审计工具。
- 精确域名集不得加入公共后缀、域名关键词或共享云/CDN；国内外条目不得重叠。
- `BiliBiliIntl.list` 必须先于 `BiliBili.list`。国际版进入现有 `Streaming`，国内 API 与视频 CDN 进入 `DIRECT`，不得新增 Bilibili 专用策略组。
- `PROTOCOL,STUN,UDP` 必须先于 `GEOIP,CN,DIRECT,no-resolve`；UDP 组默认选择 Proxy，DIRECT 仅用于用户明确排错。
- `DOMAIN-SUFFIX,viu.now.com,Streaming` 必须位于 HBO.list 前，避免 `now.com` 父级后缀抢先命中。
- `Game.list` 必须先于 `OneDrive.list` 和 `Microsoft.list`，避免 Xbox、Minecraft、Bethesda 等条目失去作用。
- Netflix 不得重新导入宽泛云厂商 CIDR；保留审核后的 `IP-ASN,2906,no-resolve`。
- 服务规则的共享云、遥测和国内例外必须通过 `Rules/upstreams.lock.json` 的排除项维护，不得只手改生成文件。
- 服务规则的每条本地补充必须进入对应 `add` 数组并披露来源状态；更新器不得读取旧输出作为生成输入。
- 10 个仓库维护列表的内容、条目数、哈希与许可状态必须同步记录在 `Rules/maintained_sources.lock.json`。
- 发布清单必须使用 `tools/release_inventory.py`；不得通过扩大排除后缀来静默跳过 `.env`、日志、未知目录或符号链接。

## 修改流程

1. 修改配置或规则源。
2. 运行 `python3 tools/convert_to_remote_rules.py`，确认主配置只引用外部规则集。
3. 运行 `python3 tools/embed_runtime_rules.py` 刷新元数据；该历史文件名不会嵌入规则内容。
4. 运行 `python3 tools/update_external_resources.py --verify-lock` 检查独立固定资源。
5. 运行 `python3 tools/audit_precise_domains.py` 检查格式、冗余和国内外交叉冲突。
6. 执行全部审计、打包和测试。
7. 重新生成 `RELEASE_MANIFEST.txt`、`SHA256SUMS.txt` 和 `SHA256SUMS_fixed.txt`。
8. 检查差异和敏感信息。
9. 执行 Wi-Fi → 蜂窝数据 → Wi-Fi 切换回归，确认没有全订阅请求风暴。
10. 在提交说明中描述行为变化及验证结果。

## 必须通过的命令

```bash
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/audit_precise_domains.py
python3 tools/test_audit_config.py
python3 tools/test_release_inventory.py
python3 tools/test_stage_surge_zip.py
python3 tools/update_external_resources.py --verify-lock
python3 tools/update_service_rules.py --verify-lock
python3 tools/package_release.py --output ../Surge-R12.17-self-maintained-20260825.zip
sha256sum -c SHA256SUMS.txt
cmp --silent SHA256SUMS.txt SHA256SUMS_fixed.txt
```

当前基线应报告 98 条活动规则、30 个仓库运行资源、33 个策略组、74 项故障注入测试、24 个 ZIP 安全回归和 10 个严格发布清单回归。数量发生变化时，必须在变更说明中解释原因并同步更新审计器，不能只修改预期数字让测试通过。
