# xiaomi_qianbao_VIP

面向 **青龙面板（QingLong）** 的小米钱包每日任务脚本。基于 `kai648846760/xiaomiwallet` 的核心登录与任务逻辑改造，去除 Flet/GUI 依赖，增加青龙订阅、扫码登录、持久化凭证和青龙内置通知。

> 建议仅在自己的本地青龙环境使用。自动化行为可能触发小米账号风控，使用者自行承担账号风险。

## 功能

- 青龙“订阅管理”直接拉取仓库
- 拉取后根据 `cron` 注释创建任务
- `小米钱包扫码登录`：手动点击运行，日志中显示二维码
- 登录后将长效凭证保存到青龙持久化配置目录
- `小米钱包每日任务`：默认每天 08:37 自动执行
- 支持多账号
- 使用青龙内置 `QLAPI.notify`，复用面板已经配置的通知渠道
- 首次运行自动补装 `requests` / `qrcode` 依赖
- 仓库更新不会覆盖账号凭证

## 1. 青龙订阅

青龙面板 → **订阅管理** → **新建订阅**：

| 项目 | 填写内容 |
| --- | --- |
| 名称 | 小米钱包 VIP |
| 类型 | 公开仓库 |
| 链接 | `https://github.com/ZzzHe2333/xiaomi_qianbao_VIP.git` |
| 分支 | `main` |
| 定时类型 | `crontab` |
| 定时规则 | `15 4 * * *` |
| 白名单 | 留空 |
| 黑名单 | 留空 |

保存后手动运行一次订阅。

青龙会根据脚本中的 `cron` 注释识别任务：

| 任务 | 默认规则 | 用途 |
| --- | --- | --- |
| 小米钱包每日任务 | `37 8 * * *` | 每天自动执行 |
| 小米钱包扫码登录 | `0 0 31 2 *` | 仅供手动点击运行，2 月 31 日不会自动触发 |

如果你的青龙版本没有自动生成“扫码登录”任务，可以在“定时任务”中新建一次：

```bash
python3 xiaomi_login.py
```

并把定时规则设为 `0 0 31 2 *`，之后需要登录时只点“运行”。

## 2. 一键扫码登录

进入 **定时任务 → 小米钱包扫码登录 → 运行 → 查看日志**。

日志会显示二维码。扫码并在手机上确认后，脚本自动保存：

- `userId`
- `passToken`
- `securityToken`

敏感 Token 不会打印到日志。

默认账号别名为 `xiaomi_1`。如需自定义/多账号，在青龙 **环境变量** 中添加：

```text
XIAOMI_WALLET_ALIAS=xiaomi_2
```

然后重新运行“扫码登录”任务。不同别名会保存为不同账号；相同别名会刷新原账号凭证。

## 3. 凭证保存位置

青龙容器内默认保存到：

```text
/ql/data/config/xiaomi_qianbao_VIP/xiaomiconfig.json
```

它位于订阅仓库目录之外，因此重新拉库/更新代码不会覆盖登录状态。

如需自定义位置，可设置：

```text
XIAOMI_WALLET_CONFIG=/你的持久化路径/xiaomiconfig.json
```

请勿把该配置文件上传到 GitHub 或发送给他人。`passToken` 属于敏感账号凭证。

## 4. 每日自动执行

默认任务：

```cron
37 8 * * *
```

每天 08:37 执行。可以直接在青龙面板修改时间。

每日执行时会用保存的 `passToken + userId` 获取临时会话 Cookie，因此不需要每天扫码。

如果凭证过期，日志/通知会提示重新运行“扫码登录”任务。

## 5. 青龙通知

脚本优先调用青龙官方 Python 任务环境提供的：

```python
QLAPI.notify(title, content)
```

因此不需要在本项目里重复配置 Bark、Telegram、企业微信等密钥；只要青龙自身的通知渠道已经配置好即可。

如不需要每日通知，可添加环境变量：

```text
XIAOMI_WALLET_NOTIFY=0
```

## 6. 可选环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `XIAOMI_WALLET_ALIAS` | `xiaomi_1` | 扫码登录时的账号别名 |
| `XIAOMI_WALLET_CONFIG` | `/ql/data/config/xiaomi_qianbao_VIP/xiaomiconfig.json` | 凭证文件位置 |
| `XIAOMI_WALLET_NOTIFY` | `1` | 是否调用青龙通知 |
| `XIAOMI_WALLET_ACCOUNT_DELAY_MAX` | `15` | 多账号之间最大随机等待秒数 |

## 7. 手动账号管理

仓库内提供：

```bash
python3 xiaomi_manage.py list
python3 xiaomi_manage.py delete xiaomi_2
```

## 项目来源与许可证

核心小米钱包登录/任务接口逻辑来源于 `kai648846760/xiaomiwallet`，本仓库使用的上游快照为：

```text
bdaa61b443a0743fc031e8875e6f26a1c4a9a5e1
```

上游 `pyproject.toml` 声明 MIT License。详细来源见 [NOTICE.md](NOTICE.md)。本仓库的青龙适配代码同样以 MIT License 发布。

## 免责声明

本项目仅用于个人学习、技术研究和个人账号自动化。小米官方接口和风控策略可能变化，本项目不保证长期可用。请勿将账号凭证提交到公开仓库。
