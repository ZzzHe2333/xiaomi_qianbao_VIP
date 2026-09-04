"""Strict sequential multi-account runner for Xiaomi Wallet."""

from __future__ import annotations

from datetime import datetime
from typing import List

from xiaomi_common import CONFIG_PATH, load_accounts, ql_notify, save_accounts
from xiaomi_daily import process_account
from xiaomi_multi import (
    ACCOUNT_INTERVAL_ENV,
    ensure_account_interval_env,
    read_account_interval_minutes,
    sleep_between_accounts,
)


def _alias_of(account: dict, fallback: str) -> str:
    return str(account.get("data", {}).get("us", fallback))


def main() -> int:
    print(f"======= 小米钱包多账号每日任务 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =======")
    print(f"配置文件：{CONFIG_PATH}")
    print("执行模式：严格串行（前一个账号完全执行结束后，才会等待并启动下一个账号）")

    ensure_account_interval_env()
    interval_minutes, interval_reason = read_account_interval_minutes()
    print(f"多账号间隔变量：{ACCOUNT_INTERVAL_ENV}")
    print(f"多账号间隔 B：{interval_minutes} 分钟（{interval_reason}）")
    print(f"账号间随机范围：{30 * interval_minutes}-{60 * interval_minutes} 秒")

    try:
        accounts = load_accounts()
    except Exception as exc:
        message = f"读取配置失败：{exc}"
        print("❌ " + message)
        ql_notify("小米钱包每日任务失败", message, globals().get("QLAPI"))
        return 1

    if not accounts:
        message = "尚未添加账号，请先运行 ZzzHe_小米钱包扫码登录。"
        print("ℹ️ " + message)
        ql_notify("小米钱包未登录", message, globals().get("QLAPI"))
        return 1

    total = len(accounts)
    print(f"检测到账号数量：{total}")
    if total > 1:
        print("多账号模式：已启用")
    else:
        print("多账号模式：当前仅 1 个账号，无账号间隔等待")

    reports: List[str] = []
    success_count = 0

    for index, account in enumerate(accounts):
        alias = _alias_of(account, f"账号{index + 1}")
        print("\n" + "=" * 56)
        print(f"▶ 开始第 {index + 1}/{total} 个账号：{alias}")
        print(f"账号开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 56)

        data = account.setdefault("data", {})
        report, ok = process_account(data)
        finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print("\n" + report)
        print(f"■ 第 {index + 1}/{total} 个账号 {alias} 已完全执行结束：{finished_at}")
        reports.append(report)
        success_count += int(ok)

        # 每个账号执行完立即持久化，避免后续账号异常导致前面结果丢失。
        save_accounts(accounts)

        if index < total - 1:
            next_alias = _alias_of(accounts[index + 1], f"账号{index + 2}")
            # 这里是同步阻塞等待，没有并发；等待结束后才进入下一次循环。
            sleep_between_accounts(alias, next_alias)

    summary = (
        f"执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"执行模式：严格串行\n"
        f"账号数：{total}，成功：{success_count}，异常：{total - success_count}\n"
        f"多账号间隔 B：{interval_minutes} 分钟\n\n"
        + "\n\n--------------------\n\n".join(reports)
    )
    title = "小米钱包每日任务" if success_count == total else "小米钱包每日任务（有异常）"
    ql_notify(title, summary, globals().get("QLAPI"))

    print("\n======= 所有账号串行执行完毕 =======")
    return 0 if success_count == total else 2


if __name__ == "__main__":
    raise SystemExit(main())
