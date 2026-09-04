"""
小米钱包每日任务核心逻辑。

真正的青龙入口为 ZzzHe_xiaomi_wallet_daily.js。
"""

from __future__ import annotations

import random
import subprocess
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


def _ensure_dependencies() -> None:
    try:
        import requests  # noqa: F401
    except ImportError:
        print("📦 首次运行，正在安装 requests...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "requests>=2.28"]
        )


_ensure_dependencies()

import requests

from xiaomi_common import (
    account_interval_delay,
    load_qinglong_cookie_accounts,
    migrate_legacy_accounts_if_needed,
    ql_notify,
)

API_HOST = "m.jr.airstarfinance.net"
ACTIVITY_CODE = "2211-videoWelfare"
USER_AGENT_MOBILE = (
    "Mozilla/5.0 (Linux; U; Android 14; zh-CN; M2012K11AC Build/UKQ1.230804.001; "
    "AppBundle/com.mipay.wallet; AppVersionName/6.89.1.5275.2323; AppVersionCode/20577595; "
    "MiuiVersion/stable-V816.0.13.0.UMNCNXM; DeviceId/alioth; NetworkType/WIFI; mix_version; "
    "WebViewVersion/118.0.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
    "Mobile Safari/5.36 XiaoMi/MiuiBrowser/4.3"
)
USER_AGENT_DESKTOP = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0"
)


def _task_params() -> Dict[str, str]:
    return {
        "activityCode": ACTIVITY_CODE,
        "app": "com.mipay.wallet",
        "isNfcPhone": "true",
        "channel": "mipay_indexicon_TVcard",
        "deviceType": "2",
        "system": "1",
        "visitEnvironment": "2",
        "userExtra": '{"platformType":1,"com.miui.player":"4.27.0.4","com.miui.video":"v2024090290(MiVideo-UN)","com.mipay.wallet":"6.83.0.5175.2256"}',
    }


