from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ..auth.dependencies import get_current_user, require_admin
from ..models.settings import NewsSourceCreate, NewsSourceOut
from ..services.news_service import NewsService
from ..services.source_service import SourceService

router = APIRouter(prefix="/api/sources", tags=["资讯源管理"])


def _get_source_service():
    from ..app import get_sqlite_client

    return SourceService(get_sqlite_client())


def _get_news_service():
    from ..app import get_sqlite_client

    return NewsService(get_sqlite_client())


@router.get("", response_model=List[NewsSourceOut])
async def list_sources(_=Depends(get_current_user)):
    svc = _get_source_service()
    rows = svc.list_all()
    return [NewsSourceOut(**row) for row in rows]


@router.post("", response_model=NewsSourceOut)
async def create_source(data: NewsSourceCreate, _=Depends(require_admin)):
    svc = _get_source_service()
    source_id = svc.create(data.model_dump())
    row = svc.get_by_id(source_id)
    return NewsSourceOut(**row)


@router.put("/{source_id}", response_model=NewsSourceOut)
async def update_source(source_id: int, data: NewsSourceCreate, _=Depends(require_admin)):
    svc = _get_source_service()
    if not svc.get_by_id(source_id):
        raise HTTPException(status_code=404, detail="资讯源不存在")
    svc.update(source_id, data.model_dump())
    row = svc.get_by_id(source_id)
    return NewsSourceOut(**row)


@router.delete("/{source_id}")
async def delete_source(source_id: int, _=Depends(require_admin)):
    svc = _get_source_service()
    if not svc.get_by_id(source_id):
        raise HTTPException(status_code=404, detail="资讯源不存在")
    svc.delete(source_id)
    return {"detail": "已删除"}


@router.post("/{source_id}/fetch")
async def fetch_source(source_id: int, _=Depends(require_admin)):
    try:
        result = _get_news_service().fetch_source(source_id)
        return {
            "success": True,
            "count": result["fetched"],
            "inserted": result["inserted"],
            "duplicates": result["duplicates"],
            "articles": result["articles"],
        }
    except ValueError as exc:
        status_code = 404 if str(exc) == "资讯源不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    except Exception as exc:
        return {"success": False, "message": str(exc)}
