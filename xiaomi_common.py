"""Shared helpers for the QingLong Xiaomi Wallet scripts."""

from __future__ import annotations

import builtins
import json
import os
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_NAME = "xiaomi_qianbao_VIP"
PROJECT_URL = "https://github.com/ZzzHe2333/xiaomi_qianbao_VIP"

RANDOM_DELAY_ENV = "ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi"
RANDOM_DELAY_REMARKS = "随机延迟"
DEFAULT_RANDOM_DELAY_MINUTES = 30
MAX_RANDOM_DELAY_MINUTES = 360

ACCOUNT_INTERVAL_ENV = "ZzzHe2333_xiaomi_qianbao_VIP_jiangeyanchi"
ACCOUNT_INTERVAL_REMARKS = "多账号间隔延迟（分钟）"
DEFAULT_ACCOUNT_INTERVAL_MINUTES = 3
MAX_ACCOUNT_INTERVAL_MINUTES_EXCLUSIVE = 60

COOKIE_ENV_PREFIX = "ZzzHe2333_xiaomi_qianbao_VIP_ck"


def _get_qlapi() -> Optional[Any]:
    return getattr(builtins, "QLAPI", None)


def _ql_data_dir() -> Path:
    configured = os.getenv("QL_DATA_DIR", "").strip()
    if configured:
        return Path(configured)
    return Path(os.getenv("QL_DIR", "/ql")) / "data"


def _get_auth_token() -> str:
    """Read QingLong's local UI auth token for its loopback API."""
    auth_file = _ql_data_dir() / "config" / "auth.json"
    data = json.loads(auth_file.read_text(encoding="utf-8"))
    token = str(data.get("token", "")).strip()
    if token:
        return token
    tokens = data.get("tokens")
    if isinstance(tokens, dict):
        for value in tokens.values():
            value = str(value or "").strip()
            if value:
                return value
    raise RuntimeError(f"无法从 {auth_file} 读取青龙认证 token")


def _ql_http_request(method: str, path: str, body: Any = None) -> Dict[str, Any]:
    """Call QingLong's local backend API; compatible with v2.17.12."""
    token = _get_auth_token()
    port = int(os.getenv("BACK_PORT", "5600") or "5600")
    payload = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json;charset=UTF-8"
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=payload,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"青龙 API HTTP {exc.code}: {raw[:300]}") from exc
    parsed = json.loads(raw or "{}")
    if not isinstance(parsed, dict):
        raise RuntimeError(f"青龙 API 返回格式异常：{type(parsed).__name__}")
    return parsed


def ql_get_envs(search_value: str) -> List[Dict[str, Any]]:
    qlapi = _get_qlapi()
    if qlapi is not None and hasattr(qlapi, "getEnvs"):
        try:
            result = qlapi.getEnvs({"searchValue": search_value})
            data = result.get("data", []) if isinstance(result, dict) else []
            if isinstance(data, list):
                return data
        except Exception as exc:
            print(f"⚠️ QLAPI.getEnvs 失败，尝试本地 API：{exc}")

    query = urllib.parse.urlencode({"searchValue": search_value})
    result = _ql_http_request("GET", f"/api/envs?{query}")
    data = result.get("data", [])
    return data if isinstance(data, list) else []


def ql_create_env(name: str, value: str, remarks: str = "") -> Dict[str, Any]:
    qlapi = _get_qlapi()
    if qlapi is not None and hasattr(qlapi, "createEnv"):
        try:
            result = qlapi.createEnv(
                {"envs": [{"name": name, "value": value, "remarks": remarks}]}
            )
            if isinstance(result, dict) and result.get("code") == 200:
                return result
        except Exception as exc:
            print(f"⚠️ QLAPI.createEnv 失败，尝试本地 API：{exc}")

    result = _ql_http_request(
        "POST",
        "/api/envs",
        [{"name": name, "value": value, "remarks": remarks}],
    )
    if result.get("code") != 200:
        raise RuntimeError(f"创建青龙环境变量失败：{result}")
    return result


