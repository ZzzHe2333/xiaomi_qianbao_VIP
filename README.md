# xiaomi_qianbao_VIP

面向 **青龙面板（QingLong）** 的小米钱包每日任务脚本。

基于 `kai648846760/xiaomiwallet` 的核心扫码登录与小米钱包任务逻辑进行青龙适配，当前主要支持：

- 青龙 v2.17.12 订阅自动生成任务
- 一键扫码登录，**扫码任务不随机延迟**
- 多账号 Cookie 环境变量：`ck1 / ck2 / ck3 ...`
- 多账号严格串行执行
- 每日任务启动随机延迟
- 多账号之间随机间隔
- 延迟环境变量自动创建
- 青龙通知
- `XIAOMI / QIANBAO` 黑白方块日志 Banner

> 建议仅在自己的本地青龙环境中使用。自动化行为可能触发账号风控，请自行评估风险。

---

## 1. 青龙会生成两个任务

成功拉取后，“定时任务”中应出现：

```text
ZzzHe_小米钱包扫码登录
ZzzHe_小米钱包每日任务
```

| 任务 | Cron | 说明 |
| --- | --- | --- |
| `ZzzHe_小米钱包扫码登录` | `0 0 29 2 *` | 主要手动运行，运行后立即生成二维码，不进行随机延迟 |
| `ZzzHe_小米钱包每日任务` | `37 8 * * *` | 每天 08:37 触发，先进行启动随机延迟，再串行执行所有账号 |

青龙真正识别的是两个 JS 入口：

```text
ZzzHe_xiaomi_wallet_daily.js
ZzzHe_xiaomi_wallet_login.js
```

JS 再调用仓库中的 Python 核心代码，因此兼容青龙 v2.17.12。

---

## 2. 订阅配置

进入：

```text
青龙面板
→ 订阅管理
→ 新建订阅
```

建议填写：

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

保存后手动运行一次订阅。

正常日志应包含：

```text
检测到有新的定时任务:
ZzzHe2333_xiaomi_qianbao_VIP/ZzzHe_xiaomi_wallet_daily.js
ZzzHe2333_xiaomi_qianbao_VIP/ZzzHe_xiaomi_wallet_login.js

开始尝试自动添加定时任务...
ZzzHe_小米钱包每日任务 -> 添加成功
ZzzHe_小米钱包扫码登录 -> 添加成功
```

---

## 3. 日志 Banner

两个任务启动时都会先用黑白方块打印：

```text
XIAOMI

QIANBAO
```

随后打印：

```text
任务名称
当前时间
项目地址：https://github.com/ZzzHe2333/xiaomi_qianbao_VIP
项目说明：本项目永久免费开源，欢迎学习、使用和 Star，请勿付费购买。
```

---

## 4. 扫码登录：不设置随机延迟

运行：

```text
ZzzHe_小米钱包扫码登录
```

执行顺序：

```text
打印 XIAOMI / QIANBAO Banner
        ↓
直接请求小米二维码
        ↓
日志显示二维码
        ↓
手机扫码确认
        ↓
自动保存为青龙 ck 环境变量
```

**扫码登录任务不会读取 `suijiyanchi`，也不会在显示二维码之前等待。**

---

## 5. 多账号 Cookie 环境变量

登录凭证不再以 `xiaomiconfig.json` 作为主要存储方式。

新版本使用：

```text
ZzzHe2333_xiaomi_qianbao_VIP_ck1
ZzzHe2333_xiaomi_qianbao_VIP_ck2
ZzzHe2333_xiaomi_qianbao_VIP_ck3
ZzzHe2333_xiaomi_qianbao_VIP_ck4
...
```

值的内部格式类似：

```text
userId=xxxxxxxx; passToken=xxxxxxxx; securityToken=xxxxxxxx
```

这些值属于敏感账号凭证，不要截图公开、发群或提交到 Issue。

