# xiaomi_qianbao_VIP

面向 **青龙面板（QingLong）** 的小米钱包每日任务脚本。

本项目基于 `kai648846760/xiaomiwallet` 的核心登录和小米钱包任务逻辑进行青龙适配。

当前青龙版采用：

```text
ZzzHe_xiaomi_wallet_login.py   → 青龙扫码登录任务入口
ZzzHe_xiaomi_wallet_daily.py   → 青龙每日任务入口

xiaomi_login.py                → 登录核心代码（依赖文件）
xiaomi_daily.py                → 每日任务核心代码（依赖文件）
xiaomi_common.py               → 配置/通知公共代码（依赖文件）
```

这样可以避免青龙把核心模块也错误识别为定时任务。

> 建议仅在自己的本地青龙环境使用。自动化操作可能触发小米账号风控，请自行评估账号风险。

---

# 一、最终会生成哪两个任务？

正确拉取后，青龙“定时任务”中应该出现：

```text
ZzzHe_小米钱包扫码登录
ZzzHe_小米钱包每日任务
```

对应规则：

| 任务 | Cron | 用途 |
| --- | --- | --- |
| `ZzzHe_小米钱包扫码登录` | `0 0 29 2 *` | 主要手动运行，用于扫码登录/刷新凭证 |
| `ZzzHe_小米钱包每日任务` | `37 8 * * *` | 每天 08:37 自动执行 |

扫码任务使用一个合法但极低频的 Cron，是为了让各版本青龙都能正常解析；实际使用时直接手动点击“运行”。

---

# 二、青龙订阅：请严格按下面填写

进入：

```text
青龙面板
→ 订阅管理
→ 新建订阅 / 编辑订阅
```

## 1. 上半部分

按照下面填写：

| 青龙字段 | 填写内容 |
| --- | --- |
| 名称 | `小米钱包` |
| 类型 | `公开仓库` |
| 链接 | `https://github.com/ZzzHe2333/xiaomi_qianbao_VIP.git` |
| 分支 | `main` |
| 定时类型 | `crontab` |
| 定时规则 | `12 12 * * *` 或你自己的更新仓库时间 |

这里的订阅定时规则只代表：

```text
青龙什么时候重新拉取 GitHub 仓库
```

不是小米钱包任务执行时间。

---

# 三、最关键：白名单、依赖文件、文件后缀

这一部分必须按下面填写。

## 白名单

填写：

```text
^ZzzHe_
```

作用：只把下面两个文件识别为真正的青龙任务：

```text
ZzzHe_xiaomi_wallet_login.py
ZzzHe_xiaomi_wallet_daily.py
```

## 黑名单

留空：

```text

```

## 依赖文件

填写：

```text
xiaomi_common.py|xiaomi_daily.py|xiaomi_login.py
```

这些文件会被复制到任务脚本目录，但不会被当成独立任务创建。

## 文件后缀

明确填写：

```text
py
```

不要留空。

这样可以避免你青龙全局 `RepoFileExtensions` 设置不同导致 Python 文件没有进入脚本清单。

---

# 四、继续向下滚动：必须打开“自动添加任务”

在你看到的“文件后缀”下面还没有到底。

继续往下滚，会依次看到：

```text
执行前
执行后
代理
自动添加任务
自动删除任务
```

请设置：

```text
执行前：留空
执行后：留空
代理：按需，正常本地能访问 GitHub 就留空

自动添加任务：开启
自动删除任务：开启（建议）
```

其中最重要的是：

```text
自动添加任务 = 开启
```

如果关闭，青龙只会把仓库拉下来，不会在“定时任务”页面创建任务。

---

# 五、完整填写模板

你的订阅建议最终是：

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

---

# 六、保存后重新运行订阅

配置完成后：

```text
订阅管理
→ 小米钱包
→ 运行
```

不要只点“保存”，要手动运行一次订阅。

正常日志应该包含类似：

```text
拉取 ZzzHe2333_xiaomi_qianbao_VIP 成功...

检测到有新的定时任务:
ZzzHe2333_xiaomi_qianbao_VIP/ZzzHe_xiaomi_wallet_daily.py
ZzzHe2333_xiaomi_qianbao_VIP/ZzzHe_xiaomi_wallet_login.py

开始尝试自动添加定时任务...
```

随后进入：

```text
青龙面板
→ 定时任务
```

应该能看到：

```text
ZzzHe_小米钱包每日任务
ZzzHe_小米钱包扫码登录
```

---

# 七、为什么之前拉库成功却没有任务？

青龙的订阅机制分两步：

```text
Git clone 拉取仓库
        ↓
生成脚本清单
        ↓
根据脚本清单创建 Cron 任务
```

所以：

```text
“仓库拉取成功” ≠ “定时任务已经创建”
```

如果下面任意一项有问题：

```text
自动添加任务关闭
Python 文件后缀没被选中
白名单没有匹配到任务入口
核心模块和任务入口没有区分
```

都可能出现：

```text
仓库能正常拉取
但定时任务页面什么都没有
```

当前版本已经专门增加两个 `ZzzHe_` 入口文件，并要求使用白名单把它们与核心文件区分开。

---

# 八、第一次使用：扫码登录

任务生成成功后找到：

```text
ZzzHe_小米钱包扫码登录
```

点击：

```text
运行
→ 日志
```

日志中会输出二维码。