def ql_update_env(item: Dict[str, Any], value: str, remarks: str = "") -> Dict[str, Any]:
    env_id = item.get("id")
    if env_id is None:
        raise RuntimeError("更新环境变量失败：缺少 id")

    qlapi = _get_qlapi()
    if qlapi is not None and hasattr(qlapi, "updateEnv"):
        try:
            result = qlapi.updateEnv(
                {
                    "env": {
                        "id": int(env_id),
                        "name": str(item.get("name", "")),
                        "value": value,
                        "remarks": remarks,
                    }
                }
            )
            if isinstance(result, dict) and result.get("code") == 200:
                return result
        except Exception as exc:
            print(f"⚠️ QLAPI.updateEnv 失败，尝试本地 API：{exc}")

    result = _ql_http_request(
        "PUT",
        "/api/envs",
        {
            "id": int(env_id),
            "name": str(item.get("name", "")),
            "value": value,
            "remarks": remarks,
        },
    )
    if result.get("code") != 200:
        raise RuntimeError(f"更新青龙环境变量失败：{result}")
    return result


def ensure_qinglong_env(name: str, default_value: str, remarks: str) -> str:
    """Ensure an enabled QingLong env exists, returning the value for this run."""
    process_value = os.getenv(name)
    try:
        items = ql_get_envs(name)
        exact = next((item for item in items if str(item.get("name", "")) == name), None)
        if exact is not None:
            if int(exact.get("status", 0) or 0) == 1:
                os.environ[name] = default_value
                print(f"ℹ️ 环境变量 {name} 已存在但被禁用，本次临时使用默认值 {default_value}。")
                return default_value
            value = str(exact.get("value", ""))
            os.environ[name] = value
            print(f"✅ 已检测到青龙环境变量：{name}={value or '(空值)'}")
            return value

        ql_create_env(name, default_value, remarks)
        os.environ[name] = default_value
        print(f"✅ 未检测到环境变量，已自动创建：{name}={default_value}，备注={remarks}")
        return default_value
    except Exception as exc:
        if process_value is not None and process_value.strip():
            print(f"⚠️ 青龙环境变量 API 检测失败，继续使用当前进程值：{exc}")
            return process_value.strip()
        os.environ[name] = default_value
        print(f"⚠️ 青龙环境变量检测/创建失败：{exc}；本次临时使用默认值 {default_value}。")
        return default_value


def _read_positive_int_env(
    name: str,
    default_value: int,
    minimum: int,
    maximum_inclusive: int,
) -> Tuple[int, str]:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default_value, "未读取到有效值，使用默认值"
    value = raw.strip()
    if not value.isdecimal():
        return default_value, f"环境变量值 {value!r} 不是正整数，使用默认值"
    number = int(value)
    if not minimum <= number <= maximum_inclusive:
        return default_value, f"环境变量值 {number} 不在 {minimum}-{maximum_inclusive} 范围内，使用默认值"
    return number, "已读取环境变量"


def _sleep_with_status(delay_seconds: int, title: str, expected_label: str) -> None:
    start_at = datetime.now() + timedelta(seconds=delay_seconds)
    print(f"{title}预计时间：{start_at.strftime('%Y-%m-%d %H:%M:%S')}")
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
                f"{expected_label}：{start_at.strftime('%Y-%m-%d %H:%M:%S')} | "
                f"剩余约 {remaining_after_sleep} 秒",
                flush=True,
            )