### 添加多个账号

第一次运行扫码登录并登录账号 A：

```text
自动创建：ZzzHe2333_xiaomi_qianbao_VIP_ck1
```

再次运行扫码任务并登录账号 B：

```text
自动创建：ZzzHe2333_xiaomi_qianbao_VIP_ck2
```

再次运行并登录账号 C：

```text
自动创建：ZzzHe2333_xiaomi_qianbao_VIP_ck3
```

依此类推。

### 重复扫码同一个账号

脚本会比较 `userId`。

如果该账号已经存在，例如原本在：

```text
ZzzHe2333_xiaomi_qianbao_VIP_ck2
```

再次扫码同一个小米账号时会更新 `ck2`，不会故意新建重复 `ck3`。

### 旧版配置迁移

如果没有任何 `ck1/ck2...`，但检测到旧版：

```text
/ql/data/config/xiaomi_qianbao_VIP/xiaomiconfig.json
```

每日任务会尝试把旧账号自动迁移为新的 `ckN` 环境变量。

---

## 6. 每日任务启动随机延迟 A

变量：

```text
ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi
```

如果不存在，每日任务会尝试自动创建：

```text
名称：ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi
值：30
备注：随机延迟
```

变量值记为 `A`，单位：**分钟**。

必须满足：

```text
A 为正整数
1 <= A <= 360
```

否则本次运行按默认：

```text
A = 30
```

随机等待公式：

```text
0.3 × A × 60 <= 实际睡眠秒数 <= A × 60
```

即：

```text
18A ～ 60A 秒
```

例如：

```text
A = 10
→ 180 ～ 600 秒
```

默认：

```text
A = 30
→ 540 ～ 1800 秒
→ 9 ～ 30 分钟
```

等待过程中每约 30 秒打印一次当前时间、预计开始时间和剩余秒数。

**该变量只用于每日任务，不用于扫码登录。**

---

## 7. 多账号间隔延迟 B

变量：

```text
ZzzHe2333_xiaomi_qianbao_VIP_jiangeyanchi
```

如果不存在，在需要执行多账号间隔时会尝试自动创建：

```text
名称：ZzzHe2333_xiaomi_qianbao_VIP_jiangeyanchi
值：3
备注：多账号间隔延迟（分钟）
```

变量值记为 `B`，单位：**分钟**。

必须满足：

```text
B 为正整数
1 <= B < 60
```

合法范围即：

```text
1 ～ 59
```

以下均为非法：

```text
0
-1
1.5
abc
60
61
空值
```

非法时本次运行按：

```text
B = 3
```

账号间实际随机等待：

```text
0.5 × B × 60 <= 实际等待秒数 <= B × 60
```

即：

```text
30B ～ 60B 秒
```

例如：

```text
B = 3
→ 90 ～ 180 秒

B = 10
→ 300 ～ 600 秒
→ 5 ～ 10 分钟
```

---

## 8. 多账号严格串行执行

每日任务不会并发执行账号。

假设存在：

```text
ck1
ck2
ck3
```

流程严格为：

```text
每日任务启动
        ↓
启动随机延迟 A
        ↓
ck1 开始
        ↓
ck1 完整执行结束
        ↓
随机等待 30B ～ 60B 秒
        ↓
ck2 开始
        ↓
ck2 完整执行结束
        ↓
随机等待 30B ～ 60B 秒
        ↓
ck3 开始
        ↓
ck3 完整执行结束
        ↓
汇总通知
```

核心原则：

> **前一个账号必须完整返回后，才会计算账号间延迟；账号间延迟结束后，下一个账号才开始。**

因此不会出现 `ck1` 与 `ck2` 同时请求小米接口的情况。

单账号时不会执行账号间隔等待。

账号间等待同样每约 30 秒输出一次日志，避免看起来像程序卡死。

---

## 9. 第一次使用建议

### 第一步：运行扫码任务

