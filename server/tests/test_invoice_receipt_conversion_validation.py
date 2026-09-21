import unittest
from uuid import UUID, uuid4

from app.common.errors import DomainError
from app.conversions.invoice_receipt import validate_invoice_conversion_eligibility
from app.invoices.models import InvoiceStatus
from tests import test_invoice_endpoint


class InvoiceReceiptConversionValidationTests(unittest.TestCase):
    setUpClass = classmethod(test_invoice_endpoint.InvoiceEndpointTests.setUpClass.__func__)
    setUp = test_invoice_endpoint.InvoiceEndpointTests.setUp
    drop_test_schema = test_invoice_endpoint.InvoiceEndpointTests.drop_test_schema
    login = test_invoice_endpoint.InvoiceEndpointTests.login
    payload = test_invoice_endpoint.InvoiceEndpointTests.payload
    post = test_invoice_endpoint.InvoiceEndpointTests.post

    def setUp(self):
        test_invoice_endpoint.InvoiceEndpointTests.setUp(self)
        self.invoice = self.post(self.payload()).json()['data']
        self.invoice_id = UUID(self.invoice['id'])

    def test_owned_non_cancelled_invoices_are_eligible(self):
        for status in (InvoiceStatus.DRAFT, InvoiceStatus.SENT, InvoiceStatus.PAID, InvoiceStatus.OVERDUE):
            self.connection.execute('UPDATE invoices SET status = %s WHERE id = %s',
                                    (status.value, self.invoice_id))
            with self.subTest(status=status):
                loaded = validate_invoice_conversion_eligibility(
                    self.connection, user_id=UUID(self.user_id), invoice_id=self.invoice_id,
                )
                self.assertEqual(loaded.invoice.id, self.invoice_id)

    def test_cancelled_invoice_is_rejected(self):
        self.connection.execute('UPDATE invoices SET status = %s WHERE id = %s',
                                (InvoiceStatus.CANCELLED.value, self.invoice_id))
        with self.assertRaises(DomainError) as error:
            validate_invoice_conversion_eligibility(
                self.connection, user_id=UUID(self.user_id), invoice_id=self.invoice_id,
            )
        self.assertEqual((error.exception.code, error.exception.status_code), ('INVALID_INVOICE_STATUS', 409))

    def test_foreign_and_missing_invoices_are_not_found(self):
        for user_id, invoice_id in ((uuid4(), self.invoice_id), (UUID(self.user_id), uuid4())):
            with self.subTest(user_id=user_id, invoice_id=invoice_id), self.assertRaises(DomainError) as error:
                validate_invoice_conversion_eligibility(
                    self.connection, user_id=user_id, invoice_id=invoice_id,
                )
            self.assertEqual((error.exception.code, error.exception.status_code), ('INVOICE_NOT_FOUND', 404))
