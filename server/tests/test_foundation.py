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
            self.assertEqual(root.json(), {"version": "v1"})
            schema = client.get("/openapi.json")
            self.assertEqual(schema.status_code, 200)
            self.assertIn("/api/v1", schema.json()["paths"])

    @patch.dict("os.environ", {"APP_NAME": "Test Billing", "APP_ENV": "test", "APP_DEBUG": "true"}, clear=True)
    def test_environment_configures_application(self):
        app = create_app()
        self.assertEqual(app.title, "Test Billing")
        self.assertTrue(app.debug)
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
