"""小米钱包账号管理工具。无 cron 注释，不会自动创建定时任务。"""

from __future__ import annotations

import sys

from xiaomi_common import CONFIG_PATH, load_accounts, save_accounts


def list_accounts() -> None:
    accounts = load_accounts()
    if not accounts:
        print("当前没有账号。")
        return
    print(f"配置文件：{CONFIG_PATH}")
    for index, item in enumerate(accounts, 1):
        data = item.get("data", {})
        print(f"{index}. {data.get('us', '未知')} / 小米ID: {data.get('userId', '未登录')}")


def delete_account(alias: str) -> int:
    accounts = load_accounts()
    kept = [item for item in accounts if str(item.get("data", {}).get("us", "")) != alias]
    if len(kept) == len(accounts):
        print(f"未找到账号别名：{alias}")
        return 1
    save_accounts(kept)
    print(f"已删除账号：{alias}")
    return 0


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        list_accounts()
        return 0
    if sys.argv[1] == "delete" and len(sys.argv) >= 3:
        return delete_account(sys.argv[2])
    print("用法：python3 xiaomi_manage.py list | delete <别名>")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
