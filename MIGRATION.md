# R12.15 迁移说明

R12.15 专门修正 Wi-Fi、蜂窝数据和热点之间切换时出现的集中测速请求。它不会写入或替换个人订阅，也不改变 Telegram、APNs、DNS 或服务分流的既有方向。

公开配置中的订阅地址仍是不可路由占位符。真实订阅、Token、节点密码和证书只能放在私有副本中。

## 升级前确认

- Surge iOS 建议使用 5.14.6 或更高版本。
- Smart 策略组最低要求 Surge iOS 5.11.0，并且属于 Surge iOS 功能更新订阅功能。
- 如果当前设备不能使用 Smart 策略组，请先升级或续订功能更新订阅，不要把新版 Smart 组自行改回全订阅 fallback 或 url-test。
- 先导出当前可用的私有配置作为回滚副本。

## 最短迁移步骤

1. 备份当前私有 Surge.conf。
2. 用 R12.15 完整文件覆盖公开仓库，不要只替换主配置。
3. 从新版 Surge.conf 再复制一份私有副本。
4. 找到旧私有配置中 AllServer 的 policy-path 值。
5. 只复制 URL 本身，填入新版 NodePool 的 policy-path。
6. 不复制旧版 AllServer、地区组、General、Host 或 Rule 段。
7. 在 Surge 中导入私有副本并重新载入配置。
8. 更新外部资源，确认 AllServer 和地区组能看到真实节点。
9. 按“升级后验证”完成 Wi-Fi 与蜂窝切换测试。

旧版写法：

~~~ini
AllServer = fallback, Fail-Closed, policy-path=https://你的私有订阅地址, ...
~~~

新版写法：

~~~ini
NodePool = select, policy-path=https://你的私有订阅地址, update-interval=3600, no-alert=0, hidden=1, include-all-proxies=0
AllServer = smart, Fail-Closed, no-alert=0, hidden=0, include-all-proxies=0, include-other-group=NodePool
~~~

不要把整条旧 AllServer 复制到新版。真正需要迁移的只有 policy-path 等号右侧的私有 URL。

## 为什么必须迁移到 NodePool

旧版把三个职责放在同一个 AllServer 中：

1. 下载订阅。
2. 保存全部节点。
3. 对全部节点执行 fallback 连通性测试。

Surge 在网络接口切换后会清除旧自动测试结果。策略组再次被使用时，fallback 会重新测试所有成员。若订阅约有 155 个节点，而每个节点产生两次 HEAD 探测，就可能在一秒内接近 310 个请求。

新版拆成两层：

| 层 | 类型 | 职责 | 是否直接被规则使用 |
| --- | --- | --- | --- |
| NodePool | select | 下载和保存订阅节点 | 否，隐藏 |
| AllServer 与地区组 | smart | 根据连接表现自动选路 | 是 |

NodePool 使用 select，因此网络切换不会让订阅容器自己遍历全部节点。Smart 组从 NodePool 读取成员，并根据实际连接表现、失败惩罚和必要的恢复探测进行决策。

## 行为变化

| 项目 | R12.14 | R12.15 |
| --- | --- | --- |
| 订阅入口 | AllServer.policy-path | NodePool.policy-path |
| 订阅容器 | fallback，同时下载和测速 | select，只下载节点 |
| 总节点自动选择 | 全成员 fallback 探测 | Smart 自学习 |
| 地区选择 | url-test，间接读取 AllServer | Smart，直接筛选 NodePool |
| 网络切换 | 首次使用可能集中重测全订阅 | 不再由订阅容器触发全量 fallback |
| 空订阅保护 | AllServer 显式 Fail-Closed | 所有 Smart 组显式 Fail-Closed |
| ApplePush | Proxy 后 DIRECT 回落 | 不变 |
| Telegram | 强制代理 | 不变 |
| DNS | AliDNS DoH/DoT 与端口控制 | 不变 |
| 活动规则 | 85 | 85 |

## 失败关闭没有被削弱

