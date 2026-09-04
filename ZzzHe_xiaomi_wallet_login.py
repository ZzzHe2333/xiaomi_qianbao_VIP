"""
ZzzHe 小米钱包扫码登录入口

name: ZzzHe_小米钱包扫码登录
cron: 0 0 29 2 *
"""

from xiaomi_login import main


if __name__ == "__main__":
    raise SystemExit(main())
