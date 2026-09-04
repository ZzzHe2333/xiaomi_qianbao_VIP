"""
小米钱包扫码登录（手动任务）

name: 小米钱包扫码登录
cron: 0 0 29 2 *

说明：使用合法 Cron 以兼容青龙订阅任务解析。
该任务主要用于手动扫码登录/刷新凭证；默认仅在闰年 2 月 29 日自动触发。
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional


def _ensure_dependencies() -> None:
    missing = []
    try:
        import requests  # noqa: F401
    except ImportError:
        missing.append("requests>=2.28")
    try:
        import qrcode  # noqa: F401
    except ImportError:
        missing.append("qrcode>=7.4.2")

    if missing:
        print("📦 首次运行，正在安装缺失依赖: " + ", ".join(missing))
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", *missing]
        )


_ensure_dependencies()

import qrcode
import requests

from xiaomi_common import CONFIG_PATH, get_default_alias, ql_notify, upsert_account

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


def get_login_qr() -> Optional[Dict[str, Any]]:
    url = "https://account.xiaomi.com/longPolling/loginUrl"
    params = {
        "_group": "DEFAULT",
        "_qrsize": "240",
        "qs": "?callback=https%3A%2F%2Faccount.xiaomi.com%2Fsts%3Fsign%3DZvAtJIzsDsFe60LdaPa76nNNP58%253D%26followup%3Dhttps%253A%252F%252Faccount.xiaomi.com%252Fpass%252Fauth%252Fsecurity%252Fhome%26sid%3Dpassport&sid=passport&_group=DEFAULT",
        "bizDeviceType": "",
        "callback": "https://account.xiaomi.com/sts?sign=ZvAtJIzsDsFe60LdaPa76nNNP58=&followup=https://account.xiaomi.com/pass/auth/security/home&sid=passport",
        "_hasLogo": "false",
        "theme": "",
        "sid": "passport",
        "needTheme": "false",
        "showActiveX": "false",
        "serviceParam": '{"checkSafePhone":false,"checkSafeAddress":false,"lsrp_score":0.0}',
        "_locale": "zh_CN",
        "_sign": "2&V1_passport&BUcblfwZ4tX84axhVUaw8t6yi2E=",
        "_dc": str(int(time.time() * 1000)),
    }
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, params=params, timeout=15)
        response.raise_for_status()
        text = response.text
        if "&&&START&&&" in text:
            text = text.split("&&&START&&&", 1)[-1].strip()
        return json.loads(text)
    except Exception as exc:
        print(f"❌ 获取登录二维码失败: {exc}")
        return None


def print_qr(qr_url: str) -> None:
    qr = qrcode.QRCode(border=2)
    qr.add_data(qr_url)
    qr.make(fit=True)
    matrix = qr.get_matrix()

    print("\n📱 请使用小米手机/小米账号支持的扫码入口扫描下方二维码：\n")
    for row in matrix:
        print("".join("██" if cell else "  " for cell in row))
    print("\n如果二维码在日志中无法识别，可复制下面的登录链接到浏览器打开：")
    print(qr_url)
    print()


def poll_login(lp_url: str, timeout: int) -> Optional[Dict[str, str]]:
    deadline = time.time() + max(30, timeout)
    last_code = None
    status_text = {700: "等待扫码", 701: "已扫码，请在手机确认", 702: "二维码已过期", 0: "登录成功"}

    while time.time() < deadline:
        remaining = int(deadline - time.time())
        try:
            response = requests.get(lp_url, timeout=60)
            text = response.text
            if "&&&START&&&" in text:
                text = text.split("&&&START&&&", 1)[-1].strip()
            result = json.loads(text)
            code = result.get("code", -1)
            if code != last_code:
                print(f"ℹ️ {status_text.get(code, f'状态码 {code}')}（剩余约 {remaining} 秒）")
                last_code = code

            if code == 0:
                user_id = result.get("userId")
                pass_token = result.get("passToken")
                security_token = result.get("ssecurity")
                if user_id and pass_token:
                    return {
                        "userId": str(user_id),
                        "passToken": str(pass_token),
                        "securityToken": str(security_token or ""),
                    }
                print("❌ 登录响应缺少 userId/passToken。")
                return None
            if code == 702:
                return None
        except requests.Timeout:
            print(f"⏳ 等待扫码确认中（剩余约 {remaining} 秒）...")
        except KeyboardInterrupt:
            print("🚫 已中断登录。")
            return None
        except Exception as exc:
            print(f"⚠️ 查询扫码状态失败: {exc}，3 秒后重试。")
            time.sleep(3)

    return None


def main() -> int:
    alias = get_default_alias()
    print("======= 小米钱包扫码登录 =======")
    print(f"账号别名: {alias}")
    print(f"凭证保存位置: {CONFIG_PATH}")
    print("提示：多账号时可在青龙环境变量设置 XIAOMI_WALLET_ALIAS 后再运行本任务。")

    login_data = get_login_qr()
    if not login_data or login_data.get("code") != 0:
        return 1

    qr_url = login_data.get("qr")
    lp_url = login_data.get("lp")
    if not qr_url or not lp_url:
        print("❌ 小米登录接口未返回 qr/lp 地址。")
        return 1

    print_qr(str(qr_url))
    result = poll_login(str(lp_url), int(login_data.get("timeout", 300)))
    if not result:
        print("❌ 登录失败或二维码已过期，请重新运行本任务。")
        return 1

    account_data = {
        "us": alias,
        **result,
        "updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    upsert_account(account_data)

    print("✅ 登录成功，长效凭证已写入青龙持久化配置目录。")
    print(f"小米 User ID: {result['userId']}")
    print("passToken/securityToken 不会输出到日志。")

    qlapi = globals().get("QLAPI")
    ql_notify(
        "小米钱包登录成功",
        f"账号别名：{alias}\n小米ID：{result['userId']}\n凭证已保存，可执行每日任务。",
        qlapi,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())