"""Shared helpers for the QingLong Xiaomi Wallet scripts."""

from __future__ import annotations

import builtins
import json
import os
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_NAME = "xiaomi_qianbao_VIP"
PROJECT_URL = "https://github.com/ZzzHe2333/xiaomi_qianbao_VIP"
RANDOM_DELAY_ENV = "ZzzHe2333_xiaomi_qianbao_VIP_suijiyanchi"
RANDOM_DELAY_REMARKS = "随机延迟"
DEFAULT_RANDOM_DELAY_MINUTES = 30
MAX_RANDOM_DELAY_MINUTES = 360


def _get_qlapi() -> Optional[Any]:
    """Return QingLong's built-in QLAPI object when running inside QingLong."""
    return getattr(builtins, "QLAPI", None)


def print_project_banner(task_name: str = "") -> None:
    """Print the ZzzHe Xiaomi Wallet project banner to the QingLong task log."""
    mi_art = (
        "■□□□■  ■■■■■",
        "■■□■■  □□■□□",
        "■□■□■  □□■□□",
        "■□□□■  □□■□□",
        "■□□□■  ■■■■■",
    )
    vip_art = (
        "■□□□■  ■■■■■  ■■■■□",
        "■□□□■  □□■□□  ■□□□■",
        "□■□■□  □□■□□  ■■■■□",
        "□■□■□  □□■□□  ■□□□□",
        "□□■□□  ■■■■■  ■□□□□",
    )

    print("\n" + "=" * 56)
    for line in mi_art:
        print(line)
    print()
    for line in vip_art:
        print(line)
    print("-" * 56)
    if task_name:
        print(f"任务名称：{task_name}")
    print(f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"项目地址：{PROJECT_URL}")
    print("项目说明：本项目永久免费开源，欢迎学习、使用和 Star，请勿付费购买。")
    print("=" * 56 + "\n")


def ensure_qinglong_random_delay_env() -> str:
    """
    Ensure the QingLong environment variable used for random delay exists.

    If it does not exist in QingLong, create it with:
      value   = "30"
      remarks = "随机延迟"

    The newly-created value is also injected into os.environ so the current
    process can use it immediately without waiting for the next task run.
    """
    process_value = os.getenv(RANDOM_DELAY_ENV)
    qlapi = _get_qlapi()

    if qlapi is not None and hasattr(qlapi, "getEnvs") and hasattr(qlapi, "createEnv"):
        try:
            response = qlapi.getEnvs({"searchValue": RANDOM_DELAY_ENV})
            items = response.get("data", []) if isinstance(response, dict) else []
            exact = next(
                (
                    item
                    for item in items
                    if str(item.get("name", "")) == RANDOM_DELAY_ENV
                ),
                None,
            )

            if exact is not None:
                status = int(exact.get("status", 0) or 0)
                db_value = str(exact.get("value", ""))
                remarks = str(exact.get("remarks", "") or "")

                if status == 1:
                    os.environ[RANDOM_DELAY_ENV] = str(DEFAULT_RANDOM_DELAY_MINUTES)
                    print(
                        f"ℹ️ 青龙环境变量 {RANDOM_DELAY_ENV} 已存在但处于禁用状态；"
                        f"本次运行临时使用默认值 {DEFAULT_RANDOM_DELAY_MINUTES}，不会重复创建或自动启用。"
                    )
                    return str(DEFAULT_RANDOM_DELAY_MINUTES)

                if process_value is None or not process_value.strip():
                    os.environ[RANDOM_DELAY_ENV] = db_value
                    process_value = db_value

                remark_text = remarks or "无备注"
                print(
                    f"✅ 已检测到青龙环境变量：{RANDOM_DELAY_ENV}="
                    f"{process_value if process_value is not None else db_value}（备注：{remark_text}）"
                )
                return process_value if process_value is not None else db_value

            create_response = qlapi.createEnv(
                {
                    "envs": [
                        {
                            "name": RANDOM_DELAY_ENV,
                            "value": str(DEFAULT_RANDOM_DELAY_MINUTES),
                            "remarks": RANDOM_DELAY_REMARKS,
                        }
                    ]
                }
            )
            if isinstance(create_response, dict) and create_response.get("code") == 200:
                os.environ[RANDOM_DELAY_ENV] = str(DEFAULT_RANDOM_DELAY_MINUTES)
                print(
                    f"✅ 未检测到青龙环境变量 {RANDOM_DELAY_ENV}，已自动创建："
                    f"值={DEFAULT_RANDOM_DELAY_MINUTES}，备注={RANDOM_DELAY_REMARKS}。"
                )
                return str(DEFAULT_RANDOM_DELAY_MINUTES)

            print(f"⚠️ 自动创建青龙环境变量失败，接口返回：{create_response}")
        except Exception as exc:
            print(f"⚠️ 检测/创建青龙环境变量时发生异常：{exc}")

    # Non-QingLong/older-QingLong fallback: keep the current run usable.
    if process_value is None or not process_value.strip():
        os.environ[RANDOM_DELAY_ENV] = str(DEFAULT_RANDOM_DELAY_MINUTES)
        print(
            f"⚠️ 当前环境无法通过 QLAPI 持久化创建 {RANDOM_DELAY_ENV}；"
            f"本次运行临时使用默认值 {DEFAULT_RANDOM_DELAY_MINUTES}。"
        )
        return str(DEFAULT_RANDOM_DELAY_MINUTES)

    return process_value


