# xiaomi_qianbao_VIP

面向 **青龙面板（QingLong）** 的小米钱包每日任务脚本。

本项目基于 `kai648846760/xiaomiwallet` 的核心扫码登录与小米钱包任务逻辑进行青龙适配，并增加：

- 青龙订阅自动生成任务
- 一键扫码登录
- 登录凭证持久化
- 每日自动任务
- 青龙通知
- MI / VIP 日志 Banner
- 随机延迟
- 随机延迟环境变量自动创建
- **青龙 v2.17.12 兼容**

> 建议仅在自己的本地青龙环境中使用。自动化行为可能触发小米账号风控，请自行评估风险。

---

# 一、当前版本为什么改成 JS 入口？

青龙 v2.17.12 拉取仓库时，会先根据 `RepoFileExtensions` / 订阅中的“文件后缀”筛选文件，然后才生成定时任务。

如果青龙全局配置只允许 `js`，即使 Git 仓库成功拉取，`.py` 文件也不会进入任务清单，日志就会出现：

```text
开始拉取仓库...
拉取成功...
执行结束...
```

但完全没有：

```text
检测到有新的定时任务
开始尝试自动添加定时任务
```

因此当前版本改为：

```text
ZzzHe_xiaomi_wallet_daily.js   ← 青龙真正识别的每日任务入口
ZzzHe_xiaomi_wallet_login.js   ← 青龙真正识别的扫码任务入口

xiaomi_runtime.cjs             ← 青龙 v2.17.12 兼容层
xiaomi_daily.py                ← 小米钱包每日任务核心
xiaomi_login.py                ← 小米扫码核心
xiaomi_common.py               ← 配置、随机延迟、通知等公共逻辑
```

青龙只负责运行两个 JS 入口；JS 再从青龙仓库目录调用 Python 核心。

---

# 二、青龙最终应生成两个任务

成功拉取后，“定时任务”中应出现：

```text
ZzzHe_小米钱包扫码登录
ZzzHe_小米钱包每日任务
```

| 任务 | Cron | 用途 |
| --- | --- | --- |
| `ZzzHe_小米钱包扫码登录` | `0 0 29 2 *` | 主要手动运行，用于首次登录或刷新凭证 |
| `ZzzHe_小米钱包每日任务` | `37 8 * * *` | 每天 08:37 触发，随机延迟后执行 |

---

# 三、青龙订阅必须这样填写

进入：

```text
青龙面板
→ 订阅管理
→ 新建订阅 / 编辑“小米钱包”
```

填写：

```text
名称：小米钱包
类型：公开仓库
链接：https://github.com/ZzzHe2333/xiaomi_qianbao_VIP.git
分支：main

定时类型：crontab
定时规则：12 12 * * *
```

然后继续填写下面几个关键字段。

## 白名单

```text
^ZzzHe_.*\.js$
```

## 黑名单

留空。

## 依赖文件

留空。

当前 JS 入口会直接从：

```text
/ql/data/repo/ZzzHe2333_xiaomi_qianbao_VIP
```

调用 Python 核心，不需要再通过“依赖文件”复制 Python 文件。

## 文件后缀

**明确填写：**

```text
js
```

不要再填写 `py`。

## 执行前 / 执行后

全部留空。

## 自动添加任务

必须开启：

```text
自动添加任务：开启
```

建议同时：

```text
自动删除任务：开启
```

### 最终完整模板

```text
名称：小米钱包
类型：公开仓库
链接：https://github.com/ZzzHe2333/xiaomi_qianbao_VIP.git
分支：main

定时类型：crontab
定时规则：12 12 * * *

白名单：^ZzzHe_.*\.js$
黑名单：
依赖文件：
文件后缀：js

执行前：
执行后：
代理：

自动添加任务：开启
自动删除任务：开启
```

---

# 四、修改完订阅后必须重新运行一次

保存后：

```text
订阅管理
→ 小米钱包
→ 运行
```

正常日志应出现：

```text
拉取 ZzzHe2333_xiaomi_qianbao_VIP 成功...

检测到有新的定时任务:
ZzzHe2333_xiaomi_qianbao_VIP/ZzzHe_xiaomi_wallet_daily.js
ZzzHe2333_xiaomi_qianbao_VIP/ZzzHe_xiaomi_wallet_login.js

开始尝试自动添加定时任务...
```

随后在：

```text
青龙 → 定时任务
```

看到：

```text
ZzzHe_小米钱包每日任务
ZzzHe_小米钱包扫码登录
```

---

# 五、任务启动日志

两个任务执行时都会先打印黑白方块组成的：

```text
MI

VIP
```

然后打印：

```text
任务名称：ZzzHe_...
当前时间：YYYY-MM-DD HH:MM:SS
项目地址：https://github.com/ZzzHe2333/xiaomi_qianbao_VIP
项目说明：本项目永久免费开源，欢迎学习、使用和 Star，请勿付费购买。
```

---

# 六、随机延迟环境变量会自动创建

变量名称：

```text
ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi
```

第一次运行任意一个 `ZzzHe_...` 任务时，脚本会先检查青龙环境变量。

如果不存在，会自动创建：

