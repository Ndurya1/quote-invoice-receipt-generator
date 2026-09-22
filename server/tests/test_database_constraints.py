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

    def test_quote_expiry_cannot_precede_issue_date(self):
        with self.assertRaises(errors.CheckViolation):
            self.connection.execute(
                '''INSERT INTO quotes
                   (user_id, client_id, quote_number, issue_date, expiry_date, currency, subtotal, total)
                   VALUES (%s, %s, 'QT-DATE', DATE '2026-09-15', DATE '2026-09-14', 'KES', 0, 0)''',
                (self.owner.id, self.owner_client),
            )
        self.assertEqual(self.connection.execute('SELECT count(*) FROM quotes').fetchone()[0], 0)

    def test_invoice_due_date_cannot_precede_issue_date(self):
        with self.assertRaises(errors.CheckViolation):
            self.connection.execute(
                '''INSERT INTO invoices
                   (user_id, client_id, invoice_number, issue_date, due_date, currency, subtotal, total)
                   VALUES (%s, %s, 'INV-DATE', DATE '2026-09-15', DATE '2026-09-14', 'KES', 0, 0)''',
                (self.owner.id, self.owner_client),
            )
        self.assertEqual(self.connection.execute('SELECT count(*) FROM invoices').fetchone()[0], 0)

    def test_document_monetary_fields_reject_negative_values(self):
        fields = ('subtotal', 'tax_rate', 'tax_amount', 'discount_value', 'discount_amount', 'total')
        for table, number_column, prefix in (
            ('quotes', 'quote_number', 'QT-MONEY'),
            ('invoices', 'invoice_number', 'INV-MONEY'),
            ('receipts', 'receipt_number', 'RCT-MONEY'),
        ):
            for field in fields:
                with self.subTest(table=table, field=field):
                    columns = ['user_id', 'client_id', number_column, 'issue_date', 'currency', 'subtotal', 'total']
                    values = [self.owner.id, self.owner_client, f'{prefix}-{field}', '2026-09-15', 'KES', 0, 0]
                    if field not in ('subtotal', 'total'):
                        columns.append(field)
                        values.append(-1)
                    else:
                        values[columns.index(field)] = -1
                    placeholders = ', '.join(['%s'] * len(values))
                    with self.assertRaises(errors.CheckViolation):
                        self.connection.execute(
                            f'INSERT INTO {table} ({", ".join(columns)}) VALUES ({placeholders})',
                            tuple(values),
                        )

    def test_line_item_fields_reject_negative_values(self):
        for parent_table, item_table, number_column, prefix in (
            ('quotes', 'quote_items', 'quote_number', 'QT-ITEM'),
            ('invoices', 'invoice_items', 'invoice_number', 'INV-ITEM'),
            ('receipts', 'receipt_items', 'receipt_number', 'RCT-ITEM'),
        ):
            parent_id = self.connection.execute(
                f'''INSERT INTO {parent_table}
                    (user_id, client_id, {number_column}, issue_date, currency, subtotal, total)
                    VALUES (%s, %s, %s, DATE '2026-09-15', 'KES', 0, 0) RETURNING id''',
                (self.owner.id, self.owner_client, prefix),
            ).fetchone()[0]
            for field in ('quantity', 'unit_price', 'line_total'):
                with self.subTest(item_table=item_table, field=field):
                    values = {
                        'parent_id': parent_id, 'description': 'Work',
                        'quantity': 1, 'unit_price': 0, 'line_total': 0,
                    }
                    values[field] = -1
                    with self.assertRaises(errors.CheckViolation):
                        self.connection.execute(
                            f'''INSERT INTO {item_table}
                                ({parent_table[:-1]}_id, description, quantity, unit_price, line_total)
                                VALUES (%(parent_id)s, %(description)s, %(quantity)s,
                                        %(unit_price)s, %(line_total)s)''',
                            values,
                        )

    def test_one_invoice_per_quote_is_enforced(self):
        quote_id = self.connection.execute(
            '''INSERT INTO quotes
               (user_id, client_id, quote_number, issue_date, currency, subtotal, total)
               VALUES (%s, %s, 'QT-SOURCE', DATE '2026-09-15', 'KES', 0, 0) RETURNING id''',
            (self.owner.id, self.owner_client),
        ).fetchone()[0]
        self.connection.execute(
            '''INSERT INTO invoices
               (user_id, client_id, source_quote_id, invoice_number, issue_date, currency, subtotal, total)
               VALUES (%s, %s, %s, 'INV-SOURCE-1', DATE '2026-09-15', 'KES', 0, 0)''',
            (self.owner.id, self.owner_client, quote_id),
        )
        with self.assertRaises(errors.UniqueViolation):
            self.connection.execute(
                '''INSERT INTO invoices
                   (user_id, client_id, source_quote_id, invoice_number, issue_date, currency, subtotal, total)
                   VALUES (%s, %s, %s, 'INV-SOURCE-2', DATE '2026-09-15', 'KES', 0, 0)''',
                (self.owner.id, self.owner_client, quote_id),
            )
        self.assertEqual(
            self.connection.execute('SELECT count(*) FROM invoices WHERE source_quote_id = %s', (quote_id,)).fetchone()[0],
            1,
        )

    def test_multiple_receipts_per_invoice_are_allowed(self):
        invoice_id = self.connection.execute(
            '''INSERT INTO invoices
               (user_id, client_id, invoice_number, issue_date, currency, subtotal, total)
               VALUES (%s, %s, 'INV-RECEIPT-SOURCE', DATE '2026-09-15', 'KES', 0, 0) RETURNING id''',
            (self.owner.id, self.owner_client),
        ).fetchone()[0]
        for number in ('RCT-SOURCE-1', 'RCT-SOURCE-2'):
            self.connection.execute(
                '''INSERT INTO receipts
                   (user_id, client_id, source_invoice_id, receipt_number, issue_date, currency, subtotal, total)
                   VALUES (%s, %s, %s, %s, DATE '2026-09-15', 'KES', 0, 0)''',
                (self.owner.id, self.owner_client, invoice_id, number),
            )
        self.assertEqual(
            self.connection.execute('SELECT count(*) FROM receipts WHERE source_invoice_id = %s', (invoice_id,)).fetchone()[0],
            2,
        )
