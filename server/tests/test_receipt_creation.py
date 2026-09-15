import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from psycopg import errors, sql
from psycopg.rows import class_row

from app.accounts.service import create_user
from app.common.database import connect_database
from app.common.errors import DomainError
from app.receipts.models import Receipt, ReceiptItem
from app.receipts.schemas import ReceiptCreate
from app.receipts.service import create_receipt
from tests import test_invoices


class ReceiptCreationTests(unittest.TestCase):
    setUpClass = classmethod(test_invoices.InvoicePersistenceTests.setUpClass.__func__)
    setUp = test_invoices.InvoicePersistenceTests.setUp
    drop_test_schema = test_invoices.InvoicePersistenceTests.drop_test_schema

    def payload(self, **changes):
        return ReceiptCreate(**{
            'client_id': self.client_id, 'issue_date': '2026-09-15',
            'currency': 'KES', 'tax_rate': '16', 'discount_type': 'FIXED', 'discount_value': '10',
            'notes': 'Notes', 'items': [
                {'description': 'First', 'quantity': '1.25', 'unit_price': '80', 'position': 2},
                {'description': 'Second', 'quantity': '2', 'unit_price': '25', 'position': 1},
            ], **changes,
        })

    def counts(self):
        return tuple(self.connection.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table))).fetchone()[0]
                     for table in ('receipts', 'receipt_items', 'receipt_number_counters'))

    def test_persists_authoritative_totals_and_all_items(self):
        payload = self.payload()
        original = payload.model_dump()
        result = create_receipt(self.connection, user_id=self.owner.id, payload=payload)
        receipt = result.receipt
        self.assertIsNone(receipt.source_invoice_id)
        self.assertEqual(receipt.receipt_number, 'RCT-0001')
        self.assertEqual((receipt.user_id, receipt.client_id), (self.owner.id, self.client_id))
        self.assertEqual((receipt.subtotal, receipt.tax_amount, receipt.discount_amount, receipt.total),
                         (Decimal('150'), Decimal('24'), Decimal('10'), Decimal('164')))
        self.assertEqual((receipt.issue_date, receipt.currency, receipt.notes),
                         (payload.issue_date, 'KES', 'Notes'))
        self.assertEqual([item.line_total for item in result.items], [Decimal('100'), Decimal('50')])
        self.assertEqual([item.position for item in result.items], [2, 1])
        self.assertTrue(all(item.receipt_id == receipt.id for item in result.items))
        self.assertEqual(len({item.id for item in result.items}), 2)
        with self.connection.cursor(row_factory=class_row(Receipt)) as cursor:
            cursor.execute('SELECT * FROM receipts WHERE id = %s', (receipt.id,))
            self.assertEqual(cursor.fetchone(), receipt)
        with self.connection.cursor(row_factory=class_row(ReceiptItem)) as cursor:
            cursor.execute('SELECT * FROM receipt_items WHERE receipt_id = %s', (receipt.id,))
            self.assertEqual({item.id: item for item in cursor.fetchall()}, {item.id: item for item in result.items})
        self.assertEqual(payload.model_dump(), original)

    def test_later_item_failure_rolls_back_parent_items_and_allocation(self):
        self.connection.execute('''CREATE FUNCTION reject_test_item() RETURNS TRIGGER LANGUAGE plpgsql AS $$
            BEGIN
                IF NEW.description = 'Second' THEN
                    RAISE EXCEPTION 'Test item failure' USING ERRCODE = '23514';
                END IF;
                RETURN NEW;
            END; $$;
            CREATE TRIGGER reject_test_item BEFORE INSERT ON receipt_items
            FOR EACH ROW EXECUTE FUNCTION reject_test_item();''')
        with self.assertRaises(errors.CheckViolation):
            create_receipt(self.connection, user_id=self.owner.id, payload=self.payload())
        self.assertEqual(self.counts(), (0, 0, 0))
        self.connection.execute('DROP TRIGGER reject_test_item ON receipt_items')
        result = create_receipt(self.connection, user_id=self.owner.id, payload=self.payload())
        self.assertEqual(result.receipt.receipt_number, 'RCT-0001')

    def test_foreign_client_and_invalid_finances_write_nothing(self):
        other = create_user(self.connection, name='Other', email='other@example.com', password='test-password')
        with self.assertRaises(DomainError) as error:
            create_receipt(self.connection, user_id=other.id, payload=self.payload())
        self.assertEqual(error.exception.code, 'CLIENT_NOT_FOUND')
        with self.assertRaises(DomainError):
            create_receipt(self.connection, user_id=self.owner.id, payload=self.payload(discount_value='1000'))
        self.assertEqual(self.counts(), (0, 0, 0))

    def test_outer_transaction_rollback_restores_existing_counter(self):
        first = create_receipt(self.connection, user_id=self.owner.id, payload=self.payload())
        with self.assertRaisesRegex(RuntimeError, 'abort'):
            with self.connection.transaction():
                create_receipt(self.connection, user_id=self.owner.id, payload=self.payload())
                raise RuntimeError('abort')
        self.assertEqual(self.counts(), (1, 2, 1))
        second = create_receipt(self.connection, user_id=self.owner.id, payload=self.payload())
        self.assertEqual((first.receipt.receipt_number, second.receipt.receipt_number), ('RCT-0001', 'RCT-0002'))

    def test_concurrent_creations_have_unique_numbers_and_complete_items(self):
        barrier = Barrier(4)
        payload = self.payload()

        def create(_):
            with connect_database(self.settings, test=True) as connection:
                connection.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(self.schema)))
                connection.execute("SET statement_timeout = '10s'")
                barrier.wait(timeout=10)
                return create_receipt(connection, user_id=self.owner.id, payload=payload)

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(create, range(4)))
        self.assertEqual(sorted(result.receipt.receipt_number for result in results), [f'RCT-{i:04d}' for i in range(1, 5)])
        self.assertTrue(all(len(result.items) == 2 for result in results))
        self.assertEqual(self.counts(), (4, 8, 1))

    def test_models_match_database_and_source_invoice_allows_multiple_receipts(self):
        for table, model in (('receipts', Receipt), ('receipt_items', ReceiptItem)):
            columns = {row[0] for row in self.connection.execute(
                'SELECT column_name FROM information_schema.columns '
                'WHERE table_schema = %s AND table_name = %s', (self.schema, table))}
            self.assertEqual(set(model.model_fields), columns)
        invoice_id = self.connection.execute(
            "INSERT INTO invoices (user_id, client_id, invoice_number, issue_date, currency, subtotal, total) "
            "VALUES (%s, %s, 'INV-0001', '2026-09-15', 'KES', 150, 150) RETURNING id",
            (self.owner.id, self.client_id),
        ).fetchone()[0]
        receipts = [create_receipt(self.connection, user_id=self.owner.id, payload=self.payload()).receipt
                    for _ in range(2)]
        for receipt in receipts:
            self.assertIsNone(receipt.source_invoice_id)
            with self.connection.cursor(row_factory=class_row(Receipt)) as cursor:
                cursor.execute('UPDATE receipts SET source_invoice_id = %s WHERE id = %s RETURNING *',
                               (invoice_id, receipt.id))
                self.assertEqual(cursor.fetchone().source_invoice_id, invoice_id)
