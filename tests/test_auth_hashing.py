import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.auth.jwt_handler import hash_password, verify_password


class TestAuthHashing(unittest.TestCase):
    """测试密码哈希"""

    def test_hash_password_supports_long_password(self):
        password = "A" * 100

        hashed = hash_password(password)

        self.assertTrue(verify_password(password, hashed))


if __name__ == "__main__":
    unittest.main()
