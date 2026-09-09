# 维护说明

保持“一个订阅 URL、外部规则、完整节点池与服务组”的使用方式。勿重新引入内嵌列表、分离代理文件或需要用户配置的新脚本。

地区受限服务只能引用严格节点源，不能加入 Proxy、Auto 或允许跨区回退的外层地区入口。新增地区需核对官方服务范围、补充名称分类和空池/错误地区回归，并同步 README 及运行锁。名称筛选、延迟测试与实际服务可用性必须分别说明。

仅调整注释时应核对有效配置指令完全一致。算法、候选范围或分流改变时，应同步审计断言及相应的行为退化案例，不跳过现有发布检查。

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
