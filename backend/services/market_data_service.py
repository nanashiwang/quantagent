import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd

from backend.services.settings_service import SettingsService
from src.data.db.sqlite_client import SQLiteClient
from src.data.sources.tushare_api import TushareAPI


SUPPORTED_DATA_TYPES = ("daily", "daily_basic", "moneyflow", "top_list")
DEFAULT_DATA_TYPES = ("daily", "daily_basic", "moneyflow")


def _parse_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value, default: int, minimum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(parsed, minimum)


def _parse_csv(value: str) -> List[str]:
    if not value:
        return []
    normalized = str(value).replace("\n", ",").replace("，", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def _normalize_trade_date(value) -> str:
    if value in (None, ""):
        return ""

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")

    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return text[:10]


def _clean_value(value):
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value
    return value


class MarketDataService:
    def __init__(self, db: SQLiteClient):
        self.db = db
        self.settings = SettingsService(db)

    def get_sync_settings(self) -> Dict:
        raw_types = _parse_csv(self.settings.get_raw_value("market_data", "data_types") or "")
        data_types = [item for item in raw_types if item in SUPPORTED_DATA_TYPES]
        if not data_types:
            data_types = list(DEFAULT_DATA_TYPES)

        return {
            "symbols": _parse_csv(self.settings.get_raw_value("market_data", "symbols") or ""),
            "data_types": data_types,
            "fetch_interval": _parse_int(
                self.settings.get_raw_value("market_data", "fetch_interval"),
                default=3600,
                minimum=60,
            ),
            "history_days": _parse_int(
                self.settings.get_raw_value("market_data", "history_days"),
                default=30,
                minimum=1,
            ),
            "auto_sync": _parse_bool(self.settings.get_raw_value("market_data", "auto_sync")),
        }

    def get_runtime_status(self) -> Dict:
        return {
            "last_sync_at": self.settings.get_raw_value("market_data_runtime", "last_sync_at") or "",
            "last_sync_status": self.settings.get_raw_value("market_data_runtime", "last_sync_status") or "",
            "last_sync_message": self.settings.get_raw_value("market_data_runtime", "last_sync_message") or "",
        }

    def sync_if_due(self) -> Dict:
        settings = self.get_sync_settings()
        if not settings["auto_sync"] or not settings["symbols"]:
            return {"success": False, "skipped": True, "message": "自动同步未启用或股票池为空"}

        last_sync_at = self.get_runtime_status()["last_sync_at"]
        if last_sync_at:
            try:
                last_sync_dt = datetime.fromisoformat(last_sync_at)
            except ValueError:
                last_sync_dt = None
            if last_sync_dt is not None:
                elapsed = datetime.now() - last_sync_dt
                if elapsed < timedelta(seconds=settings["fetch_interval"]):
                    return {"success": False, "skipped": True, "message": "未达到下一次同步间隔"}

        return self.sync_configured_data(trigger="scheduler")

    def sync_configured_data(self, trigger: str = "manual") -> Dict:
        settings = self.get_sync_settings()
        symbols = settings["symbols"]
        data_types = settings["data_types"]
        if not symbols:
            raise ValueError("请先配置需要拉取的股票代码")
        if not data_types:
            raise ValueError("请先选择至少一种拉取信息")

        token = self.settings.get_raw_value("tushare", "token")
        if not token:
            raise ValueError("请先配置 Tushare Token")
        api_url = self.settings.get_raw_value("tushare", "api_url") or ""

        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=settings["history_days"])
        end_date = end_dt.strftime("%Y%m%d")
        start_date = start_dt.strftime("%Y%m%d")

        api = TushareAPI(token, api_url=api_url)
        daily_rows = 0
        snapshot_rows = 0

        try:
            if "top_list" in data_types:
                top_df = api.get_top_list(end_date)
                if symbols:
                    top_df = top_df[top_df["ts_code"].isin(symbols)] if not top_df.empty and "ts_code" in top_df.columns else top_df
                snapshot_rows += self._store_snapshot_rows(top_df, "top_list")

            for ts_code in symbols:
                if "daily" in data_types:
                    daily_rows += self._store_daily_rows(api.get_daily_data(ts_code, start_date, end_date))
                if "daily_basic" in data_types:
                    snapshot_rows += self._store_snapshot_rows(
                        api.get_daily_basic(ts_code, start_date, end_date),
                        "daily_basic",
                    )
                if "moneyflow" in data_types:
                    snapshot_rows += self._store_snapshot_rows(
                        api.get_moneyflow(ts_code, start_date, end_date),
                        "moneyflow",
                    )
        except Exception as exc:
            self._update_runtime("failed", f"{trigger} 同步失败: {exc}")
            raise

        message = (
            f"{trigger} 同步完成，股票 {len(symbols)} 只，"
            f"日线 {daily_rows} 行，扩展指标 {snapshot_rows} 行"
        )
        self._update_runtime("success", message)
        return {
            "success": True,
            "message": message,
            "symbol_count": len(symbols),
            "symbols": symbols,
            "data_types": data_types,
            "daily_rows": daily_rows,
            "snapshot_rows": snapshot_rows,
            "range_start": start_dt.strftime("%Y-%m-%d"),
            "range_end": end_dt.strftime("%Y-%m-%d"),
        }

    def get_overview(
        self,
        ts_code: str = "",
        start_date: str = "",
        end_date: str = "",
        limit: int = 120,
    ) -> Dict:
        settings = self.get_sync_settings()
        symbols = settings["symbols"]
        selected_symbol = ts_code or (symbols[0] if symbols else "")
        runtime = self.get_runtime_status()

        if not selected_symbol:
            return {
                "symbols": [],
                "ts_code": "",
                "data_types": settings["data_types"],
                "records": [],
                "price_series": [],
                "latest_summary": {},
                "runtime": runtime,
            }

        records = self.list_records(
            ts_code=selected_symbol,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        price_series = [
            {
                "trade_date": row["trade_date"],
                "close": row.get("close"),
                "volume": row.get("volume"),
            }
            for row in reversed(records)
            if row.get("close") is not None
        ]
        latest = records[0] if records else {}
        latest_summary = {
            "trade_date": latest.get("trade_date", ""),
            "close": latest.get("close"),
            "open": latest.get("open"),
            "high": latest.get("high"),
            "low": latest.get("low"),
            "volume": latest.get("volume"),
            "amount": latest.get("amount"),
            "turnover_rate": latest.get("turnover_rate"),
            "pe": latest.get("pe"),
            "pb": latest.get("pb"),
            "net_mf_amount": latest.get("net_mf_amount"),
        }
        return {
            "symbols": symbols,
            "ts_code": selected_symbol,
            "data_types": settings["data_types"],
            "records": records,
            "price_series": price_series,
            "latest_summary": latest_summary,
            "runtime": runtime,
        }

    def list_records(
        self,
        ts_code: str,
        start_date: str = "",
        end_date: str = "",
        limit: int = 120,
    ) -> List[Dict]:
        limit = max(1, min(limit, 500))
        daily_rows = self._query_daily_rows(ts_code, start_date, end_date, limit)
        snapshot_rows = self._query_snapshot_rows(ts_code, start_date, end_date, limit * 4)

        merged: Dict[str, Dict] = {}
        for row in daily_rows:
            trade_date = row["trade_date"]
            merged[trade_date] = {
                "trade_date": trade_date,
                "ts_code": row["ts_code"],
                "open": row["open"],
                "close": row["close"],
                "high": row["high"],
                "low": row["low"],
                "volume": row["volume"],
                "amount": row["amount"],
            }

        for row in snapshot_rows:
            trade_date = row["trade_date"]
            entry = merged.setdefault(trade_date, {"trade_date": trade_date, "ts_code": row["ts_code"]})
            metrics = json.loads(row["metrics_json"] or "{}")
            self._merge_metrics(entry, row["dataset"], metrics)

        return sorted(merged.values(), key=lambda item: item["trade_date"], reverse=True)[:limit]

    def _query_daily_rows(self, ts_code: str, start_date: str, end_date: str, limit: int):
        sql = "SELECT * FROM stock_data WHERE ts_code = ?"
        values: List = [ts_code]
        if start_date:
            sql += " AND trade_date >= ?"
            values.append(start_date)
        if end_date:
            sql += " AND trade_date <= ?"
            values.append(end_date)
        sql += " ORDER BY trade_date DESC LIMIT ?"
        values.append(limit)
        with self.db.get_connection() as conn:
            return conn.execute(sql, values).fetchall()

    def _query_snapshot_rows(self, ts_code: str, start_date: str, end_date: str, limit: int):
        sql = "SELECT * FROM market_data_snapshots WHERE ts_code = ?"
        values: List = [ts_code]
        if start_date:
            sql += " AND trade_date >= ?"
            values.append(start_date)
        if end_date:
            sql += " AND trade_date <= ?"
            values.append(end_date)
        sql += " ORDER BY trade_date DESC LIMIT ?"
        values.append(limit)
        with self.db.get_connection() as conn:
            return conn.execute(sql, values).fetchall()

    def _store_daily_rows(self, frame: Optional[pd.DataFrame]) -> int:
        if frame is None or frame.empty:
            return 0

        rows = 0
        with self.db.get_connection() as conn:
            for record in frame.to_dict("records"):
                conn.execute(
                    """
                    INSERT INTO stock_data (ts_code, trade_date, open, close, high, low, volume, amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ts_code, trade_date) DO UPDATE SET
                        open = excluded.open,
                        close = excluded.close,
                        high = excluded.high,
                        low = excluded.low,
                        volume = excluded.volume,
                        amount = excluded.amount
                    """,
                    (
                        record.get("ts_code"),
                        _normalize_trade_date(record.get("trade_date")),
                        _clean_value(record.get("open")),
                        _clean_value(record.get("close")),
                        _clean_value(record.get("high")),
                        _clean_value(record.get("low")),
                        _clean_value(record.get("vol") or record.get("volume")),
                        _clean_value(record.get("amount")),
                    ),
                )
                rows += 1
            conn.commit()
        return rows

    def _store_snapshot_rows(self, frame: Optional[pd.DataFrame], dataset: str) -> int:
        if frame is None or frame.empty:
            return 0

        rows = 0
        with self.db.get_connection() as conn:
            for record in frame.to_dict("records"):
                ts_code = record.get("ts_code")
                trade_date = _normalize_trade_date(record.get("trade_date"))
                if not ts_code or not trade_date:
                    continue

                metrics = {
                    key: _clean_value(value)
                    for key, value in record.items()
                    if key not in {"ts_code", "trade_date"}
                }
                conn.execute(
                    """
                    INSERT INTO market_data_snapshots (ts_code, trade_date, dataset, metrics_json, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(ts_code, trade_date, dataset) DO UPDATE SET
                        metrics_json = excluded.metrics_json,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        ts_code,
                        trade_date,
                        dataset,
                        json.dumps(metrics, ensure_ascii=False),
                    ),
                )
                rows += 1
            conn.commit()
        return rows

    def _merge_metrics(self, target: Dict, dataset: str, metrics: Dict):
        if dataset == "daily_basic":
            for key in ("turnover_rate", "volume_ratio", "pe", "pb"):
                if key in metrics:
                    target[key] = metrics[key]
            return

        if dataset == "moneyflow":
            for key in (
                "buy_lg_amount",
                "sell_lg_amount",
                "buy_elg_amount",
                "sell_elg_amount",
                "net_mf_amount",
                "net_mf_vol",
            ):
                if key in metrics:
                    target[key] = metrics[key]
            return

        if dataset == "top_list":
            if "reason" in metrics:
                target["top_reason"] = metrics["reason"]
            if "net_amount" in metrics:
                target["top_net_amount"] = metrics["net_amount"]

    def _update_runtime(self, status: str, message: str):
        timestamp = datetime.now().isoformat(timespec="seconds")
        self.settings.update_settings(
            "market_data_runtime",
            [
                {"key": "last_sync_at", "value": timestamp, "is_secret": False},
                {"key": "last_sync_status", "value": status, "is_secret": False},
                {"key": "last_sync_message", "value": message, "is_secret": False},
            ],
        )
