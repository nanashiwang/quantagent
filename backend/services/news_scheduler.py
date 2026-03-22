import os

from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger


class NewsScheduler:
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
            id="news-sync",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self.scheduler.start()
        self._started = True
        logger.info("资讯调度器已启动")

    def shutdown(self):
        if not self._started:
            return
        self.scheduler.shutdown(wait=False)
        self._started = False

    def run_once(self):
        from .news_service import NewsService

        try:
            NewsService(self.db).sync_enabled_sources(only_due=True)
        except Exception as exc:
            logger.warning("资讯调度执行失败: {}", exc)


def should_disable_scheduler() -> bool:
    return os.getenv("DISABLE_NEWS_SCHEDULER", "").strip() == "1" or "PYTEST_CURRENT_TEST" in os.environ
