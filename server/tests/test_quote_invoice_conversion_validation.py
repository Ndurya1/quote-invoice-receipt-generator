import unittest
from uuid import UUID, uuid4

from app.common.errors import DomainError
from app.conversions.quote_invoice import validate_quote_conversion_eligibility
from app.quotes.models import QuoteStatus
from tests import test_quote_endpoint


class QuoteInvoiceConversionValidationTests(unittest.TestCase):
    setUpClass = classmethod(test_quote_endpoint.QuoteEndpointTests.setUpClass.__func__)
    setUp = test_quote_endpoint.QuoteEndpointTests.setUp
    drop_test_schema = test_quote_endpoint.QuoteEndpointTests.drop_test_schema
    login = test_quote_endpoint.QuoteEndpointTests.login
    payload = test_quote_endpoint.QuoteEndpointTests.payload
    post = test_quote_endpoint.QuoteEndpointTests.post

    def setUp(self):
        test_quote_endpoint.QuoteEndpointTests.setUp(self)
        self.quote = self.post(self.payload()).json()['data']
        self.quote_id = UUID(self.quote['id'])

    def test_only_owned_accepted_unlinked_quote_is_eligible(self):
        self.connection.execute('UPDATE quotes SET status = %s WHERE id = %s',
                                (QuoteStatus.ACCEPTED.value, self.quote_id))
        loaded = validate_quote_conversion_eligibility(
            self.connection, user_id=UUID(self.user_id), quote_id=self.quote_id,
        )
        self.assertEqual(loaded.quote.id, self.quote_id)
        for status in (QuoteStatus.DRAFT, QuoteStatus.SENT, QuoteStatus.REJECTED,
                       QuoteStatus.EXPIRED, QuoteStatus.CONVERTED):
            self.connection.execute('UPDATE quotes SET status = %s WHERE id = %s',
                                    (status.value, self.quote_id))
            with self.subTest(status=status), self.assertRaises(DomainError) as error:
                validate_quote_conversion_eligibility(
                    self.connection, user_id=UUID(self.user_id), quote_id=self.quote_id,
                )
            self.assertEqual(error.exception.code, 'INVALID_QUOTE_STATUS')

    def test_foreign_and_missing_quotes_are_not_found(self):
        for user_id, quote_id in ((uuid4(), self.quote_id), (UUID(self.user_id), uuid4())):
            with self.subTest(user_id=user_id, quote_id=quote_id), self.assertRaises(DomainError) as error:
                validate_quote_conversion_eligibility(
                    self.connection, user_id=user_id, quote_id=quote_id,
                )
            self.assertEqual((error.exception.code, error.exception.status_code), ('QUOTE_NOT_FOUND', 404))

    def test_existing_source_invoice_wins_as_already_converted(self):
        self.connection.execute('UPDATE quotes SET status = %s WHERE id = %s',
                                (QuoteStatus.ACCEPTED.value, self.quote_id))
        self.connection.execute(
            '''INSERT INTO invoices (user_id, client_id, source_quote_id, invoice_number,
               issue_date, currency, subtotal, total)
               VALUES (%s, %s, %s, 'INV-0001', '2026-09-15', 'KES', 100, 100)''',
            (UUID(self.user_id), UUID(self.client_id), self.quote_id),
        )
        with self.assertRaises(DomainError) as error:
            validate_quote_conversion_eligibility(
                self.connection, user_id=UUID(self.user_id), quote_id=self.quote_id,
            )
        self.assertEqual((error.exception.code, error.exception.status_code), ('QUOTE_ALREADY_CONVERTED', 409))
