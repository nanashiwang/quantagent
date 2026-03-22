import copy
import threading
from datetime import datetime
from typing import Dict, Optional


def _normalize_mode(mode: str) -> str:
    normalized = str(mode or "").strip().lower()
    if normalized == "backfill":
        return "backfill"
    return "incremental"


class MarketDataSyncRunner:
    """行情同步后台执行器"""

    _status: Dict[str, Dict] = {}
    _lock = threading.Lock()
    _active_sync_id: Optional[str] = None
    _latest_sync_id: Optional[str] = None

    @classmethod
    def start_sync(cls, mode: str = "incremental", trigger: str = "manual") -> Dict:
        mode = _normalize_mode(mode)

        with cls._lock:
            if cls._active_sync_id:
                active_status = cls._status.get(cls._active_sync_id)
                if active_status and active_status.get("status") == "running":
                    return {
                        "sync_id": cls._active_sync_id,
                        "status": "running",
                        "mode": active_status.get("mode", mode),
                        "message": "已有行情同步任务正在执行",
                        "reused": True,
                    }

            sync_id = f"market_data_{datetime.now():%Y%m%d%H%M%S%f}_{mode}"
            now = datetime.now().isoformat(timespec="seconds")
            cls._status[sync_id] = {
                "sync_id": sync_id,
                "status": "running",
                "mode": mode,
                "message": "同步任务已启动",
                "progress": 0,
                "current": 0,
                "total": 0,
                "current_task": "",
                "errors": [],
                "started_at": now,
                "updated_at": now,
                "result": {},
            }
            cls._active_sync_id = sync_id
            cls._latest_sync_id = sync_id

        def _run():
            try:
                from backend.app import get_sqlite_client
                from backend.services.market_data_service import MarketDataService

                service = MarketDataService(get_sqlite_client())
                result = service.sync_configured_data(
                    trigger=trigger,
                    mode=mode,
                    progress_callback=lambda payload: cls._update_progress(sync_id, payload),
                )

                final_status = "completed" if result.get("success", False) else "failed"
                cls._finalize(sync_id, final_status, result.get("message", ""), result)
            except Exception as exc:
                cls._finalize(sync_id, "failed", str(exc), {"success": False, "status": "failed", "errors": [str(exc)]})

        threading.Thread(target=_run, daemon=True).start()
        return {
            "sync_id": sync_id,
            "status": "started",
            "mode": mode,
            "message": "行情同步任务已创建",
            "reused": False,
        }

    @classmethod
    def get_status(cls, sync_id: Optional[str] = None) -> Optional[Dict]:
        with cls._lock:
            target_id = sync_id or cls._active_sync_id or cls._latest_sync_id
            if not target_id:
                return None
            status = cls._status.get(target_id)
            return copy.deepcopy(status) if status else None

    @classmethod
    def _update_progress(cls, sync_id: str, payload: Dict):
        with cls._lock:
            current_status = cls._status.get(sync_id)
            if not current_status:
                return

            current_status["message"] = payload.get("message", current_status["message"])
            current_status["progress"] = payload.get("progress", current_status["progress"])
            current_status["current"] = payload.get("current", current_status["current"])
            current_status["total"] = payload.get("total", current_status["total"])
            current_status["current_task"] = payload.get("current_task", current_status["current_task"])
            current_status["errors"] = list(payload.get("errors", current_status["errors"]))
            current_status["updated_at"] = datetime.now().isoformat(timespec="seconds")

    @classmethod
    def _finalize(cls, sync_id: str, status: str, message: str, result: Dict):
        with cls._lock:
            current_status = cls._status.get(sync_id)
            if not current_status:
                return

            if current_status.get("total", 0) > 0 and status == "completed":
                current_status["progress"] = 100
                current_status["current"] = current_status["total"]

            current_status["status"] = status
            current_status["message"] = message
            current_status["errors"] = list(result.get("errors", current_status["errors"]))
            current_status["result"] = copy.deepcopy(result)
            current_status["updated_at"] = datetime.now().isoformat(timespec="seconds")

            if cls._active_sync_id == sync_id:
                cls._active_sync_id = None
