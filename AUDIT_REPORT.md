# Surge R12.17 全仓审计与修改利弊

审计日期：2026-08-26

审计对象：`Surge.conf`、`Rules/`、四份锁文件、`tools/`、工作流、许可证与来源说明、README、迁移文档、发布清单、校验和及最终 ZIP。

## 结论

R12.17 的静态配置、规则库存、来源锁、文件哈希、策略引用、关键规则顺序、DNS 本地解析抑制、IPv4/IPv6 字面量失败关闭、故障注入与打包链路均通过检查。主配置需要的 30 份静态规则已经全部放入 `shenjlngbIng/surge` 仓库，并固定到完整规则快照提交；设备不再直接读取 Blackmatrix7、Amnesty Tech 或其他第三方规则仓库。

结论限定在“本包静态内容与可复现构建”。它不能替代 Surge iOS 对私有节点的实际解析，也不能控制代理服务器端 DNS；启用模块还可覆盖 General 并把规则插在主配置前。因此本报告不使用“绝对零泄漏”或“对所有用途完美”的表述。

公开版刻意保留下列安全占位与失败关闭哨兵：

~~~ini
Fail-Closed = http, 127.0.0.1, 1, no-error-alert=true
NodePool = select, policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL, update-interval=3600, no-alert=0, hidden=1, include-all-proxies=0
~~~

公开包因此不会泄露真实订阅，但直接导入公开配置时也不会获得节点。实际使用前必须只在私有副本中替换 `NodePool.policy-path`，不得把真实订阅重新打入公开 ZIP。

## 最终库存

| 项目 | 结果 |
| --- | ---: |
| 主配置行数 | 314 |
| 主配置 SHA-256 | `8f81e6eab5755c8a5af2235d6dc44c5eead60916e7e45d954224611c24223296` |
| 策略组 | 34 |
| 活动规则 | 109 |
| 仓库静态运行资源 | 30 |
| RULE-SET | 27 |
| DOMAIN-SET | 3 |
| 服务上游快照 | 19 |
| Pegasus 域名 | 1,438 |
| China 精确域名 | 306 |
| Global 精确域名 | 116 |
| China/Global 冲突 | 0 |
| 配置故障注入 | 97 项通过 |
| ZIP 路径回归 | 24 项通过 |
| 严格发布清单与文本完整性回归 | 15 项通过 |
| 发布清单记录 | 63 个非生成文件 |
| SHA-256 清单记录 | 64 个文件 |
| 完整 ZIP | 66 个普通文件 |

“第三方规则源为零”只表示 Surge 配置不再引用第三方规则仓库。传输仍使用 jsDelivr 读取你 GitHub 仓库的完整提交；`IP-ASN` 仍使用 Surge 数据，AliDNS 与测试 URL 仍是在线端点。这里没有把 30 个静态规则内容自有化扩大解释为整套网络基础设施自托管。

## 远程规则与附属资源检查

### 设备运行时

`Surge.conf` 中全部 30 条 `RULE-SET` 或 `DOMAIN-SET` 均满足下面的约束：

- 地址前缀统一为 `https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@d1d714d575d5494ef1a7613238f4f301e1b293df/Rules/`。
- 每条地址都固定到完整 Git 提交，不使用标签、短 SHA 或 `@main`；标签 `r12.17-20260825` 只用于人工识别并已核实指向同一提交。
- 每条地址都带 `update-interval=-1`，避免固定发布内容被周期性重复拉取。
- 27 条 `RULE-SET` 额外带 `no-resolve`，不为尚未解析的域名触发本地 DNS。
- 配置中不存在 Blackmatrix7、Amnesty Tech 或其他第三方规则仓库的运行时地址。
- 30 个 URL 与 `Rules/` 中 30 个本地文件一一对应，文件名、规则类型、策略和哈希均进入 `Rules/r10.lock.json`。

