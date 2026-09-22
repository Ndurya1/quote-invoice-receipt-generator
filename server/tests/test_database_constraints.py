import unittest

from app.accounts.service import create_user
from psycopg import errors
from tests import test_accounts


class DatabaseConstraintTests(unittest.TestCase):
    setUpClass = classmethod(test_accounts.UserPersistenceTests.setUpClass.__func__)
    setUp = test_accounts.UserPersistenceTests.setUp
    drop_test_schema = test_accounts.UserPersistenceTests.drop_test_schema

    def setUp(self):
        test_accounts.UserPersistenceTests.setUp(self)
        self.owner = create_user(
            self.connection, name='Owner', email='owner@example.com', password='test-password',
        )
        self.other = create_user(
            self.connection, name='Other', email='other@example.com', password='test-password',
        )
        self.owner_client = self.connection.execute(
            "INSERT INTO clients (user_id, name) VALUES (%s, 'Owner Client') RETURNING id",
            (self.owner.id,),
        ).fetchone()[0]
        self.other_client = self.connection.execute(
            "INSERT INTO clients (user_id, name) VALUES (%s, 'Other Client') RETURNING id",
            (self.other.id,),
        ).fetchone()[0]

    def insert_numbered_document(self, table, column, number, user_id, client_id):
        self.connection.execute(
            f'''INSERT INTO {table} (user_id, client_id, {column}, issue_date, currency, subtotal, total)
                VALUES (%s, %s, %s, DATE '2026-09-15', 'KES', 0, 0)''',
            (user_id, client_id, number),
        )

    def test_document_numbers_are_unique_per_user_but_reusable_across_users(self):
        for table, column, number in (
            ('quotes', 'quote_number', 'QT-0001'),
            ('invoices', 'invoice_number', 'INV-0001'),
            ('receipts', 'receipt_number', 'RCT-0001'),
        ):
            with self.subTest(table=table):
                self.insert_numbered_document(table, column, number, self.owner.id, self.owner_client)
                with self.assertRaises(errors.UniqueViolation):
                    self.insert_numbered_document(table, column, number, self.owner.id, self.owner_client)
                self.insert_numbered_document(table, column, number, self.other.id, self.other_client)
                self.assertEqual(
                    self.connection.execute(
                        f'SELECT count(*) FROM {table} WHERE {column} = %s', (number,),
                    ).fetchone()[0],
                    2,
                )
