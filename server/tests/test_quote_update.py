import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

from psycopg import errors, sql
from pydantic import ValidationError

from app.accounts.service import create_user
from app.common.database import connect_database
from app.common.errors import DomainError
from app.quotes.models import QuoteStatus
from app.quotes.queries import get_quote_for_user
from app.quotes.schemas import QuotePatch
from app.quotes.service import create_quote, update_quote
from tests import test_quote_creation


class QuotePatchSchemaTests(unittest.TestCase):
    def test_omission_null_and_server_managed_fields(self):
        self.assertEqual(QuotePatch().model_dump(exclude_unset=True), {})
        self.assertEqual(QuotePatch(notes=None).model_dump(exclude_unset=True), {'notes': None})
        for field in ('client_id', 'issue_date', 'currency', 'tax_rate', 'discount_type', 'discount_value', 'items'):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                QuotePatch(**{field: None})
        for field in ('id', 'user_id', 'quote_number', 'status', 'subtotal', 'tax_amount',
                      'discount_amount', 'total', 'created_at', 'updated_at', 'source_quote_id'):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                QuotePatch(**{field: 'forged'})
        for values in ({'items': []}, {'currency': 'kes'}, {'tax_rate': '-1'},
                       {'items': [{'description': 'x', 'quantity': '1', 'unit_price': '2', 'line_total': '999'}]}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                QuotePatch(**values)


class QuoteUpdateTests(unittest.TestCase):
    setUpClass = classmethod(test_quote_creation.QuoteCreationTests.setUpClass.__func__)
    drop_test_schema = test_quote_creation.QuoteCreationTests.drop_test_schema
    payload = test_quote_creation.QuoteCreationTests.payload

    def setUp(self):
        test_quote_creation.QuoteCreationTests.setUp(self)
        self.created = create_quote(self.connection, user_id=self.owner.id, payload=self.payload())
        self.quote_id = self.created.quote.id

    def update(self, **changes):
        return update_quote(self.connection, user_id=self.owner.id, quote_id=self.quote_id,
                            payload=QuotePatch(**changes))

    def loaded(self):
        return get_quote_for_user(self.connection, user_id=self.owner.id, quote_id=self.quote_id)

    def link_invoice(self):
        return self.connection.execute(
            '''INSERT INTO invoices (user_id, client_id, source_quote_id, invoice_number,
               issue_date, currency, subtotal, total)
               VALUES (%s, %s, %s, 'INV-0001', '2026-09-15', 'KES', 150, 164) RETURNING id''',
            (self.owner.id, self.client_id, self.quote_id),
        ).fetchone()[0]

    def test_partial_finances_preserve_item_identity_and_immutable_fields(self):
        changed = self.update(tax_rate='10')
        self.assertEqual(changed.quote.total, Decimal('155.00'))
        self.assertEqual(changed.quote.tax_amount, Decimal('15.00'))
        self.assertEqual({i.id for i in changed.items}, {i.id for i in self.created.items})
        for field in ('id', 'user_id', 'quote_number', 'created_at', 'status'):
            self.assertEqual(getattr(changed.quote, field), getattr(self.created.quote, field))
        self.assertGreater(changed.quote.updated_at, self.created.quote.updated_at)
        self.assertEqual(self.loaded().quote, changed.quote)
        self.assertEqual(self.update(discount_type='PERCENTAGE', discount_value='20').quote.total, Decimal('135'))

    def test_replace_items_recalculates_and_does_not_change_other_quote(self):
        other = create_quote(self.connection, user_id=self.owner.id, payload=self.payload())
        changed = self.update(items=[{'description': 'Replacement', 'quantity': '2', 'unit_price': '100'}])
        self.assertEqual(changed.quote.total, Decimal('222.00'))
        self.assertEqual(changed.items[0].line_total, Decimal('200.00'))
        self.assertFalse({i.id for i in changed.items} & {i.id for i in self.created.items})
        self.assertEqual(len(self.loaded().items), 1)
        untouched = get_quote_for_user(self.connection, user_id=self.owner.id, quote_id=other.quote.id)
        self.assertEqual(untouched.quote, other.quote)
        self.assertEqual(set(i.id for i in untouched.items), set(i.id for i in other.items))

    def test_nullable_fields_empty_patch_and_owned_replacement_client(self):
        original = self.loaded()
        self.assertEqual(self.update().quote, original.quote)
        replacement = self.connection.execute(
            "INSERT INTO clients (user_id, name) VALUES (%s, 'Replacement') RETURNING id", (self.owner.id,),
        ).fetchone()[0]
        changed = self.update(client_id=replacement, notes=None, terms=None, expiry_date=None, currency='USD')
        self.assertEqual(changed.quote.client_id, replacement)
        self.assertEqual(changed.quote.currency, 'USD')
        self.assertEqual((changed.quote.notes, changed.quote.terms, changed.quote.expiry_date), (None, None, None))

    def test_merged_dates_discount_and_foreign_client_fail_without_writes(self):
        original = self.loaded()
        other = create_user(self.connection, name='Other', email='other@example.com', password='test-password')
        foreign_client = self.connection.execute(
            "INSERT INTO clients (user_id, name) VALUES (%s, 'Foreign') RETURNING id", (other.id,),
        ).fetchone()[0]
        for changes, code in [({'issue_date': '2026-10-01'}, 'VALIDATION_ERROR'),
                              ({'discount_type': 'NONE'}, 'VALIDATION_ERROR'),
                              ({'discount_type': 'PERCENTAGE', 'discount_value': '101'}, 'VALIDATION_ERROR'),
                              ({'discount_value': '999'}, 'INVALID_DISCOUNT'),
                              ({'client_id': foreign_client}, 'CLIENT_NOT_FOUND'),
                              ({'client_id': uuid4()}, 'CLIENT_NOT_FOUND')]:
            with self.subTest(changes=changes), self.assertRaises(DomainError) as error:
                self.update(**changes)
            self.assertEqual(error.exception.code, code)
            self.assertEqual(self.loaded(), original)

    def test_all_non_draft_statuses_and_invoice_link_block_edits(self):
        for status in QuoteStatus:
            if status == QuoteStatus.DRAFT:
                continue
            self.connection.execute('UPDATE quotes SET status = %s WHERE id = %s', (status.value, self.quote_id))
            original = self.loaded()
            for changes in ({'notes': 'Changed'}, {}):
                with self.subTest(status=status), self.assertRaises(DomainError) as error:
                    self.update(**changes)
                self.assertEqual(error.exception.code, 'INVALID_QUOTE_STATUS')
                self.assertEqual(self.loaded(), original)
        self.connection.execute("UPDATE quotes SET status = 'DRAFT' WHERE id = %s", (self.quote_id,))
        self.link_invoice()
        with self.assertRaises(DomainError):
            self.update(notes='Changed')

    def test_foreign_and_missing_quotes_share_not_found(self):
        for user_id, quote_id in ((uuid4(), self.quote_id), (self.owner.id, uuid4())):
            with self.assertRaises(DomainError) as error:
                update_quote(self.connection, user_id=user_id, quote_id=quote_id, payload=QuotePatch(notes='x'))
            self.assertEqual((error.exception.code, error.exception.status_code), ('QUOTE_NOT_FOUND', 404))

    def test_later_item_failure_and_outer_rollback_restore_everything(self):
        original = self.loaded()
        self.connection.execute('''CREATE FUNCTION reject_update_item() RETURNS TRIGGER LANGUAGE plpgsql AS $$
            BEGIN
                IF NEW.description = 'Fail' THEN
                    RAISE EXCEPTION 'Test failure' USING ERRCODE = '23514';
                END IF;
                RETURN NEW;
            END; $$;
            CREATE TRIGGER reject_update_item BEFORE INSERT ON quote_items
            FOR EACH ROW EXECUTE FUNCTION reject_update_item();''')
        with self.assertRaises(errors.CheckViolation):
            self.update(notes='Changed', items=[
                {'description': 'Good', 'quantity': '1', 'unit_price': '100'},
                {'description': 'Fail', 'quantity': '1', 'unit_price': '100'},
            ])
        self.assertEqual(self.loaded(), original)
        with self.assertRaisesRegex(RuntimeError, 'abort'):
            with self.connection.transaction():
                self.update(notes='Changed')
                raise RuntimeError('abort')
        self.assertEqual(self.loaded(), original)

    def test_concurrent_partial_edits_preserve_both_changes(self):
        barrier = Barrier(2)

        def update(changes):
            with connect_database(self.settings, test=True) as connection:
                connection.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(self.schema)))
                connection.execute("SET statement_timeout = '10s'")
                barrier.wait(timeout=10)
                return update_quote(connection, user_id=self.owner.id, quote_id=self.quote_id,
                                    payload=QuotePatch(**changes))

        with ThreadPoolExecutor(max_workers=2) as executor:
            list(executor.map(update, [{'notes': 'Concurrent note'}, {'tax_rate': '10'}]))
        saved = self.loaded().quote
        self.assertEqual(saved.notes, 'Concurrent note')
        self.assertEqual(saved.total, Decimal('155'))
