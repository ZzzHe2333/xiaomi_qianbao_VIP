# xiaomi_qianbao_VIP

面向 **青龙面板（QingLong）** 的小米钱包每日任务脚本。

本项目基于 `kai648846760/xiaomiwallet` 的核心登录和小米钱包任务逻辑进行青龙适配，并增加青龙订阅、扫码登录、持久化凭证、青龙通知、启动 Banner 和随机延迟功能。

> 建议仅在自己的本地青龙环境使用。自动化操作可能触发小米账号风控，请自行评估账号风险。

---

# 一、青龙最终会生成两个任务

正确拉取后，青龙“定时任务”中应该出现：

```text
ZzzHe_小米钱包扫码登录
ZzzHe_小米钱包每日任务
```

对应规则：

| 任务 | Cron | 用途 |
| --- | --- | --- |
| `ZzzHe_小米钱包扫码登录` | `0 0 29 2 *` | 主要手动运行，用于扫码登录/刷新凭证 |
| `ZzzHe_小米钱包每日任务` | `37 8 * * *` | 每天 08:37 触发，随机延迟后执行每日任务 |

**两个生成任务在真正执行核心逻辑前都会先打印项目 Banner，并执行同一套随机延迟。**

因此：

- 每日任务：Cron 到点后先随机等待，再请求小米接口。
- 扫码登录：手动点击“运行”后也会先随机等待，等待结束后才显示二维码。

如果只是测试或想快速扫码，可以临时把随机延迟 A 设置为 `1`，这样只需随机等待 `18~60 秒`。

---

# 二、青龙订阅填写方法

进入：

```text
青龙面板
→ 订阅管理
→ 新建订阅 / 编辑订阅
```

按照下面填写：

```text
名称：小米钱包
类型：公开仓库
链接：https://github.com/ZzzHe2333/xiaomi_qianbao_VIP.git
分支：main

定时类型：crontab
定时规则：12 12 * * *

白名单：^ZzzHe_
黑名单：
依赖文件：xiaomi_common.py|xiaomi_daily.py|xiaomi_login.py
文件后缀：py

执行前：
执行后：
代理：

自动添加任务：开启
自动删除任务：开启
```

其中最关键的几项：

```text
白名单：^ZzzHe_
依赖文件：xiaomi_common.py|xiaomi_daily.py|xiaomi_login.py
文件后缀：py
自动添加任务：开启
```

仓库结构：

```text
ZzzHe_xiaomi_wallet_login.py   → 青龙扫码登录任务入口
ZzzHe_xiaomi_wallet_daily.py   → 青龙每日任务入口

xiaomi_login.py                → 登录核心代码（依赖）
xiaomi_daily.py                → 每日任务核心代码（依赖）
xiaomi_common.py               → 公共配置、Banner、随机延迟、青龙通知（依赖）
```

保存后务必手动运行一次订阅：

```text
订阅管理
→ 小米钱包
→ 运行
```

随后进入“定时任务”，确认出现：

```text
ZzzHe_小米钱包扫码登录
ZzzHe_小米钱包每日任务
```

---

# 三、任务启动日志 Banner

两个任务启动时都会先在青龙日志中打印项目 Banner。

Banner 使用黑白方块绘制：

```text
MI

VIP
```

随后打印：

```text
任务名称
当前时间
项目地址：https://github.com/ZzzHe2333/xiaomi_qianbao_VIP
项目说明：本项目永久免费开源，欢迎学习、使用和 Star，请勿付费购买。
```

这样可以直接从日志确认当前运行的是本项目脚本，并保留项目来源。

---

# 四、随机延迟环境变量【重要】

两个 `ZzzHe_...` 任务都会读取下面这个青龙环境变量：

```text
ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi
```

这个变量表示 **最大随机延迟分钟数 A**。

## A 的合法范围

A 必须满足：

```text
A 是十进制正整数
1 <= A <= 360
```

合法示例：

```text
1
10
30
60
120
360
```

以下属于非法值：

```text
0
-1
10.5
abc
361
空值
```

如果：

