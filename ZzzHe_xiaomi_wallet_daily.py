"""
ZzzHe 小米钱包每日任务入口

name: ZzzHe_小米钱包每日任务
cron: 37 8 * * *
"""

from xiaomi_daily import main


if __name__ == "__main__":
    raise SystemExit(main())