def _read_random_delay_minutes() -> Tuple[int, str]:
    """Read and validate the user-configured maximum random delay in minutes."""
    raw = os.getenv(RANDOM_DELAY_ENV)
    if raw is None or not raw.strip():
        return DEFAULT_RANDOM_DELAY_MINUTES, "未读取到环境变量，使用默认值"

    value = raw.strip()
    if not value.isdecimal():
        return DEFAULT_RANDOM_DELAY_MINUTES, f"环境变量值 {value!r} 不是正整数，使用默认值"

    minutes = int(value)
    if not 1 <= minutes <= MAX_RANDOM_DELAY_MINUTES:
        return (
            DEFAULT_RANDOM_DELAY_MINUTES,
            f"环境变量值 {minutes} 不在 1-{MAX_RANDOM_DELAY_MINUTES} 范围内，使用默认值",
        )

    return minutes, "已读取环境变量"


def random_start_delay() -> int:
    """
    Sleep for a random amount before the task starts.

    A is minutes. Actual delay is an integer number of seconds in:
        0.3 * A * 60 <= delay <= A * 60
    For integer A, the lower bound is exactly 18 * A seconds.
    """
    ensure_qinglong_random_delay_env()
    minutes, reason = _read_random_delay_minutes()
    min_seconds = 18 * minutes
    max_seconds = 60 * minutes
    delay_seconds = random.randint(min_seconds, max_seconds)

    start_at = datetime.now() + timedelta(seconds=delay_seconds)
    print("【随机延迟】")
    print(f"环境变量：{RANDOM_DELAY_ENV}")
    print(f"读取结果：{reason}")
    print(f"有效 A 值：{minutes} 分钟")
    print(f"随机范围：{min_seconds}-{max_seconds} 秒")
    print(f"本次随机睡眠：{delay_seconds} 秒（约 {delay_seconds / 60:.2f} 分钟）")
    print(f"预计开始时间：{start_at.strftime('%Y-%m-%d %H:%M:%S')}")

    deadline = time.monotonic() + delay_seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break

        time.sleep(min(30.0, remaining))
        remaining_after_sleep = max(0, int(round(deadline - time.monotonic())))
        now = datetime.now()
        if remaining_after_sleep > 0:
            print(
                f"⏳ 当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')} | "
                f"预计开始：{start_at.strftime('%Y-%m-%d %H:%M:%S')} | "
                f"剩余约 {remaining_after_sleep} 秒",
                flush=True,
            )

    print(f"▶ 随机延迟结束，开始执行：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return delay_seconds


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
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except OSError:
        pass
    return CONFIG_PATH


def load_accounts() -> List[Dict[str, Any]]:
    path = ensure_config()
    try:
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            return []
        data = json.loads(content)
        if not isinstance(data, list):
            raise ValueError("配置文件根节点必须是列表")
        return data
    except Exception as exc:
        raise RuntimeError(f"读取账号配置失败: {exc}") from exc


def save_accounts(accounts: List[Dict[str, Any]]) -> None:
    path = ensure_config()
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(accounts, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def upsert_account(account_data: Dict[str, Any]) -> None:
    alias = str(account_data.get("us", "")).strip()
    if not alias:
        raise ValueError("账号别名不能为空")

    accounts = load_accounts()
    for item in accounts:
        data = item.setdefault("data", {})
        if str(data.get("us", "")).strip() == alias:
            data.update(account_data)
            save_accounts(accounts)
            return

    accounts.append({"data": account_data})
    save_accounts(accounts)


def get_default_alias() -> str:
    configured = os.getenv("XIAOMI_WALLET_ALIAS", "").strip()
    if configured:
        return configured

    try:
        accounts = load_accounts()
    except RuntimeError:
        accounts = []

    if len(accounts) == 1:
        alias = str(accounts[0].get("data", {}).get("us", "")).strip()
        if alias:
            return alias
    return "xiaomi_1"


def ql_notify(title: str, content: str, qlapi: Optional[Any] = None) -> bool:
    """Send through QingLong's built-in notification API when available."""
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