- 没有创建这个环境变量
- 环境变量为空
- A 不是正整数
- A > 360
- A <= 0

脚本都会自动回退到：

```text
A = 30
```

即默认最大随机延迟为 30 分钟。

---

# 五、随机睡眠公式

读取到有效 A 后，实际睡眠时间在下面区间随机选择一个整数秒数：

```text
0.3 × A × 60 <= 实际睡眠秒数 <= A × 60
```

由于 A 是整数，也可以写成：

```text
18 × A <= 实际睡眠秒数 <= 60 × A
```

## 示例：A = 10

如果设置：

```text
ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi=10
```

则：

```text
最短延迟 = 0.3 × 10 × 60 = 180 秒
最长延迟 = 10 × 60 = 600 秒
```

实际每次运行随机选择：

```text
180 ~ 600 秒
```

例如某次可能是 `347 秒`，下一次可能是 `581 秒`。

## 默认 A = 30

没有设置变量或变量无效时：

```text
A = 30
```

随机范围：

```text
540 ~ 1800 秒
```

也就是：

```text
9 ~ 30 分钟
```

---

# 六、如何在青龙设置随机延迟

进入：

```text
青龙面板
→ 环境变量
→ 新建变量
```

例如最大随机延迟 10 分钟：

```text
名称：ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi
值：10
```

例如最大随机延迟 60 分钟：

```text
名称：ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi
值：60
```

实际随机范围就是：

```text
18 分钟 ~ 60 分钟
```

最大允许：

```text
360
```

如果填写 `361`、`0`、负数、小数或其他非法值，统一回退到：

```text
30
```

---

# 七、随机等待期间日志不会像“卡死”

随机睡眠开始时，日志会打印：

```text
【随机延迟】
环境变量：ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi
有效 A 值：10 分钟
随机范围：180-600 秒
本次随机睡眠：xxx 秒
预计开始时间：2026-xx-xx xx:xx:xx
```

等待期间，脚本会 **每 30 秒打印一次** 当前状态：

```text
⏳ 当前时间：2026-xx-xx 08:42:30 | 预计开始：2026-xx-xx 08:47:13 | 剩余约 283 秒
```

约 30 秒后继续：

```text
⏳ 当前时间：2026-xx-xx 08:43:00 | 预计开始：2026-xx-xx 08:47:13 | 剩余约 253 秒
```

直到随机延迟结束：

```text
▶ 随机延迟结束，开始执行：2026-xx-xx xx:xx:xx
```

然后才进入对应核心逻辑。

---

# 八、扫码登录

找到：

```text
ZzzHe_小米钱包扫码登录
```

点击：

```text
运行
→ 日志
```

执行顺序：

```text
打印 MI / VIP Banner
→ 读取随机延迟环境变量
→ 随机等待
→ 每 30 秒打印状态
→ 等待结束
→ 生成二维码
→ 手机扫码确认
```

默认未设置随机延迟变量时，扫码任务也会等待 `9~30 分钟`。

如果准备立即扫码，建议临时设置：

```text
ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi=1
```

此时只随机等待：

```text
18 ~ 60 秒
```

扫码成功后日志类似：

```text
✅ 登录成功，长效凭证已写入青龙持久化配置目录。
小米 User ID: xxxxxxxx
passToken/securityToken 不会输出到日志。
```

如果二维码在青龙日志中无法识别，脚本还会打印对应登录链接，可复制到浏览器打开后再扫码。

---

# 九、账号凭证保存位置

扫码成功后默认保存到：

```text
/ql/data/config/xiaomi_qianbao_VIP/xiaomiconfig.json
```

保存内容包括：

```text
账号别名
userId
passToken
securityToken
更新时间
```

这个目录位于 Git 仓库目录之外，所以正常重新拉取订阅不会覆盖账号登录状态。

`passToken` 和 `securityToken` 属于敏感账号凭证，不要上传 GitHub、发群、截图公开或提交到 Issue。

---

# 十、测试每日任务

扫码登录完成后，可以手动运行：

```text
ZzzHe_小米钱包每日任务
```

