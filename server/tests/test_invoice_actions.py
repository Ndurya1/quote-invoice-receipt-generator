import unittest
from uuid import UUID

from app.invoices.models import InvoiceStatus
from tests import test_invoice_endpoint


class InvoiceActionLifecycleTests(unittest.TestCase):
    setUpClass = classmethod(test_invoice_endpoint.InvoiceEndpointTests.setUpClass.__func__)
    setUp = test_invoice_endpoint.InvoiceEndpointTests.setUp
    drop_test_schema = test_invoice_endpoint.InvoiceEndpointTests.drop_test_schema
    login = test_invoice_endpoint.InvoiceEndpointTests.login
    payload = test_invoice_endpoint.InvoiceEndpointTests.payload
    post = test_invoice_endpoint.InvoiceEndpointTests.post

    def action(self, invoice_id, action):
        return self.client.post(f'/api/v1/invoices/{invoice_id}/{action}',
                                headers={'Authorization': 'Bearer ' + self.token})

    def create(self):
        return self.post(self.payload()).json()['data']

    def test_draft_send_then_paid(self):
        invoice = self.create()
        sent = self.action(invoice['id'], 'send')
        self.assertEqual(sent.status_code, 200)
        self.assertEqual(sent.json()['data']['status'], InvoiceStatus.SENT)
        paid = self.action(invoice['id'], 'mark-paid')
        self.assertEqual(paid.status_code, 200)
        self.assertEqual(paid.json()['data']['status'], InvoiceStatus.PAID)
        self.assertEqual(paid.json()['data']['invoice_number'], invoice['invoice_number'])

    def test_draft_and_sent_cancel(self):
        draft = self.create()
        self.assertEqual(self.action(draft['id'], 'cancel').json()['data']['status'], InvoiceStatus.CANCELLED)
        sent = self.create()
        self.assertEqual(self.action(sent['id'], 'send').status_code, 200)
        self.assertEqual(self.action(sent['id'], 'cancel').json()['data']['status'], InvoiceStatus.CANCELLED)

    def test_overdue_can_be_paid_or_cancelled(self):
        paid = self.create()
        self.connection.execute('UPDATE invoices SET status = %s WHERE id = %s',
                                (InvoiceStatus.OVERDUE.value, UUID(paid['id'])))
        self.assertEqual(self.action(paid['id'], 'mark-paid').json()['data']['status'], InvoiceStatus.PAID)
        cancelled = self.create()
        self.connection.execute('UPDATE invoices SET status = %s WHERE id = %s',
                                (InvoiceStatus.OVERDUE.value, UUID(cancelled['id'])))
        self.assertEqual(self.action(cancelled['id'], 'cancel').json()['data']['status'], InvoiceStatus.CANCELLED)

    def test_terminal_and_invalid_actions_return_conflicts(self):
        invoice = self.create()
        self.assertEqual(self.action(invoice['id'], 'cancel').status_code, 200)
        for action in ('send', 'mark-paid', 'cancel'):
            with self.subTest(action=action):
                response = self.action(invoice['id'], action)
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json()['error']['code'], 'INVALID_INVOICE_STATUS')

    def test_openapi_documents_all_invoice_action_routes(self):
        paths = self.client.get('/openapi.json').json()['paths']
        detail = paths['/api/v1/invoices/{invoice_id}']
        self.assertEqual(set(detail), {'get', 'patch', 'delete'})
        for action in ('send', 'mark-paid', 'cancel'):
            operation = paths[f'/api/v1/invoices/{{invoice_id}}/{action}']['post']
            self.assertEqual(operation['security'], [{'HTTPBearer': []}])
            self.assertIn('200', operation['responses'])
