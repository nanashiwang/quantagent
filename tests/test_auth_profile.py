import os
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-profile-tests"

import backend.app as backend_app_module
from backend.auth.jwt_handler import create_access_token, hash_password, verify_password
from backend.services.user_service import UserService
from src.data.db.sqlite_client import SQLiteClient


class TestAuthProfile(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "profile.db"
        self.db = SQLiteClient(str(db_path))
        self.user_service = UserService(self.db)

        self.original_sqlite_client = backend_app_module._sqlite_client
        backend_app_module._sqlite_client = self.db

        self.user_id = self.user_service.create_user(
            "alice",
            hash_password("old-password"),
            "user",
        )
        self.user_service.create_user(
            "existing-user",
            hash_password("another-password"),
            "user",
        )

    def tearDown(self):
        backend_app_module._sqlite_client = self.original_sqlite_client
        self.temp_dir.cleanup()

    def _auth_headers(self):
        token = create_access_token({"sub": "alice", "role": "user", "uid": self.user_id})
        return {"Authorization": f"Bearer {token}"}

    def test_get_me_returns_current_user(self):
        with TestClient(backend_app_module.app) as client:
            response = client.get("/api/auth/me", headers=self._auth_headers())

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["username"], "alice")
        self.assertEqual(body["role"], "user")

    def test_update_me_changes_username_and_password(self):
        with TestClient(backend_app_module.app) as client:
            response = client.put(
                "/api/auth/me",
                headers=self._auth_headers(),
                json={
                    "username": "alice-new",
                    "current_password": "old-password",
                    "new_password": "new-password-123",
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["user"]["username"], "alice-new")
        self.assertTrue(body["access_token"])

        updated_user = self.user_service.get_by_id(self.user_id)
        self.assertEqual(updated_user["username"], "alice-new")
        self.assertTrue(verify_password("new-password-123", updated_user["password_hash"]))

    def test_update_me_rejects_wrong_current_password(self):
        with TestClient(backend_app_module.app) as client:
            response = client.put(
                "/api/auth/me",
                headers=self._auth_headers(),
                json={
                    "username": "alice-new",
                    "current_password": "wrong-password",
                },
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("当前密码错误", response.json()["detail"])

    def test_update_me_rejects_duplicate_username(self):
        with TestClient(backend_app_module.app) as client:
            response = client.put(
                "/api/auth/me",
                headers=self._auth_headers(),
                json={
                    "username": "existing-user",
                    "current_password": "old-password",
                },
            )

        self.assertEqual(response.status_code, 409)
        self.assertIn("用户名已存在", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