def random_start_delay() -> int:
    """Daily-task startup delay: 0.3*A*60 through A*60 seconds."""
    ensure_qinglong_env(
        RANDOM_DELAY_ENV,
        str(DEFAULT_RANDOM_DELAY_MINUTES),
        RANDOM_DELAY_REMARKS,
    )
    minutes, reason = _read_positive_int_env(
        RANDOM_DELAY_ENV,
        DEFAULT_RANDOM_DELAY_MINUTES,
        1,
        MAX_RANDOM_DELAY_MINUTES,
    )
    min_seconds = 18 * minutes
    max_seconds = 60 * minutes
    delay_seconds = random.randint(min_seconds, max_seconds)
    print("【任务启动随机延迟】")
    print(f"环境变量：{RANDOM_DELAY_ENV}")
    print(f"读取结果：{reason}")
    print(f"有效 A 值：{minutes} 分钟")
    print(f"随机范围：{min_seconds}-{max_seconds} 秒")
    print(f"本次随机睡眠：{delay_seconds} 秒（约 {delay_seconds / 60:.2f} 分钟）")
    _sleep_with_status(delay_seconds, "", "预计开始")
    print(f"▶ 启动随机延迟结束：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return delay_seconds


def account_interval_delay(next_account: str = "下一个账号") -> int:
    """Serial multi-account gap: 0.5*B*60 through B*60 seconds."""
    ensure_qinglong_env(
        ACCOUNT_INTERVAL_ENV,
        str(DEFAULT_ACCOUNT_INTERVAL_MINUTES),
        ACCOUNT_INTERVAL_REMARKS,
    )
    minutes, reason = _read_positive_int_env(
        ACCOUNT_INTERVAL_ENV,
        DEFAULT_ACCOUNT_INTERVAL_MINUTES,
        1,
        MAX_ACCOUNT_INTERVAL_MINUTES_EXCLUSIVE - 1,
    )
    min_seconds = 30 * minutes
    max_seconds = 60 * minutes
    delay_seconds = random.randint(min_seconds, max_seconds)
    print("\n【多账号间隔延迟】")
    print(f"环境变量：{ACCOUNT_INTERVAL_ENV}")
    print(f"读取结果：{reason}")
    print(f"有效 B 值：{minutes} 分钟")
    print(f"随机范围：{min_seconds}-{max_seconds} 秒")
    print(f"本次账号间等待：{delay_seconds} 秒（约 {delay_seconds / 60:.2f} 分钟）")
    _sleep_with_status(delay_seconds, "", f"{next_account}预计开始")
    print(f"▶ 账号间隔结束，开始 {next_account}：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return delay_seconds


def _parse_cookie_string(value: str) -> Dict[str, str]:
    value = (value or "").strip()
    if not value:
        return {}
    if value.startswith("{"):
        try:
            obj = json.loads(value)
            if isinstance(obj, dict):
                return {str(k): str(v) for k, v in obj.items() if v is not None}
        except Exception:
            pass
    result: Dict[str, str] = {}
    for part in value.split(";"):
        if "=" not in part:
            continue
        key, item_value = part.split("=", 1)
        result[key.strip()] = item_value.strip()
    return result


def _cookie_value(account_data: Dict[str, Any]) -> str:
    pieces = [
        f"userId={str(account_data.get('userId', '')).strip()}",
        f"passToken={str(account_data.get('passToken', '')).strip()}",
    ]
    security = str(account_data.get("securityToken", "")).strip()
    if security:
        pieces.append(f"securityToken={security}")
    return "; ".join(pieces)


def _cookie_env_index(name: str) -> Optional[int]:
    match = re.fullmatch(re.escape(COOKIE_ENV_PREFIX) + r"(\d+)", name)
    if not match:
        return None
    number = int(match.group(1))
    return number if number > 0 else None


def _all_cookie_env_items() -> List[Dict[str, Any]]:
    by_name: Dict[str, Dict[str, Any]] = {}

    for name, value in os.environ.items():
        if _cookie_env_index(name) is not None:
            by_name[name] = {"name": name, "value": value, "status": 0}

    try:
        for item in ql_get_envs(COOKIE_ENV_PREFIX):
            name = str(item.get("name", ""))
            if _cookie_env_index(name) is not None:
                by_name[name] = item
    except Exception as exc:
        if not by_name:
            print(f"⚠️ 无法从青龙 API 获取 ck 环境变量：{exc}")

    return sorted(
        by_name.values(),
        key=lambda item: _cookie_env_index(str(item.get("name", ""))) or 10**9,
    )


def load_qinglong_cookie_accounts() -> List[Dict[str, Any]]:
    accounts: List[Dict[str, Any]] = []
    for item in _all_cookie_env_items():
        if int(item.get("status", 0) or 0) == 1:
            continue
        name = str(item.get("name", ""))
        parsed = _parse_cookie_string(str(item.get("value", "")))
        user_id = parsed.get("userId", "")
        pass_token = parsed.get("passToken", "")
        if not user_id or not pass_token:
            print(f"⚠️ 跳过 {name}：缺少 userId/passToken。")
            continue
        index = _cookie_env_index(name) or len(accounts) + 1
        accounts.append(
            {
                "data": {
                    "us": f"ck{index}",
                    "envName": name,
                    "userId": user_id,
                    "passToken": pass_token,
                    "securityToken": parsed.get("securityToken", parsed.get("ssecurity", "")),
                }
            }
        )
    return accounts


def save_qinglong_cookie_account(account_data: Dict[str, Any]) -> Tuple[str, bool]:
    """Save one Xiaomi account to ckN. Returns (env_name, created_new)."""
    user_id = str(account_data.get("userId", "")).strip()
    pass_token = str(account_data.get("passToken", "")).strip()
    if not user_id or not pass_token:
        raise ValueError("账号缺少 userId/passToken")

    items = _all_cookie_env_items()
    used_indexes = {
        index
        for item in items
        if (index := _cookie_env_index(str(item.get("name", "")))) is not None
    }

    for item in items:
        if int(item.get("status", 0) or 0) == 1:
            continue
        parsed = _parse_cookie_string(str(item.get("value", "")))
        if parsed.get("userId") == user_id:
            name = str(item.get("name", ""))
            index = _cookie_env_index(name) or 1
            value = _cookie_value(account_data)
            ql_update_env(item, value, f"小米钱包账号{index}")
            os.environ[name] = value
            return name, False

    index = 1
    while index in used_indexes:
        index += 1
    name = f"{COOKIE_ENV_PREFIX}{index}"
    value = _cookie_value(account_data)
    ql_create_env(name, value, f"小米钱包账号{index}")
    os.environ[name] = value
    return name, True


def _default_config_path() -> Path:
    override = os.getenv("XIAOMI_WALLET_CONFIG", "").strip()
    if override:
        return Path(override).expanduser()
    ql_data = Path("/ql/data")
    if ql_data.exists():
        return ql_data / "config" / PROJECT_NAME / "xiaomiconfig.json"
    return Path(__file__).resolve().parent / "data" / "xiaomiconfig.json"


CONFIG_PATH = _default_config_path()


def ensure_config() -> Path:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text("[]\n", encoding="utf-8")
    return CONFIG_PATH


def load_accounts() -> List[Dict[str, Any]]:
    """Legacy JSON config reader, kept only for automatic migration."""
    path = ensure_config()
    try:
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            return []
        data = json.loads(content)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def migrate_legacy_accounts_if_needed() -> int:
    if load_qinglong_cookie_accounts():
        return 0
    legacy = load_accounts()
    migrated = 0
    if not legacy:
        return 0
    print("ℹ️ 检测到旧版 xiaomiconfig.json，开始自动迁移到 ck 环境变量。")
    for item in legacy:
        data = item.get("data", {}) if isinstance(item, dict) else {}
        if data.get("userId") and data.get("passToken"):
            try:
                name, _ = save_qinglong_cookie_account(data)
                print(f"  ✅ 已迁移到 {name}")
                migrated += 1
            except Exception as exc:
                print(f"  ⚠️ 迁移账号失败：{exc}")
    return migrated


def ql_notify(title: str, content: str, qlapi: Optional[Any] = None) -> bool:
    enabled = os.getenv("XIAOMI_WALLET_NOTIFY", "1").strip().lower()
    if enabled in {"0", "false", "off", "no"}:
        return False
    if qlapi is None:
        qlapi = _get_qlapi()
    if qlapi is not None and hasattr(qlapi, "notify"):
        try:
            qlapi.notify(title, content)
            print("✅ 已调用青龙内置通知。")
            return True
        except Exception as exc:
            print(f"⚠️ 青龙内置通知调用失败: {exc}")
    print("ℹ️ 当前执行环境未提供 QLAPI.notify，通知内容已输出到日志。")
    return False
