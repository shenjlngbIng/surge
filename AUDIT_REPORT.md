# R13.23 配置复核

复核日期为 2026-09-08。比较基线为 R13.22，提交 `dd8d94e486d7b85f1e3634d653ca78f120ca5ebf`。本次对照用户事件截图、当前代码、官方文档及推送参考方案检查。

## 已确认的问题与证据边界

截图列出了 Microsoft、OneDrive、Game 和 Google 规则加载失败，以及 include-all-networks 的兼容性警告。截图没有具体网络错误码或失败请求的出口，不能据此区分首次下载、超时、DNS、TLS 或节点故障。规则警告的时间早于截图中的接管警告，亦不能仅按排列顺序认定两者具有因果关系。

R13.22 仍有 Telegram 外部规则、ApplePush 组、APNs 外部规则和接管开关，推送功能未删除。ApplePush 隐藏不影响分流。[隐藏参数](https://manual.nssurge.com/policy-groups/parameters.html)

离线模型复现了一条可修复的失效路径。Proxy 通过 NodePool 固定到不可用节点，订阅中另有健康节点时，旧版 GitHub raw 请求失败，ApplePush 选择 DIRECT，Auto 实际仍能选择健康节点。本次修正此路径，不把模型复现等同于用户手机故障已经定位。

## 配置修改

| 位置 | 修改后行为 |
| --- | --- |
| ApplePush | Proxy、Auto、DIRECT 依次选择，保留 60 秒间隔、首次使用前检查及隐藏状态 |
| GitHub raw 前置规则 | 使用 Auto，不跟随 Proxy 的手动节点选择，无新增直连回退 |
| 说明与注释 | 解释接管警告、外部资源恢复顺序及锁屏推送验收 |

仅两条有效配置指令改变。其余全局参数、Telegram 数据分流、订阅、40 个组和 142 条主规则保持。29 份外置列表内容、URL、顺序及匹配选项全部不变，继续固定在 `6e8e1bfbbdda66ee8ad0a5ad3979b6de8b5b7a51`，不内嵌规则、不清理缓存、不添加公共转换服务。

## 推送参考方案核对

用户给出的 [NodeSeek 归档](https://web.archive.org/web/20260715022631/https://www.nodeseek.com/post-709310-1) 未能读取全文，原站访问返回 403。检索找到同题公开说明及其指向的 [APNs 源列表](https://github.com/QuixoticHeart/rule-set/blob/ruleset/loon/apns.list)，仅将其作为待核对方案，实际参数依据官方文档确认。

- [Surge 全局参数](https://manual.nssurge.com/profile/general.html) 明确 include-apns 依赖 include-all-networks。保留两项及警告日志，避免为消除提示而取消推送接管。
- [Apple 推送网络要求](https://support.apple.com/en-us/102266) 公布的 5 个 IPv4 和 4 个 IPv6 网段，当前 APNs.list 全部覆盖。5223 为设备推送连接端口，443 是受支持的回退路径。
- 参考列表包含整个 akadns.net、Apple 共享 CDN 关键词及 identity.apple.com。[Apple 企业网络说明](https://support.apple.com/en-us/101555) 将 identity.apple.com 列为 APNs 证书申请门户。未找到这些宽泛新增项是普通 Telegram 通知必需条件的证据，因此保留精确规则，避免扩大代理范围。
- [Fallback](https://manual.nssurge.com/policy-groups/fallback.html) 使用通用 URL 测试判断可用性；[Smart](https://manual.nssurge.com/policy-groups/smart.html) 可以根据实际连接质量重试节点。两者均不证明 APNs 实际通知送达。

## 验证范围

- 107 项配置故障注入，包括恢复旧下载出口、删除推送 Auto 回退和删除 DIRECT 保底。
- 保留 23 个原有域名/SNI、16 个正常网站、8 个广告、132 个 DNS 端口、6 个配置损坏及 10 个行为退化案例。
- 新增 27 个推送和下载域名、79 个 IP/端口、6 个推送 SNI 案例，以及 6 个规则行为退化案例。IP 模型不模拟 ASN、GeoIP、DNS 解析或真实网络。
- 新增 11 项推送和下载路径检查，以及恢复旧 ApplePush 成员时的失败检验。覆盖手选坏节点、健康备用、空订阅、全部失效及 Auto 临时覆盖限制。
- 固定规则及来源锁检查通过。29 个在线资源均可读取，与本地文件逐字一致，包括截图中报错的四份文件；这是当前检查环境的结果。
- 发布清单、校验和和维护归档采用同一文件库存生成并检查。

## 手机端仍需验收

下载分流只对经过活动规则系统的请求有效。首次导入、无可用节点或 Auto 被手动覆盖时仍可能下载失败。网络恢复后应更新失败资源并查看当前状态，不把历史事件当作新一次失败。

APNs 需要系统长连接。应用新配置、规则下载成功后，应重新建立连接并锁屏收取新消息，分别验证 Wi-Fi 和蜂窝网络。没有连接用户手机或私人节点，本次不宣称推送、UDP 或所有资源在该手机网络上已恢复。