执行顺序：

```text
打印 MI / VIP Banner
→ 读取随机延迟环境变量
→ 随机等待
→ 每 30 秒输出等待状态
→ 获取临时会话 Cookie
→ 执行钱包任务
→ 查询奖励
→ 青龙通知
```

如果测试时不想等待太久，可以临时使用：

```text
ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi=1
```

测试完成后再改成你希望的 A。

---

# 十一、每天自动执行

每日任务默认 Cron：

```cron
37 8 * * *
```

表示每天 `08:37` 由青龙触发。

例如 A=30 时，真正开始核心任务大约在：

```text
08:46 ~ 09:07
```

例如 A=10 时，大约在：

```text
08:40 ~ 08:47
```

如果修改青龙中的 Cron，随机延迟会从新的触发时间开始计算。

---

# 十二、青龙通知

每日任务执行结束后会尝试调用：

```python
QLAPI.notify(title, content)
```

因此可以复用青龙已经配置的通知渠道。

关闭通知：

```text
XIAOMI_WALLET_NOTIFY=0
```

开启：

```text
XIAOMI_WALLET_NOTIFY=1
```

默认开启。

---

# 十三、多账号

默认账号别名：

```text
xiaomi_1
```

添加第二个账号时，在青龙环境变量添加：

```text
名称：XIAOMI_WALLET_ALIAS
值：xiaomi_2
```

然后运行：

```text
ZzzHe_小米钱包扫码登录
```

添加第三个账号：

```text
XIAOMI_WALLET_ALIAS=xiaomi_3
```

再次扫码即可。

每日任务会依次执行所有保存账号。

---

# 十四、常用环境变量汇总

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi` | `30` | 两个生成任务启动核心逻辑前的最大随机延迟 A，单位分钟，只允许 `1-360` 的正整数 |
| `XIAOMI_WALLET_ALIAS` | `xiaomi_1` | 扫码登录账号别名 |
| `XIAOMI_WALLET_CONFIG` | `/ql/data/config/xiaomi_qianbao_VIP/xiaomiconfig.json` | 凭证文件位置 |
| `XIAOMI_WALLET_NOTIFY` | `1` | 是否启用青龙通知 |
| `XIAOMI_WALLET_ACCOUNT_DELAY_MAX` | `15` | 多账号之间额外随机等待的最大秒数 |

随机延迟变量再次强调：

```text
ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi
```

必须满足：

```text
1 <= A <= 360
且 A 为正整数
```

否则自动使用：

```text
A = 30
```

---

# 十五、如果拉取后没有生成任务

检查订阅：

```text
白名单：^ZzzHe_
依赖文件：xiaomi_common.py|xiaomi_daily.py|xiaomi_login.py
文件后缀：py
自动添加任务：开启
```

然后手动重新运行一次订阅。

正常应该生成：

```text
ZzzHe_小米钱包扫码登录
ZzzHe_小米钱包每日任务
```

---

# 十六、最简使用流程

```text
① 青龙订阅拉取仓库

② 确认生成两个 ZzzHe_ 任务

③ 环境变量按需设置：
   ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi=30

④ 运行 ZzzHe_小米钱包扫码登录
   → Banner
   → 随机延迟
   → 二维码
   → 手机确认

⑤ 运行 ZzzHe_小米钱包每日任务测试
   → Banner
   → 随机延迟
   → 钱包任务
   → 青龙通知

⑥ 以后每天自动执行
```

---

# 项目地址

```text
https://github.com/ZzzHe2333/xiaomi_qianbao_VIP
```

**本项目永久免费开源，欢迎学习、使用和 Star，请勿付费购买。**

核心小米钱包接口和扫码逻辑来源于：

```text
kai648846760/xiaomiwallet
```

详细来源说明见 `NOTICE.md`。

---

# 免责声明

本项目仅用于个人学习、技术研究和个人账号自动化。小米官方接口、活动规则和风控策略可能随时变化，本项目不保证长期有效。使用者应自行承担因自动化操作、账号异常、接口变化等产生的风险。
