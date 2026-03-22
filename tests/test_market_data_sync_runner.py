import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.market_data_sync_runner import MarketDataSyncRunner


def _fake_sync(self, trigger="manual", mode="incremental", progress_callback=None):
    if progress_callback is not None:
        progress_callback(
            {
                "current": 1,
                "total": 2,
                "progress": 50,
                "current_task": "000001.SZ 日线行情",
                "message": "已完成 1/2 个任务",
                "errors": [],
            }
        )
    return {
        "success": True,
        "status": "success",
        "message": f"{trigger} {mode} 完成",
        "mode": mode,
        "errors": [],
    }


class TestMarketDataSyncRunner(unittest.TestCase):
    def setUp(self):
        MarketDataSyncRunner._status = {}
        MarketDataSyncRunner._active_sync_id = None
        MarketDataSyncRunner._latest_sync_id = None

    def tearDown(self):
        MarketDataSyncRunner._status = {}
        MarketDataSyncRunner._active_sync_id = None
        MarketDataSyncRunner._latest_sync_id = None

    def test_start_sync_updates_progress_and_final_status(self):
        with patch("backend.app.get_sqlite_client", return_value=None), patch(
            "backend.services.market_data_service.MarketDataService.sync_configured_data",
            new=_fake_sync,
        ):
            result = MarketDataSyncRunner.start_sync(mode="backfill", trigger="manual")

            status = None
            for _ in range(30):
                status = MarketDataSyncRunner.get_status(result["sync_id"])
                if status and status["status"] != "running":
                    break
                time.sleep(0.05)

        self.assertIsNotNone(status)
        self.assertEqual(status["mode"], "backfill")
        self.assertEqual(status["status"], "completed")
        self.assertEqual(status["progress"], 100)
        self.assertEqual(status["result"]["status"], "success")

    def test_start_sync_reuses_active_task(self):
        with patch("backend.app.get_sqlite_client", return_value=None), patch(
            "backend.services.market_data_service.MarketDataService.sync_configured_data",
            side_effect=lambda *args, **kwargs: time.sleep(0.2) or {
                "success": True,
                "status": "success",
                "message": "manual incremental 完成",
                "mode": "incremental",
                "errors": [],
            },
        ):
            first = MarketDataSyncRunner.start_sync(mode="incremental", trigger="manual")
            second = MarketDataSyncRunner.start_sync(mode="backfill", trigger="manual")

            self.assertEqual(second["sync_id"], first["sync_id"])
            self.assertTrue(second["reused"])

            for _ in range(30):
                status = MarketDataSyncRunner.get_status(first["sync_id"])
                if status and status["status"] != "running":
                    break
                time.sleep(0.05)


if __name__ == "__main__":
    unittest.main()
