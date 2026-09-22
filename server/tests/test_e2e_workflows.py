import unittest

from tests import test_login


class EndToEndWorkflowTests(unittest.TestCase):
    setUpClass = classmethod(test_login.LoginTests.setUpClass.__func__)
    setUp = test_login.LoginTests.setUp
    drop_test_schema = test_login.LoginTests.drop_test_schema
    login = test_login.LoginTests.login

    def headers(self, token):
        return {"Authorization": "Bearer " + token}

    def owner_token(self):
        return self.login().json()["data"]["access_token"]

    def create_client(self, token, name="Acme Ltd"):
        response = self.client.post(
            "/api/v1/clients", json={"name": name}, headers=self.headers(token),
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["data"]

    def quote_payload(self, client_id, **changes):
        return {
            "client_id": client_id,
            "issue_date": "2026-09-15",
            "expiry_date": "2026-09-30",
            "currency": "KES",
            "tax_rate": "16",
            "discount_type": "FIXED",
            "discount_value": "10",
            "notes": "Thank you.",
            "terms": "Valid for 14 days.",
            "items": [{"description": "Website work", "quantity": "1", "unit_price": "100"}],
            **changes,
        }

    def invoice_payload(self, client_id, **changes):
        return {
            "client_id": client_id,
            "issue_date": "2026-09-15",
            "due_date": "2026-09-30",
            "currency": "KES",
            "tax_rate": "16",
            "discount_type": "FIXED",
            "discount_value": "10",
            "items": [{"description": "Consulting", "quantity": "1", "unit_price": "100"}],
            **changes,
        }

    def receipt_payload(self, client_id, **changes):
        return {
            "client_id": client_id,
            "issue_date": "2026-09-15",
            "currency": "KES",
            "tax_rate": "16",
            "discount_type": "FIXED",
            "discount_value": "10",
            "items": [{"description": "Support", "quantity": "1", "unit_price": "100"}],
            **changes,
        }

    def assert_pdf(self, resource, document, token):
        response = self.client.get(
            f"/api/v1/{resource}/{document['id']}/pdf",
            headers=self.headers(token),
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        singular = resource[:-1]
        self.assertIn(
            f'filename="{document[singular + "_number"]}.pdf"',
            response.headers["content-disposition"],
        )
        self.assertIn(document[singular + "_number"].encode(), response.content)
        return response

    def test_first_user_can_register_setup_create_quote_retrieve_and_download_pdf(self):
        registered = self.client.post("/api/v1/auth/register", json={
            "name": "First User", "email": "first@example.com", "password": "ExactPassword123",
        })
        self.assertEqual(registered.status_code, 201, registered.text)
        token = self.login(email="first@example.com", password="ExactPassword123").json()["data"]["access_token"]

        profile = self.client.put(
            "/api/v1/business-profile",
            json={"business_name": "First User Studio", "default_currency": "KES"},
            headers=self.headers(token),
        )
        self.assertEqual(profile.status_code, 200, profile.text)
        client = self.create_client(token)
        created = self.client.post(
            "/api/v1/quotes", json=self.quote_payload(client["id"]), headers=self.headers(token),
        )
        self.assertEqual(created.status_code, 201, created.text)
        quote = created.json()["data"]
        self.assertEqual(quote["quote_number"], "QT-0001")
        self.assertEqual(quote["total"], "106.00")

        retrieved = self.client.get(
            f"/api/v1/quotes/{quote['id']}", headers=self.headers(token),
        )
        self.assertEqual(retrieved.status_code, 200)
        self.assertEqual(retrieved.json()["data"], quote)
        self.assert_pdf("quotes", quote, token)
