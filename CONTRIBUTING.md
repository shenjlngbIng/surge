# 贡献与维护

R13.4 把主配置、规则快照、来源锁、运行锁、审计器、故障注入、发布清单和安装工作流视为一个整体。任何规则或配置变化都要同步更新相关元数据，并让完整测试通过。

## 必须保持的边界

- 公开 `Surge.conf` 只能保留 `https://example.invalid/REPLACE_WITH_SUB_STORE_URL`，不能提交真实订阅或令牌。
- 原 30 个远程资源继续固定到完整提交 `d1d714d575d5494ef1a7613238f4f301e1b293df`；新增资源只允许三条已审阅的 `ruleset.skk.moe` 精确 URL。
- 运行时资源固定为 33 个，本地 `.list` 文件固定为 30 个，主配置不得内嵌规则内容。
- Pegasus 必须通过固定 `DOMAIN-SET` 指向 `Security`；动态钓鱼必须位于 Pegasus 之前。
- 固定 Ads 与动态基础广告分别通过 `RULE-SET` 和 `DOMAIN-SET` 指向 `AdBlock`，固定 Ads 必须在动态基础广告之前。
- 动态国内 `RULE-SET`、固定 China `DOMAIN-SET` 和 `GEOIP,CN` 必须指向 `Domestic`，并保持审计定义的首条命中顺序。
- `NodePool` 保持可见的手动 `select`，首个成员为 `Fail-Closed`。`Proxy` 默认使用 `AllServer`；`UDP` 默认使用 `Proxy`。
- `AllServer` 和五个地区组保持 `smart`，只导入 `NodePool`，不能退回 `url-test` 或直接导入订阅。
- `ApplePush`、`AdBlock`、`Security`、`UDP` 和 `Domestic` 保持隐藏；后四组的定义、成员与规则引用不得删除；`wifi-assist` 保持关闭。
- Surge 自身 DNS 使用两个 AliDNS 地址、两个 DoH 端点和固定引导地址，证书校验保持开启。
- STUN 必须位于公网 DNS 端口和公网域名、IP 规则之前。
- 16 个大陆应用 DNS 主机必须完整、连续地位于 STUN 后和通用端口拒绝前，策略为 `Domestic`；13 个境外应用 DNS 主机位于端口拒绝后，策略为 `Proxy`。
- 53、853 和 8853 端口必须在局域网规则之后拒绝。
- `GEOIP,CN,Domestic,no-resolve` 位于 Global 后且不得移除 `no-resolve`；IPv4 与 IPv6 公网字面量代理规则紧贴唯一末尾 `FINAL`。
- 发布目录只允许 `release_inventory.py` 中的 66 个文件。

## 修改规则文件

19 份固定服务规则由 `Rules/upstreams.lock.json` 记录来源提交、Git Blob、本地增删边界、活动条目数和 SHA-256。Pegasus 由 `Rules/resources.lock.json` 管理。其余 10 份仓库维护列表由 `Rules/maintained_sources.lock.json` 披露来源和许可状态。

更改内容前先确认来源固定到完整提交，并复核许可证。不要用自动更新覆盖审阅过的本地边界。每次变化都要记录活动条目数、内容哈希和差异决定。

更新固定第三方资源时可使用下面的维护命令。`--download --check` 只比较，不写文件。

```bash
python3 tools/update_external_resources.py --download --check
python3 tools/update_service_rules.py --download --check
```

三份动态运行资源不复制到仓库。更改 URL、类型、策略或顺序前必须重新审阅许可、规模和误判风险，并同步修改配置、`convert_to_remote_rules.py`、运行锁生成器、审计器和文档。使用下面的命令检查当前在线内容，不要因为正常哈希变化自动提交快照。

```bash
python3 tools/audit_rules.py --check-dynamic
```

## 修改主配置

先在配置中完成改动，再同步修改 `convert_to_remote_rules.py`、`generate_runtime_lock.py`、`audit_config.py` 和 `test_audit_config.py`。新增策略组要检查引用和循环。新增规则要说明首条命中位置，并为容易退化的条件加入故障注入。

不要为了让审计通过而放宽断言。需要改变边界时，应同时更新迁移说明、审计报告和变更记录，让使用者知道新的行为与代价。

## 完整验证

```bash
export PYTHONDONTWRITEBYTECODE=1
python3 -m compileall -q tools
python3 tools/convert_to_remote_rules.py
python3 tools/generate_runtime_lock.py
python3 tools/update_external_resources.py --verify-lock
python3 tools/update_service_rules.py --verify-lock
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/audit_rules.py --check-dynamic
python3 tools/audit_precise_domains.py
python3 tools/test_audit_config.py
python3 tools/test_release_inventory.py
python3 tools/test_stage_surge_zip.py
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
sha256sum -c SHA256SUMS.txt
cmp --silent SHA256SUMS.txt SHA256SUMS_fixed.txt
python3 tools/package_release.py --output ../Surge-R13.4-Complete-No-Embedded-20260828.zip
```

生成清单和哈希后再次运行全部审计。压缩包应包含 66 个文件，并在相同输入下产生相同 SHA-256。

## 提交前检查

- `git diff --check` 没有空白错误。
- 所有文本为 UTF-8、LF、无 BOM，并保留结尾换行。
- 没有 `.env`、日志、缓存、临时文件、额外压缩包或符号链接。
- 文档里的版本、日期、数量、命令和包名与脚本一致。
- 私有订阅、令牌、设备日志和个人域名没有进入差异。
- 真机行为变化已经完成 Wi-Fi、蜂窝、APNs、DNS、双栈、UDP、Smart 和 Domestic 验收。