class ApiRequest:
    def __init__(self, cookies: Union[str, Dict[str, str]]):
        self.session = requests.Session()
        self.headers = {"Host": API_HOST, "User-Agent": USER_AGENT_MOBILE}
        self.update_cookies(cookies)

    @staticmethod
    def _parse_cookies(cookie_string: str) -> Dict[str, str]:
        result: Dict[str, str] = {}
        for item in cookie_string.split(";"):
            if "=" in item:
                key, value = item.split("=", 1)
                result[key.strip()] = value.strip()
        return result

    def update_cookies(self, cookies: Union[str, Dict[str, str]]) -> None:
        parsed = self._parse_cookies(cookies) if isinstance(cookies, str) else cookies
        if not parsed:
            return
        self.session.cookies.update(parsed)
        self.headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in parsed.items())

    def request(self, method: str, url: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        headers = {**self.headers, **kwargs.pop("headers", {})}
        try:
            response = self.session.request(method, url, headers=headers, timeout=20, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            print(f"  ⚠️ 请求失败: {exc}")
            return None

    def get(self, url: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        return self.request("POST", url, **kwargs)


class XiaomiWalletTask:
    def __init__(self, api: ApiRequest):
        self.api = api
        self.t_id: Optional[str] = None
        self.total_days = "未知"
        self.today_records: List[Dict[str, Any]] = []
        self.error_info = ""

    def get_task_list(self) -> Optional[List[Dict[str, Any]]]:
        response = self.api.post(
            f"https://{API_HOST}/mp/api/generalActivity/getTaskList",
            data={"activityCode": ACTIVITY_CODE},
        )
        if response and response.get("code") == 0:
            info_list = response.get("value", {}).get("taskInfoList", [])
            return [item for item in info_list if "浏览组浏览任务" in item.get("taskName", "")]
        self.error_info = f"获取任务列表失败：{response}"
        return None

    def get_task(self, task_code: str) -> Optional[str]:
        response = self.api.post(
            f"https://{API_HOST}/mp/api/generalActivity/getTask",
            data={
                "activityCode": ACTIVITY_CODE,
                "taskCode": task_code,
                "jrairstar_ph": "98lj8puDf9Tu/WwcyMpVyQ==",
            },
        )
        if response and response.get("code") == 0:
            return response.get("value", {}).get("taskInfo", {}).get("userTaskId")
        self.error_info = f"获取任务信息失败：{response}"
        return None

    def complete_task(self, task_id: str, t_id: str, click_url_id: str) -> Optional[str]:
        params = {
            **_task_params(),
            "taskId": task_id,
            "browsTaskId": t_id,
            "browsClickUrlId": click_url_id,
            "clickEntryType": "undefined",
            "festivalStatus": "0",
        }
        response = self.api.get(
            f"https://{API_HOST}/mp/api/generalActivity/completeTask",
            params=params,
        )
        if response and response.get("code") == 0:
            return response.get("value")
        self.error_info = f"完成任务失败：{response}"
        return None

    def receive_award(self, user_task_id: str) -> bool:
        response = self.api.get(
            f"https://{API_HOST}/mp/api/generalActivity/luckDraw",
            params={**_task_params(), "userTaskId": user_task_id},
        )
        if response and response.get("code") == 0:
            return True
        self.error_info = f"领取奖励失败：{response}"
        return False

    def query_user_info_and_records(self) -> bool:
        base = f"https://{API_HOST}/mp/api/generalActivity"
        params = _task_params()
        total = self.api.get(f"{base}/queryUserGoldRichSum", params=params)
        if not total or total.get("code") != 0:
            self.error_info = f"获取可兑换视频天数失败：{total}"
            return False

        try:
            self.total_days = f"{int(total.get('value', 0)) / 100:.2f}天"
        except Exception:
            self.total_days = str(total.get("value", "未知"))

        records = self.api.get(
            f"{base}/queryUserJoinList",
            params={**params, "pageNum": 1, "pageSize": 20},
        )
        if not records or records.get("code") != 0:
            self.error_info = f"查询任务记录失败：{records}"
            return False

        today = datetime.now().strftime("%Y-%m-%d")
        self.today_records = [
            item
            for item in records.get("value", {}).get("data", [])
            if str(item.get("createTime", "")).startswith(today)
        ]
        return True

    def run(self) -> bool:
        if not self.query_user_info_and_records():
            return False

        for round_index in range(2):
            print(f"  - 开始第 {round_index + 1} 轮任务")
            tasks = self.get_task_list()
            if not tasks:
                print("  - 未发现可执行浏览任务，可能今日已完成。")
                break

            task = tasks[0]
            info = task.get("generalActivityUrlInfo") or {}
            self.t_id = info.get("id")
            if not self.t_id:
                self.error_info = "无法获取任务 t_id"
                return False

            time.sleep(random.randint(10, 15))
            user_task_id = self.complete_task(
                str(task.get("taskId", "")),
                str(self.t_id),
                str(info.get("browsClickUrlId", "")),
            )
            time.sleep(random.randint(2, 4))

            if not user_task_id:
                user_task_id = self.get_task(str(task.get("taskCode", "")))
                time.sleep(random.randint(2, 4))

            if user_task_id:
                self.receive_award(str(user_task_id))
            else:
                print("  - 未获取 userTaskId，本轮无法领取奖励。")
            time.sleep(random.randint(2, 4))

        self.query_user_info_and_records()
        return not bool(self.error_info)


def get_session_cookie(pass_token: str, user_id: str) -> Optional[str]:
    login_url = (
        "https://account.xiaomi.com/pass/serviceLogin?callback=https%3A%2F%2Fapi.jr.airstarfinance.net%2Fsts"
        "%3Fsign%3D1dbHuyAmee0NAZ2xsRw5vhdVQQ8%253D%26followup%3Dhttps%253A%252F%252Fm.jr.airstarfinance.net"
        "%252Fmp%252Fapi%252Flogin%253Ffrom%253Dmipay_indexicon_TVcard%2526deepLinkEnable%253Dfalse"
        "%2526requestUrl%253Dhttps%25253A%25252F%25252Fm.jr.airstarfinance.net%25252Fmp%25252Factivity"
        "%25252FvideoActivity%25253Ffrom%25253Dmipay_indexicon_TVcard%252526_noDarkMode%25253Dtrue"
        "%252526_transparentNaviBar%25253Dtrue%252526cUserId%25253Dusyxgr5xjumiQLUoAKTOgvi858Q"
        "%252526_statusBarHeight%25253D137&sid=jrairstar&_group=DEFAULT&_snsNone=true&_loginType=ticket"
    )
    session = requests.Session()
    try:
        session.get(
            login_url,
            headers={
                "User-Agent": USER_AGENT_DESKTOP,
                "Cookie": f"passToken={pass_token}; userId={user_id};",
            },
            timeout=20,
        )
        cookies = session.cookies.get_dict()
        c_user_id = cookies.get("cUserId")
        service_token = cookies.get("serviceToken")
        if c_user_id and service_token:
            return f"cUserId={c_user_id}; jrairstar_serviceToken={service_token}"
    except Exception as exc:
        print(f"  ⚠️ 获取临时会话 Cookie 失败: {exc}")
    return None


def make_report(alias: str, user_id: str, task: XiaomiWalletTask) -> str:
    lines = [
        f"账号：{alias}",
        f"小米ID：{user_id}",
        f"当前可兑换视频天数：{task.total_days}",
    ]
    if task.today_records:
        lines.append("今日奖励记录：")
        for record in task.today_records:
            value = record.get("value", 0)
            try:
                days = int(value) / 100
                value_text = f"+{days:.2f}天"
            except Exception:
                value_text = str(value)
            lines.append(f"- {record.get('createTime', '未知时间')} {value_text}")
    else:
        lines.append("今日暂无新增奖励记录")
    if task.error_info:
        lines.append(f"异常：{task.error_info}")
    return "\n".join(lines)


def process_account(data: Dict[str, Any]) -> tuple[str, bool]:
    alias = str(data.get("us", "未知"))
    user_id = str(data.get("userId", ""))
    pass_token = str(data.get("passToken", ""))

    print(f"\n>>>>>>>>>> 账号 {alias} <<<<<<<<<<")
    if not user_id or not pass_token:
        return f"账号：{alias}\n异常：ck 环境变量缺少 userId/passToken，请重新扫码登录。", False

    cookie = get_session_cookie(pass_token, user_id)
    task = XiaomiWalletTask(ApiRequest(cookie or ""))
    if not cookie:
        task.error_info = "长效凭证可能已失效，请重新运行扫码登录任务刷新该小米账号。"
        return make_report(alias, user_id, task), False

    print("  - 临时会话 Cookie 获取成功。")
    try:
        ok = task.run()
    except Exception as exc:
        task.error_info = f"执行异常：{exc}"
        ok = False
    return make_report(alias, user_id, task), ok


def main() -> int:
    print(f"======= 小米钱包每日任务 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =======")

    accounts = load_qinglong_cookie_accounts()
    if not accounts:
        migrate_legacy_accounts_if_needed()
        accounts = load_qinglong_cookie_accounts()

    if not accounts:
        message = "尚未检测到 ck1/ck2...，请先运行 ZzzHe_小米钱包扫码登录。"
        print("ℹ️ " + message)
        ql_notify("小米钱包未登录", message, globals().get("QLAPI"))
        return 1

    print(f"检测到 {len(accounts)} 个账号，将严格串行执行。")
    for index, account in enumerate(accounts, start=1):
        env_name = account.get("data", {}).get("envName", "")
        print(f"  {index}. {env_name}")

    reports: List[str] = []
    success_count = 0

    for index, account in enumerate(accounts):
        data = account.setdefault("data", {})
        report, ok = process_account(data)
        print("\n" + report)
        reports.append(report)
        success_count += int(ok)

        # 严格串行：只有当前账号 process_account 完整返回后，才可能等待并启动下一个账号。
        if index < len(accounts) - 1:
            next_alias = str(accounts[index + 1].get("data", {}).get("us", f"ck{index + 2}"))
            account_interval_delay(next_alias)

    summary = (
        f"执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"账号数：{len(accounts)}，成功：{success_count}，异常：{len(accounts) - success_count}\n\n"
        + "\n\n--------------------\n\n".join(reports)
    )
    title = "小米钱包每日任务" if success_count == len(accounts) else "小米钱包每日任务（有异常）"
    ql_notify(title, summary, globals().get("QLAPI"))
    print("\n======= 全部账号执行完毕 =======")
    return 0 if success_count == len(accounts) else 2


if __name__ == "__main__":
    raise SystemExit(main())
