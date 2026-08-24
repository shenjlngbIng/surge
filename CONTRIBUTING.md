# 贡献指南

## 基本要求

- 不提交真实订阅、节点、Token、密码或证书。
- 不引入未经固定版本或本仓库审计的远程脚本、`RULE-SET` 或 `DOMAIN-SET`。
- 不为 Telegram 增加 `DIRECT` 路径。
- 不把全部 Apple 流量改为代理；APNs 只进入 `ApplePush` Fallback。
- 保留 `include-all-networks=true`、`include-apns=true` 和 `ApplePush = fallback, Proxy, DIRECT`。
- 不重新启用 `include-cellular-services`，除非同时给出运营商兼容性验证与回滚方案。
- DNS 必须保持加密出站，禁止恢复 `system` 上游或明文直连绕过。
- `encrypted-dns-follow-outbound-mode=false` 时，不增加不会参与内部解析链的 DOH、DOH3、DOQ 规则组。
- `dns.alidns.com` 的 IPv4 与 IPv6 引导地址必须保留在同一个 Host 映射中。
- 保留 `ls.apple.com` 和 `100.64.0.0/10` 的本地直连边界。
- 不把 `Final` 改为默认直连。
- 不删除规则快照、许可证或审计工具。
- 精确域名集不得加入公共后缀、域名关键词或共享云/CDN；国内外条目不得重叠。

## 修改流程

1. 修改配置或规则源。
2. 运行 `python3 tools/convert_to_remote_rules.py`，确认主配置只引用外部规则集。
3. 运行 `python3 tools/embed_runtime_rules.py` 刷新元数据；该历史文件名不会嵌入规则内容。
4. 运行 `python3 tools/audit_precise_domains.py` 检查格式、冗余和国内外交叉冲突。
5. 执行全部审计、打包和测试。
6. 重新生成 `RELEASE_MANIFEST.txt`、`SHA256SUMS.txt` 和 `SHA256SUMS_fixed.txt`。
7. 检查差异和敏感信息。
8. 在提交说明中描述行为变化及验证结果。

## 必须通过的命令

```bash
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/audit_precise_domains.py
python3 tools/test_audit_config.py
python3 tools/test_stage_surge_zip.py
python3 tools/package_release.py --output ../Surge-R12.14-release.zip
sha256sum -c SHA256SUMS.txt
```
