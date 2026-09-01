# R13.11 到 R13.12 真实代理诊断迁移说明

R13.11 删除了会产生 TCP 假绿、UDP 必败的本机 SOCKS5 回环，但仍把私人节点放在 `NodePool.policy-path`。这种外置节点能正常分流，却不会成为主配置 `[Proxy]` 的代理实体，因此真机全局网络诊断中的“测试代理策略”和“UDP 代理转发”保持空白。

R13.12 不再接受这个空白结果。私人节点改由本机托管配置 `Private-Proxies.conf` 的 `[Proxy]` 段提供；主配置通过 `#!include Private-Proxies.conf` 关联它，`NodePool` 再用 `include-all-proxies=true` 复用真实节点。凭据仍不进入公开仓库，网络诊断测试的也不再是回环或拒绝策略。

## 关键差异

| 项目 | R13.11 | R13.12 |
| --- | --- | --- |
| 私人节点来源 | `NodePool.policy-path` | `Private-Proxies.conf` 的真实 `[Proxy]` 段 |
| `NodePool` | `REJECT`＋外置策略 | `REJECT`＋`include-all-proxies=true` |
| 全局代理诊断 | 空白 | 显示真实代理 HTTP 探针结果 |
| 全局 UDP 诊断 | 空白 | 显示真实成功或明确失败 |
| 本机回环代理 | 禁止 | 继续禁止 |
| 空源行为 | 显式 `REJECT` | 显式 `REJECT`；关联文件缺失时配置直接报错 |
| 自动组 | 10 个带 `REJECT` 的 `url-test` | 不变 |
| 活动规则 / 策略组 | 142 / 30 | 142 / 30 |
| 运行锁 | schema 25 | schema 26 |
| 故障注入 | 133 | 133 |
| Sub-Store 转换器测试 | 无 | 7 项 |
| 完整包 | `Surge-R13.11-Complete-No-Embedded-20260831.zip` | `Surge-R13.12-Complete-No-Embedded-20260901.zip` |

## 升级步骤

1. 保留当前私人订阅或 Sub-Store 组合订阅地址，但不要把它提交到仓库。
2. 若服务商直接提供完整 Surge 托管配置，在 Surge 中安装后将文件名保存为 `Private-Proxies.conf`，确认其中有 `[Proxy]` 与真实节点，然后跳到第 6 步。
3. 若使用 Sub-Store，在对应组合订阅的最后增加 `Response Transformer`，脚本 URL 为：

   ```text
   https://raw.githubusercontent.com/shenjlngbIng/surge/r13.12-20260901/Scripts/SubStore-Surge-Profile.js
   ```

4. 给原 Surge 输出链接加入 `surge-profile=1`。例如：

   ```text
   http://sub.store/download/collection/Surge/Surge?surge-profile=1
   ```

5. 用 Safari 打开该地址并交给 Surge 安装，文件名必须为 `Private-Proxies.conf`。确认首行含 `#!MANAGED-CONFIG`，且 `[Proxy]` 下存在至少一个真实代理。
6. 完整导入 R13.12 `Surge.conf`，不要只复制策略组或规则段。
7. 打开 `NodePool`，确认第一项为 `REJECT`，后面为 `Private-Proxies.conf` 中的真实节点；再把 `Proxy` 选择为 `Auto`。
8. 运行网络诊断。“测试代理策略”不应为空；“UDP 代理转发”应给出成功或明确失败，而不是空白。
9. 若 UDP 失败，检查被测协议是否支持 UDP、Shadowsocks/SOCKS5 是否含 `udp-relay=true`，以及服务端是否真的开放 UDP。不得把不支持行为改为 `DIRECT`。

## 预期事件

- 删除、改名或未先安装 `Private-Proxies.conf` 时，R13.12 主配置应明确报告关联文件缺失。这是防止空节点悄悄运行的失败关闭行为。
- `Smart ... SUBSTITUTE` 不应出现，因为 R13.12 没有 Smart 组。
- 本机 HTTP/SOCKS5 监听 INFO 事件仍可能出现，那是 Surge 自身服务，不是诊断桥。
- `include-all-networks` 警告仍会出现；该选项为 APNs 与防旁路保留。
- UDP 行为由真实节点协议、订阅参数和服务器能力共同决定。配置只能让结果真实显示，不能把不支持的服务器变成支持。

## 回退

不建议回退到 R13.11，因为它的代理与 UDP 全局诊断必然空白。更不能回退到 R13.10 的本机回环桥。若必须回退，应恢复整套对应版本文件、运行锁、审计器、清单和校验和，不能跨版本混用。
