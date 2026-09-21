import unittest
from uuid import UUID, uuid4

from app.common.errors import DomainError
from app.invoices.models import InvoiceStatus
from app.invoices.service import create_invoice, transition_invoice, validate_invoice_transition
from tests import test_invoice_creation


class InvoiceTransitionRuleTests(unittest.TestCase):
    def test_explicit_policy(self):
        allowed = {
            (InvoiceStatus.DRAFT, InvoiceStatus.SENT),
            (InvoiceStatus.DRAFT, InvoiceStatus.CANCELLED),
            (InvoiceStatus.SENT, InvoiceStatus.PAID),
            (InvoiceStatus.SENT, InvoiceStatus.CANCELLED),
            (InvoiceStatus.OVERDUE, InvoiceStatus.PAID),
            (InvoiceStatus.OVERDUE, InvoiceStatus.CANCELLED),
        }
        for current in InvoiceStatus:
            for target in InvoiceStatus:
                with self.subTest(current=current, target=target):
                    if (current, target) in allowed:
                        validate_invoice_transition(current, target)
                    else:
                        with self.assertRaises(DomainError) as error:
                            validate_invoice_transition(current, target)
                        self.assertEqual(error.exception.code, 'INVALID_INVOICE_STATUS')


class InvoiceTransitionTests(unittest.TestCase):
    setUpClass = classmethod(test_invoice_creation.InvoiceCreationTests.setUpClass.__func__)
    drop_test_schema = test_invoice_creation.InvoiceCreationTests.drop_test_schema
    payload = test_invoice_creation.InvoiceCreationTests.payload

    def setUp(self):
        test_invoice_creation.InvoiceCreationTests.setUp(self)
        self.created = create_invoice(self.connection, user_id=self.owner.id, payload=self.payload())
        self.invoice_id = self.created.invoice.id

    def transition(self, target, user_id=None):
        return transition_invoice(self.connection, user_id=user_id or self.owner.id,
                                  invoice_id=self.invoice_id, target=target)

    def test_allowed_transitions_change_only_status_and_updated_at(self):
        sent = self.transition(InvoiceStatus.SENT)
        self.assertEqual(sent.invoice.status, InvoiceStatus.SENT)
        self.assertEqual({item.id for item in sent.items}, {item.id for item in self.created.items})
        paid = self.transition(InvoiceStatus.PAID)
        self.assertEqual(paid.invoice.status, InvoiceStatus.PAID)
        self.assertEqual(paid.invoice.invoice_number, self.created.invoice.invoice_number)
        self.assertGreater(paid.invoice.updated_at, self.created.invoice.updated_at)

    def test_cancel_draft_and_overdue_paths(self):
        cancelled = self.transition(InvoiceStatus.CANCELLED)
        self.assertEqual(cancelled.invoice.status, InvoiceStatus.CANCELLED)
        self.connection.execute('UPDATE invoices SET status = %s WHERE id = %s',
                                (InvoiceStatus.OVERDUE.value, self.invoice_id))
        paid = self.transition(InvoiceStatus.PAID)
        self.assertEqual(paid.invoice.status, InvoiceStatus.PAID)

    def test_invalid_repeated_missing_and_foreign_transitions(self):
        self.transition(InvoiceStatus.SENT)
        for target in (InvoiceStatus.DRAFT, InvoiceStatus.SENT):
            with self.subTest(target=target), self.assertRaises(DomainError) as error:
                self.transition(target)
            self.assertEqual(error.exception.code, 'INVALID_INVOICE_STATUS')
        with self.assertRaises(DomainError) as error:
            self.transition(InvoiceStatus.PAID, user_id=uuid4())
        self.assertEqual((error.exception.code, error.exception.status_code), ('INVOICE_NOT_FOUND', 404))
