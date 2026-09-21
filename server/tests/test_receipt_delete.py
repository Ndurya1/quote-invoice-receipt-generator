import unittest
from uuid import UUID, uuid4

from app.common.errors import DomainError
from app.receipts.service import delete_receipt
from tests import test_receipt_patch


class ReceiptDeleteTests(unittest.TestCase):
    setUpClass = classmethod(test_receipt_patch.ReceiptPatchTests.setUpClass.__func__)
    setUp = test_receipt_patch.ReceiptPatchTests.setUp
    drop_test_schema = test_receipt_patch.ReceiptPatchTests.drop_test_schema
    login = test_receipt_patch.ReceiptPatchTests.login
    payload = test_receipt_patch.ReceiptPatchTests.payload
    post = test_receipt_patch.ReceiptPatchTests.post
    get = test_receipt_patch.ReceiptPatchTests.get

    def delete(self, url=None):
        return self.client.delete(url or self.url, headers={'Authorization': 'Bearer ' + self.token})

    def test_direct_deletion_cascades_items_and_never_reuses_number(self):
        other = self.post(self.payload()).json()['data']
        response = self.delete()
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')
        self.assertEqual(self.connection.execute('SELECT count(*) FROM receipt_items WHERE receipt_id = %s',
                                                  (UUID(self.receipt['id']),)).fetchone()[0], 0)
        saved = self.client.get('/api/v1/receipts/' + other['id'],
                                headers={'Authorization': 'Bearer ' + self.token}).json()['data']
        self.assertEqual(saved, other)
        self.assertEqual(self.delete().status_code, 404)
        self.assertEqual(self.post(self.payload()).json()['data']['receipt_number'], 'RCT-0003')

    def test_invoice_linked_receipt_cannot_be_deleted(self):
        invoice_id = self.connection.execute(
            "INSERT INTO invoices (user_id, client_id, invoice_number, issue_date, currency, subtotal, total) "
            "VALUES (%s, %s, 'INV-0001', '2026-09-15', 'KES', 100, 100) RETURNING id",
            (UUID(self.user_id), UUID(self.client_id)),
        ).fetchone()[0]
        self.connection.execute('UPDATE receipts SET source_invoice_id = %s WHERE id = %s',
                                (invoice_id, UUID(self.receipt['id'])))
        response = self.delete()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['error']['code'], 'INVALID_RECEIPT_STATUS')
        saved = self.get()
        self.assertEqual(saved['id'], self.receipt['id'])
        self.assertEqual(saved['source_invoice_id'], str(invoice_id))

    def test_authentication_foreign_missing_and_invalid_uuid(self):
        self.assertEqual(self.client.delete(self.url).status_code, 401)
        self.assertEqual(self.delete('/api/v1/receipts/bad').status_code, 422)
        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'ExactPassword123',
        })
        owner_token = self.token
        self.token = self.client.post('/api/v1/auth/login', json={
            'email': 'other@example.com', 'password': 'ExactPassword123',
        }).json()['data']['access_token']
        foreign = self.delete()
        missing = self.delete('/api/v1/receipts/' + str(uuid4()))
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(foreign.json(), missing.json())
        self.assertEqual(foreign.json()['error']['code'], 'RECEIPT_NOT_FOUND')
        self.token = owner_token
        self.assertEqual(self.get(), self.receipt)

    def test_outer_rollback_restores_receipt_and_items(self):
        with self.assertRaisesRegex(RuntimeError, 'abort'):
            with self.connection.transaction():
                delete_receipt(self.connection, user_id=UUID(self.user_id), receipt_id=UUID(self.receipt['id']))
                raise RuntimeError('abort')
        self.assertEqual(self.get(), self.receipt)
