import unittest

from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, field_validator

from app.common.errors import DomainError
from app.common.settings import Settings
from app.main import create_app


class ValidationPayload(BaseModel):
    quantity: int
    password: str

    @field_validator("password")
    @classmethod
    def reject_password(cls, value: str) -> str:
        raise ValueError(f"Private validator context: {value}")


class ErrorHandlerTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(Settings(environment="test"))
        self.client = TestClient(self.app, raise_server_exceptions=False)
        self.addCleanup(self.client.close)

    def test_domain_status_codes_and_public_details(self):
        codes = {
            400: "INVALID_DATE_RANGE", 401: "INVALID_CREDENTIALS",
            403: "FORBIDDEN_RESOURCE", 404: "CLIENT_NOT_FOUND",
            409: "QUOTE_ALREADY_CONVERTED", 422: "INVALID_QUANTITY",
        }

        @self.app.get("/domain/{status_code}")
        def fail(status_code: int):
            raise DomainError(
                codes[status_code], "Public business message.",
                status_code=status_code, details={"field": "example"},
                headers={"WWW-Authenticate": "Bearer"} if status_code == 401 else None,
            )

        for status, code in codes.items():
            with self.subTest(status=status):
                response = self.client.get(f"/domain/{status}")
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.json(), {"error": {
                    "code": code, "message": "Public business message.",
                    "details": {"field": "example"},
                }})
                if status == 401:
                    self.assertEqual(response.headers["www-authenticate"], "Bearer")

    def test_framework_http_errors_have_stable_codes_and_hide_details(self):
        codes = {
            400: "BAD_REQUEST", 401: "AUTHENTICATION_REQUIRED", 403: "FORBIDDEN_RESOURCE",
            404: "RESOURCE_NOT_FOUND", 409: "STATE_CONFLICT", 422: "VALIDATION_ERROR",
            429: "TOO_MANY_REQUESTS", 500: "INTERNAL_SERVER_ERROR",
        }

        @self.app.get("/http/{status_code}")
        def fail(status_code: int):
            raise HTTPException(status_code, detail="private-database-information", headers={"Retry-After": "10"})

        for status, code in codes.items():
            with self.subTest(status=status):
                response = self.client.get(f"/http/{status}")
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.json()["error"]["code"], code)
                self.assertEqual(response.json()["error"]["details"], {})
                self.assertEqual(response.headers["retry-after"], "10")
                self.assertNotIn("private-database-information", response.text)

    def test_router_not_found_and_method_not_allowed(self):
        missing = self.client.get("/does-not-exist")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["error"]["code"], "RESOURCE_NOT_FOUND")
        wrong_method = self.client.post("/api/v1")
        self.assertEqual(wrong_method.status_code, 405)
        self.assertEqual(wrong_method.json()["error"]["code"], "METHOD_NOT_ALLOWED")
        self.assertIn("GET", wrong_method.headers["allow"])

    def test_request_validation_omits_values_and_validator_exceptions(self):
        @self.app.post("/validate")
        def validate(payload: ValidationPayload):
            return payload

        response = self.client.post("/validate", json={"quantity": "private-input", "password": "secret-password"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")
        errors = response.json()["error"]["details"]["errors"]
        self.assertEqual({tuple(error["loc"]) for error in errors}, {("body", "quantity"), ("body", "password")})
        for value in ("private-input", "secret-password", "Private validator context"):
            self.assertNotIn(value, response.text)
        self.assertTrue(all(set(error) == {"loc", "type", "message"} for error in errors))

        missing = self.client.post("/validate", json={})
        self.assertEqual(missing.status_code, 422)
        self.assertTrue(all(error["message"] == "Field is required." for error in missing.json()["error"]["details"]["errors"]))
        malformed = self.client.post("/validate", content='{"password":', headers={"Content-Type": "application/json"})
        self.assertEqual(malformed.status_code, 422)
        self.assertEqual(malformed.json()["error"]["code"], "VALIDATION_ERROR")

    def test_unexpected_errors_never_return_tracebacks_even_in_debug(self):
        for debug in (False, True):
            with self.subTest(debug=debug):
                app = create_app(Settings(environment="test", debug=debug))

                @app.get("/crash")
                def crash():
                    raise RuntimeError("secret-password and private SQL")

                with TestClient(app, raise_server_exceptions=False) as client:
                    response = client.get("/crash", headers={"Accept": "text/html"})
                self.assertEqual(response.status_code, 500)
                self.assertEqual(response.headers["content-type"], "application/json")
                self.assertEqual(response.json(), {"error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred.", "details": {},
                }})

    def test_response_validation_failure_is_server_error(self):
        @self.app.get("/invalid-response", response_model=int)
        def invalid_response():
            return {"private": "server-data"}

        response = self.client.get("/invalid-response")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"]["code"], "INTERNAL_SERVER_ERROR")
        self.assertNotIn("server-data", response.text)