[Surge Rule Set 文档](https://manual.nssurge.com/rules/ruleset.html)明确说明，调用层 `no-resolve` 会移除整组 DNS 要求并强制所有子规则不解析；负 `update-interval` 会关闭自动更新。[jsDelivr 官方 GitHub 用法](https://github.com/jsdelivr/jsdelivr)支持完整提交 SHA，并把静态版本/提交哈希视为长期不可变缓存，因此这里不再用标签充当运行内容身份。

AliDNS、Cloudflare 与华为连通性检测地址属于在线服务端点，不是可复制的静态规则文件，因此没有镜像进仓库。代理订阅同样属于私有动态资源，只保留用户指定的占位符。

### 19 份服务规则

19 份服务列表继续固定到 `blackmatrix7/ios_rule_script` 提交 `c00517ce10760a93728b241923a451dfa617be80`。锁文件记录完整提交、路径、Git Blob、SHA-256、排除项和本地补充。终审把此前未声明的 278 条历史本地行全部写入对应 `add` 数组，更新器不再读取旧输出作为输入；固定上游加锁文件从零重建 19 份快照结果为 `changed=0`。

本次还与 2026-08-23 的比较提交 `f42be99379fcd1a1dd03469e8b56dcb46888fcea` 核对了相同 19 个上游文件，活动规则新增 0、删除 0。因此保留当前固定提交，不为了更新版本号制造无内容变化。

没有把 Blackmatrix7 整个 `rule` 目录搬入仓库。完整集合包含本配置不需要的服务、宽泛网段、关键词规则和共享基础设施，全部引入会扩大误分流面，也会增加更新审计成本。

### Pegasus

唯一剩余的第三方运行时静态资源已由远程直读改为本地固定副本：

| 校验项 | 值 |
| --- | --- |
| 本地文件 | `Rules/Pegasus.list` |
| 固定仓库 | `AmnestyTech/investigations` |
| 固定提交 | `3d8f248a0d015f183724ae7d096a5c46a8bb5fc7` |
| 上游路径 | `2021-07-18_nso/domains.txt` |
| Git Blob | `b504b555e89b280a41c1b81a87735f214660483e` |
| 上游 SHA-256 | `780f16136724fbd6f6b1029aed545be7ff84ef4baa4a3238be5acf158f1c48ca` |
| 本地 SHA-256 | `2611d760c310b3d51376c2741c204f6f5f297432c3f6c1a5a3616b0c2c680c3e` |
| 活动域名 | 1,438 |

本地处理只保留源文件的非空域名，不把精确域名扩大为后缀。`tools/update_external_resources.py --download --check` 已联网下载固定提交，并同时核对 URL、完整提交、Git Blob、上游哈希、条目数量和本地渲染哈希，结果为 `changed=0`。

固定提交根目录没有找到 `LICENSE`、`LICENSE.md`、`COPYING` 或 `COPYING.md`。包内保留了 `THIRD_PARTY_LICENSES/AmnestyTech-NOTICE.txt`，但该说明不能替代权利人许可。若公开再分发用途需要明确授权，应先向来源项目确认数据许可。

## 公开配置逐份对照

以下结论来自 2026-08-26 重新读取的公开原文。比较的是默认文本，不推测作者私有节点、UI 临时选择或未公开模块；“移动引用”包括 `main`、`master` 等会随仓库变化的分支。关闭 IPv6、写入 DoH 或测试页只显示境外地址，都不能单独证明没有泄漏。

### 用户指定的配置

| 配置 | DNS、VIF 与接管 | 规则解析与来源 | DIRECT/最终边界 | 对本配置的启发与取舍 |
| --- | --- | --- | --- | --- |
| [Rabbit Developer](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-Developer.conf) | `ipv6=false`；AliDNS 与 114 明文 DNS；没有 `hijack-dns=*` 或全网络接管 | 5 个 RULE-SET 调用，其中 3 个外部 URL 跟随分支；调用层无 `no-resolve` | `GEOIP,CN,DIRECT`，Final 为 Proxy | 最大优点是短小、易读、单订阅入口；适合作为语法起点，不是 DNS/双栈隐私硬化基线 |
| [Lucky](https://raw.githubusercontent.com/As-Lucky/Lucky/main/Lucky-Surge.conf) | `ipv6=false`；`system`、多组明文 DNS 与 AliDNS/DNSPod DoH 混用；无全端口劫持；热点与本地 Web 面板开启 | 11 个外部 RULE-SET 全为移动引用；文件名虽有 `No_Resolve`，调用层没有统一 `no-resolve` | 6 个组暴露 DIRECT，最终组也可选 DIRECT | 功能丰富、排错入口多；本配置保留 UDP REJECT 思路，但拒绝 system 上游、移动运行源和最终直连 |
| [Rabbit Surge-EN](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-EN.conf) | `ipv6=false`、`ipv6-vif=disabled`；system 加国内明文 DNS；只劫持 Google DNS 地址 | 17 个外部资源，16 个跟随移动分支；调用层无统一 `no-resolve` | Apple、BiliBili、Microsoft、Game 等组提供 DIRECT；中国 GEOIP 直连 | 服务组清楚且 Smart 地区组易用；本配置沿用“订阅容器加地区组”思想，但收紧双栈、全 53 接管和代理业务 DIRECT |
| [Coldvvater](https://gist.githubusercontent.com/Coldvvater/8093bc6be4340b5324b4a343493becfe/raw/Surge,conf) | `compatibility-mode=1`；IPv6 关闭；`*:53`；国内明文 DNS，加密 DNS注释 | 27 个外部资源、26 个移动引用；调用层无 `no-resolve` | Proxy 与 Final 均可选 DIRECT，约 10 个组暴露 DIRECT | 全 53 接管值得保留；本配置不采用明文上游、系统代理兼容模式或最终直连 |
| [Aegis](https://github.com/Thoseyearsbrian/Aegis) | 分开提供 IPv4/IPv6；全网络、Local、APNs、蜂窝服务接管；ICMP 关闭；AliDNS+Cloudflare 加密 DNS；UDP REJECT | 22 个外部资源，21 个移动引用；7 个调用带 `no-resolve`；恶意源覆盖面显著更广 | `FINAL,REJECT`，但中国 GEOIP 仍直连 | 是指定样本中最接近隐私/防火墙目标的一套，并在恶意源覆盖上胜出；本配置把 `no-resolve` 扩到全部 27 个 RULE-SET，保留日常 Proxy/REJECT Final，并避免接管运营商专用蜂窝服务 |
| [Blackmatrix7 规则库](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule) | 不提供主配置，因而不决定 DNS、VIF 或 IPv6 | 提供大量 Surge/No_Resolve 变体和 IP 规则，是数据源而非运行边界 | 不决定策略组或 Final | 本配置只取 19 份固定提交输入，逐服务过滤共享 CDN/遥测，再在调用层强制 `no-resolve`；没有搬入整个规则仓库 |

### 另外抽样的公开配置

| 配置 | 观察 | 适用性判断 |
| --- | --- | --- |
| [Surge 官方 Quick Start](https://manual.nssurge.com/getting-started/quick-start.html) | `system, 1.1.1.1, 8.8.8.8`、Proxy 可选 DIRECT、`GEOIP,CN,DIRECT`；目标是演示四个基本章节 | 权威的最小语法示例，不应误当成隐私强化模板 |
| [GetSomeCats 最小配置](https://github.com/getsomecat/GetSomeCats/blob/Surge/Surge.conf) | 国内明文 DNS、IPv6 关闭、本地 Web 面板、Blankwonder 移动规则 | 容易理解和启动，供应链固定、双栈接管与失败关闭不如当前包 |
| [iFaNGMiNGi Surge-Config](https://github.com/iFaNGMiNGi/Surge-Config) | Surge 6 配置使用 Google/Cloudflare 加密 DNS、`*:53` 和 UDP REJECT，但 IPv6 VIF 关闭、加密 DNS跟随出站，服务组普遍可选 DIRECT，运行规则跟随第三方分支 | 现代且便于手选；本配置更强调单节点检测、运行快照和无最终直连 |
| [chenyk1219 iPhone](https://github.com/chenyk1219/surge/blob/main/iPhone.conf) | system 加多组明文 DNS，多个国内加密 DNS且跟随出站，`*:53`、证书校验开启、UDP REJECT，但 IPv6/VIF 关闭 | 注释详尽、DNS 选项全面；混合上游和双栈关闭不符合本次“真实 ISP DNS 不出现”的目标 |

### 综合结论

当前 R12.17 在“客户端双栈不旁路、RULE-SET 不触发本机解析、检测流量固定单节点、未知公网 IP 不直连、运行规则可复现”这五项组合上，比上述样本默认文本更收紧。代价是配置和发布链更复杂，国内 IP 字面量失去 GEOIP 直连优化，首次隐私检测需要等待 `url-test`，而 Aegis 的恶意域名/威胁源覆盖仍更广。

其中最关键的反例是 `ipv6=false` 与 `ipv6-vif=disabled`。[Surge General 文档](https://manual.nssurge.com/profile/general.html)说明前者只停止普通域名的 AAAA 查询，IPv6 字面量仍可访问；后者不让原始 IPv6 进入 VIF。因此本配置保留 `ipv6=true` 与 `ipv6-vif=auto`，再用 `IP-CIDR6,::/0,Proxy,no-resolve` 处理公网 IPv6 字面量。

## 修改前后与利弊

这里的“修改前”分两层。仓库公开 R12.16 是 31 个策略组、86 条活动规则；检查过程中形成的 `R12.16 Reviewed v3` 已有 33 个策略组和 98 条规则，但 Pegasus 仍从第三方地址加载。R12.17 合并了审阅稿中的配置修正，并完成资源自有化。

| 项目 | 修改前 | 修改后 | 主要收益 | 成本或取舍 |
| --- | --- | --- | --- | --- |
| Pegasus 来源 | Reviewed v3 由设备直读 Amnesty 固定提交；公开 R12.16 未启用 | 本仓库固定副本进入 `Security` | 第三方仓库故障或内容移动不会直接影响设备；内容可复核、可回滚 | 你需要自行审阅和发布更新；再分发许可仍需注意 |
| 规则发布引用 | 29 份仓库规则固定在标签 `r12.16-20260825` | 30 份规则固定在完整提交 `d1d714d…93df`，统一 `update-interval=-1` | URL 内容身份不依赖可移动标签；配置、规则与锁形成同一快照 | 新规则必须先形成新提交并在线校验，不能把旧 URL 偷换到新内容 |
| 测试端点 | `gstatic`，全局超时 8 秒 | Cloudflare 204，全局超时 5 秒，并增加 UDP 探测 | 更快发现不可用代理，UDP 能力有独立信号 | 某些网络可能限制 Cloudflare；更短超时对高延迟线路更严格 |
| 游戏真实 IP | 未覆盖 Nintendo、PlayStation、Xbox 的部分 STUN/服务域名 | 补入 `always-real-ip` | 减少 Fake IP 对主机联机与 STUN 的干扰 | 这些域名会执行真实解析，DNS 请求量略增 |
| QUIC | `block-quic=all-proxy` | `block-quic=per-policy` | 由策略能力决定，兼容支持 UDP/QUIC 的节点 | 行为不再是所有代理统一阻断，排障时要看实际所选策略 |
| ApplePush | 组内写 `timeout=5` | 使用全局 `test-timeout=5` 加 `evaluate-before-use=true` | 首次使用先评估，参数语义与全局探测一致 | 首次 APNs 选择可能等待一轮评估；代理失败后仍可能直连，这是既定可达性取舍 |
| 广告排错 | `REJECT`、`REJECT-DROP` | 增加 DIRECT 临时开关 | 误拦截时无需改配置即可定位 | 用户误选 DIRECT 会暂时放行广告域名 |
| 安全规则 | 无独立安全组 | `Security` 默认 REJECT，含 REJECT-DROP 与 DIRECT | Pegasus 命中可阻断，也能在误报时人工关闭 | IOC 很旧且不能覆盖新威胁；DIRECT 开关被误选会关闭该层保护 |
| STUN | 直接进入 Proxy | 进入 `UDP`，默认 Proxy，可选 DIRECT 或 REJECT | 对 WebRTC、游戏与 UDP 故障更容易分离排查 | DIRECT 会暴露真实公网 IP，必须只在明确需要时使用 |
| 功能组显示 | ApplePush、AdBlock、Security、UDP 显示在策略页 | 四组保持原最优默认值并统一 `hidden=1` | 策略页面更简洁，减少误触 DIRECT 或关闭阻断的风险 | 临时排错前需要编辑私有配置取消隐藏 |
| DNS/出口检测 | 测试域名跟随 Proxy/Smart，可能按站点使用不同节点 | 9 组探测域名和 `1.1.1.1/32` 出口探针进入隐藏的 PrivacyAuto `url-test`，后台自动选择一个统一节点并保留 Fail-Closed | 无需人工显示或切换；同一轮检测保持单节点边界 | 首次使用需等待评估；自动选中节点的服务端 DNS 不合格时仍需停用该节点 |
| RULE-SET 本地解析 | 混合列表的 IP 子规则可能为域名启动本地 DNS | 27 个运行时 RULE-SET 统一 `no-resolve` | 代理域名不在分流阶段暴露给本地 AliDNS | 只靠 IP 范围识别的域名可能落入后续 Proxy，而不是专用服务组 |
| YouTube/Google | 依赖大列表首条命中 | `yt3.ggpht.com` 明确给 YouTube；通用 ggpht/gvt 给 Google | 共享基础设施归属更可预测 | 需要持续维护少量显式覆盖；未来域名归属变化要复核 |
| Viu/HBO | HBO 的 `now.com` 父级后缀可能先命中 | HBO 前增加 `viu.now.com → Streaming` | HBO 与 Streaming 选择不同地区时，Viu 不会走错组 | 只覆盖当前确认的 Viu 后缀；新域名仍需观察 |
| Game/Microsoft | Game 与 Microsoft 的共享登录、商店和云网段有抢占风险 | 登录/商店主机先给 Microsoft，`35.192.0.0/12` 先给 Proxy，Game 仍位于 Microsoft 前 | Xbox 等专属域名继续进入 Games，共享设施不被整个归入游戏 | IP 字面量命中该大网段时只能走通用 Proxy，不能自动识别具体服务 |
| 公网 IP 字面量 | 中国 GEOIP 可把 IPv4/IPv6 字面量直接放行 | 本地与服务规则后，`0.0.0.0/0`、`::/0` 统一进入 Proxy | 未知公网字面量不再因归属中国而暴露本机出口 | 未被专用 IP 规则覆盖的国内字面量失去直连优化 |
| 文档与审计 | 规则、来源与测试基线较少 | 四份锁、15 个工具、97 项故障注入、24 项 ZIP 与 15 项发布清单测试 | 修改后可以复现并自动拦截配置、路径和文本编码回归 | 维护步骤更多，不能只手改一个列表后直接发布 |
| GitHub Actions | 官方 Action 使用可移动的大版本标签；ZIP 只用包内校验和 | Action 固定提交；解压前验证包外整包 SHA-256；升级精确清理旧受管理文件 | 防止 ZIP 与内部校验和一起被替换，也避免旧发布文件残留 | 每次手动安装必须从独立渠道复制正确整包哈希；Action 升级仍需人工审阅 |
| 旧规则标签发布 | 安装流程提交新配置后尝试把既有 `r12.17-20260825` 指向新 HEAD | 工作流只核对该标签仍指向已审计规则提交，运行 URL 直接使用完整 SHA | 修复每次配置补丁都因“旧标签已存在”而失败的发布逻辑，也不移动快照 | 标签核对仍依赖 GitHub 可达；运行时不依赖标签 |
| 加密 DNS 证书 | 依赖默认值 | 显式 `encrypted-dns-skip-cert-verification=false` 并进入审计锁 | 防止以后复制片段或默认认知变化时关闭证书校验 | 证书链异常会明确失败，不会用不安全跳过掩盖问题 |

## 关键规则顺序检查

以下顺序已写入审计器，不只依赖人工阅读：

1. 9 组 DNS/出口检测域名与 `1.1.1.1/32` 出口探针位于全部运行资源和国内规则前，进入 `PrivacyAuto`。
2. Pegasus 位于其他业务规则前，命中后进入 Security。
3. APNs 位于通用 Apple 与最终规则前，进入 ApplePush。
4. YouTube 位于 Google 前，显式共享域名覆盖又位于 YouTube 列表前。
5. `viu.now.com` 位于 HBO.list 的 `now.com` 父级后缀前。
6. BiliBiliIntl 位于 BiliBili 国内规则前。
7. Game 位于 OneDrive 与 Microsoft 前；Microsoft 共享主机及 `35.192.0.0/12` 覆盖又位于 Game 前。
8. China 与 Global 精确域名位于 STUN、公网字面量和 Final 前。
9. `PROTOCOL,STUN,UDP` 位于 IPv4/IPv6 公网字面量失败关闭前。
10. 最后一条保持 `FINAL,Final,dns-failed`。

全部规则策略都能解析到存在的策略组或 Surge 内建策略。规则文件无重复活动行，DOMAIN-SET 只含域名，CIDR 可解析，Netflix 不含宽泛 `IP-CIDR`/`IP-CIDR6`，并保留 `IP-ASN,2906,no-resolve`。

## 发布终审问题修复

| 问题 | 修改前 | 修改后 | 收益 | 成本或仍存边界 |
| --- | --- | --- | --- | --- |
| 打包文件收集 | 递归接受除少量后缀外的所有普通文件，并跟随符号链接 | 打包、清单与校验和共用严格路径清单；未知文件、`.env`、日志、链接和特殊文件直接失败 | 防止本地秘密、日志或链接目标意外进入下次发布 | 每新增一个正式文件都必须同步审阅允许清单 |
| 服务规则重建 | 8 个文件有 278 条只存在于旧输出的本地行 | 278 条全部显式进入锁；生成只使用固定上游与锁输入 | 可以从空目录重建，未声明手改不会被静默续存 | 历史第三方来源无法凭技术手段补造，锁中继续披露许可待所有者复核 |
| ZIP 真实性 | 用 ZIP 内校验和验证同一个 ZIP | 工作流要求包外整包 SHA-256，并在解压、执行代码前验证 | ZIP 与内部校验和同时被替换时会失败 | 用户必须从独立交付说明取得正确哈希 |
| 系统资源边界 | “全部运行资源自有化”容易被理解得过宽 | README 明确 30 个静态规则与 jsDelivr、GeoIP/ASN、DNS、测试端点和订阅的边界 | 描述与真实运行依赖一致 | GeoIP/ASN 仍是 Surge 系统依赖；没有额外复制不需要的巨大数据库 |
| 升级同步 | 覆盖复制，不删除新版已取消的旧文件 | 只删除旧发布清单管理、但新清单已取消的路径 | 避免未来升级残留废弃规则和工具 | 用户自有文件故意不清理，需要用户自行管理 |
| ZIP 暂存 | 精确路径去重，失败可能留下暂存半成品 | 增加大小写/Unicode 碰撞检测，临时目录完整写入后原子替换 | 兼容默认 macOS 文件系统，CRC/写入失败不留下输出 | 父目录创建和最终文件系统错误仍会明确失败，不会写入正式目录 |

这次修复没有改变用户指定保留的“问题一”：`Fail-Closed` 与公开 `NodePool` 占位地址仍保持原样。

## 安全与隐私检查

- `Surge.conf` 中只有一个 `policy-path`，且仍为 `example.invalid` 占位符。
- 未发现真实订阅、节点、Token、Cookie、用户名、密码、私钥或证书。
- 没有 `[MITM]`、`[Script]`、`[URL Rewrite]` 或外部模块。
- Telegram 组没有 DIRECT；Final 没有 DIRECT；代理业务组没有 DIRECT。
- `include-all-networks=true`、`include-apns=true` 保留，APNs 的唯一可用性例外仍是 ApplePush 的 Proxy 到 DIRECT 回落。
- `ApplePush`、`AdBlock`、`Security`、`UDP` 均为 `hidden=1`；隐藏未改变其规则目标、成员顺序或默认路径。
- `PrivacyAuto` 为隐藏的 `url-test`，仅声明 Fail-Closed 并从 NodePool 复制具体代理；首次使用前自动评估，且不含 DIRECT 或嵌套组。
- 27 个运行时 RULE-SET 均带 `no-resolve`；公网 IPv4/IPv6 字面量没有 DIRECT 兜底。
- Wi-Fi 代理、热点代理和 Web 控制面板保持关闭。
- `Fail-Closed` 和 NodePool 占位设计未改。

### 真机模块根因与复测

用户提供的 Surge 最近请求记录中，启用 `dandanvip.sgmodule` 时出现 `Rule evaluating requires DNS lookup for rule: RULE-SET dandan.list`。模块规则位于主配置检测域名规则之前，先触发了本地 DNS，这与 Net.Coffee 同时显示 `111.44.252.67/68` 中国移动解析器相吻合。[Surge 官方模块说明](https://manual.nssurge.com/profile/module.html)也确认，模块设置优先于主配置，Rule/Host 等新增行会插入原内容顶部。

卸载该模块后的连续截图显示：Net.Coffee 报告“未检测到 DNS 泄露”，解析器全部为所选日本节点侧的 Cloudflare 地址；IPPure 同样只列出日本 Cloudflare IPv4/IPv6，网页出口为 `38.207.136.179`。这证明用户当时设备状态已消除“本机中国移动解析器”这一具体泄漏现象，但不等同于以后启用任意模块或切换任意节点仍永久无泄漏。

最终包不包含 Module、MITM、Script 或 Rewrite。真机复测必须先关闭所有未逐行审阅的模块，重新载入配置、清理 DNS/网页缓存，并用新无痕页面发起一轮新的唯一域名测试。

## 自动验证结果

| 验证 | 结果 |
| --- | --- |
| Python 工具编译 | 通过 |
| 远程资源库存 | 30 个本仓库资源，未嵌入规则内容 |
| 规则快照标签映射 | `r12.17-20260825` 精确指向 `d1d714d575d5494ef1a7613238f4f301e1b293df` |
| 完整提交在线 URL | 30/30 返回且内容 SHA-256 与本地、运行锁同时一致 |
| Pegasus 离线来源锁 | 1 份、1,438 条，通过 |
| Pegasus 固定源联网重下 | Blob、上游哈希、本地哈希一致，changed=0 |
| 服务来源锁 | 19 份通过 |
| 服务从零重建 | 固定上游加显式锁输入，19 份 changed=0 |
| 仓库维护列表披露锁 | 10 份数量、哈希、来源状态与许可说明通过 |
| 配置审计 | R12.17、34 组、109 规则、30 资源，通过 |
| 规则审计 | 30 本地规则文件、全部数量和哈希通过 |
| China/Global 精确域名 | 306/116，冲突 0 |
| 故障注入 | 97/97 通过 |
| ZIP 白名单回归 | 24/24 通过 |
| 严格发布清单与文本完整性回归 | 15/15 通过 |
| JSON 锁文件解析 | 4/4 通过 |
| GitHub Actions YAML 解析 | 1/1 通过 |
| 凭据与已知私密材料扫描 | 66 个发布文件通过；主配置只有 1 个 `example.invalid` policy-path |
| 发布清单与双 SHA-256 清单 | 重新生成并逐项通过 |
| 完整 ZIP 解压测试 | 66/66 文件通过 |
| 解压后全量复审 | 配置、规则、来源锁与 136 项回归测试全部通过 |
| 确定性打包 | 从解压内容重打包后逐字节一致 |

最终构建已经重新生成 `RELEASE_MANIFEST.txt` 与两份 SHA-256 清单，并对完整 ZIP 执行解压、校验和、解压后复审及确定性重打包比较。ZIP 自身的 SHA-256 位于包外交付说明中，避免归档把自身哈希写入自身造成递归变化。

## 发布前必须完成

1. 把完整包按原目录结构上传到仓库，不能只上传 `Surge.conf` 或 `Rules/Pegasus.list`；手动工作流需要填写包外交付的整包 SHA-256。
2. 确认原规则快照标签 `r12.17-20260825` 仍指向 `d1d714d575d5494ef1a7613238f4f301e1b293df`；不要移动或重建旧标签。
3. 确认 jsDelivr 可读取该完整提交的 30 个 URL 后再刷新 Surge 外部资源；运行时不依赖标签。
4. 在私有副本中替换 NodePool 占位订阅，不得把真实地址提交到公开仓库。
5. 保持 `dandanvip.sgmodule` 和其他未审阅模块关闭；在 Surge iOS 真机完成配置解析、节点导入、PrivacyAuto 与四个功能组隐藏、PrivacyAuto 自动单节点 DNS/出口检测、APNs、Telegram、流媒体地区、UDP/STUN、Wi-Fi 到蜂窝再回 Wi-Fi 的回归。

静态工具可以确认文本、来源、哈希、引用、顺序和包结构，不能模拟真实订阅内容、节点质量、运营商网络、地区版权响应或 Surge App 的运行时状态。因此真机项目属于发布门槛，不应被本报告的“通过”替代。
