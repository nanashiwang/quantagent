from fastapi import APIRouter, Depends, Query

from ..auth.dependencies import get_current_user, require_admin
from ..models.market_data import MarketDataOverviewOut, MarketDataSyncResult
from ..services.market_data_service import MarketDataService

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


@router.post("/sync", response_model=MarketDataSyncResult)
async def sync_market_data(_=Depends(require_admin)):
    result = _get_service().sync_configured_data(trigger="manual")
    return MarketDataSyncResult(**result)
