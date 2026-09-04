"""
ZzzHe 小米钱包每日任务入口

name: ZzzHe_小米钱包每日任务
cron: 37 8 * * *
"""

from xiaomi_common import print_project_banner, random_start_delay
from xiaomi_daily import main


if __name__ == "__main__":
    print_project_banner("ZzzHe_小米钱包每日任务")
    random_start_delay()
    raise SystemExit(main())
