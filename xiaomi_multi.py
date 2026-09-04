"""Multi-account helpers for xiaomi_qianbao_VIP."""

from __future__ import annotations

import json
import os
import random
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from xiaomi_common import load_accounts

ACCOUNT_INTERVAL_ENV = "ZzzHe2333_xiaomi_qianbao_VIP_jiangeyanchi"
ACCOUNT_INTERVAL_DEFAULT_MINUTES = 3
ACCOUNT_INTERVAL_MIN_MINUTES = 1
ACCOUNT_INTERVAL_MAX_EXCLUSIVE = 60
ACCOUNT_INTERVAL_REMARKS = "多账号间隔延迟（分钟）"


def _ql_dir() -> str:
    return os.getenv("QL_DIR", "/ql").rstrip("/") or "/ql"


def _get_internal_token() -> str:
    ql_dir = _ql_dir()
    shell = (
        f'. "{ql_dir}/shell/share.sh"; '
        f'. "{ql_dir}/shell/api.sh"; '
        'get_token; printf "%s" "$__ql_token__"'
    )
    return subprocess.check_output(
        ["bash", "-lc", shell],
        text=True,
        stderr=subprocess.DEVNULL,
        timeout=20,
    ).strip()


def _request_json(method: str, path: str, token: str, body: Any = None) -> Dict[str, Any]:
    payload = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json;charset=UTF-8"

    request = urllib.request.Request(
        f"http://127.0.0.1:5600{path}",
        data=payload,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read().decode("utf-8", errors="replace")
    return json.loads(raw) if raw else {}


def ensure_account_interval_env() -> str:
    """Ensure the QingLong account-interval variable exists and return its value."""
    current = os.getenv(ACCOUNT_INTERVAL_ENV)
    if current is not None and current.strip():
        return current.strip()

    try:
        token = _get_internal_token()
        query = urllib.parse.quote(ACCOUNT_INTERVAL_ENV, safe="")
        found = _request_json("GET", f"/open/envs?searchValue={query}", token)
        items = found.get("data", []) if isinstance(found, dict) else []
        exact = next(
            (
                item
                for item in items
                if isinstance(item, dict) and str(item.get("name", "")) == ACCOUNT_INTERVAL_ENV
            ),
            None,
        )

        if exact is not None:
            if int(exact.get("status", 0) or 0) == 1:
                value = str(ACCOUNT_INTERVAL_DEFAULT_MINUTES)
                os.environ[ACCOUNT_INTERVAL_ENV] = value
                print(
                    f"ℹ️ 环境变量 {ACCOUNT_INTERVAL_ENV} 已存在但被禁用；"
                    f"本次临时使用默认值 {value} 分钟。"
                )
                return value

            value = str(exact.get("value", ""))
            os.environ[ACCOUNT_INTERVAL_ENV] = value
            return value

        created = _request_json(
            "POST",
            "/open/envs",
            token,
            [
                {
                    "name": ACCOUNT_INTERVAL_ENV,
                    "value": str(ACCOUNT_INTERVAL_DEFAULT_MINUTES),
                    "remarks": ACCOUNT_INTERVAL_REMARKS,
                }
            ],
        )
        if created.get("code") == 200:
            value = str(ACCOUNT_INTERVAL_DEFAULT_MINUTES)
            os.environ[ACCOUNT_INTERVAL_ENV] = value
            print(
                f"✅ 已自动创建青龙环境变量：{ACCOUNT_INTERVAL_ENV}={value}，"
                f"备注={ACCOUNT_INTERVAL_REMARKS}"
            )
            return value
        print(f"⚠️ 自动创建多账号间隔变量失败：{created}")
    except Exception as exc:
        print(f"⚠️ 检测/创建多账号间隔变量失败：{exc}")

    value = str(ACCOUNT_INTERVAL_DEFAULT_MINUTES)
    os.environ[ACCOUNT_INTERVAL_ENV] = value
    print(f"⚠️ 本次临时使用默认多账号间隔 B={value} 分钟。")
    return value


def read_account_interval_minutes() -> Tuple[int, str]:
    raw = ensure_account_interval_env().strip()
    if not raw.isdecimal():
        return (
            ACCOUNT_INTERVAL_DEFAULT_MINUTES,
            f"环境变量值 {raw!r} 不是正整数，使用默认值",
        )

    minutes = int(raw)
    if not ACCOUNT_INTERVAL_MIN_MINUTES <= minutes < ACCOUNT_INTERVAL_MAX_EXCLUSIVE:
        return (
            ACCOUNT_INTERVAL_DEFAULT_MINUTES,
            f"环境变量值 {minutes} 不满足 1 <= B < 60，使用默认值",
        )

    return minutes, "已读取有效环境变量"


def sleep_between_accounts(current_alias: str, next_alias: str) -> int:
    """Serial-only delay between two completed/next accounts."""
    minutes, reason = read_account_interval_minutes()
    min_seconds = 30 * minutes
    max_seconds = 60 * minutes
    delay_seconds = random.randint(min_seconds, max_seconds)
    start_at = datetime.now() + timedelta(seconds=delay_seconds)

    print("\n【多账号间隔延迟】")
    print(f"已完成账号：{current_alias}")
    print(f"下一个账号：{next_alias}")
    print(f"环境变量：{ACCOUNT_INTERVAL_ENV}")
    print(f"读取结果：{reason}")
    print(f"有效 B 值：{minutes} 分钟")
    print(f"随机范围：{min_seconds}-{max_seconds} 秒")
    print(f"本次等待：{delay_seconds} 秒（约 {delay_seconds / 60:.2f} 分钟）")
    print(f"预计下一个账号开始时间：{start_at.strftime('%Y-%m-%d %H:%M:%S')}")

    deadline = time.monotonic() + delay_seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(30.0, remaining))
        remaining_after_sleep = max(0, int(round(deadline - time.monotonic())))
        if remaining_after_sleep > 0:
            print(
                f"⏳ 当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                f"下一个账号：{next_alias} | "
                f"预计开始：{start_at.strftime('%Y-%m-%d %H:%M:%S')} | "
                f"剩余约 {remaining_after_sleep} 秒",
                flush=True,
            )

    print(
        f"▶ 账号间隔结束，准备执行 {next_alias}："
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    return delay_seconds


def get_next_login_alias() -> Tuple[str, bool]:
    """Return (alias, explicit_alias). Without XIAOMI_WALLET_ALIAS, pick next xiaomi_N."""
    configured = os.getenv("XIAOMI_WALLET_ALIAS", "").strip()
    if configured:
        return configured, True

    try:
        accounts = load_accounts()
    except Exception:
        accounts = []

    used = {
        str(item.get("data", {}).get("us", "")).strip()
        for item in accounts
        if isinstance(item, dict)
    }
    index = 1
    while f"xiaomi_{index}" in used:
        index += 1
    return f"xiaomi_{index}", False


def existing_alias_for_user(user_id: str) -> str:
    try:
        accounts: List[Dict[str, Any]] = load_accounts()
    except Exception:
        return ""

    for item in accounts:
        data = item.get("data", {}) if isinstance(item, dict) else {}
        if str(data.get("userId", "")) == str(user_id):
            return str(data.get("us", "")).strip()
    return ""
