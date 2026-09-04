"""
小米钱包每日任务核心逻辑。

真正的青龙入口为 ZzzHe_xiaomi_wallet_daily.js。
"""

from __future__ import annotations

import base64
import hashlib
import json
import random
import subprocess
import sys
import time
import uuid
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
APP_VERSION_NAME = "6.98.0.5484.2643"
APP_VERSION_CODE = "20577630"
DEVICE_NAME = "alioth"
LEGACY_JRAIRSTAR_PH = "98lj8puDf9Tu/WwcyMpVyQ=="

USER_AGENT_MOBILE = (
    "Mozilla/5.0 (Linux; U; Android 13; zh-CN; M2012K11AC Build/TKQ1.221114.001; "
    f"AppBundle/com.mipay.wallet; AppVersionName/{APP_VERSION_NAME}; AppVersionCode/{APP_VERSION_CODE}; "
    "MiuiVersion/stable-V816.0.6.0.TKHCNXM; DeviceId/alioth; NetworkType/WIFI; mix_version; "
    "WebViewVersion/116.0.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
    "Mobile Safari/537.36 XiaoMi/MiuiBrowser/4.3"
)
USER_AGENT_DESKTOP = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)
USER_EXTRA = (
    '{"platformType":1,"com.miui.player":"4.38.0.2",'
    '"com.miui.video":"v2025082090(MiVideo-UN)",'
    f'"com.mipay.wallet":"{APP_VERSION_NAME}"}}'
)
APP_LIMIT = (
    '{"com.qiyi.video":false,"com.youku.phone":false,"com.tencent.qqlive":false,'
    '"com.hunantv.imgo.activity":false,"com.cmcc.cmvideo":false,"com.sankuai.meituan":true,'
    '"com.anjuke.android.app":false,"com.tal.abctimelibrary":false,"com.lianjia.beike":false,'
    '"com.kmxs.reader":false,"com.jd.jrapp":false,"com.smile.gifmaker":false,'
    '"com.kuaishou.nebula":false}'
)


def _device_profile(user_id: str) -> Dict[str, str]:
    """为同一个小米账号生成稳定的伪设备参数，避免每天随机变化。"""
    seed = hashlib.sha256(f"ZzzHe2333:xiaomi_qianbao_VIP:{user_id}".encode("utf-8")).digest()
    hex_seed = seed.hex()
    return {
        "oaid": hex_seed[:16],
        "androidId": hex_seed[16:32],
        "regId": base64.b64encode(seed).decode("ascii"),
    }


def _task_params(session_tid: str, device: Dict[str, str]) -> Dict[str, str]:
    return {
        "tid": session_tid,
        "activityCode": ACTIVITY_CODE,
        "app": "com.mipay.wallet",
        "oaid": device["oaid"],
        "regId": device["regId"],
        "versionCode": APP_VERSION_CODE,
        "versionName": APP_VERSION_NAME,
        "isNfcPhone": "true",
        "channel": "mipay_indexicon_TVcard",
        "deviceType": "2",
        "system": "1",
        "visitEnvironment": "2",
        "userExtra": USER_EXTRA,
    }


