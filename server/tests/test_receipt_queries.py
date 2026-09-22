import unittest
from uuid import UUID, uuid4
from unittest.mock import Mock

from app.receipts.queries import get_receipt_for_user, paginate_receipts_for_user
from tests import test_receipt_endpoint


class ReceiptQueryTests(unittest.TestCase):
    setUpClass = classmethod(test_receipt_endpoint.ReceiptEndpointTests.setUpClass.__func__)
    setUp = test_receipt_endpoint.ReceiptEndpointTests.setUp
    drop_test_schema = test_receipt_endpoint.ReceiptEndpointTests.drop_test_schema
    login = test_receipt_endpoint.ReceiptEndpointTests.login
    payload = test_receipt_endpoint.ReceiptEndpointTests.payload
    post = test_receipt_endpoint.ReceiptEndpointTests.post

    def test_owned_relations_and_foreign_missing(self):
        receipt = self.post(self.payload()).json()['data']
        result = get_receipt_for_user(self.connection, user_id=UUID(self.user_id), receipt_id=UUID(receipt['id']))
        self.assertEqual(str(result.client.id), self.client_id)
        self.assertEqual(str(result.items[0].id), receipt['items'][0]['id'])
        self.assertIsNone(get_receipt_for_user(self.connection, user_id=uuid4(), receipt_id=result.receipt.id))
        self.assertIsNone(get_receipt_for_user(self.connection, user_id=UUID(self.user_id), receipt_id=uuid4()))

    def test_pagination_order_bounds_and_isolation(self):
        ids = [self.post(self.payload()).json()['data']['id'] for _ in range(3)]
        rows, total = paginate_receipts_for_user(self.connection, user_id=UUID(self.user_id), page=2, page_size=1)
        self.assertEqual(total, 3)
        self.assertEqual(str(rows[0].receipt.id), ids[1])
        self.assertEqual(paginate_receipts_for_user(self.connection, user_id=uuid4(), page=1, page_size=20), ([], 0))
        self.assertEqual(paginate_receipts_for_user(self.connection, user_id=UUID(self.user_id), page=9, page_size=20), ([], 3))
        for page, size in [(0, 20), (1, 101), (1, 0)]:
            with self.assertRaises(ValueError):
                paginate_receipts_for_user(self.connection, user_id=UUID(self.user_id), page=page, page_size=size)

    def test_related_loading_has_constant_query_count(self):
        for _ in range(3):
            self.post(self.payload())

        connection = Mock(wraps=self.connection)
        rows, total = paginate_receipts_for_user(
            connection, user_id=UUID(self.user_id), page=1, page_size=3,
        )

        self.assertEqual(total, 3)
        self.assertEqual(len(rows), 3)
        self.assertEqual(connection.execute.call_count, 1)
        self.assertEqual(connection.cursor.call_count, 3)
        self.assertTrue(all(row.client and row.items for row in rows))
