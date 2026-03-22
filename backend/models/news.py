from typing import Optional

from pydantic import BaseModel, Field


class NewsArticleOut(BaseModel):
    id: int
    source_id: Optional[int] = None
    source_name: str = ""
    source_type: str = ""
    source_market: str = ""
    source_category: str = ""
    source_priority: float = 0.5
    source_credibility: float = 0.5
    title: str
    summary: str = ""
    content: str = ""
    url: str = ""
    published_at: Optional[str] = None
    symbols: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    importance: float = 0.5
    created_at: Optional[str] = None


class NewsBriefOut(BaseModel):
    id: int
    date: str
    content: str
    source: Optional[str] = None
    created_at: Optional[str] = None


class NewsSyncResult(BaseModel):
    success: bool
    fetched_sources: int = 0
    inserted_articles: int = 0
    duplicate_articles: int = 0
    message: str = ""
