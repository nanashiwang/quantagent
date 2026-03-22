import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.data.db.sqlite_client import SQLiteClient


DEFAULT_NEWS_SOURCES = [
    {
        "name": "巨潮资讯",
        "type": "cninfo",
        "category": "公告",
        "market": "A股",
        "dedup_strategy": "url",
        "parser": "announcements_api",
        "priority": 1.0,
        "credibility": 1.0,
        "is_enabled": True,
        "fetch_interval": 7200,
        "config": {
            "dataset": "announcements",
            "page_size": 50,
            "column": "szse_latest",
            "plate": "",
        },
    },
    {
        "name": "上交所",
        "type": "crawler",
        "category": "监管动态",
        "market": "上交所",
        "dedup_strategy": "url",
        "parser": "anchor_list",
        "priority": 1.0,
        "credibility": 1.0,
        "is_enabled": True,
        "fetch_interval": 14400,
        "config": {
            "url": "https://www.sse.com.cn/home/component/news/",
            "base_url": "https://www.sse.com.cn",
            "mode": "anchor_list",
            "include_href_keywords": ["/home/component/news/c/"],
            "exclude_title_keywords": ["[时政]"],
            "max_items": 40,
        },
    },
    {
        "name": "深交所",
        "type": "crawler",
        "category": "交易所要闻",
        "market": "深交所",
        "dedup_strategy": "url",
        "parser": "anchor_list",
        "priority": 1.0,
        "credibility": 1.0,
        "is_enabled": True,
        "fetch_interval": 14400,
        "config": {
            "url": "https://www.szse.cn/",
            "base_url": "https://www.szse.cn/",
            "mode": "anchor_list",
            "include_href_keywords": ["/aboutus/trends/news/t"],
            "max_items": 40,
        },
    },
    {
        "name": "证监会",
        "type": "crawler",
        "category": "监管规则",
        "market": "全市场",
        "dedup_strategy": "url",
        "parser": "anchor_list",
        "priority": 1.0,
        "credibility": 1.0,
        "is_enabled": True,
        "fetch_interval": 21600,
        "config": {
            "url": "https://www.csrc.gov.cn/csrc/xwfb/index.shtml",
            "base_url": "https://www.csrc.gov.cn",
            "mode": "anchor_list",
            "include_href_keywords": ["/content.shtml"],
            "max_items": 40,
        },
    },
    {
        "name": "人民银行",
        "type": "crawler",
        "category": "货币政策",
        "market": "宏观",
        "dedup_strategy": "url",
        "parser": "anchor_list",
        "priority": 1.0,
        "credibility": 1.0,
        "is_enabled": True,
        "fetch_interval": 21600,
        "config": {
            "url": "https://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html",
            "base_url": "https://www.pbc.gov.cn",
            "mode": "anchor_list",
            "include_href_keywords": ["/goutongjiaoliu/113456/113469/"],
            "max_items": 40,
        },
    },
    {
        "name": "国家统计局",
        "type": "crawler",
        "category": "数据发布",
        "market": "宏观",
        "dedup_strategy": "url",
        "parser": "anchor_list",
        "priority": 1.0,
        "credibility": 1.0,
        "is_enabled": True,
        "fetch_interval": 21600,
        "config": {
            "url": "https://www.stats.gov.cn/xw/tjxw/",
            "base_url": "https://www.stats.gov.cn/xw/tjxw/",
            "mode": "anchor_list",
            "include_href_keywords": ["./tjdt/", "/tjdt/", "./tzgg/", "/tzgg/"],
            "max_items": 40,
        },
    },
    {
        "name": "Tushare Pro",
        "type": "tushare",
        "category": "新闻/公告/互动/研报",
        "market": "A股",
        "dedup_strategy": "content_hash",
        "parser": "multi_dataset",
        "priority": 0.9,
        "credibility": 0.9,
        "is_enabled": False,
        "fetch_interval": 7200,
        "config": {
            "datasets": [
                {"name": "news", "params": {"src": "sina"}},
                {"name": "anns_d", "params": {}},
                {"name": "irm_qa_sh", "params": {}},
                {"name": "irm_qa_sz", "params": {}},
                {"name": "report_rc", "params": {}},
            ],
            "limit_per_dataset": 50,
        },
    },
    {
        "name": "RSSHub 自建",
        "type": "rsshub",
        "category": "快讯/情绪",
        "market": "全市场",
        "dedup_strategy": "url",
        "parser": "multi_feed",
        "priority": 0.7,
        "credibility": 0.7,
        "is_enabled": False,
        "fetch_interval": 1800,
        "config": {
            "base_url": "http://127.0.0.1:1200",
            "routes": [
                {"path": "/cls/telegraph", "label": "财联社电报"},
                {"path": "/wallstreetcn/news", "label": "华尔街见闻快讯"},
                {"path": "/xueqiu/hotstock", "label": "雪球热股"},
            ],
        },
    },
]


