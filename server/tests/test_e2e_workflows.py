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

    def test_quote_invoice_receipt_lifecycle_preserves_lineage_and_independence(self):
        token = self.owner_token()
        client = self.create_client(token)
        quote = self.client.post(
            "/api/v1/quotes", json=self.quote_payload(client["id"]), headers=self.headers(token),
        ).json()["data"]
        quote_before_conversion = self.client.get(
            f"/api/v1/quotes/{quote['id']}", headers=self.headers(token),
        ).json()["data"]

        sent = self.client.post(
            f"/api/v1/quotes/{quote['id']}/send", headers=self.headers(token),
        )
        accepted = self.client.post(
            f"/api/v1/quotes/{quote['id']}/accept", headers=self.headers(token),
        )
        self.assertEqual(sent.status_code, 200, sent.text)
        self.assertEqual(accepted.status_code, 200, accepted.text)

        invoice_response = self.client.post(
            f"/api/v1/quotes/{quote['id']}/convert",
            json={"issue_date": "2026-09-20", "due_date": "2026-10-01"},
            headers=self.headers(token),
        )
        self.assertEqual(invoice_response.status_code, 201, invoice_response.text)
        invoice = invoice_response.json()["data"]
        invoice_before_send = dict(invoice)
        self.assertEqual(invoice["source_quote_id"], quote["id"])
        self.assertEqual(invoice["client_id"], quote["client_id"])
        self.assertEqual(invoice["currency"], quote["currency"])
        self.assertEqual(invoice["total"], quote["total"])
        self.assertEqual(invoice["items"][0]["description"], quote["items"][0]["description"])
        self.assertNotEqual(invoice["id"], quote["id"])

        sent_invoice = self.client.post(
            f"/api/v1/invoices/{invoice['id']}/send", headers=self.headers(token),
        )
        self.assertEqual(sent_invoice.status_code, 200, sent_invoice.text)
        receipt_response = self.client.post(
            f"/api/v1/invoices/{invoice['id']}/convert",
            json={"issue_date": "2026-10-02"}, headers=self.headers(token),
        )
        self.assertEqual(receipt_response.status_code, 201, receipt_response.text)
        receipt = receipt_response.json()["data"]
        self.assertEqual(receipt["source_invoice_id"], invoice["id"])
        self.assertEqual(receipt["client_id"], invoice["client_id"])
        self.assertEqual(receipt["currency"], invoice["currency"])
        self.assertEqual(receipt["total"], invoice["total"])
        self.assertEqual(receipt["items"][0]["description"], invoice["items"][0]["description"])
        self.assertNotEqual(receipt["id"], invoice["id"])

        saved_quote = self.client.get(
            f"/api/v1/quotes/{quote['id']}", headers=self.headers(token),
        ).json()["data"]
        saved_invoice = self.client.get(
            f"/api/v1/invoices/{invoice['id']}", headers=self.headers(token),
        ).json()["data"]
        for field in quote_before_conversion.keys() - {"status", "updated_at"}:
            self.assertEqual(saved_quote[field], quote_before_conversion[field], field)
        self.assertEqual(saved_quote["status"], "CONVERTED")
        for field in invoice_before_send.keys() - {"status", "updated_at"}:
            self.assertEqual(saved_invoice[field], invoice_before_send[field], field)
        self.assertEqual(saved_invoice["status"], "SENT")
        for resource, document in (("quotes", saved_quote), ("invoices", saved_invoice), ("receipts", receipt)):
            with self.subTest(resource=resource):
                self.assert_pdf(resource, document, token)
