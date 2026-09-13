import unittest
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.common.responses import collection_response, error_response, resource_response


class ResponseTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)

    def test_resource_serialization_and_created_status(self):
        @self.app.post("/resource")
        def resource():
            return resource_response({
                "id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
                "issue_date": date(2026, 9, 13),
                "total": Decimal("999999999999.99"),
                "items": [{"quantity": Decimal("1.000"), "unit_price": Decimal("20.00")}],
            }, status_code=201)

        response = self.client.post("/resource")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertEqual(response.json(), {"data": {
            "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "issue_date": "2026-09-13",
            "total": "999999999999.99",
            "items": [{"quantity": "1.000", "unit_price": "20.00"}],
        }})

    def test_collection_preserves_pagination_metadata(self):
        @self.app.get("/collection")
        def collection():
            return collection_response([{"name": "Client"}], page=2, page_size=1, total=7)

        response = self.client.get("/collection")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "data": [{"name": "Client"}], "meta": {"page": 2, "page_size": 1, "total": 7},
        })

    def test_empty_collection(self):
        @self.app.get("/collection")
        def collection():
            return collection_response([], page=1, page_size=20, total=0)

        self.assertEqual(self.client.get("/collection").json(), {
            "data": [], "meta": {"page": 1, "page_size": 20, "total": 0},
        })

    def test_error_with_details(self):
        @self.app.get("/conflict")
        def conflict():
            return error_response(
                "QUOTE_ALREADY_CONVERTED", "This quote has already been converted.",
                status_code=409, details={"quote_number": "QT-0001"},
            )

        response = self.client.get("/conflict")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {"error": {
            "code": "QUOTE_ALREADY_CONVERTED",
            "message": "This quote has already been converted.",
            "details": {"quote_number": "QT-0001"},
        }})

    def test_error_defaults_and_http_headers(self):
        @self.app.get("/unauthenticated")
        def unauthenticated():
            return error_response(
                "AUTHENTICATION_REQUIRED", "Authentication is required.",
                status_code=401, headers={"WWW-Authenticate": "Bearer"},
            )

        response = self.client.get("/unauthenticated")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["www-authenticate"], "Bearer")
        self.assertEqual(response.json(), {"error": {
            "code": "AUTHENTICATION_REQUIRED",
            "message": "Authentication is required.",
            "details": {},
        }})
