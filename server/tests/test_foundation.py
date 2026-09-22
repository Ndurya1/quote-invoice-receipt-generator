import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.common.settings import Settings
from app.main import create_app


class ApplicationTests(unittest.TestCase):
    def test_startup_health_and_api_namespace(self):
        with TestClient(create_app(Settings(environment="test"))) as client:
            health = client.get("/health")
            self.assertEqual(health.status_code, 200)
            self.assertEqual(health.json(), {"status": "ok"})
            root = client.get("/api/v1")
            self.assertEqual(root.status_code, 200)
            self.assertEqual(root.json(), {"data": {"version": "v1"}})
            schema = client.get("/openapi.json")
            self.assertEqual(schema.status_code, 200)
            self.assertIn("/api/v1", schema.json()["paths"])

    @patch.dict("os.environ", {"APP_NAME": "Test Billing", "APP_ENV": "test", "APP_DEBUG": "true"}, clear=True)
    def test_environment_configures_application(self):
        app = create_app()
        self.assertEqual(app.title, "Test Billing")
        self.assertTrue(app.state.settings.debug)
        self.assertFalse(app.debug)
        self.assertEqual(app.state.settings.environment, "test")

    @patch.dict("os.environ", {}, clear=True)
    def test_defaults_allow_startup_without_database_or_secrets(self):
        app = create_app()
        self.assertFalse(app.debug)
        self.assertEqual(app.state.settings.environment, "development")

    def test_invalid_environment_configuration_fails_early(self):
        for values in ({"APP_DEBUG": "perhaps"}, {"APP_ENV": "unknown"}, {"APP_NAME": " "}):
            with self.subTest(values=values), patch.dict("os.environ", values, clear=True):
                with self.assertRaises(ValueError):
                    Settings.from_environment()

    @patch.dict("os.environ", {"CORS_ALLOWED_ORIGINS": "https://app.example.com, https://admin.example.com/"}, clear=True)
    def test_cors_origins_are_loaded_from_environment(self):
        settings = Settings.from_environment()
        self.assertEqual(settings.cors_origins, ("https://app.example.com", "https://admin.example.com"))

    @patch.dict("os.environ", {"CORS_ALLOWED_ORIGINS": "*"}, clear=True)
    def test_wildcard_cors_is_rejected(self):
        with self.assertRaises(ValueError):
            Settings.from_environment()

    @patch.dict("os.environ", {"APP_ENV": "production", "APP_DEBUG": "true"}, clear=True)
    def test_production_rejects_debug_mode(self):
        with self.assertRaises(ValueError):
            Settings.from_environment()

    @patch.dict(
        "os.environ",
        {
            "APP_ENV": "production",
            "APP_DEBUG": "false",
            "CORS_ALLOWED_ORIGINS": "https://app.example.com",
            "ALLOWED_HOSTS": "api.example.com",
            "JWT_SECRET_KEY": "production-test-secret-that-is-at-least-32-bytes-long",
        },
        clear=True,
    )
    def test_production_configuration_is_validated(self):
        app = create_app()
        self.assertEqual(app.state.settings.environment, "production")
        self.assertTrue(app.state.settings.force_https)

    @patch.dict("os.environ", {"APP_ENV": "production", "APP_DEBUG": "false"}, clear=True)
    def test_production_requires_explicit_origins_and_hosts(self):
        with self.assertRaises(ValueError):
            create_app()

    def test_cors_allows_configured_origin_only(self):
        with TestClient(create_app(Settings(environment="test"))) as client:
            allowed = client.get("/health", headers={"Origin": "http://localhost:5173"})
            denied = client.get("/health", headers={"Origin": "https://untrusted.example"})
        self.assertEqual(allowed.headers.get("access-control-allow-origin"), "http://localhost:5173")
        self.assertNotIn("access-control-allow-origin", denied.headers)