Surge iOS 5.11.3 以后，完全没有子策略的 Smart 组可使用替代策略。为避免空订阅时出现意外 DIRECT，R12.15 没有依赖空组行为，而是在 AllServer 和五个地区组中明确写入 Fail-Closed。

因此：

- NodePool 下载失败时，AllServer 仍至少含有 Fail-Closed。
- 地区正则没有匹配到节点时，该地区组仍至少含有 Fail-Closed。
- 规则集失效时，流量仍进入 FINAL,Final,dns-failed。
- Final 的默认选择仍是 Proxy，并保留手动 REJECT。
- NodePool 被隐藏，规则和可见策略组不能直接选择它。

Fail-Closed 指向本机未监听端口。连接失败是预期行为，no-error-alert 仅隐藏这个刻意失败产生的提醒，不会把失败改为直连。

## Telegram 与 APNs

升级不会把 Telegram 改为直连。

- Telegram 消息、媒体和前台连接仍由 Rules/Telegram.list 进入 Telegram 代理策略组。
- iOS 后台通知仍由 Rules/APNs.list 进入 ApplePush。
- ApplePush 仍按 Proxy、DIRECT 的顺序回落。
- include-all-networks=true 与 include-apns=true 均保留。
- include-cellular-services=false 只退出 IMS、VoLTE、Wi-Fi Calling、MMS 和可视语音邮件等运营商专用流量，不影响普通 4G/5G 数据或 APNs。

Telegram 的应用数据与 Apple 的通知唤醒链路是两条不同连接。Telegram 必须代理不代表 APNs 也必须永久强制代理，因此 ApplePush 单独保留直连容灾。

## 升级后验证

### 1. 订阅与策略组

- 更新外部资源没有 404、500 或超时。
- AllServer 中能解析到真实节点。
- 香港、台湾、日本、新加坡和美国组能按名称筛选出对应节点。
- NodePool 不出现在普通策略选择页面，这是 hidden=1 的预期结果。
- 若只有 Fail-Closed，先修复订阅输出，不要把 Final 改成 DIRECT。

### 2. 网络切换

按以下顺序测试：

1. 连接 Wi-Fi，打开一个需要代理的网站。
2. 关闭 Wi-Fi，等待蜂窝数据接管，再打开同一网站。
3. 恢复 Wi-Fi，再访问一次。
4. 查看 Surge 最近请求和通知。

预期结果：

- 不再出现“过去一秒处理约 310 个请求”的全订阅集中探测。
- 网络切换后允许出现少量必要探测和真实业务请求。
- Smart 可能在节点故障或恢复时做后台验证，这不是零探测模式。
- 若仍有请求风暴，按主 README 的“网络切换后仍有大量请求”排查发起进程和测试 URL。

### 3. 推送与系统服务

- Telegram 前台消息和媒体正常。
- 锁屏数分钟后，Telegram 通知仍能唤醒设备。
- configuration.ls.apple.com 或同类 ls.apple.com 请求命中 DIRECT。
- 电话、短信、VoLTE、Wi-Fi Calling、MMS 和可视语音邮件保持正常。

### 4. DNS

- dns.alidns.com 使用 Host 中固定的两个 IPv4 与一个 IPv6 引导地址。
- 加密 DNS 仍为 AliDNS HTTPS 与 TLS。
- 普通应用尝试访问 53、853 或 8853 端口时按配置被拦截。
- 不要加入 system DNS 来掩盖订阅服务器或代理节点自身的解析问题。

## 回滚

若设备确实无法使用 Smart：

1. 重新导入升级前备份的私有配置。
2. 保留 R12.15 仓库副本，不要把不兼容的本地改法提交到公开分支。
3. 升级 Surge 或恢复功能更新订阅后再迁移。

不建议用下面这些方法回滚单个字段：

- 把 AllServer 改回包含全订阅的 fallback。
- 把地区组改回全节点 url-test。
- 用 no-alert 隐藏请求风暴。
- 把 interval 调得很大并认为网络切换后不会重测。
- 删除 Fail-Closed 或在 Final 中加入默认 DIRECT。

这些改动要么恢复原问题，要么削弱失败关闭边界。
