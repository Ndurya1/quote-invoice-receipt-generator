import unittest
from decimal import Decimal
from uuid import uuid4

from pydantic import ValidationError

from app.common.errors import DomainError
from app.receipts.queries import get_receipt_for_user
from app.receipts.schemas import ReceiptPatch
from app.receipts.service import create_receipt, update_receipt
from tests import test_receipt_creation


class ReceiptPatchSchemaTests(unittest.TestCase):
    def test_omission_null_and_server_managed_fields(self):
        self.assertEqual(ReceiptPatch().model_dump(exclude_unset=True), {})
        self.assertEqual(ReceiptPatch(notes=None).model_dump(exclude_unset=True), {'notes': None})
        for field in ('client_id', 'issue_date', 'currency', 'tax_rate', 'discount_type', 'discount_value', 'items'):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                ReceiptPatch(**{field: None})
        for field in ('id', 'user_id', 'receipt_number', 'source_invoice_id', 'subtotal',
                      'tax_amount', 'discount_amount', 'total', 'created_at', 'updated_at'):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                ReceiptPatch(**{field: 'forged'})
        with self.assertRaises(ValidationError):
            ReceiptPatch(items=[])


class ReceiptUpdateTests(unittest.TestCase):
    setUpClass = classmethod(test_receipt_creation.ReceiptCreationTests.setUpClass.__func__)
    drop_test_schema = test_receipt_creation.ReceiptCreationTests.drop_test_schema
    payload = test_receipt_creation.ReceiptCreationTests.payload

    def setUp(self):
        test_receipt_creation.ReceiptCreationTests.setUp(self)
        self.created = create_receipt(self.connection, user_id=self.owner.id, payload=self.payload())
        self.receipt_id = self.created.receipt.id

    def update(self, **changes):
        return update_receipt(self.connection, user_id=self.owner.id, receipt_id=self.receipt_id,
                              payload=ReceiptPatch(**changes))

    def loaded(self):
        return get_receipt_for_user(self.connection, user_id=self.owner.id, receipt_id=self.receipt_id)

    def test_partial_finances_preserve_item_identity_and_immutable_fields(self):
        changed = self.update(tax_rate='10')
        self.assertEqual(changed.receipt.total, Decimal('155.00'))
        self.assertEqual(changed.receipt.tax_amount, Decimal('15.00'))
        self.assertEqual({item.id for item in changed.items}, {item.id for item in self.created.items})
        for field in ('id', 'user_id', 'receipt_number', 'created_at', 'source_invoice_id'):
            self.assertEqual(getattr(changed.receipt, field), getattr(self.created.receipt, field))
        self.assertGreater(changed.receipt.updated_at, self.created.receipt.updated_at)

    def test_replace_items_recalculates(self):
        changed = self.update(items=[{'description': 'Replacement', 'quantity': '2', 'unit_price': '100'}])
        self.assertEqual(changed.receipt.total, Decimal('222.00'))
        self.assertEqual(changed.items[0].line_total, Decimal('200.00'))
        self.assertNotEqual(changed.items[0].id, self.created.items[0].id)

    def test_nullable_fields_owned_client_and_empty_patch(self):
        original = self.loaded()
        self.assertEqual(self.update().receipt, original.receipt)
        replacement = self.connection.execute(
            "INSERT INTO clients (user_id, name) VALUES (%s, 'Replacement') RETURNING id", (self.owner.id,),
        ).fetchone()[0]
        changed = self.update(client_id=replacement, notes=None, currency='USD')
        self.assertEqual(changed.receipt.client_id, replacement)
        self.assertEqual((changed.receipt.notes, changed.receipt.currency), (None, 'USD'))

    def test_invalid_and_foreign_values_do_not_write(self):
        original = self.loaded()
        other = test_receipt_creation.create_user(self.connection, name='Other', email='other@example.com', password='test-password')
        foreign_client = self.connection.execute(
            "INSERT INTO clients (user_id, name) VALUES (%s, 'Foreign') RETURNING id", (other.id,),
        ).fetchone()[0]
        for changes, code in [({'discount_type': 'NONE'}, 'VALIDATION_ERROR'),
                              ({'discount_value': '999'}, 'INVALID_DISCOUNT'),
                              ({'client_id': foreign_client}, 'CLIENT_NOT_FOUND'),
                              ({'client_id': uuid4()}, 'CLIENT_NOT_FOUND')]:
            with self.subTest(changes=changes), self.assertRaises(DomainError) as error:
                self.update(**changes)
            self.assertEqual(error.exception.code, code)
            self.assertEqual(self.loaded(), original)

    def test_invoice_linked_receipts_cannot_be_edited(self):
        invoice_id = self.connection.execute(
            "INSERT INTO invoices (user_id, client_id, invoice_number, issue_date, currency, subtotal, total) "
            "VALUES (%s, %s, 'INV-0001', '2026-09-15', 'KES', 100, 100) RETURNING id",
            (self.owner.id, self.client_id),
        ).fetchone()[0]
        self.connection.execute('UPDATE receipts SET source_invoice_id = %s WHERE id = %s',
                                (invoice_id, self.receipt_id))
        with self.assertRaises(DomainError) as error:
            self.update(notes='Changed')
        self.assertEqual(error.exception.code, 'INVALID_RECEIPT_STATUS')
