# 贡献说明

R13.18 的主配置、29 个来源快照、生成器、锁文件和发布清单共同构成可复现版本。

- 用户只维护一处 NodePool.policy-path。公开文件不可带入私人订阅或凭据。
- 保留完整节点池、Smart、地区与服务策略；不要添加回环假代理修饰诊断结果。
- 主配置不含外部 RULE-SET/DOMAIN-SET，原始维护副本仍保留在 Rules/。
- 不可把静态检查当成 Surge 原生解析、订阅在线、真实代理或 UDP 验证。
- 不可宣称 Smart 空组严格失败关闭，或宣称 PROTOCOL DNS 能识别所有应用解析器。
- 编辑来源之后先生成内置规则，再更新锁、发布清单和校验和。保留规则顺序和 no-resolve/extended-matching 语义。

```bash
python3 tools/embed_runtime_rules.py
python3 tools/generate_runtime_lock.py
python3 tools/test_embed_runtime_rules.py
python3 tools/audit_config.py
python3 tools/audit_rules.py
python3 tools/audit_precise_domains.py
python3 tools/test_audit_config.py
python3 tools/test_release_inventory.py
python3 tools/test_stage_surge_zip.py
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
python3 tools/package_release.py --output ../Surge-R13.18-Single-File-20260907.zip
```

保留的旧命令 `convert_to_remote_rules.py` 现在仅检查内置来源清单，不转换回远程引用。
