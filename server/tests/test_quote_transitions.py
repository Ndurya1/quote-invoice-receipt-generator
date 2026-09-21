import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID, uuid4

from psycopg import sql

from app.common.database import connect_database
from app.common.errors import DomainError
from app.quotes.models import QuoteStatus
from app.quotes.service import transition_quote, validate_quote_transition
from tests import test_quote_patch


class QuoteTransitionRuleTests(unittest.TestCase):
    def test_valid_transitions(self):
        for current, target in [('DRAFT', 'SENT'), ('DRAFT', 'ACCEPTED'),
                                ('SENT', 'ACCEPTED'), ('SENT', 'REJECTED'),
                                ('SENT', 'EXPIRED'), ('ACCEPTED', 'CONVERTED')]:
            with self.subTest(current=current, target=target):
                validate_quote_transition(QuoteStatus(current), QuoteStatus(target))

    def test_invalid_and_repeated_transitions(self):
        for current, target in [('DRAFT', 'REJECTED'), ('DRAFT', 'CONVERTED'),
                                ('SENT', 'SENT'), ('CONVERTED', 'ACCEPTED')]:
            with self.subTest(current=current, target=target), self.assertRaises(DomainError) as error:
                validate_quote_transition(QuoteStatus(current), QuoteStatus(target))
            self.assertEqual(error.exception.code, 'INVALID_QUOTE_STATUS')
            self.assertEqual(error.exception.status_code, 409)


class QuoteTransitionTests(unittest.TestCase):
    setUpClass = classmethod(test_quote_patch.QuotePatchTests.setUpClass.__func__)
    setUp = test_quote_patch.QuotePatchTests.setUp
    drop_test_schema = test_quote_patch.QuotePatchTests.drop_test_schema
    login = test_quote_patch.QuotePatchTests.login
    payload = test_quote_patch.QuotePatchTests.payload
    post = test_quote_patch.QuotePatchTests.post
    get = test_quote_patch.QuotePatchTests.get

    def transition(self, target, **changes):
        return transition_quote(self.connection, **{
            'user_id': UUID(self.user_id), 'quote_id': UUID(self.quote['id']),
            'target': QuoteStatus(target), **changes,
        })

    def test_transition_changes_only_status_and_updated_timestamp(self):
        result = self.transition('SENT')
        saved = self.get()
        self.assertEqual(saved['status'], 'SENT')
        self.assertGreater(saved['updated_at'], self.quote['updated_at'])
        self.assertEqual(str(result.quote.id), saved['id'])
        for field in self.quote.keys() - {'status', 'updated_at'}:
            self.assertEqual(saved[field], self.quote[field], field)
        with self.assertRaises(DomainError):
            self.transition('SENT')
        self.assertEqual(self.get(), saved)

    def test_foreign_and_missing_quotes_are_not_found(self):
        for changes in ({'user_id': uuid4()}, {'quote_id': uuid4()}):
            with self.subTest(changes=changes), self.assertRaises(DomainError) as error:
                self.transition('SENT', **changes)
            self.assertEqual(error.exception.code, 'QUOTE_NOT_FOUND')
            self.assertEqual(error.exception.status_code, 404)
        self.assertEqual(self.get(), self.quote)

    def test_outer_failure_rolls_back_transition(self):
        with self.assertRaisesRegex(RuntimeError, 'abort'):
            with self.connection.transaction():
                self.transition('ACCEPTED')
                raise RuntimeError('abort')
        self.assertEqual(self.get(), self.quote)

    def test_conversion_without_link_is_rejected(self):
        self.transition('ACCEPTED')
        before = self.get()
        with self.assertRaises(DomainError) as error:
            self.transition('CONVERTED')
        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(self.get(), before)

    def link_invoice(self):
        return self.connection.execute(
            '''INSERT INTO invoices (user_id, client_id, source_quote_id, invoice_number,
               issue_date, currency, subtotal, total)
               VALUES (%s, %s, %s, 'INV-0001', '2026-09-15', 'KES', 100, 106) RETURNING id''',
            (UUID(self.user_id), UUID(self.client_id), UUID(self.quote['id'])),
        ).fetchone()[0]

    def test_every_status_pair_obeys_matrix_and_preserves_document(self):
        allowed = {('DRAFT', 'SENT'), ('DRAFT', 'ACCEPTED'), ('SENT', 'ACCEPTED'),
                   ('SENT', 'REJECTED'), ('SENT', 'EXPIRED'), ('ACCEPTED', 'CONVERTED')}
        for current in QuoteStatus:
            for target in QuoteStatus:
                with self.subTest(current=current, target=target):
                    self.connection.execute('UPDATE quotes SET status = %s WHERE id = %s',
                                            (current.value, UUID(self.quote['id'])))
                    before = self.get()
                    if (current, target) in allowed:
                        if target == QuoteStatus.CONVERTED:
                            self.link_invoice()
                        result = self.transition(target)
                        saved = self.get()
                        self.assertEqual(result.quote.status, target)
                        self.assertEqual(saved['status'], target)
                        for field in before.keys() - {'status', 'updated_at'}:
                            self.assertEqual(saved[field], before[field], field)
                    else:
                        with self.assertRaises(DomainError) as error:
                            self.transition(target)
                        self.assertEqual(error.exception.code, 'INVALID_QUOTE_STATUS')
                        self.assertEqual(error.exception.status_code, 409)
                        self.assertEqual(self.get(), before)

    def test_conversion_transition_joins_invoice_transaction(self):
        self.transition('ACCEPTED')
        before = self.get()
        with self.assertRaisesRegex(RuntimeError, 'abort'):
            with self.connection.transaction():
                self.link_invoice()
                self.transition('CONVERTED')
                raise RuntimeError('abort')
        self.assertEqual(self.get(), before)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM invoices').fetchone()[0], 0)
        with self.connection.transaction():
            invoice_id = self.link_invoice()
            self.transition('CONVERTED')
        self.assertEqual(self.get()['status'], 'CONVERTED')
        self.assertEqual(self.connection.execute('SELECT source_quote_id FROM invoices WHERE id = %s',
                                                (invoice_id,)).fetchone()[0], UUID(self.quote['id']))

    def test_competing_transitions_validate_after_lock(self):
        for initial, targets in [('DRAFT', ('SENT', 'SENT')), ('SENT', ('ACCEPTED', 'REJECTED'))]:
            with self.subTest(initial=initial, targets=targets):
                self.connection.execute('UPDATE quotes SET status = %s WHERE id = %s',
                                        (initial, UUID(self.quote['id'])))
                barrier = Barrier(2)

                def change(target):
                    with connect_database(self.database_settings, test=True) as connection:
                        connection.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(self.schema)))
                        connection.execute("SET statement_timeout = '10s'")
                        barrier.wait(timeout=10)
                        try:
                            result = transition_quote(connection, user_id=UUID(self.user_id),
                                                      quote_id=UUID(self.quote['id']), target=QuoteStatus(target))
                            return 200, result.quote.status.value
                        except DomainError as exc:
                            return exc.status_code, exc.code

                with ThreadPoolExecutor(max_workers=2) as executor:
                    results = list(executor.map(change, targets))
                self.assertEqual(sorted(code for code, _ in results), [200, 409])
                winner = next(status for code, status in results if code == 200)
                self.assertEqual(self.get()['status'], winner)
                self.assertIn((409, 'INVALID_QUOTE_STATUS'), results)
                self.assertEqual(self.get()['items'], self.quote['items'])
