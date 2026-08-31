# 贡献与维护

R13.9 把主配置、固定快照、来源锁、运行锁、审计器、故障注入、发布清单和安装工作流视为一个整体。任何行为变化都要同步更新这些边界，并完成本页的全套验证。

## 必须保持的边界

- 公开 `Surge.conf` 只能保留 `https://example.invalid/REPLACE_WITH_SUB_STORE_URL`，不能提交真实订阅或令牌。
- 29 个远程资源固定到完整提交 `2b8fa93901061cf0482b079203630bcd11bfe0b1`；唯一动态资源是精确 URL `https://ruleset.skk.moe/List/non_ip/domestic.conf`。
- 主配置不得加载动态 `reject.conf` 或 `reject_phishing.conf`，不得使用分支、标签、raw `main` 或其他可变 URL。
- 运行时资源固定为 29 个不可变资源加 1 个动态国内补充；本地 `.list` 文件固定为 29 个，主配置不得嵌入规则快照。
- `Pegasus.list` 与 `Ads.list` 固定指向内建 `REJECT`；STUN 固定指向 `Proxy`；WeChat、Direct、BiliBili、China、动态国内补充与 `GEOIP,CN` 固定指向内建 `DIRECT`。
- 主配置不得定义 `[Proxy]` 静态拒绝别名；网络诊断必须能够选择真实订阅代理。
- `NodePool` 必须保持手动 `select`，不得含显式成员，私人订阅只允许从这一组的 `policy-path` 导入。
- `Smart` 必须为可见 `smart`，只通过 `include-other-group=NodePool` 导入真实代理。
- 五个地区组必须为可见 Smart，只导入名称匹配的 `NodePool` 节点。
- 总入口 `Smart` 与五个地区组必须保持 `evaluate-before-use=true`、`hidden=0`、`include-all-proxies=0` 和唯一 `NodePool` 来源；禁止添加对 Smart 无效的 `interval`、`tolerance` 或显式内建成员。
- `Proxy` 默认 `Smart`，第二项必须为手动 `NodePool`，末项保留内建 `REJECT`。ChatGPT、Claude、Gemini 与 TikTok 必须保持可见 Smart，只递归导入日本、新加坡、台湾、美国；Bahamut 保持台湾、香港的手动顺序。
- 禁止恢复 `url-test`、load-balance 或第二套自动总入口。文档必须说明自动空组可能发生 `DIRECT/SUBSTITUTE`，不得把 Smart 混合模式描述为全局严格失败关闭。
- `Auto`、`AllServer`、`AdBlock`、`Security`、`UDP` 和 `Domestic` 必须保持删除。
- 国内 BiliBili 固定规则必须使用 `DIRECT`；退役国际版不得恢复专用策略组或规则文件，七条历史兼容域名只走通用 `Proxy`。
- 九条已审阅的功能域名护栏必须位于 Ads 前，防止 BiliBili、Spotify、Google 更新与 OpenAI 遥测依赖被固定广告表误杀。
- 除 Ads 外的固定运行资源必须启用 `extended-matching`；动态国内补充也必须启用。
- Surge DNS 保留双 DoH、证书校验、AliDNS 双 IPv4/双 IPv6 引导和 DNSPod 动态主机名引导。禁止重新钉住 `doh.pub` 旧 IP。STUN 位于公网 DNS 拒绝之前；已审阅的大陆与境外应用 DNS 顺序不得颠倒。
- 53、853、8853 在局域网规则之后拒绝；`GEOIP,CN,DIRECT,no-resolve` 保持 `no-resolve`；IPv4 与 IPv6 公网字面量代理规则紧贴唯一末尾 `FINAL`。
- 发布目录只允许 `release_inventory.py` 声明的文件。

## 修改规则文件

18 份服务规则由 `Rules/upstreams.lock.json` 记录来源提交、Git Blob、本地增删边界、活动条目数和 SHA-256。Pegasus 由 `Rules/resources.lock.json` 管理，其余仓库维护列表由 `Rules/maintained_sources.lock.json` 披露来源与许可状态。

更新前必须固定来源提交、复核许可和差异。不要让自动更新覆盖已审阅的本地边界。下面的命令只比较，不写文件。

```bash
python3 tools/update_external_resources.py --download --check
python3 tools/update_service_rules.py --download --check
```

动态国内规则不复制到仓库。更改其 URL、类型、策略或顺序前，必须复核规模、格式与误判风险，并同步更新配置、转换器、运行锁、审计器和文档。

## 修改主配置

配置变化至少要同步检查 `convert_to_remote_rules.py`、`generate_runtime_lock.py`、`audit_config.py`、`audit_rules.py` 和 `test_audit_config.py`。新增规则必须说明首条命中位置；新增或修改策略组必须检查引用、循环、默认成员和无节点行为。

不要为了让审计通过而放宽断言。确需改变安全或性能边界时，应同步更新迁移说明、审计报告、安全说明与更新日志。

## 完整验证

```bash
export PYTHONDONTWRITEBYTECODE=1
python3 -m compileall -q tools
python3 tools/convert_to_remote_rules.py
python3 tools/generate_runtime_lock.py
python3 tools/update_external_resources.py --verify-lock
python3 tools/update_service_rules.py --verify-lock
python3 tools/update_external_resources.py --download --check
python3 tools/update_service_rules.py --download --check
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/audit_rules.py --check-dynamic
python3 tools/audit_rules.py --check-runtime-remote
python3 tools/audit_precise_domains.py
python3 tools/test_audit_config.py
python3 tools/test_release_inventory.py
python3 tools/test_stage_surge_zip.py
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
sha256sum -c SHA256SUMS.txt
cmp --silent SHA256SUMS.txt SHA256SUMS_fixed.txt
python3 tools/package_release.py --output ../Surge-R13.9-Complete-No-Embedded-20260830.zip
```

固定远程校验要求快照提交已推送并可从 jsDelivr 读取。生成清单和哈希后再次运行本地审计，确保生成物没有掩盖未同步变化。

## 提交前检查

- `git diff --check` 没有空白错误。
- 所有文本为 UTF-8、LF、无 BOM、无 NUL，并保留结尾换行。
- 没有 `.env`、日志、缓存、临时文件、额外压缩包或符号链接。
- 文档里的版本、日期、数量、命令和包名与脚本一致。
- 私有订阅、令牌、设备日志和个人域名没有进入差异。
- 真机已完成 Wi-Fi、蜂窝、BiliBili、AI、APNs、DNS、双栈和 UDP 验收。
