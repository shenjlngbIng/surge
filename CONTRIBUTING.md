# 维护说明

保持“一个订阅 URL、外部规则、完整节点池与服务组”的使用方式。勿重新引入内嵌列表、分离代理文件或需要用户配置的新脚本。

修改规则文件后，先审阅来源与分流影响，把来源提交推送到仓库，再更新固定引用 SHA。重新生成运行锁、发布清单和校验和；规则文件修改与发布配置不能使用尚不存在的自引用提交。

```bash
python3 tools/convert_to_remote_rules.py
python3 tools/generate_runtime_lock.py
python3 tools/audit_config.py
python3 tools/audit_rules.py --check-runtime-remote
python3 tools/test_runtime_rules.py
python3 tools/test_policy_failover.py
python3 tools/test_audit_config.py
python3 tools/update_external_resources.py --verify-lock
python3 tools/update_service_rules.py --verify-lock
python3 tools/generate_release_manifest.py
python3 tools/generate_checksums.py
python3 tools/package_release.py
```

不得把离线模型通过表述成 iPhone、UDP 或真实代理已测试成功。保留订阅/Smart 的保护成员及无循环关系；新增控制组必须接到实际规则。公开仓库和归档不得含私人订阅。
