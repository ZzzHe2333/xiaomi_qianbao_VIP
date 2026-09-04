# xiaomi_qianbao_VIP

面向 **青龙面板（QingLong）** 的小米钱包每日任务脚本。

本项目基于 [`kai648846760/xiaomiwallet`](https://github.com/kai648846760/xiaomiwallet) 的核心扫码登录与小米钱包任务逻辑进行青龙适配，增加：

- 青龙订阅直接拉取
- 自动创建青龙定时任务
- 一键扫码登录
- 登录凭证持久化保存
- 每日自动执行
- 多账号
- 青龙内置通知 `QLAPI.notify`

> 建议仅在自己的本地青龙环境使用。自动化行为可能触发小米账号风控，请自行承担账号风险。

---

# 先看这里：最简安装流程

```text
青龙 → 订阅管理 → 新建订阅
        ↓
填入本仓库地址
        ↓
务必开启“自动增加定时任务”
        ↓
手动运行一次订阅
        ↓
定时任务中出现：
① 小米钱包扫码登录
② 小米钱包每日任务
        ↓
先手动运行“扫码登录”
        ↓
打开日志扫码并确认
        ↓
再手动运行一次“每日任务”测试
        ↓
以后每天自动执行
```

仓库地址：

```text
https://github.com/ZzzHe2333/xiaomi_qianbao_VIP.git
```

---

# 一、使用前准备

需要一个可以正常使用的青龙面板。

例如：

```text
Windows
  ↓
Docker Desktop
  ↓
青龙面板
  ↓
xiaomi_qianbao_VIP
```

本项目不需要 Flet，也不需要桌面 GUI。

Python 脚本所需的 `requests`、`qrcode` 缺失时会尝试自动安装。

---

# 二、在青龙“订阅管理”中拉取仓库

进入：

```text
青龙面板
  ↓
订阅管理
  ↓
新建订阅
```

建议这样填写：

| 项目 | 内容 |
| --- | --- |
| 名称 | 小米钱包 VIP |
| 类型 | 公开仓库 |
| 链接 | `https://github.com/ZzzHe2333/xiaomi_qianbao_VIP.git` |
| 分支 | `main` |
| 定时类型 | `crontab` |
| 定时规则 | `15 4 * * *` |
| 白名单 | 留空 |
| 黑名单 | 留空 |
| 文件后缀 / Extensions | 留空；如果必须填，填写 `py` |
| 自动增加定时任务 | **开启** |
| 自动删除失效定时任务 | 建议开启 |

## 最重要的一项

请确认：

```text
自动增加定时任务
```

处于：

```text
开启 / ON
```

不同青龙版本可能显示为：

```text
自动增加定时任务
自动添加任务
AutoAddCron
```

它们表示同一个功能。

如果这里只是成功拉取仓库，但这个开关没有开启，**代码会下载成功，但“定时任务”页面可能不会自动出现小米钱包任务。**

订阅定时：

```cron
15 4 * * *
```

仅表示每天 `04:15` 自动检查仓库更新，不是小米钱包执行时间。

---

# 三、第一次拉取

保存订阅后，在订阅列表找到：

```text
小米钱包 VIP
```

点击：

```text
运行
```

建议第一次手动运行一次。

正常日志中应看到类似：

```text
拉取仓库成功
检测到有新的定时任务
开始尝试自动添加定时任务
```

青龙官方的仓库更新逻辑只有在 `AutoAddCron=true` 时才会自动增加新任务。

---

# 四、拉取后应该出现哪些任务

进入：

```text
青龙面板
  ↓
定时任务
```

正常应该出现两个任务。

## 1. 小米钱包每日任务

```text
名称：小米钱包每日任务
Cron：37 8 * * *
```

表示：

```text
每天 08:37 自动执行
```

对应脚本：

```text
xiaomi_daily.py
```

## 2. 小米钱包扫码登录

```text
名称：小米钱包扫码登录
Cron：0 0 29 2 *
```

对应：

```text
xiaomi_login.py
```

这个 Cron 使用合法的 `2 月 29 日`，主要是为了让不同版本青龙都可以正常解析并创建任务。

此任务日常用途仍然是：

```text
需要登录时 → 手动点击运行
```

不需要每天执行。

---

# 五、如果“仓库拉取成功，但任务没有出现”

这是最常见的问题。

请按下面顺序检查。

## 检查 1：自动增加定时任务

进入：

```text
订阅管理
  ↓
编辑“小米钱包 VIP”
```

找到：

```text
自动增加定时任务
```

确保开启。

然后保存，再重新点击一次：

```text
运行订阅
```

## 检查 2：文件后缀

如果你的青龙订阅里有：

```text
文件后缀
Extensions
```

推荐：

```text
留空
```

如果你的版本必须填写，填：

```text
py
```

不要只填写：

```text
js
```

否则 Python 脚本不会被当作任务脚本处理。

## 检查 3：白名单 / 黑名单

推荐第一次部署：

```text
白名单：留空
黑名单：留空
```

如果设置了白名单，需要至少包含：

```text
xiaomi_daily
xiaomi_login
```

## 检查 4：重新运行订阅

修改以上配置后必须重新：

```text
订阅管理 → 小米钱包 VIP → 运行
```

只保存配置而不重新拉取，有些青龙版本不会立即补建任务。

## 检查 5：看订阅日志

如果仍然没有任务，请打开该订阅的日志，重点看有没有：

```text
检测到有新的定时任务
开始尝试自动添加定时任务
```

如果日志只有：

```text
拉取成功
```

但完全没有“自动添加定时任务”，优先检查 `AutoAddCron`。

---

# 六、仍然没有自动生成任务：手动补建

即使青龙版本的自动识别有问题，脚本仍然可以正常运行。

进入：

```text
青龙面板 → 定时任务 → 新建任务
```

## 每日任务

名称：

```text
小米钱包每日任务
```

Cron：

```cron
37 8 * * *
```

命令需要指向青龙拉取后的 `xiaomi_daily.py`。

通常订阅成功后，青龙会把脚本复制到 `/ql/data/scripts/` 下的订阅目录。

可以在青龙终端中查找：

```bash
find /ql/data/scripts -name xiaomi_daily.py
```

假设返回：

```text
/ql/data/scripts/ZzzHe2333_xiaomi_qianbao_VIP_main/xiaomi_daily.py
```

则命令可写：

```bash
python3 /ql/data/scripts/ZzzHe2333_xiaomi_qianbao_VIP_main/xiaomi_daily.py
```

## 扫码登录任务

名称：

```text
小米钱包扫码登录
```

Cron：

```cron
0 0 29 2 *
```

先查路径：

```bash
find /ql/data/scripts -name xiaomi_login.py
```

再将对应路径填入：

```bash
python3 /实际路径/xiaomi_login.py
```

---

# 七、第一次使用：扫码登录

进入：

```text
青龙面板
  ↓
定时任务
  ↓
小米钱包扫码登录
  ↓
运行
```

然后立即打开任务日志。

日志会显示：

```text
======= 小米钱包扫码登录 =======
账号别名: xiaomi_1
凭证保存位置: /ql/data/config/xiaomi_qianbao_VIP/xiaomiconfig.json
```

随后显示二维码。

使用小米账号支持的扫码入口扫码并在手机上确认。

状态一般会变成：

```text
等待扫码
↓
已扫码，请在手机确认
↓
登录成功
```

成功后日志显示：

```text
✅ 登录成功，长效凭证已写入青龙持久化配置目录。
小米 User ID: xxxxxxxx
passToken/securityToken 不会输出到日志。
```

如果日志里的字符二维码无法识别，脚本还会输出二维码对应的登录链接，可复制到浏览器打开后再扫码。

---

# 八、登录信息保存在哪里

默认保存：

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
最后运行记录
```

这个配置文件和 GitHub 拉取目录是分开的，因此：

```text
重新拉库
更新订阅
更新 GitHub 代码
```

不会正常情况下覆盖登录凭证。

## 安全提醒

`passToken` 和 `securityToken` 属于敏感登录凭证。

不要：

- 上传到 GitHub
- 发到群聊
- 提交 Issue 时贴出来
- 将完整配置文件公开

---

# 九、登录后手动测试每日任务

扫码成功后，建议马上测试一次。

进入：

```text
定时任务
  ↓
小米钱包每日任务
  ↓
运行
```

正常情况下会看到：

```text
>>>>>>>>>> 账号 xiaomi_1 <<<<<<<<<<
  - 临时会话 Cookie 获取成功。
  - 开始第 1 轮任务...
  - 开始第 2 轮任务...
```

最终类似：

```text
账号：xiaomi_1
小米ID：xxxxxxxx
当前可兑换视频天数：xx.xx天
今日奖励记录：...
```

看到：

```text
临时会话 Cookie 获取成功
```

说明扫码保存的 `passToken + userId` 已经可以正常换取小米钱包临时会话。

---

# 十、每天自动执行

每日任务默认：

```cron
37 8 * * *
```

即每天：

```text
08:37
```

执行流程：

```text
读取本地账号凭证
      ↓
passToken + userId
      ↓
获取临时 Session Cookie
      ↓
查询小米钱包任务
      ↓
完成任务
      ↓
领取奖励
      ↓
查询奖励记录
      ↓
青龙通知
```

正常情况下只需要第一次扫码，之后每日自动执行。

---

# 十一、修改执行时间

直接在青龙“定时任务”中修改即可。

例如：

每天 `09:26`：

```cron
26 9 * * *
```

每天 `12:18`：

```cron
18 12 * * *
```

每天 `20:43`：

```cron
43 20 * * *
```

---

# 十二、青龙通知

脚本优先调用：

```python
QLAPI.notify(title, content)
```

因此只要青龙自身已经配置好通知渠道，就不需要在本项目里重复填写 Bark、Telegram、PushPlus、企业微信等参数。

关闭本项目通知：

```text
XIAOMI_WALLET_NOTIFY=0
```

重新开启：

```text
XIAOMI_WALLET_NOTIFY=1
```

---

# 十三、多账号

默认第一次账号别名：

```text
xiaomi_1
```

添加第二个账号时，在青龙：

```text
环境变量 → 新建
```

添加：

```text
名称：XIAOMI_WALLET_ALIAS
值：xiaomi_2
```

然后重新运行：

```text
小米钱包扫码登录
```

扫描第二个小米账号。

再添加第三个：

```text
XIAOMI_WALLET_ALIAS=xiaomi_3
```

每日任务会自动遍历所有已保存账号。

如果某个账号凭证失效，只需把 `XIAOMI_WALLET_ALIAS` 改回对应别名，再重新扫码，即可覆盖刷新原凭证。

---

# 十四、账号管理

查看已保存账号：

```bash
python3 xiaomi_manage.py list
```

删除账号：

```bash
python3 xiaomi_manage.py delete xiaomi_2
```

如果不知道脚本所在目录，可以先：

```bash
find /ql/data/scripts -name xiaomi_manage.py
```

---

# 十五、环境变量

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `XIAOMI_WALLET_ALIAS` | `xiaomi_1` | 扫码时账号别名 |
| `XIAOMI_WALLET_CONFIG` | `/ql/data/config/xiaomi_qianbao_VIP/xiaomiconfig.json` | 凭证保存位置 |
| `XIAOMI_WALLET_NOTIFY` | `1` | 是否发送青龙通知 |
| `XIAOMI_WALLET_ACCOUNT_DELAY_MAX` | `15` | 多账号之间最大随机等待秒数 |

一般单账号用户不需要创建任何环境变量。

---

# 十六、手动 Git Clone 部署

如果不使用“订阅管理”，也可以在青龙容器终端运行：

```bash
cd /ql/data/scripts
git clone https://github.com/ZzzHe2333/xiaomi_qianbao_VIP.git
cd xiaomi_qianbao_VIP
```

扫码：

```bash
python3 xiaomi_login.py
```

每日任务：

```bash
python3 xiaomi_daily.py
```

但推荐仍使用青龙订阅管理，这样后续更新更方便。

---

# 十七、常见问题

## 1. 拉库成功但没有任务

优先检查：

```text
自动增加定时任务 = 开启
文件后缀 = 留空 或 py
白名单 = 留空
黑名单 = 留空
```

修改后重新运行订阅。

## 2. 日志提示没有账号

说明还没有扫码成功。

运行：

```text
小米钱包扫码登录
```

## 3. 提示 passToken 失效

重新运行扫码登录任务即可。

## 4. 二维码无法扫描

复制日志中的登录链接到浏览器打开，然后扫码。

## 5. 今日暂无新增奖励记录

不一定是异常，可能今天已经领取过，或当前活动接口没有返回新的记录。

## 6. 缺少 requests / qrcode

脚本会尝试自动安装。

也可以在青龙“依赖管理”手动安装：

```text
requests
qrcode
```

---

# 十八、项目文件

```text
xiaomi_qianbao_VIP/
├── xiaomi_daily.py       # 每日任务
├── xiaomi_login.py       # 扫码登录
├── xiaomi_manage.py      # 账号管理
├── xiaomi_common.py      # 配置/通知等公共功能
├── requirements.txt
├── README.md
├── NOTICE.md
├── LICENSE
└── .gitignore
```

---

# 十九、上游项目

核心小米账号扫码登录和小米钱包任务接口逻辑来源：

```text
kai648846760/xiaomiwallet
```

本项目最初适配所参考的上游快照：

```text
bdaa61b443a0743fc031e8875e6f26a1c4a9a5e1
```

上游项目声明 MIT License。本仓库保留来源说明，详见 `NOTICE.md`。

---

# 二十、免责声明

本项目仅用于个人学习、技术研究和个人账号自动化。

小米官方接口、活动规则和风控策略均可能发生变化，本项目不保证长期有效。

请勿将账号 Token 或配置文件提交到公开仓库。