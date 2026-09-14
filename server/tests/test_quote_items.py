import unittest
from decimal import Decimal
from uuid import UUID, uuid4

from psycopg import errors, sql
from psycopg.rows import class_row

from app.quotes.models import QuoteItem
from tests import test_quotes


class QuoteItemPersistenceTests(unittest.TestCase):
    setUpClass = classmethod(test_quotes.QuotePersistenceTests.setUpClass.__func__)
    setUp = test_quotes.QuotePersistenceTests.setUp
    drop_test_schema = test_quotes.QuotePersistenceTests.drop_test_schema
    insert_quote = test_quotes.QuotePersistenceTests.insert

    def insert_item(self, quote_id, **changes):
        values = {'quote_id': quote_id, 'description': "Consultant's work",
                  'quantity': Decimal('1.250'), 'unit_price': Decimal('12.40'),
                  'line_total': Decimal('15.50'), **changes}
        with self.connection.cursor(row_factory=class_row(QuoteItem)) as cursor:
            cursor.execute(sql.SQL('INSERT INTO quote_items ({}) VALUES ({}) RETURNING *').format(
                sql.SQL(', ').join(map(sql.Identifier, values)),
                sql.SQL(', ').join(sql.Placeholder() for _ in values),
            ), tuple(values.values()))
            return cursor.fetchone()

    def test_persisted_fields_and_default_position(self):
        quote = self.insert_quote()
        item = self.insert_item(quote.id)
        self.assertIsInstance(item, QuoteItem)
        self.assertIsInstance(item.id, UUID)
        self.assertEqual(item.quote_id, quote.id)
        self.assertEqual(item.description, "Consultant's work")
        self.assertEqual(item.position, 0)
        for field, value in (('quantity', '1.250'), ('unit_price', '12.40'), ('line_total', '15.50')):
            self.assertIsInstance(getattr(item, field), Decimal)
            self.assertEqual(str(getattr(item, field)), value)
        self.assertEqual(self.insert_item(quote.id, position=5).position, 5)

    def test_amount_constraints_and_zero_price(self):
        quote = self.insert_quote()
        for changes in ({'quantity': Decimal('0')}, {'quantity': Decimal('-1')},
                        {'unit_price': Decimal('-0.01')}, {'line_total': Decimal('-0.01')}):
            with self.subTest(changes=changes), self.assertRaises(errors.CheckViolation):
                self.insert_item(quote.id, **changes)
        free = self.insert_item(quote.id, quantity=Decimal('0.001'), unit_price=Decimal('0'), line_total=Decimal('0'))
        self.assertEqual(free.line_total, Decimal('0.00'))

    def test_parent_and_required_fields_enforced(self):
        quote = self.insert_quote()
        with self.assertRaises(errors.ForeignKeyViolation):
            self.insert_item(uuid4())
        with self.assertRaises(errors.NotNullViolation):
            self.insert_item(None)
        for field in ('description', 'quantity', 'unit_price', 'line_total', 'position'):
            with self.subTest(field=field), self.assertRaises(errors.NotNullViolation):
                self.insert_item(quote.id, **{field: None})

    def test_database_precision_and_parent_index(self):
        columns = self.connection.execute(
            "SELECT column_name, numeric_precision, numeric_scale FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = 'quote_items' "
            "AND column_name IN ('quantity', 'unit_price', 'line_total')"
        ).fetchall()
        self.assertEqual({name: (precision, scale) for name, precision, scale in columns},
                         {'quantity': (12, 3), 'unit_price': (14, 2), 'line_total': (14, 2)})
        index = self.connection.execute(
            "SELECT indexdef FROM pg_indexes WHERE schemaname = current_schema() AND indexname = 'quote_items_quote_id_idx'"
        ).fetchone()[0]
        self.assertIn('(quote_id)', index)

    def test_parent_deletion_cascades_only_to_its_items(self):
        first, second = self.insert_quote(), self.insert_quote()
        self.insert_item(first.id)
        self.insert_item(first.id)
        survivor = self.insert_item(second.id)
        self.connection.execute('DELETE FROM quotes WHERE id = %s', (first.id,))
        self.assertEqual(self.connection.execute('SELECT id FROM quote_items').fetchall(), [(survivor.id,)])
        self.assertEqual(self.connection.execute('SELECT id FROM quotes').fetchall(), [(second.id,)])

    def test_item_insertion_respects_transaction_rollback(self):
        quote = self.insert_quote()
        with self.assertRaisesRegex(RuntimeError, 'abort'):
            with self.connection.transaction():
                self.insert_item(quote.id)
                raise RuntimeError('abort')
        self.assertEqual(self.connection.execute('SELECT count(*) FROM quote_items').fetchone()[0], 0)
