import unittest
import logging
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.common.logging_config import SensitiveDataFilter
from app.common.settings import Settings
from app.main import create_app


class LoggingTests(unittest.TestCase):
    def test_sensitive_filter_redacts_credential_shaped_values(self):
        record = logging.LogRecord(
            "app.test", logging.INFO, __file__, 1,
            "password=secret token=jwt-value database_url=postgres-secret", (), None,
        )
        self.assertTrue(SensitiveDataFilter().filter(record))
        self.assertNotIn("secret", record.getMessage())
        self.assertNotIn("jwt-value", record.getMessage())
        self.assertNotIn("postgres-secret", record.getMessage())
        self.assertIn("[REDACTED]", record.getMessage())

    @patch.dict("os.environ", {"LOG_LEVEL": "not-a-level"}, clear=True)
    def test_invalid_log_level_fails_configuration(self):
        with self.assertRaises(ValueError):
            create_app(Settings(environment="test"))

    def test_unexpected_errors_log_safe_operational_context(self):
        application = create_app(Settings(environment="test"))

        @application.get("/log-crash")
        def crash():
            raise RuntimeError("password=private-password token=private-token")

        with TestClient(application, raise_server_exceptions=False) as client:
            with self.assertLogs("app.errors", level="ERROR") as captured:
                response = client.get("/log-crash")
        self.assertEqual(response.status_code, 500)
        self.assertIn("method=GET", captured.output[0])
        self.assertIn("path=/log-crash", captured.output[0])
        self.assertIn("error_type=RuntimeError", captured.output[0])
        self.assertNotIn("private-password", captured.output[0])
        self.assertNotIn("private-token", captured.output[0])
