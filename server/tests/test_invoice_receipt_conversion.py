import unittest
from datetime import date
from decimal import Decimal

from app.common.errors import DomainError
from app.conversions.invoice_receipt import convert_invoice_to_receipt
from app.invoices.models import InvoiceStatus
from app.invoices.queries import get_invoice_for_user
from app.invoices.service import create_invoice
from tests import test_invoice_creation


class InvoiceReceiptConversionTests(unittest.TestCase):
    setUpClass = classmethod(test_invoice_creation.InvoiceCreationTests.setUpClass.__func__)
    setUp = test_invoice_creation.InvoiceCreationTests.setUp
    drop_test_schema = test_invoice_creation.InvoiceCreationTests.drop_test_schema
    payload = test_invoice_creation.InvoiceCreationTests.payload

    def setUp(self):
        test_invoice_creation.InvoiceCreationTests.setUp(self)
        self.invoice = create_invoice(self.connection, user_id=self.owner.id, payload=self.payload())

    def convert(self, **changes):
        return convert_invoice_to_receipt(
            self.connection, user_id=self.owner.id, invoice_id=self.invoice.invoice.id,
            issue_date=changes.get('issue_date', date(2026, 10, 1)),
        )

    def test_conversion_copies_lineage_metadata_and_recalculates(self):
        result = self.convert()
        receipt = result.receipt
        self.assertEqual(receipt.source_invoice_id, self.invoice.invoice.id)
        self.assertEqual(receipt.receipt_number, 'RCT-0001')
        self.assertEqual((receipt.user_id, receipt.client_id, receipt.currency),
                         (self.owner.id, self.client_id, self.invoice.invoice.currency))
        self.assertEqual(receipt.notes, self.invoice.invoice.notes)
        self.assertEqual(receipt.total, Decimal('164.00'))
        self.assertEqual(len(result.items), len(self.invoice.items))
        self.assertNotEqual(result.items[0].id, self.invoice.items[0].id)
        self.assertTrue(all(item.receipt_id == receipt.id for item in result.items))
        source = get_invoice_for_user(self.connection, user_id=self.owner.id, invoice_id=self.invoice.invoice.id)
        self.assertEqual(source.invoice, self.invoice.invoice)
        self.assertEqual({item.id for item in source.items}, {item.id for item in self.invoice.items})

    def test_multiple_receipts_are_allowed_and_numbers_are_independent(self):
        first = self.convert()
        second = self.convert(issue_date=date(2026, 10, 2))
        self.assertEqual((first.receipt.receipt_number, second.receipt.receipt_number), ('RCT-0001', 'RCT-0002'))
        self.assertEqual(first.receipt.source_invoice_id, second.receipt.source_invoice_id)
        self.assertNotEqual(first.receipt.id, second.receipt.id)

    def test_cancelled_invoice_is_rejected_without_receipt(self):
        self.connection.execute('UPDATE invoices SET status = %s WHERE id = %s',
                                (InvoiceStatus.CANCELLED.value, self.invoice.invoice.id))
        with self.assertRaises(DomainError) as error:
            self.convert()
        self.assertEqual(error.exception.code, 'INVALID_INVOICE_STATUS')
        self.assertEqual(self.connection.execute('SELECT count(*) FROM receipts').fetchone()[0], 0)

    def test_item_failure_rolls_back_receipt_number_and_source(self):
        self.connection.execute('''CREATE FUNCTION reject_invoice_receipt_item() RETURNS TRIGGER LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'Private invoice receipt detail'; END; $$;
            CREATE TRIGGER reject_invoice_receipt_item BEFORE INSERT ON receipt_items
            FOR EACH ROW EXECUTE FUNCTION reject_invoice_receipt_item();''')
        with self.assertRaisesRegex(Exception, 'Private invoice receipt detail'):
            self.convert()
        self.assertEqual(self.connection.execute('SELECT count(*) FROM receipts').fetchone()[0], 0)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM receipt_number_counters').fetchone()[0], 0)
        source = get_invoice_for_user(self.connection, user_id=self.owner.id, invoice_id=self.invoice.invoice.id)
        self.assertEqual(source.invoice, self.invoice.invoice)
