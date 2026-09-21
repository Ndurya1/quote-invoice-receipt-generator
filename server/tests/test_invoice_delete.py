import unittest
from uuid import UUID, uuid4

from app.common.errors import DomainError
from app.invoices.models import InvoiceStatus
from app.invoices.service import delete_invoice
from tests import test_invoice_patch


class InvoiceDeleteTests(unittest.TestCase):
    setUpClass = classmethod(test_invoice_patch.InvoicePatchTests.setUpClass.__func__)
    setUp = test_invoice_patch.InvoicePatchTests.setUp
    drop_test_schema = test_invoice_patch.InvoicePatchTests.drop_test_schema
    login = test_invoice_patch.InvoicePatchTests.login
    payload = test_invoice_patch.InvoicePatchTests.payload
    post = test_invoice_patch.InvoicePatchTests.post
    get = test_invoice_patch.InvoicePatchTests.get

    def delete(self, url=None):
        return self.client.delete(url or self.url, headers={'Authorization': 'Bearer ' + self.token})

    def test_draft_deletion_cascades_items_and_never_reuses_number(self):
        other = self.post(self.payload()).json()['data']
        response = self.delete()
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')
        self.assertEqual(self.connection.execute('SELECT count(*) FROM invoice_items WHERE invoice_id = %s',
                                                  (UUID(self.invoice['id']),)).fetchone()[0], 0)
        saved = self.client.get('/api/v1/invoices/' + other['id'],
                                headers={'Authorization': 'Bearer ' + self.token}).json()['data']
        self.assertEqual(saved, other)
        self.assertEqual(self.delete().status_code, 404)
        self.assertEqual(self.post(self.payload()).json()['data']['invoice_number'], 'INV-0003')

    def test_every_non_draft_status_is_protected(self):
        for status in InvoiceStatus:
            if status == InvoiceStatus.DRAFT:
                continue
            self.connection.execute('UPDATE invoices SET status = %s WHERE id = %s',
                                    (status.value, UUID(self.invoice['id'])))
            with self.subTest(status=status):
                response = self.delete()
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json()['error']['code'], 'INVALID_INVOICE_STATUS')
            self.connection.execute('UPDATE invoices SET status = %s WHERE id = %s',
                                    ('DRAFT', UUID(self.invoice['id'])))

    def test_receipt_link_blocks_even_draft(self):
        self.connection.execute(
            '''INSERT INTO receipts (user_id, client_id, source_invoice_id, receipt_number,
               issue_date, currency, subtotal, total)
               VALUES (%s, %s, %s, 'REC-0001', '2026-09-15', 'KES', 100, 100)''',
            (UUID(self.user_id), UUID(self.client_id), UUID(self.invoice['id'])),
        )
        response = self.delete()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['error']['code'], 'INVALID_INVOICE_STATUS')
        self.assertEqual(self.get(), self.invoice)

    def test_authentication_foreign_missing_and_invalid_uuid(self):
        self.assertEqual(self.client.delete(self.url).status_code, 401)
        self.assertEqual(self.delete('/api/v1/invoices/bad').status_code, 422)
        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'ExactPassword123',
        })
        owner_token = self.token
        self.token = self.client.post('/api/v1/auth/login', json={
            'email': 'other@example.com', 'password': 'ExactPassword123',
        }).json()['data']['access_token']
        foreign = self.delete()
        missing = self.delete('/api/v1/invoices/' + str(uuid4()))
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(foreign.json(), missing.json())
        self.assertEqual(foreign.json()['error']['code'], 'INVOICE_NOT_FOUND')
        self.token = owner_token
        self.assertEqual(self.get(), self.invoice)

    def test_outer_rollback_restores_invoice_and_items(self):
        with self.assertRaisesRegex(RuntimeError, 'abort'):
            with self.connection.transaction():
                delete_invoice(self.connection, user_id=UUID(self.user_id), invoice_id=UUID(self.invoice['id']))
                raise RuntimeError('abort')
        self.assertEqual(self.get(), self.invoice)
