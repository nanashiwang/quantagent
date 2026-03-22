import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.news_service import NewsService
from backend.services.source_service import SourceService
from src.data.db.sqlite_client import SQLiteClient


class TestNewsService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = SQLiteClient(str(Path(self.temp_dir.name) / "news.db"))
        self.sources = SourceService(self.db)
        self.source_id = self.sources.create(
            {
                "name": "测试资讯源",
                "type": "crawler",
                "config": {"url": "https://example.com"},
                "is_enabled": True,
                "fetch_interval": 3600,
                "category": "测试",
                "market": "A股",
                "dedup_strategy": "content_hash",
                "parser": "anchor_list",
                "priority": 0.8,
                "credibility": 0.9,
            }
        )
        self.service = NewsService(self.db)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_store_articles_deduplicates_by_hash(self):
        article = {
            "title": "测试标题",
            "summary": "测试摘要",
            "content": "测试内容",
            "url": "",
            "published_at": "2026-03-22 10:00:00",
            "content_hash": "hash-1",
            "symbols": ["000001.SZ"],
            "tags": ["测试"],
            "importance": 0.7,
            "raw_payload": {"hello": "world"},
        }

        inserted = self.service.store_articles(self.source_id, [article, article.copy()])

        self.assertEqual(inserted, 1)
        rows = self.service.list_articles(limit=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["symbols"], ["000001.SZ"])

    def test_refresh_daily_brief_creates_digest_record(self):
        self.service.store_articles(
            self.source_id,
            [
                {
                    "title": "监管动态更新",
                    "summary": "监管动态更新",
                    "content": "监管动态更新",
                    "url": "https://example.com/a",
                    "published_at": "2026-03-22 09:30:00",
                    "content_hash": "hash-a",
                    "symbols": [],
                    "tags": ["监管"],
                    "importance": 0.8,
                    "raw_payload": {},
                },
                {
                    "title": "公告披露完成",
                    "summary": "公告披露完成",
                    "content": "公告披露完成",
                    "url": "https://example.com/b",
                    "published_at": "2026-03-22 11:00:00",
                    "content_hash": "hash-b",
                    "symbols": [],
                    "tags": ["公告"],
                    "importance": 0.9,
                    "raw_payload": {},
                },
            ],
        )

        self.service.refresh_daily_brief("2026-03-22")
        briefs = self.service.list_briefs(limit=5)

        self.assertEqual(len(briefs), 1)
        self.assertIn("每日资讯简报 2026-03-22", briefs[0]["content"])
        self.assertEqual(briefs[0]["source"], "news_digest")


if __name__ == "__main__":
    unittest.main()
