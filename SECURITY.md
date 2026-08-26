# 安全规范

## 敏感信息

不要在提交、Issue、Pull Request、日志或截图中公开：

- 订阅地址和 Sub-Store 私有接口
- 代理节点、端口、用户名和密码
- API Token、Bot Token、Cookie 和会话信息
- 私钥、CA、客户端证书和设备标识

## 报告问题

发现可能泄露敏感信息或绕过失败关闭边界的问题时，不要公开披露具体凭据。请先撤销或轮换相关凭据，再通过仓库所有者提供的私密联系方式报告。

## 支持范围

本项目只审计仓库内公开配置。用户自行添加的节点、订阅、Module、MITM、脚本和重写规则不在公开审计范围内。

R12.17 的静态运行规则必须全部来自本仓库完整提交 `d1d714d575d5494ef1a7613238f4f301e1b293df`。`Rules/upstreams.lock.json` 和 `Rules/resources.lock.json` 中的第三方 URL 仅用于维护时核对固定提交，不允许直接复制到 `Surge.conf`；`Rules/maintained_sources.lock.json` 必须披露其余仓库维护列表。若发现运行配置绕过本仓库、锁文件哈希失配、规则快照标签不再指向该提交或出现未声明本地规则，应按供应链问题处理并停止发布。

发布工具使用 `tools/release_inventory.py` 的严格允许清单。未知文件、`.env`、日志、符号链接、特殊文件、非 UTF-8/BOM/CRLF/NUL/缺少尾换行的文本，以及路径大小写或 Unicode 碰撞不得进入发布包。安装工作流必须在解压和执行 ZIP 内代码前验证包外提供的整包 SHA-256；ZIP 内的 `SHA256SUMS.txt` 只用于验证归档内部文件，不能代替整包真实性验证。

`ApplePush`、`AdBlock`、`Security` 与 `UDP` 的 `hidden=1` 仅隐藏策略选择界面，不构成安全隔离，也不会删除组内成员。其默认顺序仍由配置审计器和运行锁约束；临时排错必须在私有副本中显式取消隐藏，避免误以为隐藏组无法被规则调用。

`PrivacyAuto` 是 DNS/出口检测的隐藏自动单节点边界，不是匿名性保证。它必须保持 `url-test, Fail-Closed`、不含 DIRECT 或嵌套组，并只从 NodePool 复制具体代理。27 个运行时 RULE-SET 必须带 `no-resolve`，公网 IPv4/IPv6 字面量必须在本地和专用规则之后进入 Proxy。自动选中的具体节点仍出现异常解析器属于节点服务端风险，应停止使用该节点；公开配置无法审计或改写私有节点的递归 DNS、NAT 与分流出口。

Surge 模块高于主配置：General 可覆盖，Rule/Host/Script/Rewrite 会插入主配置内容前。任何未审阅模块都可能重新打开 DNS 或直连路径；公开基线测试必须先关闭这些模块。本包不包含 `dandanvip.sgmodule`，本次真机测试也只有在卸载该模块后才恢复到无本机 ISP 解析器的结果。