class SourceService:
    def __init__(self, db: SQLiteClient):
        self.db = db

    def _serialize(self, data: Dict) -> Dict:
        payload = data.copy()
        payload["config"] = json.dumps(payload.get("config", {}), ensure_ascii=False)
        return payload

    def _deserialize_row(self, row) -> Dict:
        item = dict(row)
        config = item.get("config")
        if isinstance(config, str):
            try:
                item["config"] = json.loads(config) if config else {}
            except json.JSONDecodeError:
                item["config"] = {}
        return item

    def list_all(self) -> List[Dict]:
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM news_sources ORDER BY priority DESC, id ASC").fetchall()
            return [self._deserialize_row(r) for r in rows]

    def list_enabled(self) -> List[Dict]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM news_sources WHERE is_enabled = 1 ORDER BY priority DESC, id ASC"
            ).fetchall()
            return [self._deserialize_row(r) for r in rows]

    def list_due_sources(self, now: Optional[datetime] = None) -> List[Dict]:
        current = now or datetime.now()
        due_sources = []
        for source in self.list_enabled():
            last_fetched = source.get("last_fetched")
            if not last_fetched:
                due_sources.append(source)
                continue

            try:
                last_dt = datetime.fromisoformat(str(last_fetched))
            except ValueError:
                due_sources.append(source)
                continue

            interval = max(int(source.get("fetch_interval") or 0), 60)
            if current - last_dt >= timedelta(seconds=interval):
                due_sources.append(source)
        return due_sources

    def get_by_id(self, source_id: int) -> Optional[Dict]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM news_sources WHERE id = ?", (source_id,)).fetchone()
            return self._deserialize_row(row) if row else None

    def get_by_name(self, name: str) -> Optional[Dict]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM news_sources WHERE name = ?", (name,)).fetchone()
            return self._deserialize_row(row) if row else None

    def create(self, data: Dict) -> int:
        payload = self._serialize(data)
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO news_sources (
                    name, type, config, is_enabled, fetch_interval,
                    category, market, dedup_strategy, parser, priority, credibility
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["name"],
                    payload["type"],
                    payload["config"],
                    payload.get("is_enabled", True),
                    payload.get("fetch_interval", 3600),
                    payload.get("category", ""),
                    payload.get("market", ""),
                    payload.get("dedup_strategy", "content_hash"),
                    payload.get("parser", ""),
                    payload.get("priority", 0.5),
                    payload.get("credibility", 0.5),
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def update(self, source_id: int, data: Dict):
        payload = self._serialize(data)
        with self.db.get_connection() as conn:
            sets = ", ".join(f"{key} = ?" for key in payload)
            values = list(payload.values()) + [source_id]
            conn.execute(f"UPDATE news_sources SET {sets} WHERE id = ?", values)
            conn.commit()

    def delete(self, source_id: int):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM news_sources WHERE id = ?", (source_id,))
            conn.commit()

    def update_last_fetched(self, source_id: int):
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE news_sources SET last_fetched = ? WHERE id = ?",
                (datetime.now().isoformat(timespec="seconds"), source_id),
            )
            conn.commit()

    def seed_defaults(self):
        for source in DEFAULT_NEWS_SOURCES:
            if self.get_by_name(source["name"]):
                continue
            self.create(source)
