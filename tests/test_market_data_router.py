import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-market-data-router"

import backend.app as backend_app_module
from backend.auth.jwt_handler import create_access_token
from src.data.db.sqlite_client import SQLiteClient


class TestMarketDataRouter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = SQLiteClient(str(Path(self.temp_dir.name) / "market-router.db"))
        self.original_sqlite_client = backend_app_module._sqlite_client
        backend_app_module._sqlite_client = self.db

    def tearDown(self):
        backend_app_module._sqlite_client = self.original_sqlite_client
        self.temp_dir.cleanup()

    def _auth_headers(self):
        token = create_access_token({"sub": "admin", "role": "admin", "uid": 1})
        return {"Authorization": f"Bearer {token}"}

    def test_sync_endpoint_starts_runner(self):
        with patch(
            "backend.routers.market_data.MarketDataSyncRunner.start_sync",
            return_value={
                "sync_id": "market_data_001",
                "status": "started",
                "mode": "backfill",
                "message": "行情同步任务已创建",
                "reused": False,
            },
        ) as mock_start:
            with TestClient(backend_app_module.app) as client:
                response = client.post(
                    "/api/market-data/sync",
                    headers=self._auth_headers(),
                    json={"mode": "backfill"},
                )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["sync_id"], "market_data_001")
        self.assertEqual(body["mode"], "backfill")
        mock_start.assert_called_once_with(mode="backfill", trigger="manual")

    def test_sync_status_endpoint_returns_runner_status(self):
        with patch(
            "backend.routers.market_data.MarketDataSyncRunner.get_status",
            return_value={
                "sync_id": "market_data_001",
                "status": "running",
                "mode": "incremental",
                "message": "已完成 2/6 个任务",
                "progress": 33,
                "current": 2,
                "total": 6,
                "current_task": "000001.SZ 日线行情",
                "errors": ["600519.SH 资金流向: timeout"],
                "started_at": "2026-03-22T12:00:00",
                "updated_at": "2026-03-22T12:00:05",
                "result": {},
            },
        ) as mock_get:
            with TestClient(backend_app_module.app) as client:
                response = client.get(
                    "/api/market-data/sync/status",
                    headers=self._auth_headers(),
                    params={"sync_id": "market_data_001"},
                )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "running")
        self.assertEqual(body["progress"], 33)
        self.assertEqual(body["errors"], ["600519.SH 资金流向: timeout"])
        mock_get.assert_called_once_with(sync_id="market_data_001")


if __name__ == "__main__":
    unittest.main()