def _yimi_data(device: Dict[str, str]) -> str:
    payload = {
        "clientInfo": {
            "deviceInfo": {
                "androidVersion": "33",
                "device": DEVICE_NAME,
                "miuiVersion": 816,
                "miuiVersionName": "V816",
                "model": "M2012K11AC",
                "restrictImei": "true",
                "screenHeight": 873,
                "screenWidth": 393,
            },
            "userInfo": {
                "androidId": device["androidId"],
                "connectionType": "WIFI",
                "oaid": device["oaid"],
                "country": "CN",
                "isPersonalizedAdEnabled": True,
                "language": "zh-rCN",
                "ua": USER_AGENT_MOBILE,
            },
            "appInfo": {
                "packageName": "com.mipay.wallet",
                "version": APP_VERSION_NAME,
            },
            "context": {"eid": ""},
            "impRequests": [{"adsCount": 1, "tagId": "1.140.4.1"}],
        }
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class ApiRequest:
    def __init__(self, cookies: Union[str, Dict[str, str]]):
        self.session = requests.Session()
        self.headers = {
            "Host": API_HOST,
            "User-Agent": USER_AGENT_MOBILE,
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "com.mipay.wallet",
        }
        self.last_status: Optional[int] = None
        self.last_error = ""
        self.update_cookies(cookies)

    @staticmethod
    def _parse_cookies(cookie_string: str) -> Dict[str, str]:
        result: Dict[str, str] = {}
        for item in cookie_string.split(";"):
            if "=" in item:
                key, value = item.split("=", 1)
                result[key.strip()] = value.strip()
        return result

    def cookie_value(self, name: str) -> str:
        value = self.session.cookies.get(name)
        if value is not None:
            return str(value)
        return self._parse_cookies(self.headers.get("Cookie", "")).get(name, "")

    def update_cookies(self, cookies: Union[str, Dict[str, str]]) -> None:
        parsed = self._parse_cookies(cookies) if isinstance(cookies, str) else cookies
        if not parsed:
            return
        self.session.cookies.update(parsed)
        self.headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in parsed.items())

    @staticmethod
    def _safe_response_text(response: requests.Response) -> str:
        text = (response.text or "").strip().replace("\r", " ").replace("\n", " ")
        return text[:500]

    def request(self, method: str, url: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        headers = {**self.headers, **kwargs.pop("headers", {})}
        self.last_status = None
        self.last_error = ""
        try:
            response = self.session.request(
                method.upper(),
                url,
                headers=headers,
                timeout=20,
                **kwargs,
            )
            self.last_status = response.status_code
            if not response.ok:
                body = self._safe_response_text(response)
                self.last_error = f"HTTP {response.status_code}: {body or response.reason}"
                endpoint = url.rsplit("/", 1)[-1]
                print(f"  ⚠️ {endpoint} 请求失败：{self.last_error}")
                return None
            try:
                return response.json()
            except ValueError:
                body = self._safe_response_text(response)
                self.last_error = f"响应不是 JSON：{body}"
                endpoint = url.rsplit("/", 1)[-1]
                print(f"  ⚠️ {endpoint} 返回无法解析：{body}")
                return None
        except requests.RequestException as exc:
            self.last_error = str(exc)
            endpoint = url.rsplit("/", 1)[-1]
            print(f"  ⚠️ {endpoint} 网络请求失败：{exc}")
            return None

    def get(self, url: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        return self.request("POST", url, **kwargs)


class XiaomiWalletTask:
    def __init__(self, api: ApiRequest, user_id: str):
        self.api = api
        self.user_id = user_id
        self.session_tid = str(uuid.uuid4())
        self.device = _device_profile(user_id)
        self.t_id: Optional[str] = None
        self.total_days = "未知"
        self.today_records: List[Dict[str, Any]] = []
        self.error_info = ""

    def _dynamic_ph(self) -> str:
        value = self.api.cookie_value("jrairstar_ph")
        if value:
            return value
        print("  ⚠️ 临时会话中未发现动态 jrairstar_ph，使用旧版兼容值重试。")
        return LEGACY_JRAIRSTAR_PH

    def get_task_list(self) -> Optional[List[Dict[str, Any]]]:
        response = self.api.post(
            f"https://{API_HOST}/mp/api/generalActivity/getTaskList",
            data={"tid": self.session_tid, "activityCode": ACTIVITY_CODE},
        )
        if response and response.get("code") == 0:
            info_list = response.get("value", {}).get("taskInfoList", [])
            return [item for item in info_list if "浏览组浏览任务" in item.get("taskName", "")]
        message = f"获取任务列表失败：{response if response is not None else self.api.last_error}"
        self.error_info = message
        print(f"  ⚠️ {message}")
        return None

    def get_task(self, task_code: str) -> Optional[str]:
        data = {
            **_task_params(self.session_tid, self.device),
            "device": DEVICE_NAME,
            "appLimit": APP_LIMIT,
            "pagination": "0",
            "dataType": "0",
            "yimiData": _yimi_data(self.device),
            "taskCode": task_code,
            "componentStatus": "0",
            "jrairstar_ph": self._dynamic_ph(),
        }
        response = self.api.post(
            f"https://{API_HOST}/mp/api/generalActivity/getTask",
            data=data,
        )
        if response and response.get("code") == 0:
            user_task_id = response.get("value", {}).get("taskInfo", {}).get("userTaskId")
            if user_task_id:
                return str(user_task_id)
        message = f"获取任务信息失败：{response if response is not None else self.api.last_error}"
        self.error_info = message
        print(f"  ⚠️ {message}")
        return None

    def complete_task(self, task_id: str, t_id: str, click_url_id: str) -> Optional[str]:
        params = {
            **_task_params(self.session_tid, self.device),
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
            value = response.get("value")
            if isinstance(value, dict):
                nested_id = value.get("userTaskId") or value.get("taskId")
                return str(nested_id) if nested_id else None
            if value not in (None, "", False):
                return str(value)
            print("  ℹ️ completeTask 返回成功但未直接给出 userTaskId，将调用 getTask 获取。")
            return None
        message = f"完成任务失败：{response if response is not None else self.api.last_error}"
        self.error_info = message
        print(f"  ⚠️ {message}")
        return None

    def receive_award(self, user_task_id: str) -> bool:
        params = {
            **_task_params(self.session_tid, self.device),
            "imei": "",
            "device": DEVICE_NAME,
            "appLimit": APP_LIMIT,
            "userTaskId": user_task_id,
        }
        response = self.api.get(
            f"https://{API_HOST}/mp/api/generalActivity/luckDraw",
            params=params,
        )
        if response and response.get("code") == 0:
            return True
        if response and any(
            text in str(response.get("message", ""))
            for text in ("今日奖励已领取", "已领取")
        ):
            print("  ℹ️ 本轮奖励已领取，按成功处理。")
            return True
        message = f"领取奖励失败：{response if response is not None else self.api.last_error}"
        self.error_info = message
        print(f"  ⚠️ {message}")
        return False

    def query_user_info_and_records(self) -> bool:
        base = f"https://{API_HOST}/mp/api/generalActivity"
        params = _task_params(self.session_tid, self.device)
        total = self.api.get(f"{base}/queryUserGoldRichSum", params=params)
        if not total or total.get("code") != 0:
            self.error_info = f"获取可兑换视频天数失败：{total if total is not None else self.api.last_error}"
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
            self.error_info = f"查询任务记录失败：{records if records is not None else self.api.last_error}"
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

        round_errors: List[str] = []
        for round_index in range(2):
            print(f"  - 开始第 {round_index + 1} 轮任务")
            self.error_info = ""
            tasks = self.get_task_list()
            if not tasks:
                if self.error_info:
                    round_errors.append(f"第{round_index + 1}轮：{self.error_info}")
                else:
                    print("  - 未发现可执行浏览任务，可能今日已完成。")
                break

            task = tasks[0]
            info = task.get("generalActivityUrlInfo") or {}
            self.t_id = info.get("id")
            if not self.t_id:
                round_errors.append(f"第{round_index + 1}轮：无法获取任务 t_id")
                continue

            time.sleep(random.randint(10, 15))
            user_task_id = self.complete_task(
                str(task.get("taskId", "")),
                str(self.t_id),
                str(info.get("browsClickUrlId", "")),
            )
            time.sleep(random.randint(2, 4))

            if not user_task_id:
                print("  - completeTask 未取得 userTaskId，使用动态业务参数调用 getTask。")
                user_task_id = self.get_task(str(task.get("taskCode", "")))
                time.sleep(random.randint(2, 4))

            if not user_task_id:
                round_errors.append(
                    f"第{round_index + 1}轮：{self.error_info or '未获取 userTaskId'}"
                )
                print("  - 未获取 userTaskId，本轮无法领取奖励。")
                continue

            if self.receive_award(str(user_task_id)):
                print("  - 本轮奖励领取完成。")
                self.error_info = ""
            else:
                round_errors.append(
                    f"第{round_index + 1}轮：{self.error_info or '奖励领取失败'}"
                )
            time.sleep(random.randint(2, 4))

        final_query_ok = self.query_user_info_and_records()
        if not final_query_ok:
            round_errors.append(self.error_info or "最终数据刷新失败")

        if round_errors:
            self.error_info = "；".join(round_errors)
            return False

        self.error_info = ""
        return True


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
        response = session.get(
            login_url,
            headers={
                "User-Agent": USER_AGENT_DESKTOP,
                "Cookie": f"passToken={pass_token}; userId={user_id};",
            },
            timeout=20,
            allow_redirects=True,
        )
        response.raise_for_status()
        cookies = session.cookies.get_dict()
        c_user_id = cookies.get("cUserId")
        service_token = cookies.get("serviceToken") or cookies.get("jrairstar_serviceToken")
        if c_user_id and service_token:
            parts = [
                f"cUserId={c_user_id}",
                f"jrairstar_serviceToken={service_token}",
            ]
            dynamic_ph = cookies.get("jrairstar_ph")
            dynamic_slh = cookies.get("jrairstar_slh")
            if dynamic_ph:
                parts.append(f"jrairstar_ph={dynamic_ph}")
            if dynamic_slh:
                parts.append(f"jrairstar_slh={dynamic_slh}")

            if dynamic_ph and dynamic_slh:
                print("  - 已获取动态业务 Cookie（jrairstar_ph / jrairstar_slh）。")
            elif dynamic_ph:
                print("  - 已获取动态 jrairstar_ph；未发现 jrairstar_slh。")
            else:
                print("  ⚠️ 登录成功但未获取动态 jrairstar_ph，后续将使用旧版兼容值。")
            return "; ".join(parts)

        print("  ⚠️ 获取的临时会话 Cookie 不完整，可能 passToken 已失效。")
    except requests.RequestException as exc:
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
    task = XiaomiWalletTask(ApiRequest(cookie or ""), user_id=user_id)
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
