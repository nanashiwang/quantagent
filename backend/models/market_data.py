from typing import Any, Dict, List

from pydantic import BaseModel, Field


class MarketDataOverviewOut(BaseModel):
    symbols: List[str] = Field(default_factory=list)
    ts_code: str = ""
    data_types: List[str] = Field(default_factory=list)
    records: List[Dict[str, Any]] = Field(default_factory=list)
    price_series: List[Dict[str, Any]] = Field(default_factory=list)
    latest_summary: Dict[str, Any] = Field(default_factory=dict)
    runtime: Dict[str, Any] = Field(default_factory=dict)


class MarketDataSyncResult(BaseModel):
    success: bool
    message: str = ""
    symbol_count: int = 0
    symbols: List[str] = Field(default_factory=list)
    data_types: List[str] = Field(default_factory=list)
    daily_rows: int = 0
    snapshot_rows: int = 0
    range_start: str = ""
    range_end: str = ""