```text
名称：ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi
值：30
备注：随机延迟
```

青龙 v2.17.12 没有新版的 `QLAPI.getEnvs/createEnv`，因此当前兼容层会使用青龙自身的内部 Open API 完成检测和创建，不直接修改数据库文件。

如果变量已经存在，则保持用户原值，不覆盖。

如果变量存在但被禁用，则不重复创建，也不自动启用；本次临时使用默认值 `30`。

---

# 七、随机延迟规则

变量值记为 `A`，单位默认是分钟。

要求：

```text
A 必须是正整数
1 <= A <= 360
```

不满足条件时，本次任务按：

```text
A = 30
```

执行。

实际随机睡眠秒数满足：

```text
0.3 × A × 60 <= 实际睡眠秒数 <= A × 60
```

即：

```text
18 × A <= 实际睡眠秒数 <= 60 × A
```

例如：

```text
A = 10
```

则实际等待：

```text
180 ~ 600 秒
```

默认：

```text
A = 30
```

则实际等待：

```text
540 ~ 1800 秒
= 9 ~ 30 分钟
```

以下均视为非法值并按 `30`：

```text
0
-1
10.5
abc
361
空值
```

---

# 八、随机等待期间不会像卡死

任务开始随机等待时会打印：

```text
【随机延迟】
环境变量：ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi
有效 A 值：10 分钟
随机范围：180-600 秒
本次随机睡眠：xxx 秒
预计开始时间：2026-xx-xx xx:xx:xx
```

等待过程中每约 30 秒打印一次：

```text
⏳ 当前时间：2026-xx-xx 08:42:30 | 预计开始：2026-xx-xx 08:47:13 | 剩余约 283 秒
```

直到：

```text
▶ 随机延迟结束，开始执行：2026-xx-xx xx:xx:xx
```

---

# 九、第一次扫码登录

任务生成后找到：

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
→ 检查/创建随机延迟变量
→ 随机等待
→ 输出二维码
→ 手机扫码
→ 手机确认
→ 保存登录凭证
```

如果测试阶段不想等待太久，可以把：

```text
ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi
```

改成：

```text
1
```

则只随机等待：

```text
18 ~ 60 秒
```

---

# 十、登录凭证保存位置

扫码成功后默认保存：

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

凭证目录和 Git 仓库目录分开，所以正常更新订阅不会清除登录状态。

`passToken`、`securityToken` 属于敏感凭证，不要公开、发群或提交到 Issue。

---

# 十一、每日任务

登录完成后可以手动运行：

```text
ZzzHe_小米钱包每日任务
```

默认 Cron：

```cron
37 8 * * *
```

即每天 08:37 触发。

例如默认 `A=30`，核心任务实际开始时间大约为：

```text
08:46 ~ 09:07
```

---

# 十二、青龙通知

每日任务执行结束后会尝试调用青龙通知。

当前 v2.17.12 JS 兼容层会在转调 Python 时补齐青龙 Python preload 和 `notify.py` 路径，因此可以继续复用青龙已有通知配置。

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

添加第二个账号：

```text
XIAOMI_WALLET_ALIAS=xiaomi_2
```

然后运行：

```text
ZzzHe_小米钱包扫码登录
```

添加第三个账号：

```text
XIAOMI_WALLET_ALIAS=xiaomi_3
```

每日任务会依次处理保存的所有账号。

---

# 十四、如果还是没有生成任务

先看订阅日志。

## 情况 1：只有“拉取成功”，没有“检测到新的定时任务”

检查：

```text
白名单：^ZzzHe_.*\.js$
文件后缀：js
```

不要填写 `py`。

## 情况 2：出现“检测到新的定时任务”，但没有“开始尝试自动添加”

检查：

```text
自动添加任务：开启
```

## 情况 3：已经开始添加，但返回 API 错误

把从：

```text
检测到有新的定时任务
```

到执行结束的完整日志提交到 Issue 或用于排查。

---

# 十五、最简使用流程

```text
① 编辑订阅

白名单：^ZzzHe_.*\.js$
依赖文件：留空
文件后缀：js
自动添加任务：开启
自动删除任务：开启

        ↓

② 保存并手动运行一次订阅

        ↓

③ 定时任务中出现：
ZzzHe_小米钱包扫码登录
ZzzHe_小米钱包每日任务

        ↓

④ 运行扫码登录任务

        ↓

⑤ 第一次运行自动创建：
ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi=30
备注：随机延迟

        ↓

⑥ 扫码确认

        ↓

⑦ 手动测试每日任务

        ↓

⑧ 以后每天自动执行
```

---

# 项目地址

```text
https://github.com/ZzzHe2333/xiaomi_qianbao_VIP
```

**本项目永久免费开源，欢迎学习、使用和 Star，请勿付费购买。**

核心逻辑来源：

```text
kai648846760/xiaomiwallet
```

详细来源说明见 `NOTICE.md`。

---

# 免责声明

本项目仅用于个人学习、技术研究和个人账号自动化。小米官方接口、活动规则和风控策略可能随时变化，本项目不保证长期有效。使用者应自行承担因自动化操作、账号异常、接口变化等产生的风险。
