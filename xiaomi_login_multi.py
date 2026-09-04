"""Multi-account login wrapper for Xiaomi Wallet."""

from __future__ import annotations

from datetime import datetime

from xiaomi_common import CONFIG_PATH, ql_notify, upsert_account
from xiaomi_login import get_login_qr, poll_login, print_qr
from xiaomi_multi import existing_alias_for_user, get_next_login_alias


def main() -> int:
    suggested_alias, explicit_alias = get_next_login_alias()

    print("======= 小米钱包多账号扫码登录 =======")
    print(f"凭证保存位置：{CONFIG_PATH}")
    if explicit_alias:
        print(f"账号别名：{suggested_alias}（来自 XIAOMI_WALLET_ALIAS，用于指定新增/刷新账号）")
    else:
        print(f"账号别名：{suggested_alias}（自动分配）")
        print("多账号模式：重复运行本扫码任务，会自动分配 xiaomi_1 / xiaomi_2 / xiaomi_3 ...")
        print("如需刷新指定账号，可设置 XIAOMI_WALLET_ALIAS 后再运行。")

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

    alias = suggested_alias
    if not explicit_alias:
        existing_alias = existing_alias_for_user(result["userId"])
        if existing_alias:
            alias = existing_alias
            print(f"ℹ️ 检测到该小米账号已存在，将刷新原账号别名：{alias}")

    account_data = {
        "us": alias,
        **result,
        "updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    upsert_account(account_data)

    print("✅ 登录成功，长效凭证已写入青龙持久化配置目录。")
    print(f"账号别名：{alias}")
    print(f"小米 User ID：{result['userId']}")
    print("passToken/securityToken 不会输出到日志。")

    ql_notify(
        "小米钱包登录成功",
        f"账号别名：{alias}\n小米ID：{result['userId']}\n凭证已保存，可执行多账号每日任务。",
        globals().get("QLAPI"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
