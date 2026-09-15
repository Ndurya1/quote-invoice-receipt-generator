import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from psycopg import errors, sql
from psycopg.rows import class_row

from app.accounts.service import create_user
from app.common.database import connect_database
from app.common.errors import DomainError
from app.invoices.models import Invoice, InvoiceItem, InvoiceStatus
from app.invoices.schemas import InvoiceCreate
from app.invoices.service import create_invoice
from tests import test_invoices


class InvoiceCreationTests(unittest.TestCase):
    setUpClass = classmethod(test_invoices.InvoicePersistenceTests.setUpClass.__func__)
    setUp = test_invoices.InvoicePersistenceTests.setUp
    drop_test_schema = test_invoices.InvoicePersistenceTests.drop_test_schema

    def payload(self, **changes):
        return InvoiceCreate(**{
            'client_id': self.client_id, 'issue_date': '2026-09-15', 'due_date': '2026-09-30',
            'currency': 'KES', 'tax_rate': '16', 'discount_type': 'FIXED', 'discount_value': '10',
            'notes': 'Notes', 'terms': 'Terms', 'items': [
                {'description': 'First', 'quantity': '1.25', 'unit_price': '80', 'position': 2},
                {'description': 'Second', 'quantity': '2', 'unit_price': '25', 'position': 1},
            ], **changes,
        })

    def counts(self):
        return tuple(self.connection.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table))).fetchone()[0]
                     for table in ('invoices', 'invoice_items', 'invoice_number_counters'))

    def test_persists_authoritative_totals_and_all_items(self):
        payload = self.payload()
        original = payload.model_dump()
        result = create_invoice(self.connection, user_id=self.owner.id, payload=payload)
        invoice = result.invoice
        self.assertIsNone(invoice.source_quote_id)
        self.assertEqual(invoice.invoice_number, 'INV-0001')
        self.assertIs(invoice.status, InvoiceStatus.DRAFT)
        self.assertEqual((invoice.user_id, invoice.client_id), (self.owner.id, self.client_id))
        self.assertEqual((invoice.subtotal, invoice.tax_amount, invoice.discount_amount, invoice.total),
                         (Decimal('150'), Decimal('24'), Decimal('10'), Decimal('164')))
        self.assertEqual((invoice.issue_date, invoice.due_date, invoice.currency, invoice.notes, invoice.terms),
                         (payload.issue_date, payload.due_date, 'KES', 'Notes', 'Terms'))
        self.assertEqual([item.line_total for item in result.items], [Decimal('100'), Decimal('50')])
        self.assertEqual([item.position for item in result.items], [2, 1])
        self.assertTrue(all(item.invoice_id == invoice.id for item in result.items))
        self.assertEqual(len({item.id for item in result.items}), 2)
        with self.connection.cursor(row_factory=class_row(Invoice)) as cursor:
            cursor.execute('SELECT * FROM invoices WHERE id = %s', (invoice.id,))
            self.assertEqual(cursor.fetchone(), invoice)
        with self.connection.cursor(row_factory=class_row(InvoiceItem)) as cursor:
            cursor.execute('SELECT * FROM invoice_items WHERE invoice_id = %s', (invoice.id,))
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
            CREATE TRIGGER reject_test_item BEFORE INSERT ON invoice_items
            FOR EACH ROW EXECUTE FUNCTION reject_test_item();''')
        with self.assertRaises(errors.CheckViolation):
            create_invoice(self.connection, user_id=self.owner.id, payload=self.payload())
        self.assertEqual(self.counts(), (0, 0, 0))
        self.connection.execute('DROP TRIGGER reject_test_item ON invoice_items')
        result = create_invoice(self.connection, user_id=self.owner.id, payload=self.payload())
        self.assertEqual(result.invoice.invoice_number, 'INV-0001')

    def test_foreign_client_and_invalid_finances_write_nothing(self):
        other = create_user(self.connection, name='Other', email='other@example.com', password='test-password')
        with self.assertRaises(DomainError) as error:
            create_invoice(self.connection, user_id=other.id, payload=self.payload())
        self.assertEqual(error.exception.code, 'CLIENT_NOT_FOUND')
        with self.assertRaises(DomainError):
            create_invoice(self.connection, user_id=self.owner.id, payload=self.payload(discount_value='1000'))
        self.assertEqual(self.counts(), (0, 0, 0))

    def test_outer_transaction_rollback_restores_existing_counter(self):
        first = create_invoice(self.connection, user_id=self.owner.id, payload=self.payload())
        with self.assertRaisesRegex(RuntimeError, 'abort'):
            with self.connection.transaction():
                create_invoice(self.connection, user_id=self.owner.id, payload=self.payload())
                raise RuntimeError('abort')
        self.assertEqual(self.counts(), (1, 2, 1))
        second = create_invoice(self.connection, user_id=self.owner.id, payload=self.payload())
        self.assertEqual((first.invoice.invoice_number, second.invoice.invoice_number), ('INV-0001', 'INV-0002'))

    def test_concurrent_creations_have_unique_numbers_and_complete_items(self):
        barrier = Barrier(4)
        payload = self.payload()

        def create(_):
            with connect_database(self.settings, test=True) as connection:
                connection.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(self.schema)))
                connection.execute("SET statement_timeout = '10s'")
                barrier.wait(timeout=10)
                return create_invoice(connection, user_id=self.owner.id, payload=payload)

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(create, range(4)))
        self.assertEqual(sorted(result.invoice.invoice_number for result in results), [f'INV-{i:04d}' for i in range(1, 5)])
        self.assertTrue(all(len(result.items) == 2 for result in results))
        self.assertEqual(self.counts(), (4, 8, 1))
