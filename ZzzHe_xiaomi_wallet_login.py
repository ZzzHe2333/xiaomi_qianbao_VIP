"""
ZzzHe 小米钱包扫码登录入口

name: ZzzHe_小米钱包扫码登录
cron: 0 0 29 2 *
"""

from xiaomi_common import print_project_banner
from xiaomi_login import main


if __name__ == "__main__":
    print_project_banner("ZzzHe_小米钱包扫码登录")
    raise SystemExit(main())