```text
ZzzHe_小米钱包扫码登录
```

现在不会随机延迟，应很快看到二维码。

扫码成功后进入：

```text
青龙 → 环境变量
```

确认出现：

```text
ZzzHe2333_xiaomi_qianbao_VIP_ck1
```

### 第二步：需要多账号就继续扫码

再次运行相同扫码任务，登录第二个账号。

确认出现：

```text
ZzzHe2333_xiaomi_qianbao_VIP_ck2
```

第三个账号同理。

### 第三步：测试每日任务

为了测试时不用等太久，可以临时设置：

```text
ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi=1
ZzzHe2333_xiaomi_qianbao_VIP_jiangeyanchi=1
```

此时：

```text
启动随机延迟：18 ～ 60 秒
账号间随机延迟：30 ～ 60 秒
```

测试完成后再改成你希望的值。

---

## 10. 每日自动执行

默认 Cron：

```cron
37 8 * * *
```

即每天 `08:37` 由青龙触发。

实际核心任务开始时间还会受到 `A` 的启动随机延迟影响。

例如默认 `A=30`：

```text
08:37 触发
→ 随机等待 9 ～ 30 分钟
→ 大约 08:46 ～ 09:07 开始 ck1
```

后续账号再按 `B` 串行间隔。

---

## 11. 青龙通知

每日任务全部账号执行结束后会汇总通知。

默认启用：

```text
XIAOMI_WALLET_NOTIFY=1
```

关闭：

```text
XIAOMI_WALLET_NOTIFY=0
```

会复用青龙本身已经配置的通知渠道。

---

## 12. 环境变量汇总

| 环境变量 | 默认值 | 单位 | 作用 | 合法范围 |
| --- | ---: | --- | --- | --- |
| `ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi` | `30` | 分钟 | 每日任务启动随机延迟 | `1-360` 正整数 |
| `ZzzHe2333_xiaomi_qianbao_VIP_jiangeyanchi` | `3` | 分钟 | 多账号之间的串行随机间隔 | `1-59` 正整数 |
| `ZzzHe2333_xiaomi_qianbao_VIP_ck1` | 无 | Cookie | 第 1 个小米账号 | 自动创建 |
| `ZzzHe2333_xiaomi_qianbao_VIP_ck2` | 无 | Cookie | 第 2 个小米账号 | 自动创建 |
| `ZzzHe2333_xiaomi_qianbao_VIP_ck3...` | 无 | Cookie | 更多小米账号 | 自动创建 |
| `XIAOMI_WALLET_NOTIFY` | `1` | - | 是否启用青龙通知 | `0/1` |

---

## 13. 当前仓库结构

```text
xiaomi_qianbao_VIP/
├── ZzzHe_xiaomi_wallet_daily.js   # 青龙每日任务入口
├── ZzzHe_xiaomi_wallet_login.js   # 青龙扫码入口
├── xiaomi_runtime.cjs             # v2.17.12 运行兼容层 / Banner
├── xiaomi_common.py               # 青龙环境变量、ck、多账号延迟、通知
├── xiaomi_daily.py                # 小米钱包每日任务核心
├── xiaomi_login.py                # 小米扫码登录核心
├── requirements.txt
├── NOTICE.md
├── LICENSE
└── README.md
```

---

## 14. 项目地址与来源

项目地址：

```text
https://github.com/ZzzHe2333/xiaomi_qianbao_VIP
```

**本项目永久免费开源，欢迎学习、使用和 Star，请勿付费购买。**

核心小米钱包接口与扫码逻辑来源于：

```text
kai648846760/xiaomiwallet
```

详细来源说明见 `NOTICE.md`。

---

## 免责声明

本项目仅用于个人学习、技术研究和个人账号自动化。小米官方接口、活动规则及风控策略可能随时变化，本项目不保证长期有效。使用者应自行承担因自动化操作、接口变化、账号异常等产生的风险。
