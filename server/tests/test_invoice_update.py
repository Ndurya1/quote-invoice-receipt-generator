import unittest
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import ValidationError

from app.common.errors import DomainError
from app.invoices.models import InvoiceStatus
from app.invoices.queries import get_invoice_for_user
from app.invoices.schemas import InvoicePatch
from app.invoices.service import create_invoice, update_invoice
from tests import test_invoice_creation


class InvoicePatchSchemaTests(unittest.TestCase):
    def test_omission_null_and_server_managed_fields(self):
        self.assertEqual(InvoicePatch().model_dump(exclude_unset=True), {})
        self.assertEqual(InvoicePatch(notes=None).model_dump(exclude_unset=True), {'notes': None})
        for field in ('client_id', 'issue_date', 'currency', 'tax_rate', 'discount_type', 'discount_value', 'items'):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                InvoicePatch(**{field: None})
        for field in ('id', 'user_id', 'invoice_number', 'status', 'subtotal', 'tax_amount',
                      'discount_amount', 'total', 'created_at', 'updated_at', 'source_quote_id'):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                InvoicePatch(**{field: 'forged'})


class InvoiceUpdateTests(unittest.TestCase):
    setUpClass = classmethod(test_invoice_creation.InvoiceCreationTests.setUpClass.__func__)
    drop_test_schema = test_invoice_creation.InvoiceCreationTests.drop_test_schema
    payload = test_invoice_creation.InvoiceCreationTests.payload

    def setUp(self):
        test_invoice_creation.InvoiceCreationTests.setUp(self)
        self.created = create_invoice(self.connection, user_id=self.owner.id, payload=self.payload())
        self.invoice_id = self.created.invoice.id

    def update(self, **changes):
        return update_invoice(self.connection, user_id=self.owner.id, invoice_id=self.invoice_id,
                              payload=InvoicePatch(**changes))

    def loaded(self):
        return get_invoice_for_user(self.connection, user_id=self.owner.id, invoice_id=self.invoice_id)

    def test_partial_finances_preserve_item_identity_and_immutable_fields(self):
        changed = self.update(tax_rate='10')
        self.assertEqual(changed.invoice.total, Decimal('155.00'))
        self.assertEqual(changed.invoice.tax_amount, Decimal('15.00'))
        self.assertEqual({i.id for i in changed.items}, {i.id for i in self.created.items})
        for field in ('id', 'user_id', 'invoice_number', 'created_at', 'status', 'source_quote_id'):
            self.assertEqual(getattr(changed.invoice, field), getattr(self.created.invoice, field))
        self.assertGreater(changed.invoice.updated_at, self.created.invoice.updated_at)

    def test_replace_items_recalculates(self):
        changed = self.update(items=[{'description': 'Replacement', 'quantity': '2', 'unit_price': '100'}])
        self.assertEqual(changed.invoice.total, Decimal('222.00'))
        self.assertEqual(changed.items[0].line_total, Decimal('200.00'))
        self.assertNotEqual(changed.items[0].id, self.created.items[0].id)

    def test_nullable_fields_and_owned_replacement_client(self):
        original = self.loaded()
        self.assertEqual(self.update().invoice, original.invoice)
        replacement = self.connection.execute(
            "INSERT INTO clients (user_id, name) VALUES (%s, 'Replacement') RETURNING id", (self.owner.id,),
        ).fetchone()[0]
        changed = self.update(client_id=replacement, notes=None, terms=None, due_date=None, currency='USD')
        self.assertEqual(changed.invoice.client_id, replacement)
        self.assertEqual((changed.invoice.notes, changed.invoice.terms, changed.invoice.due_date), (None, None, None))

    def test_invalid_and_foreign_values_do_not_write(self):
        original = self.loaded()
        other = test_invoice_creation.create_user(self.connection, name='Other', email='other@example.com', password='test-password')
        foreign_client = self.connection.execute(
            "INSERT INTO clients (user_id, name) VALUES (%s, 'Foreign') RETURNING id", (other.id,),
        ).fetchone()[0]
        for changes, code in [({'issue_date': '2026-10-01'}, 'VALIDATION_ERROR'),
                              ({'discount_type': 'NONE'}, 'VALIDATION_ERROR'),
                              ({'discount_value': '999'}, 'INVALID_DISCOUNT'),
                              ({'client_id': foreign_client}, 'CLIENT_NOT_FOUND'),
                              ({'client_id': uuid4()}, 'CLIENT_NOT_FOUND')]:
            with self.subTest(changes=changes), self.assertRaises(DomainError) as error:
                self.update(**changes)
            self.assertEqual(error.exception.code, code)
            self.assertEqual(self.loaded(), original)

    def test_non_draft_and_linked_invoices_block_edits(self):
        for status in InvoiceStatus:
            if status == InvoiceStatus.DRAFT:
                continue
            self.connection.execute('UPDATE invoices SET status = %s WHERE id = %s', (status.value, self.invoice_id))
            with self.assertRaises(DomainError) as error:
                self.update(notes='Changed')
            self.assertEqual(error.exception.code, 'INVALID_INVOICE_STATUS')
            self.connection.execute('UPDATE invoices SET status = %s WHERE id = %s', ('DRAFT', self.invoice_id))
        self.connection.execute(
            '''INSERT INTO quotes (user_id, client_id, quote_number, issue_date, currency, subtotal, total)
               VALUES (%s, %s, 'QT-0001', '2026-09-15', 'KES', 1, 1) RETURNING id''',
            (self.owner.id, self.client_id),
        )
        quote_id = self.connection.execute('SELECT id FROM quotes WHERE quote_number = %s', ('QT-0001',)).fetchone()[0]
        self.connection.execute('UPDATE invoices SET source_quote_id = %s WHERE id = %s', (quote_id, self.invoice_id))
        with self.assertRaises(DomainError) as error:
            self.update(notes='Changed')
        self.assertEqual(error.exception.code, 'INVALID_INVOICE_STATUS')

    def test_foreign_and_missing_invoices_share_not_found(self):
        for user_id, invoice_id in ((uuid4(), self.invoice_id), (self.owner.id, uuid4())):
            with self.assertRaises(DomainError) as error:
                update_invoice(self.connection, user_id=user_id, invoice_id=invoice_id, payload=InvoicePatch(notes='x'))
            self.assertEqual((error.exception.code, error.exception.status_code), ('INVOICE_NOT_FOUND', 404))
