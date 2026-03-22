import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.sources.tushare_api import TushareAPI


class TestTushareAPI(unittest.TestCase):
    def test_custom_api_url_is_normalized_and_applied(self):
        fake_pro = Mock()

        with patch("src.data.sources.tushare_api.ts.pro_api", return_value=fake_pro) as mock_pro_api:
            api = TushareAPI("test-token", "http://121.40.135.59:8010")

        self.assertEqual(api.api_url, "http://121.40.135.59:8010/")
        self.assertEqual(fake_pro._DataApi__http_url, "http://121.40.135.59:8010/")
        mock_pro_api.assert_called_once_with("test-token")

    def test_empty_api_url_keeps_default_gateway(self):
        fake_pro = Mock()

        with patch("src.data.sources.tushare_api.ts.pro_api", return_value=fake_pro):
            api = TushareAPI("test-token", "")

        self.assertEqual(api.api_url, "")
        self.assertNotIn("_DataApi__http_url", fake_pro.__dict__)
