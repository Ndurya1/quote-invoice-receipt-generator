import unittest
from uuid import UUID, uuid4

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
