from fastapi import APIRouter, Body, Depends, Query

from ..auth.dependencies import get_current_user, require_admin
from ..models.market_data import (
    MarketDataOverviewOut,
    MarketDataSyncRequest,
    MarketDataSyncStartOut,
    MarketDataSyncStatusOut,
)
from ..services.market_data_service import MarketDataService
from ..services.market_data_sync_runner import MarketDataSyncRunner

router = APIRouter(prefix="/api/market-data", tags=["行情数据中心"])


def _get_service():
    from ..app import get_sqlite_client

    return MarketDataService(get_sqlite_client())


@router.get("/overview", response_model=MarketDataOverviewOut)
async def get_market_data_overview(
    ts_code: str = "",
    start_date: str = "",
    end_date: str = "",
    limit: int = Query(default=120, ge=1, le=500),
    _=Depends(get_current_user),
):
    result = _get_service().get_overview(
        ts_code=ts_code,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return MarketDataOverviewOut(**result)


@router.post("/sync", response_model=MarketDataSyncStartOut)
async def sync_market_data(
    payload: MarketDataSyncRequest | None = Body(default=None),
    _=Depends(require_admin),
):
    payload = payload or MarketDataSyncRequest()
    result = MarketDataSyncRunner.start_sync(mode=payload.mode, trigger="manual")
    return MarketDataSyncStartOut(**result)


@router.get("/sync/status", response_model=MarketDataSyncStatusOut)
async def get_market_data_sync_status(
    sync_id: str = Query(default=""),
    _=Depends(require_admin),
):
    result = MarketDataSyncRunner.get_status(sync_id=sync_id or None)
    if not result:
        return MarketDataSyncStatusOut(sync_id=sync_id or "", status="unknown")
    return MarketDataSyncStatusOut(**result)
