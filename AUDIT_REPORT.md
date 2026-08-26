# Surge R12.17 全仓审计与修改利弊

审计日期：2026-08-26

审计对象：`Surge.conf`、`Rules/`、四份锁文件、`tools/`、工作流、许可证与来源说明、README、迁移文档、发布清单、校验和及最终 ZIP。

## 结论

R12.17 的静态配置、规则库存、来源锁、文件哈希、策略引用、关键规则顺序、DNS 本地解析抑制、IPv4/IPv6 字面量失败关闭、故障注入与打包链路均通过检查。主配置需要的 30 份静态规则已经全部放入 `shenjlngbIng/surge` 仓库；设备不再直接读取 Blackmatrix7、Amnesty Tech 或其他第三方规则仓库。

问题一按用户要求不处理，下面两行保持原样：

~~~ini
Fail-Closed = http, 127.0.0.1, 1, no-error-alert=true
NodePool = select, policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL, update-interval=3600, no-alert=0, hidden=1, include-all-proxies=0
~~~

公开包因此不会泄露真实订阅，但直接导入公开配置时也不会获得节点。实际使用前必须只在私有副本中替换 `NodePool.policy-path`。

## 最终库存

| 项目 | 结果 |
| --- | ---: |
| 主配置行数 | 313 |
| 主配置 SHA-256 | `b845363d2f21d9cd3ec72f21c176d5810f0281ccc7320ad6beb07142492fa3fe` |
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
| 配置故障注入 | 90 项通过 |
| ZIP 路径回归 | 24 项通过 |
| 严格发布清单回归 | 10 项通过 |
| 发布清单记录 | 63 个非生成文件 |
| SHA-256 清单记录 | 64 个文件 |
| 完整 ZIP | 66 个普通文件 |

“第三方规则源为零”只表示 Surge 配置不再引用第三方规则仓库。传输仍使用 jsDelivr 读取你 GitHub 仓库的固定标签；`IP-ASN` 仍使用 Surge 数据，AliDNS 与测试 URL 仍是在线端点。这里没有把 30 个静态规则内容自有化扩大解释为整套网络基础设施自托管。

## 远程规则与附属资源检查

### 设备运行时

`Surge.conf` 中全部 30 条 `RULE-SET` 或 `DOMAIN-SET` 均满足下面的约束：

- 地址前缀统一为 `https://cdn.jsdelivr.net/gh/shenjlngbIng/surge@r12.17-20260825/Rules/`。
- 每条地址都固定到不可变发布标签，不使用 `@main`。
- 每条地址都带 `update-interval=-1`，避免固定发布内容被周期性重复拉取。
- 27 条 `RULE-SET` 额外带 `no-resolve`，不为尚未解析的域名触发本地 DNS。
- 配置中不存在 Blackmatrix7、Amnesty Tech 或其他第三方规则仓库的运行时地址。
- 30 个 URL 与 `Rules/` 中 30 个本地文件一一对应，文件名、规则类型、策略和哈希均进入 `Rules/r10.lock.json`。

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

## 参考配置的 DNS 处理对照

以下结论来自 2026-08-26 重新读取的公开文件，不把“关闭 IPv6”“使用 DoH”或“DNS 检测只显示境外地址”单独等同于无泄漏。