使用小米账号支持的扫码入口扫码，并在手机端确认登录。

如果二维码排版导致无法识别，日志还会输出登录链接，可以复制到浏览器打开。

成功后会看到类似：

```text
✅ 登录成功，长效凭证已写入青龙持久化配置目录。
小米 User ID: xxxxxxxx
passToken/securityToken 不会输出到日志。
```

---

# 九、登录凭证保存在哪里？

默认保存：

```text
/ql/data/config/xiaomi_qianbao_VIP/xiaomiconfig.json
```

其中保存：

```text
账号别名
userId
passToken
securityToken
更新时间
```

这个目录位于 Git 仓库目录之外，因此正常重新拉取订阅不会覆盖登录状态。

注意：

```text
passToken
securityToken
```

属于敏感账号凭证，不要发给他人，也不要上传到 GitHub。

---

# 十、登录后测试每日任务

扫码成功后，建议马上手动运行一次：

```text
ZzzHe_小米钱包每日任务
```

正常情况下日志会看到：

```text
临时会话 Cookie 获取成功
开始第 1 轮任务
开始第 2 轮任务
...
```

然后显示当前奖励/视频会员天数等结果。

---

# 十一、每天自动执行

每日任务入口写入的 Cron：

```cron
37 8 * * *
```

即每天：

```text
08:37
```

自动执行。

如果你想换时间，直接在青龙“定时任务”中编辑即可。

例如每天 09:26：

```cron
26 9 * * *
```

---

# 十二、青龙通知

每日任务执行结束后会尝试使用：

```python
QLAPI.notify(title, content)
```

因此可以复用青龙本身已经配置好的通知渠道。

如不希望发送通知，可添加环境变量：

```text
XIAOMI_WALLET_NOTIFY=0
```

重新开启：

```text
XIAOMI_WALLET_NOTIFY=1
```

---

# 十三、多账号

默认账号别名：

```text
xiaomi_1
```

添加第二个账号时，在青龙“环境变量”增加：

```text
名称：XIAOMI_WALLET_ALIAS
值：xiaomi_2
```

然后重新运行：

```text
ZzzHe_小米钱包扫码登录
```

登录第二个账号。

添加第三个账号：

```text
XIAOMI_WALLET_ALIAS=xiaomi_3
```

再次运行扫码登录即可。

每日任务会依次处理保存的所有账号。

---

# 十四、凭证失效怎么办？

如果每日任务提示：

```text
长效凭证可能已失效
```

把 `XIAOMI_WALLET_ALIAS` 设置成需要刷新的账号别名，然后重新运行：

```text
ZzzHe_小米钱包扫码登录
```

再次扫码即可覆盖刷新该账号凭证。

---

# 十五、如果仍然没有生成任务

先检查订阅运行日志中有没有：

```text
检测到有新的定时任务
```

### 情况 A：没有“检测到有新的定时任务”

重点检查：

```text
白名单：^ZzzHe_
文件后缀：py
```

### 情况 B：有“检测到有新的定时任务”，但没有“开始尝试自动添加定时任务”

说明：

```text
自动添加任务
```

没有开启。

### 情况 C：出现“开始尝试自动添加定时任务”，但 API 返回错误

把从：

```text
检测到有新的定时任务
```

开始到订阅结束的日志贴出来排查。

---

# 十六、当前仓库文件说明

```text
xiaomi_qianbao_VIP/
├── ZzzHe_xiaomi_wallet_daily.py   ← 青龙任务入口
├── ZzzHe_xiaomi_wallet_login.py   ← 青龙扫码入口
├── xiaomi_daily.py                ← 每日任务核心逻辑
├── xiaomi_login.py                ← 小米扫码登录核心逻辑
├── xiaomi_common.py               ← 配置和青龙通知
├── xiaomi_manage.py               ← 手动账号管理工具
├── requirements.txt
├── NOTICE.md
├── LICENSE
└── README.md
```

青龙订阅中通过：

```text
白名单 = ^ZzzHe_
```

只把前两个入口文件作为定时任务。

再通过：

```text
依赖文件 = xiaomi_common.py|xiaomi_daily.py|xiaomi_login.py
```

把运行所需核心代码复制到相同目录。

---

# 十七、最简流程

```text
① 编辑订阅

白名单：^ZzzHe_
依赖文件：xiaomi_common.py|xiaomi_daily.py|xiaomi_login.py
文件后缀：py
自动添加任务：开启
自动删除任务：开启

        ↓

② 保存并运行一次订阅

        ↓

③ 定时任务里出现：
ZzzHe_小米钱包扫码登录
ZzzHe_小米钱包每日任务

        ↓

④ 运行 ZzzHe_小米钱包扫码登录

        ↓

⑤ 扫码并确认

        ↓

⑥ 手动运行一次 ZzzHe_小米钱包每日任务测试

        ↓

⑦ 以后每天自动执行
```

---

# 项目来源

核心小米钱包接口和扫码逻辑来源于：

```text
kai648846760/xiaomiwallet
```

本项目针对青龙订阅、持久化、任务入口和通知机制进行了适配。

详细来源说明见 `NOTICE.md`。

---

# 免责声明

本项目仅用于个人学习、技术研究和个人账号自动化。

小米官方接口和风控规则可能随时变化，本项目不保证长期有效。使用自动化脚本产生的账号风险由使用者自行承担。
