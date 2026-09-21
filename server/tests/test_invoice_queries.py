import unittest
from uuid import UUID, uuid4

from app.invoices.queries import get_invoice_for_user, paginate_invoices_for_user
from tests import test_invoice_endpoint


class InvoiceQueryTests(unittest.TestCase):
    setUpClass = classmethod(test_invoice_endpoint.InvoiceEndpointTests.setUpClass.__func__)
    setUp = test_invoice_endpoint.InvoiceEndpointTests.setUp
    drop_test_schema = test_invoice_endpoint.InvoiceEndpointTests.drop_test_schema
    login = test_invoice_endpoint.InvoiceEndpointTests.login
    payload = test_invoice_endpoint.InvoiceEndpointTests.payload
    post = test_invoice_endpoint.InvoiceEndpointTests.post

    def test_owned_invoice_items_and_foreign_missing(self):
        invoice = self.post(self.payload()).json()['data']
        result = get_invoice_for_user(
            self.connection, user_id=UUID(self.user_id), invoice_id=UUID(invoice['id'])
        )
        self.assertEqual(str(result.invoice.id), invoice['id'])
        self.assertEqual(str(result.items[0].id), invoice['items'][0]['id'])
        self.assertIsNone(get_invoice_for_user(self.connection, user_id=uuid4(), invoice_id=result.invoice.id))
        self.assertIsNone(get_invoice_for_user(self.connection, user_id=UUID(self.user_id), invoice_id=uuid4()))

    def test_pagination_order_bounds_and_isolation(self):
        ids = [self.post(self.payload()).json()['data']['id'] for _ in range(3)]
        rows, total = paginate_invoices_for_user(
            self.connection, user_id=UUID(self.user_id), page=2, page_size=1
        )
        self.assertEqual(total, 3)
        self.assertEqual(str(rows[0].invoice.id), ids[1])
        self.assertEqual(paginate_invoices_for_user(self.connection, user_id=uuid4(), page=1, page_size=20), ([], 0))
        self.assertEqual(paginate_invoices_for_user(self.connection, user_id=UUID(self.user_id), page=9, page_size=20), ([], 3))
        for page, size in [(0, 20), (1, 101), (1, 0)]:
            with self.assertRaises(ValueError):
                paginate_invoices_for_user(self.connection, user_id=UUID(self.user_id), page=page, page_size=size)