| 配置 | 主要做法 | 仍存边界 | 本配置的取舍 |
| --- | --- | --- | --- |
| [Rabbit Developer](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-Developer.conf) | 关闭 IPv6；AliDNS 与 114 明文 DNS；DoH 留作机场自填 | 无全端口 DNS 接管；RULE-SET/GEOIP 可触发本地解析 | 不采用关闭 VIF 或明文 DNS；保留其简洁的单一订阅入口思路 |
| [Rabbit Surge-EN](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-EN.conf) | 关闭 IPv6；`system` 加国内明文 DNS；只接管 Google DNS 地址 | 系统/运营商解析器本来就会出现，硬编码其他 DNS 也可绕过 | 使用 `*:53`，禁止 system 上游 |
| [Lucky](https://raw.githubusercontent.com/As-Lucky/Lucky/main/Lucky-Surge.conf) | 关闭 IPv6；system/国内/Cloudflare 普通 DNS并配 AliDNS、DNSPod DoH；部分使用 No Resolve 规则 | 未设置 `hijack-dns=*`; GEOIP 可解析；DIRECT 入口较多 | 保留 UDP REJECT，放弃 system 与混合普通 DNS |
| [Coldvvater](https://gist.github.com/Coldvvater/8093bc6be4340b5324b4a343493becfe) | 关闭 IPv6；`*:53`；国内普通 DNS；加密 DNS被注释 | Final/Proxy 可选 DIRECT，普通 RULE-SET 与 GEOIP 会本地解析 | 吸收全端口接管，不吸收明文上游和最终直连 |
| [Aegis](https://github.com/Thoseyearsbrian/Aegis) | 分开提供 IPv4/IPv6 配置；AliDNS+Cloudflare 加密 DNS；全网络接管、ICMP 关闭、UDP REJECT、恶意规则 `no-resolve`、FINAL REJECT | 普通服务 RULE-SET 与 `GEOIP,CN,DIRECT` 仍可解析；Smart 没有单节点检测边界 | 吸收加密 DNS、VIF、ICMP/UDP 和 no-resolve 思路，并扩展到所有运行时 RULE-SET；日常 Final 保持可用的 Proxy/REJECT |
| [Blackmatrix7 规则库](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule) | Surge IP 条目普遍附带 `no-resolve`，并提供聚合列表 | 它是规则数据，不负责 VIF、上游 DNS、IPv6 或最终策略 | 固定、筛选所需快照，并在 RULE-SET 调用层再次强制 `no-resolve` |

其中最关键的反例是 `ipv6=false` 与 `ipv6-vif=disabled`。Surge 官方说明前者只停止普通域名的 AAAA 查询，IPv6 字面量仍可访问；后者不让原始 IPv6 进入 VIF。因此本配置保留 `ipv6=true` 与 `ipv6-vif=auto`，再用 `IP-CIDR6,::/0,Proxy,no-resolve` 处理公网 IPv6 字面量。

## 修改前后与利弊

这里的“修改前”分两层。仓库公开 R12.16 是 31 个策略组、86 条活动规则；检查过程中形成的 `R12.16 Reviewed v3` 已有 33 个策略组和 98 条规则，但 Pegasus 仍从第三方地址加载。R12.17 合并了审阅稿中的配置修正，并完成资源自有化。

| 项目 | 修改前 | 修改后 | 主要收益 | 成本或取舍 |
| --- | --- | --- | --- | --- |
| Pegasus 来源 | Reviewed v3 由设备直读 Amnesty 固定提交；公开 R12.16 未启用 | 本仓库固定副本进入 `Security` | 第三方仓库故障或内容移动不会直接影响设备；内容可复核、可回滚 | 你需要自行审阅和发布更新；再分发许可仍需注意 |
| 规则发布引用 | 29 份仓库规则固定在 `r12.16-20260825` | 30 份规则固定在 `r12.17-20260825`，统一 `update-interval=-1` | 配置、规则与锁文件形成同一发布快照 | 新标签未创建前 30 份规则都会 404；以后更新必须发新标签 |
| 测试端点 | `gstatic`，全局超时 8 秒 | Cloudflare 204，全局超时 5 秒，并增加 UDP 探测 | 更快发现不可用代理，UDP 能力有独立信号 | 某些网络可能限制 Cloudflare；更短超时对高延迟线路更严格 |
| 游戏真实 IP | 未覆盖 Nintendo、PlayStation、Xbox 的部分 STUN/服务域名 | 补入 `always-real-ip` | 减少 Fake IP 对主机联机与 STUN 的干扰 | 这些域名会执行真实解析，DNS 请求量略增 |
| QUIC | `block-quic=all-proxy` | `block-quic=per-policy` | 由策略能力决定，兼容支持 UDP/QUIC 的节点 | 行为不再是所有代理统一阻断，排障时要看实际所选策略 |
| ApplePush | 组内写 `timeout=5` | 使用全局 `test-timeout=5` 加 `evaluate-before-use=true` | 首次使用先评估，参数语义与全局探测一致 | 首次 APNs 选择可能等待一轮评估；代理失败后仍可能直连，这是既定可达性取舍 |
| 广告排错 | `REJECT`、`REJECT-DROP` | 增加 DIRECT 临时开关 | 误拦截时无需改配置即可定位 | 用户误选 DIRECT 会暂时放行广告域名 |
| 安全规则 | 无独立安全组 | `Security` 默认 REJECT，含 REJECT-DROP 与 DIRECT | Pegasus 命中可阻断，也能在误报时人工关闭 | IOC 很旧且不能覆盖新威胁；DIRECT 开关被误选会关闭该层保护 |
| STUN | 直接进入 Proxy | 进入 `UDP`，默认 Proxy，可选 DIRECT 或 REJECT | 对 WebRTC、游戏与 UDP 故障更容易分离排查 | DIRECT 会暴露真实公网 IP，必须只在明确需要时使用 |
| 功能组显示 | ApplePush、AdBlock、Security、UDP 显示在策略页 | 四组保持原最优默认值并统一 `hidden=1` | 策略页面更简洁，减少误触 DIRECT 或关闭阻断的风险 | 临时排错前需要编辑私有配置取消隐藏 |
| DNS/出口检测 | 测试域名跟随 Proxy/Smart，可能按站点使用不同节点 | 9 组探测域名和 `1.1.1.1/32` 出口探针进入可固定具体节点的 Privacy，默认 Fail-Closed | 同一轮检测只观察一个节点，能区分客户端路径与节点侧 DNS | 检测前多一步人工选节点；节点侧 DNS 不合格仍需换节点 |
| RULE-SET 本地解析 | 混合列表的 IP 子规则可能为域名启动本地 DNS | 27 个运行时 RULE-SET 统一 `no-resolve` | 代理域名不在分流阶段暴露给本地 AliDNS | 只靠 IP 范围识别的域名可能落入后续 Proxy，而不是专用服务组 |
| YouTube/Google | 依赖大列表首条命中 | `yt3.ggpht.com` 明确给 YouTube；通用 ggpht/gvt 给 Google | 共享基础设施归属更可预测 | 需要持续维护少量显式覆盖；未来域名归属变化要复核 |
| Viu/HBO | HBO 的 `now.com` 父级后缀可能先命中 | HBO 前增加 `viu.now.com → Streaming` | HBO 与 Streaming 选择不同地区时，Viu 不会走错组 | 只覆盖当前确认的 Viu 后缀；新域名仍需观察 |
| Game/Microsoft | Game 与 Microsoft 的共享登录、商店和云网段有抢占风险 | 登录/商店主机先给 Microsoft，`35.192.0.0/12` 先给 Proxy，Game 仍位于 Microsoft 前 | Xbox 等专属域名继续进入 Games，共享设施不被整个归入游戏 | IP 字面量命中该大网段时只能走通用 Proxy，不能自动识别具体服务 |
| 公网 IP 字面量 | 中国 GEOIP 可把 IPv4/IPv6 字面量直接放行 | 本地与服务规则后，`0.0.0.0/0`、`::/0` 统一进入 Proxy | 未知公网字面量不再因归属中国而暴露本机出口 | 未被专用 IP 规则覆盖的国内字面量失去直连优化 |
| 文档与审计 | 规则、来源与测试基线较少 | 四份锁、15 个工具、90 项故障注入、24 项 ZIP 与 10 项发布清单测试 | 修改后可以复现和自动拦截回归 | 维护步骤更多，不能只手改一个列表后直接发布 |
| GitHub Actions | 官方 Action 使用可移动的大版本标签；ZIP 只用包内校验和 | Action 固定提交；解压前验证包外整包 SHA-256；升级精确清理旧受管理文件 | 防止 ZIP 与内部校验和一起被替换，也避免旧发布文件残留 | 每次手动安装必须从独立渠道复制正确整包哈希；Action 升级仍需人工审阅 |

## 关键规则顺序检查

以下顺序已写入审计器，不只依赖人工阅读：

1. 9 组 DNS/出口检测域名与 `1.1.1.1/32` 出口探针位于全部运行资源和国内规则前，进入 Privacy。
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
- `Privacy` 可见、默认 Fail-Closed、不含 DIRECT，并只从 NodePool 展开具体代理。
- 27 个运行时 RULE-SET 均带 `no-resolve`；公网 IPv4/IPv6 字面量没有 DIRECT 兜底。
- Wi-Fi 代理、热点代理和 Web 控制面板保持关闭。
- `Fail-Closed` 和 NodePool 占位设计未改。

## 自动验证结果

| 验证 | 结果 |
| --- | --- |
| Python 工具编译 | 通过 |
| 远程资源库存 | 30 个本仓库资源，未嵌入规则内容 |
| Pegasus 离线来源锁 | 1 份、1,438 条，通过 |
| Pegasus 固定源联网重下 | Blob、上游哈希、本地哈希一致，changed=0 |
| 服务来源锁 | 19 份通过 |
| 服务从零重建 | 固定上游加显式锁输入，19 份 changed=0 |
| 仓库维护列表披露锁 | 10 份数量、哈希、来源状态与许可说明通过 |
| 配置审计 | R12.17、34 组、109 规则、30 资源，通过 |
| 规则审计 | 30 本地规则文件、全部数量和哈希通过 |
| China/Global 精确域名 | 306/116，冲突 0 |
| 故障注入 | 90/90 通过 |
| ZIP 白名单回归 | 24/24 通过 |
| 严格发布清单回归 | 10/10 通过 |
| JSON 锁文件解析 | 4/4 通过 |
| 发布清单与双 SHA-256 清单 | 重新生成并逐项通过 |
| 完整 ZIP 解压测试 | 66/66 文件通过 |
| 解压后全量复审 | 配置、规则、来源锁与 124 项回归测试全部通过 |
| 确定性打包 | 从解压内容重打包后逐字节一致 |

最终构建已经重新生成 `RELEASE_MANIFEST.txt` 与两份 SHA-256 清单，并对完整 ZIP 执行解压、校验和、解压后复审及确定性重打包比较。ZIP 自身的 SHA-256 位于包外交付说明中，避免归档把自身哈希写入自身造成递归变化。

## 发布前必须完成

1. 把完整包按原目录结构上传到仓库，不能只上传 `Surge.conf` 或 `Rules/Pegasus.list`；手动工作流需要填写包外交付的整包 SHA-256。
2. 确认原规则快照标签 `r12.17-20260825` 仍存在且未移动；DNS 补丁只改变主配置和审计元数据，不改写该不可变规则标签。
3. 确认 jsDelivr 可读取该标签后再刷新 Surge 外部资源。
4. 在私有副本中替换 NodePool 占位订阅，不得把真实地址提交到公开仓库。
5. 在 Surge iOS 真机完成配置解析、节点导入、四个功能组隐藏、Privacy 单节点 DNS/出口检测、APNs、Telegram、流媒体地区、UDP/STUN、Wi-Fi 到蜂窝再回 Wi-Fi 的回归。

静态工具可以确认文本、来源、哈希、引用、顺序和包结构，不能模拟真实订阅内容、节点质量、运营商网络、地区版权响应或 Surge App 的运行时状态。因此真机项目属于发布门槛，不应被本报告的“通过”替代。
