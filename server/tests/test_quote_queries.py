import unittest
from unittest.mock import Mock
from uuid import UUID, uuid4

from app.quotes.queries import get_quote_for_user, paginate_quotes_for_user
from tests import test_quote_endpoint


class QuoteQueryTests(unittest.TestCase):
    setUpClass = classmethod(test_quote_endpoint.QuoteEndpointTests.setUpClass.__func__)
    setUp = test_quote_endpoint.QuoteEndpointTests.setUp
    drop_test_schema = test_quote_endpoint.QuoteEndpointTests.drop_test_schema
    login = test_quote_endpoint.QuoteEndpointTests.login
    payload = test_quote_endpoint.QuoteEndpointTests.payload
    post = test_quote_endpoint.QuoteEndpointTests.post

    def test_owned_relations_and_foreign_missing(self):
        quote = self.post(self.payload()).json()['data']
        result = get_quote_for_user(self.connection, user_id=UUID(self.user_id), quote_id=UUID(quote['id']))
        self.assertEqual(str(result.client.id), self.client_id)
        self.assertEqual(str(result.items[0].id), quote['items'][0]['id'])
        self.assertIsNone(get_quote_for_user(self.connection, user_id=uuid4(), quote_id=result.quote.id))
        self.assertIsNone(get_quote_for_user(self.connection, user_id=UUID(self.user_id), quote_id=uuid4()))

    def test_pagination_order_bounds_and_isolation(self):
        ids = [self.post(self.payload()).json()['data']['id'] for _ in range(3)]
        rows, total = paginate_quotes_for_user(self.connection, user_id=UUID(self.user_id), page=2, page_size=1)
        self.assertEqual(total, 3)
        self.assertEqual(str(rows[0].quote.id), ids[1])
        self.assertEqual(paginate_quotes_for_user(self.connection, user_id=uuid4(), page=1, page_size=20), ([], 0))
        self.assertEqual(paginate_quotes_for_user(self.connection, user_id=UUID(self.user_id), page=9, page_size=20), ([], 3))
        for page, size in [(0, 20), (1, 101), (1, 0)]:
            with self.assertRaises(ValueError):
                paginate_quotes_for_user(self.connection, user_id=UUID(self.user_id), page=page, page_size=size)

    def test_related_loading_has_constant_query_count_and_item_order(self):
        for _ in range(3):
            self.post(self.payload(items=[
                {'description': 'Last', 'quantity': '1', 'unit_price': '20', 'position': 9},
                {'description': 'First', 'quantity': '1', 'unit_price': '20', 'position': 0},
            ]))
        for size in (1, 3):
            connection = Mock(wraps=self.connection)
            rows, total = paginate_quotes_for_user(connection, user_id=UUID(self.user_id), page=1, page_size=size)
            self.assertEqual(total, 3)
            self.assertEqual(connection.execute.call_count, 1)
            self.assertEqual(connection.cursor.call_count, 3)
            self.assertEqual(len(rows), size)
            for row in rows:
                self.assertEqual([item.description for item in row.items], ['First', 'Last'])
