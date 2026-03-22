import os

from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger


class MarketDataScheduler:
    def __init__(self, db):
        self.db = db
        self.scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
        self._started = False

    def start(self):
        if self._started:
            return
        self.scheduler.add_job(
            self.run_once,
            "interval",
            seconds=60,
            id="market-data-sync",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self.scheduler.start()
        self._started = True
        logger.info("行情数据调度器已启动")

    def shutdown(self):
        if not self._started:
            return
        self.scheduler.shutdown(wait=False)
        self._started = False

    def run_once(self):
        from .market_data_service import MarketDataService

        try:
            MarketDataService(self.db).sync_if_due()
        except Exception as exc:
            logger.warning("行情数据调度执行失败: {}", exc)


def should_disable_market_data_scheduler() -> bool:
    return os.getenv("DISABLE_MARKET_DATA_SCHEDULER", "").strip() == "1" or "PYTEST_CURRENT_TEST" in os.environ
