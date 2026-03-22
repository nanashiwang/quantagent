import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.source_service import DEFAULT_NEWS_SOURCES, SourceService
from src.data.db.sqlite_client import SQLiteClient


class TestSourceService(unittest.TestCase):
    def test_seed_defaults_creates_expected_sources_once(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db = SQLiteClient(str(Path(temp_dir) / "test.db"))
            service = SourceService(db)

            service.seed_defaults()
            service.seed_defaults()

            rows = service.list_all()
            self.assertEqual(len(rows), len(DEFAULT_NEWS_SOURCES))
            self.assertIn("证监会", {row["name"] for row in rows})
            self.assertIn("RSSHub 自建", {row["name"] for row in rows})


if __name__ == "__main__":
    unittest.main()
