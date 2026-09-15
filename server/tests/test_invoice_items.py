import unittest
from decimal import Decimal
from uuid import UUID, uuid4

from psycopg import errors, sql
from psycopg.rows import class_row

from app.invoices.models import InvoiceItem
from tests import test_invoices


class InvoiceItemPersistenceTests(unittest.TestCase):
    setUpClass = classmethod(test_invoices.InvoicePersistenceTests.setUpClass.__func__)
    setUp = test_invoices.InvoicePersistenceTests.setUp
    drop_test_schema = test_invoices.InvoicePersistenceTests.drop_test_schema
    insert_invoice = test_invoices.InvoicePersistenceTests.insert

    def insert_item(self, invoice_id, **changes):
        values = {'invoice_id': invoice_id, 'description': "Consultant's work",
                  'quantity': Decimal('1.250'), 'unit_price': Decimal('12.40'),
                  'line_total': Decimal('15.50'), **changes}
        with self.connection.cursor(row_factory=class_row(InvoiceItem)) as cursor:
            cursor.execute(sql.SQL('INSERT INTO invoice_items ({}) VALUES ({}) RETURNING *').format(
                sql.SQL(', ').join(map(sql.Identifier, values)),
                sql.SQL(', ').join(sql.Placeholder() for _ in values),
            ), tuple(values.values()))
            return cursor.fetchone()

    def test_persisted_fields_and_default_position(self):
        invoice = self.insert_invoice()
        item = self.insert_item(invoice.id)
        self.assertIsInstance(item, InvoiceItem)
        self.assertIsInstance(item.id, UUID)
        self.assertEqual(item.invoice_id, invoice.id)
        self.assertEqual(item.description, "Consultant's work")
        self.assertEqual(item.position, 0)
        for field, value in (('quantity', '1.250'), ('unit_price', '12.40'), ('line_total', '15.50')):
            self.assertIsInstance(getattr(item, field), Decimal)
            self.assertEqual(str(getattr(item, field)), value)
        self.assertEqual(self.insert_item(invoice.id, position=5).position, 5)

    def test_amount_constraints_and_zero_price(self):
        invoice = self.insert_invoice()
        for changes in ({'quantity': Decimal('0')}, {'quantity': Decimal('-1')},
                        {'unit_price': Decimal('-0.01')}, {'line_total': Decimal('-0.01')}):
            with self.subTest(changes=changes), self.assertRaises(errors.CheckViolation):
                self.insert_item(invoice.id, **changes)
        free = self.insert_item(invoice.id, quantity=Decimal('0.001'), unit_price=Decimal('0'), line_total=Decimal('0'))
        self.assertEqual(free.line_total, Decimal('0.00'))

    def test_parent_and_required_fields_enforced(self):
        invoice = self.insert_invoice()
        with self.assertRaises(errors.ForeignKeyViolation):
            self.insert_item(uuid4())
        with self.assertRaises(errors.NotNullViolation):
            self.insert_item(None)
        for field in ('description', 'quantity', 'unit_price', 'line_total', 'position'):
            with self.subTest(field=field), self.assertRaises(errors.NotNullViolation):
                self.insert_item(invoice.id, **{field: None})

    def test_database_precision_and_parent_index(self):
        columns = self.connection.execute(
            "SELECT column_name, numeric_precision, numeric_scale FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = 'invoice_items' "
            "AND column_name IN ('quantity', 'unit_price', 'line_total')"
        ).fetchall()
        self.assertEqual({name: (precision, scale) for name, precision, scale in columns},
                         {'quantity': (12, 3), 'unit_price': (14, 2), 'line_total': (14, 2)})
        index = self.connection.execute(
            "SELECT indexdef FROM pg_indexes WHERE schemaname = current_schema() AND indexname = 'invoice_items_invoice_id_idx'"
        ).fetchone()[0]
        self.assertIn('(invoice_id)', index)

    def test_parent_deletion_cascades_only_to_its_items(self):
        first, second = self.insert_invoice(), self.insert_invoice()
        self.insert_item(first.id)
        self.insert_item(first.id)
        survivor = self.insert_item(second.id)
        self.connection.execute('DELETE FROM invoices WHERE id = %s', (first.id,))
        self.assertEqual(self.connection.execute('SELECT id FROM invoice_items').fetchall(), [(survivor.id,)])
        self.assertEqual(self.connection.execute('SELECT id FROM invoices').fetchall(), [(second.id,)])

    def test_item_insertion_respects_transaction_rollback(self):
        invoice = self.insert_invoice()
        with self.assertRaisesRegex(RuntimeError, 'abort'):
            with self.connection.transaction():
                self.insert_item(invoice.id)
                raise RuntimeError('abort')
        self.assertEqual(self.connection.execute('SELECT count(*) FROM invoice_items').fetchone()[0], 0)
