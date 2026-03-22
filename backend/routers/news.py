from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from ..auth.dependencies import get_current_user, require_admin
from ..models.news import NewsArticleOut, NewsBriefOut, NewsSyncResult
from ..services.news_service import NewsService

router = APIRouter(prefix="/api/news", tags=["资讯中心"])


def _get_service():
    from ..app import get_sqlite_client

    return NewsService(get_sqlite_client())


@router.get("/articles", response_model=List[NewsArticleOut])
async def list_articles(
    keyword: str = "",
    source_id: Optional[int] = None,
    date_from: str = "",
    date_to: str = "",
    limit: int = Query(default=100, ge=1, le=500),
    _=Depends(get_current_user),
):
    rows = _get_service().list_articles(
        keyword=keyword,
        source_id=source_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return [NewsArticleOut(**row) for row in rows]


@router.get("/briefs", response_model=List[NewsBriefOut])
async def list_briefs(limit: int = Query(default=30, ge=1, le=120), _=Depends(get_current_user)):
    rows = _get_service().list_briefs(limit=limit)
    return [NewsBriefOut(**dict(row)) for row in rows]


@router.post("/sync", response_model=NewsSyncResult)
async def sync_news(only_due: bool = False, _=Depends(require_admin)):
    result = _get_service().sync_enabled_sources(only_due=only_due)
    return NewsSyncResult(**result)
