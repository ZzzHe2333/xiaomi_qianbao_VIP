"""Shared helpers for the QingLong Xiaomi Wallet scripts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_NAME = "xiaomi_qianbao_VIP"


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

    if qlapi is not None and hasattr(qlapi, "notify"):
        try:
            qlapi.notify(title, content)
            print("✅ 已调用青龙内置通知。")
            return True
        except Exception as exc:
            print(f"⚠️ 青龙内置通知调用失败: {exc}")

    print("ℹ️ 当前执行环境未提供 QLAPI.notify，通知内容已输出到日志。")
    return False
