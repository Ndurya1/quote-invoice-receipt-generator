import unittest
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.common.errors import DomainError
from app.conversions.quote_invoice import convert_quote_to_invoice
from app.quotes.models import QuoteStatus
from app.quotes.queries import get_quote_for_user
from app.quotes.service import create_quote
from tests import test_quote_creation


class QuoteInvoiceConversionTests(unittest.TestCase):
    setUpClass = classmethod(test_quote_creation.QuoteCreationTests.setUpClass.__func__)
    setUp = test_quote_creation.QuoteCreationTests.setUp
    drop_test_schema = test_quote_creation.QuoteCreationTests.drop_test_schema
    payload = test_quote_creation.QuoteCreationTests.payload

    def setUp(self):
        test_quote_creation.QuoteCreationTests.setUp(self)
        self.quote = create_quote(self.connection, user_id=self.owner.id, payload=self.payload())
        self.connection.execute('UPDATE quotes SET status = %s WHERE id = %s',
                                (QuoteStatus.ACCEPTED.value, self.quote.quote.id))

    def convert(self, **changes):
        return convert_quote_to_invoice(
            self.connection, user_id=self.owner.id, quote_id=self.quote.quote.id,
            issue_date=changes.get('issue_date', date(2026, 9, 20)),
            due_date=changes.get('due_date', date(2026, 10, 1)),
        )

    def test_conversion_copies_lineage_metadata_and_recalculates(self):
        result = self.convert()
        invoice = result.invoice
        self.assertEqual(invoice.source_quote_id, self.quote.quote.id)
        self.assertEqual(invoice.invoice_number, 'INV-0001')
        self.assertEqual(invoice.status.value, 'DRAFT')
        self.assertEqual((invoice.user_id, invoice.client_id, invoice.currency),
                         (self.owner.id, self.client_id, self.quote.quote.currency))
        self.assertEqual((invoice.notes, invoice.terms), (self.quote.quote.notes, self.quote.quote.terms))
        self.assertEqual(invoice.total, Decimal('164.00'))
        self.assertEqual(len(result.items), len(self.quote.items))
        self.assertNotEqual(result.items[0].id, self.quote.items[0].id)
        self.assertTrue(all(item.invoice_id == invoice.id for item in result.items))
        saved_quote = get_quote_for_user(self.connection, user_id=self.owner.id, quote_id=self.quote.quote.id)
        self.assertEqual(saved_quote.quote.status, QuoteStatus.CONVERTED)
        self.assertEqual({item.description for item in saved_quote.items},
                         {item.description for item in self.quote.items})

    def test_repeated_conversion_is_rejected_without_second_invoice(self):
        self.convert()
        with self.assertRaises(DomainError) as error:
            self.convert()
        self.assertEqual((error.exception.code, error.exception.status_code), ('QUOTE_ALREADY_CONVERTED', 409))
        self.assertEqual(self.connection.execute('SELECT count(*) FROM invoices').fetchone()[0], 1)

    def test_invalid_dates_roll_back_without_creating_invoice(self):
        with self.assertRaises(ValueError):
            self.convert(due_date=date(2026, 9, 19))
        self.assertEqual(self.connection.execute('SELECT count(*) FROM invoices').fetchone()[0], 0)
        self.assertEqual(get_quote_for_user(self.connection, user_id=self.owner.id,
                                            quote_id=self.quote.quote.id).quote.status, QuoteStatus.ACCEPTED)

    def test_item_failure_rolls_back_invoice_number_and_quote_status(self):
        self.connection.execute('''CREATE FUNCTION reject_conversion_item() RETURNS TRIGGER LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'Private conversion detail'; END; $$;
            CREATE TRIGGER reject_conversion_item BEFORE INSERT ON invoice_items
            FOR EACH ROW EXECUTE FUNCTION reject_conversion_item();''')
        with self.assertRaisesRegex(Exception, 'Private conversion detail'):
            self.convert()
        self.assertEqual(self.connection.execute('SELECT count(*) FROM invoices').fetchone()[0], 0)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM invoice_number_counters').fetchone()[0], 0)
        self.assertEqual(get_quote_for_user(self.connection, user_id=self.owner.id,
                                            quote_id=self.quote.quote.id).quote.status, QuoteStatus.ACCEPTED)
